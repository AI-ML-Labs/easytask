import itertools
import threading
import time
from collections import deque
from typing import Callable, Dict, Union

from .log import get_log_level
from .ThreadLocalStorage import ThreadLocalStorage


class Thread:
    _by_ident : Dict[int, 'Thread'] = {}
    _unnamed_counter = itertools.count()

    def __init__(self, name : str = None, **kwargs):
        """
        Create easytask.Thread
        """

        self._name = name if name is not None else f'Unnamed #{next(Thread._unnamed_counter)}'
        self._created = create = not kwargs.get('register', False)
        self._lock = threading.Lock()
        self._active_tasks_ev = threading.Event()
        self._active_tasks = deque()

        self._finalizing_ev = threading.Event()
        self._finalized_ev = threading.Event()

        self._ident = None
        if create:
            if get_log_level() >= 2:
                print(f"{('Creating'):12} {self}")

            self._t = threading.Thread(target=self._thread_func, daemon=True)
            self._t.start()
        else:
            self._t = None
            self._initialize_thread(threading.get_ident())

    def finalize(self):
        """
        Finalize the Thread.
        All active tasks assigned to the Thread will be cancelled.
        New tasks which are switching to finalized thread will be cancelled immediately.
        """
        self._lock.acquire()

        if not self._finalizing_ev.is_set():
            self._finalizing_ev.set()
            self._lock.release()

            if get_log_level() >= 2:
                print(f"{('Finalizing'):12} {self}")

            if self.is_created():
                if threading.get_ident() != self._ident:
                    self._finalized_ev.wait()

            else:
                if threading.get_ident() != self._ident:
                    raise Exception('non-created Thread.finalize() must be called from the same OS thread.')
                self._finalize_thread()
        else:
            # Already finalizing
            self._lock.release()
            self._finalized_ev.wait()


    def assert_current_thread(self):
        if threading.get_ident() != self._ident:
            raise Exception('Wrong current thread.')

    def is_created(self) -> bool:
        """whether Thread is created or registered"""
        return self._created

    def get_active_tasks(self):
        active_tasks = self._active_tasks
        return deque(active_tasks) if active_tasks is not None else deque()

    def get_active_tasks_count(self) -> int:
        active_tasks = self._active_tasks
        return len(active_tasks) if active_tasks is not None else 0

    def get_ident(self) -> int: return self._ident
    def get_name(self): return self._name
    def get_tls(self) -> ThreadLocalStorage: return ThreadLocalStorage._by_ident[self._ident]
    def set_name(self, name : str): self._name = name

    def execute_tasks_once(self):
        """
        Execute active tasks once.
        """
        if threading.get_ident() != self._ident:
            raise Exception('execute_tasks_once must be called from OS thread where the Thread was created/registered.')

        for task in self._fetch_active_tasks():
            task._exec()

    def execute_tasks_loop(self, condition : Callable[[], bool] = None):
        """
        Execute active tasks in loop until Thread finalize or condition() is True

            condition(None)     Callable    called every tick once to check if exit from loop is needed.
        """
        time_since_last_sleep = time.perf_counter()

        while not self._finalizing_ev.is_set():
            if condition is not None and condition():
                break

            time_exec_start = time.perf_counter()

            self.execute_tasks_once()

            time_to_sleep = 0.0
            if time.perf_counter() - time_since_last_sleep >= 1.0:
                time_to_sleep = 0.005

            time_exec = time.perf_counter() - time_exec_start
            if time_exec < 0.005:
                time_to_sleep = max(time_to_sleep, 0.005-time_exec)

            if time_to_sleep != 0.0:
                time.sleep(time_to_sleep)
                time_since_last_sleep = time.perf_counter()


    def _thread_func(self):
        self._initialize_thread(threading.get_ident())
        self.execute_tasks_loop()
        self._finalize_thread()

    def _initialize_thread(self, ident):
        if ident in Thread._by_ident:
            raise Exception(f'Thread {ident} is already registered.')

        self._ident = ident
        Thread._by_ident[ident] = self
        ThreadLocalStorage._by_ident[ident] = ThreadLocalStorage()

        if get_log_level() >= 2:
            print(f"{('Initialized'):12} {self}")

    def _finalize_thread(self):
        # Cancel remaining tasks registered in thread.
        for task in self._fetch_active_tasks(finalize=True):
            task.cancel()

        Thread._by_ident.pop(self._ident)
        ThreadLocalStorage._by_ident.pop(self._ident)
        self._finalized_ev.set()

        if get_log_level() >= 2:
            print(f"{('Finalized'):12} {self}")

    def _add_task(self, task) -> bool:
        with self._lock:
            if self._active_tasks is None:
                return False
            self._active_tasks.append(task)
            self._active_tasks_ev.set()
            return True

    def _fetch_active_tasks(self, finalize=False):
        if self._active_tasks_ev.is_set() or finalize:
            with self._lock:
                tasks, self._active_tasks = self._active_tasks, (None if finalize else deque())
                self._active_tasks_ev.clear()
            return tasks
        return ()

    def get_printable_info(self, include_tasks=False) -> str:
        s = '[Thread-S]' if self.is_created() else '[Thread-R]'

        s += f'[{self._name}]'
        s += f'[{self._ident}]' if self._ident is not None else '[...]'

        if self._finalized_ev.is_set():
            s += '[FINALIZED]'

        if include_tasks:
            with self._lock:
                if self._active_tasks is not None:
                    active_tasks = tuple( task for task in self._active_tasks if not task.is_done() )
                    if len(active_tasks) != 0:
                        s += '\nThread active tasks:'
                        for i, task in enumerate(active_tasks):
                            s += f'\n[{i}]: {task}'
        return s

    def __repr__(self): return self.__str__()
    def __str__(self): return self.get_printable_info()


def create_thread(name : str = None) -> Thread:
    return Thread(name=name, create=True,  check=1)

def get_current_thread() -> Union[Thread, None]:
    """get current easytask.Thread or register new"""
    thread = Thread._by_ident.get(threading.get_ident(), None)
    if thread is None:
        thread = Thread(register=True)
    return thread
