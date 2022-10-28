from .Thread import Thread
from .Task import Task

def print_debug_info():
    """
    Prints active Threads and Tasks
    """
    s = ''

    active_tasks = set(Task._active_tasks)

    if len(Thread._by_ident) != 0:
        s += '\nUnfinalized threads: '

        for i, thread in enumerate(Thread._by_ident.values()):

            for task in thread.get_active_tasks():
                if task in active_tasks:
                    active_tasks.remove(task)

            s += f'\n[{i}]: {thread.get_printable_info(include_tasks=True)}'

    if len(active_tasks) != 0:
        s += '\nTasks not attached to threads: '
        for i, task in enumerate(active_tasks):
            s += f'\n[{i}]: {task}'

    if len(s) != 0:
        s = '\neasytask debug info:' + s + '\n'
        print(s)