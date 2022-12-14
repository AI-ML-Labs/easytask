from collections import deque
from typing import Dict


class ThreadLocalStorage:
    _by_ident : Dict[int, 'ThreadLocalStorage'] = {}

    def __init__(self):
        self._ts_scope = deque()        # Taskset scope
        self._task_exec_stack = deque() # Stack of Tasks execution
