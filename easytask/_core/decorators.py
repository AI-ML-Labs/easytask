from types import GeneratorType

from .Task import Task
from .TaskExecutor import TaskExecutor


def taskmethod():    
    """decorator.

    Method always returns Task object. You should annotate method with return type -> easytask.Task[ return_type ]

    available yields inside taskmethod : easytask.yield_*

        return value will finish the Task with success state and result value
        
    decorator args
    
    If your taskmethod use some outter resources,
    and you want to finalize them on task done by any reason (success, cancel),
    wrap with 
    ```
        try:
            
            yield easytask.yield_success()
            # or 
            yield easytask.yield_cancel()
            
        except ETaskDone:
            ...
        
        and do resource finalization after exception.
    ```
    """
    def declaration_wrapper(method):

        def method_wrapper(*args, **kwargs):
            task = Task(name=f'{method.__qualname__}')
                        
            result = method(*args, **kwargs)
            if isinstance(result, GeneratorType):
                TaskExecutor(task, result)
            else:
                task.success(result)
            
            return task
            
        return method_wrapper
        
    return declaration_wrapper
