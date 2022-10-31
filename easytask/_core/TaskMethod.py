from types import GeneratorType

from .Task import Task
from .TaskExecutor import TaskExecutor

class TaskMethod:
    def __init__(self, method):
        self._method = method
        
    def get_method(self): return self._method
        
    def __call__(self, *args, **kwargs):
        task = Task(name=f'{self._method.__qualname__}')

        result = self._method(*args, **kwargs)
        if isinstance(result, GeneratorType):
            TaskExecutor(task, result)
        else:
            task.success(result)

        return task