from types import GeneratorType

from .Task import Task
from .TaskExecutor import TaskExecutor

def taskmethod():
    """decorator.

    Method always returns Task object. You should annotate method with return type -> easytask.Task[ return_type ]

    available yields inside taskmethod : easytask.yield_*
    """
    def declaration_wrapper(method):
        
        def easytask_method(*args, **kwargs):
            task = Task(name=f'{method.__qualname__}')

            result = method(*args, **kwargs)
            if isinstance(result, GeneratorType):
                TaskExecutor(task, result)
            else:
                task.success(result)

            return task
        
        easytask_method._wrapped_method = method
        
        return easytask_method
         
    return declaration_wrapper
