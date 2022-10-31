from .TaskMethod import TaskMethod

        
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
        return TaskMethod(method)
    return declaration_wrapper
