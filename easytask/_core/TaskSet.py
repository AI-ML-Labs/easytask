import threading
from collections import deque
from typing import Deque, Generic, TypeVar

from .log import get_log_level
from .Task import Task

T = TypeVar('T')

class TaskSet(Generic[T]):
    
    def __init__(self, name : str = None):
        """
        Provides a set of Tasks.

        Tasks can be registered/unregistered/cancelled/fetched in/from TaskSet from any thread safely.
        """
        self._name = name
        self._lock = threading.RLock()
        self._tasks = set()

    def finalize(self):
        """
        Finalize TaskSet. Cancel all tasks. 
        New Tasks that are added to TaskSet using yield will be automatically canceled.
        """
        if get_log_level() >= 2:
            print(f"{('Finalizing'):12} {self}")

        with self._lock:
            tasks, self._tasks = self._tasks, None

        for task in tasks:
            task.cancel()

    def count(self) -> int:
        tasks = self._tasks
        return 0 if tasks is None else len(tasks)

    def get_name(self) -> str: return self._name
    def is_empty(self): return len(self._tasks) == 0

    def cancel_all(self):
        """Cancel all current active tasks in TaskSet"""
        with self._lock:
            tasks, self._tasks = self._tasks, set()

        if len(tasks) != 0:
            if get_log_level() >= 2:
                print(f'Cancelling {len(tasks)} tasks in {self._name} TaskSet.')

        for task in tasks:
            task.cancel()

    
    def add(self, task : Task[T], remove_on_done=False) -> bool:
        """add Task, returns True if success"""
        with task._lock:
            if task._state == Task._State.ACTIVE:
                with self._lock:
                    tasks = self._tasks
                    if tasks is not None:
                        if task not in tasks:
                            tasks.add(task)
                            
                        if remove_on_done:
                            task.call_on_done(self.remove)
                            
                        return True
        return False
        
    def remove(self, task : Task[T]):
        """"""
        with task._lock:
            with self._lock:
                tasks = self._tasks
                if tasks is not None and task in tasks:
                    tasks.remove(task)
                
        
    def fetch(self, done=None, success=None) -> Deque[Task[T]]:
        """
        fetch Task's from TaskSet with specific conditions

            done(None)  None : don't check
                        True : task is done
                        False : task is not done

            success(None)  None : don't check
                           True : task is success
                           False : task is not success

        if both args None, fetches all tasks.
        """
        out_tasks = deque()
        
        with self._lock:
            for task in self._tasks:
                if  (done    is None or done    == task.is_done()) and \
                    (success is None or success == task.is_succeeded()):
                        out_tasks.append(task)

        for task in out_tasks:
            self.remove(task)

        return out_tasks

    def __repr__(self): return self.__str__()
    def __str__(self):
        s = '[TaskSet]'
        if self._name is not None:
            s += f'[{self._name}]'
        tasks = self._tasks
        if tasks is not None:
            s += f'[{len(self._tasks)} tasks]'
        else:
            s += '[FINALIZED]'
        return s


