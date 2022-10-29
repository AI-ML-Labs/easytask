import traceback
from types import GeneratorType

from .exceptions import ETaskDone
from .log import get_log_level
from .Task import Task
from .Thread import get_current_thread
from .yields import (yield_add_to, yield_cancel, yield_propagate, yield_sleep,
                     yield_sleep_tick, yield_success, yield_switch_thread,
                     yield_wait)


class TaskExecutor:

    def __init__(self, task : Task, gen : GeneratorType):
        self._task = task
        self._gen = gen

        self._continue_execution = True
        self._current_thread = get_current_thread()
        self._send_param = None
        self._yield_value = None

        task._executor = self
        task.call_on_done(self._on_task_done)

        self.exec()

    def _on_task_done(self, task : Task):
        if self._gen is not None:
            try:
                self._gen.throw( ETaskDone(self._task) )
            except Exception as e:
                ...
            self._gen.close()
            self._gen = None

    def exec(self):
        task = self._task

        with task._lock:
            if task._state != Task._State.ACTIVE:
                return

            current_thread = get_current_thread()
            tls = current_thread.get_tls()

            # add Task to ThreadLocalStorage Task execution stack
            tls._task_exec_stack.append(task)

            while True:

                if self._continue_execution:
                    try:
                        self._yield_value = self._gen.send(self._send_param) if self._send_param is not None else next(self._gen)
                        self._send_param = None
                    except StopIteration as e:
                        # Method returns value directly
                        task.success(e.value)
                        break
                    except Exception as e:
                        # Unhandled exception
                        if get_log_level() >= 1:
                            print(f'Unhandled exception {e} occured during execution of task {task}. Traceback:\n{traceback.format_exc()}')
                        task.cancel(exception=e)
                        break

                # Process yield value
                yield_func = TaskExecutor._yield_to_func.get(self._yield_value.__class__, None)
                if yield_func is None:
                    print(f'{task} Unknown type of yield value: {self._yield_value}')
                    task.cancel()
                    break

                yield_func(self, self._yield_value)

                if task.is_done():
                    break
                elif not self._continue_execution:
                    # Task still active, assign to Thread.
                    if self._current_thread is not None and \
                       not self._current_thread._add_task(task):
                        # Unable to add Task to Thread, finalized or other reason, cancel without exception
                        task.cancel()
                    break

            # remove Task from ThreadLocalStorage Task execution stack
            tls._task_exec_stack.pop()


    def _on_yield_add_to(self, yield_value : yield_add_to):
        task = self._task

        if yield_value._ts.add(task, remove_on_done=True):
            self._continue_execution = True
        else:
            task.cancel()
            self._continue_execution = False

    def _on_yield_switch_thread(self, yield_value : yield_switch_thread):
        if self._current_thread.get_ident() == yield_value._thread.get_ident():
            self._continue_execution = True
        else:
            self._continue_execution = False
            self._current_thread = yield_value._thread

    def _on_yield_wait(self, yield_value : yield_wait):
        self._continue_execution = yield_value.is_done()

    def _on_yield_success(self, yield_value : yield_success):
        self._task.success(result=yield_value._result)
        self._continue_execution = False

    def _on_yield_cancel(self, yield_value : yield_cancel):
        self._task.cancel(exception=yield_value._exception)
        self._continue_execution = False

    def _on_yield_propagate(self, yield_value : yield_propagate):
        self._task.propagate(yield_value._task)
        self._continue_execution = False
        self._current_thread = None

    def _on_yield_sleep_tick(self, yield_value : yield_sleep_tick):
        if yield_value.remain_ticks == 0:
            self._continue_execution = True
        else:
            self._continue_execution = False
            yield_value.remain_ticks -= 1

    def _on_yield_sleep(self, yield_value : yield_sleep):
        if yield_value._sec == 0 or yield_value.is_done():
            self._continue_execution = True
        else:
            self._continue_execution = False


    _yield_to_func = {
            yield_add_to : _on_yield_add_to,
            yield_switch_thread : _on_yield_switch_thread,
            yield_wait : _on_yield_wait,
            yield_success : _on_yield_success,
            yield_cancel : _on_yield_cancel,
            yield_propagate : _on_yield_propagate,
            yield_sleep_tick : _on_yield_sleep_tick,
            yield_sleep : _on_yield_sleep,
        }
