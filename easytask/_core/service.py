from .Thread import Thread
from .Task import Task

def clear():
    """
    Finalize all Threads, cancel all tasks, and clear resources.
    """
    while True:
        threads = list(Thread._by_ident.values())
        if len(threads) == 0:
            break
        thread = threads[0]
        thread.finalize()
    
    while len(Task._active_tasks) != 0:
        for task in tuple(Task._active_tasks):
            task.cancel()
    