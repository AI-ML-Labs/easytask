import threading
from datetime import datetime
from typing import Iterable, Set, Union

from .Task import Task
from .TaskSet import TaskSet
from .Thread import Thread

class yield_lock:
    def __init__(self, lock : Union[threading.Lock, threading.RLock]):
        """Acquire python threading.Lock object. Like any task, waiting Lock will not block the Thread."""
        self._lock = lock

class yield_unlock:
    def __init__(self, lock : Union[threading.Lock, threading.RLock]):
        """Release python threading.Lock object."""
        self._lock = lock

class yield_add_to:
    def __init__(self, ts : TaskSet, remove_parent = True):
        """
        Add current Task to TaskSet.
        If TaskSet is finalized, current Task will be cancelled without exception.

            remove_parent(True)     parent from Task will be removed.
                                    It's mean when parent Task is cancelled, this Task will continue work.
        """
        self._ts = ts
        self._remove_parent = remove_parent

class yield_success:
    def __init__(self, result = None):
        """
        Done task execution and set success result.
        Same as return value, but you have more freedom to return value from nested loops
        and do resource finalization when Task is done.
        """
        self._result = result

class yield_cancel:
    def __init__(self, exception : Exception = None):
        """Done task execution and mark this Task as cancelled with optional exception"""
        self._exception = exception

class yield_propagate:
    def __init__(self, task : Task):
        """Wait Task and returns it's result as result of this Task"""
        self._task = task

class yield_switch_thread:
    def __init__(self, thread : Thread):
        """
        Switch thread of this Task.
        If Task already in Thread, execution will continue immediately.
        If Thread is finalized, Task will be cancelled.
        """
        self._thread = thread

class yield_sleep:
    def __init__(self, sec : float):
        """
        Sleep execution of this Task.

        `yield_sleep(0)` will continue execution without interruption.

        Use `yield_sleep_tick()` to sleep minimal amount of time.
        """
        self._time = datetime.now().timestamp()
        self._sec = sec

    def is_done(self):
        return (datetime.now().timestamp() - self._time) >= self._sec

class yield_sleep_tick:
    def __init__(self):
        """Sleep single tick, i.e. minimum possible amount of time between two executions of Tasks"""
        self.remain_ticks = 1

class yield_wait:
    def __init__(self, task_or_list : Union[Task, Iterable[Task] ] ):
        """Stop execution until task_or_list will be entered to done state."""
        if not isinstance(task_or_list, Iterable):
            task_or_list = (task_or_list,)

        self._lock = threading.Lock()
        self._count = len(task_or_list)

        for task in task_or_list:
            task.call_on_done(self._on_task_done)

        self._task_list = task_or_list

    def _on_task_done(self, task):
        with self._lock:
            self._count -=1

    def is_done(self):
        return self._count == 0

class yield_cancel_all:
    def __init__(self, tasks : Set[Task]):
        """Cancel all Tasks in Set of Task"""
        if not isinstance(tasks, set):
            raise ValueError(f'{tasks} must be an instance of set.')
        self._tasks = tasks
