import threading


class Section:
    def __init__(self):
        """
        Section is syncronization primitive.
        Only single Task can enter Section, other tasks will wait while section will be freed to enter.
        """
        
        self._lock = threading.RLock()
        self._task = None
        
    def _try_enter(self, task) -> bool:
        with self._lock:
            if self._task is None:
                self._task = task
                
                with task._done_lock:
                    task._in_sections.add(self)
                
                return True
        return False
        
    def _leave(self, task):
        if self._task is task:
            
            with task._done_lock:
                task._in_sections.remove(self)
            
            self._task = None
            