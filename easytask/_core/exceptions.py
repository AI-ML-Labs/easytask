from .Task import Task

class ETaskDone(Exception):
    def __init__(self, task : Task):
        self._task = task

    def __str__(self): return f'ETaskDone of {self._task}'
    def __repr__(self): return self.__str__()

