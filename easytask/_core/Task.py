import threading
from collections import deque
from enum import Enum
from typing import Any, Callable, Generic, TypeVar, Union

from .log import get_log_level

T = TypeVar('T')

from .Thread import get_current_thread


class Task(Generic[T]):
    _active_tasks = set()

    class _State(Enum):
        ACTIVE = 0
        SUCCEEDED = 1
        CANCELLED = 2

    def __init__(self, name : str = None):
        self._name = name

        self._lock = threading.RLock()
        self._done_lock = threading.RLock()
        self._on_done_funcs = deque()      # accessed inside Task._done_lock only
        self._state = Task._State.ACTIVE
        self._executor = None
        self._in_locks = deque()
        self._parent : Task = None
        self._child_tasks = set()  # add - accessed inside Task._lock
                                   # remove - no lock

        Task._active_tasks.add(self)

        tls = get_current_thread().get_tls()

        if len(tls._task_exec_stack) != 0:
            # Task created inside execution of other Task in current thread
            # add to parent's child in order to be cancelled when parent is done.
            # Parent is removed when Task added to TaskSet assuming TaskSet acquires control of Task
            parent_task : Task = tls._task_exec_stack[-1]
            parent_task._child_tasks.add(self)
            self._parent = parent_task

        if get_log_level() >= 2:
            print(f"{('Starting'):12} {self}")

    def get_name(self) -> str: return self._name
    def is_done(self) -> bool:        return self._state in (Task._State.SUCCEEDED, Task._State.CANCELLED)
    def is_succeeded(self) -> bool:   return self._state == Task._State.SUCCEEDED

    def call_on_done(self, func : Callable[ ['Task'], None ]):
        """
        call func when Task is done.
        If Task is already done, func will be called immediately.
        """
        with self._done_lock:
            if self._state == Task._State.ACTIVE:
                self._on_done_funcs.append(func)
                return
        func(self)

    def wait(self):
        """
        Block execution and wait Task in current (or automatically registered) easytask.Thread

        raises Exception if calling wait() inside Task.
        """
        if get_current_task() != None:
            raise Exception('Unable to .wait() inside Task. Use yield easytask.wait(task)')

        get_current_thread().execute_tasks_loop(condition=self.is_done)
        return self

    def propagate(self, other_task : 'Task'):
        """
        result of `other_task` will be set as result of this Task on `other_task`'s done.
        """
        other_task.call_on_done (lambda done_task, task=self: Task._propagate_task_result(done_task, task) )

    def result(self) -> T:
        if self._state != Task._State.SUCCEEDED:
            raise Exception(f'{self} no result() for non-succeeded task.')
        return self._result

    def exception(self) -> Union[Exception, None]:
        if self._state != Task._State.CANCELLED:
            raise Exception(f'{self} no exception() for non-cancelled task.')
        return self._exception

    def cancel(self, exception : Exception = None):
        """
        Done task, stop its execution and set Task to cancelled state with optional Exception(default None).
        If it is already done, nothing will happen.
        """
        self._done(False, exception=exception)

    def success(self, result : Any = None):
        """
        Done task, stop its execution and set Task to done succeeded state optional result(default None).
        All tasks created during execution of this task will be cancelled.
        If it is already done, nothing will happen.
        """
        self._done(True, result)

    def _done(self, success : bool, result = None, exception = None):
        on_done_funcs = None
        with self._lock:
            with self._done_lock:
                if self._state == Task._State.ACTIVE:
                    child_tasks = tuple(self._child_tasks)

                    if get_log_level() >= 2:
                        print(f"{('Finishing'):12} {self} Child tasks:[{len(child_tasks)}]")

                    if success:
                        self._result = result
                        self._state = Task._State.SUCCEEDED
                    else:
                        self._exception = exception
                        self._state = Task._State.CANCELLED

                    for lock in self._in_locks:
                        lock.release()

                    for child_task in child_tasks:
                        child_task.cancel()

                    if self._parent is not None:
                        self._parent._child_tasks.remove(self)
                        self._parent = None

                    on_done_funcs, self._on_done_funcs = self._on_done_funcs, None
                    for func in on_done_funcs:
                        func(self)

                    Task._active_tasks.remove(self)

                    if get_log_level() >= 2:
                        print(f"{('Done'):12} {self}")

    def _exec(self):
        self._executor.exec()

    def __repr__(self): return self.__str__()
    def __str__(self):
        s = f'[Task][{self.get_name()}]'

        if self.is_done():
            if self.is_succeeded():
                s += f'[SUCCEEDED][Result: {type(self.result()).__name__}]'
            else:
                s += f'[CANCELLED]'
                exception = self.exception()
                if exception is not None:
                    s += f'[Exception:{exception}]'
        else:
            s += f'[ACTIVE]'

        return s

    @staticmethod
    def _propagate_task_result(from_task, to_task):
        if from_task.is_succeeded():
            to_task.success(from_task.result())
        else:
            to_task.cancel(exception=from_task.exception())

def get_current_task() -> Union[Task, None]:
    current_thread = get_current_thread()
    tls = current_thread.get_tls()
    if len(tls._task_exec_stack) != 0:
        return tls._task_exec_stack[-1]
    return None


