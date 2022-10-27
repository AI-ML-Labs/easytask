import random
import threading

from .debug import print_debug_info
from .decorators import taskmethod
from .exceptions import ETaskDone
from .log import get_log_level, set_log_level
from .Section import Section
from .service import clear
from .Task import Task, get_current_task
from .TaskSet import TaskSet
from .Thread import Thread, get_current_thread
from .yields import (yield_add_to, yield_cancel, yield_enter, yield_leave,
                     yield_propagate, yield_sleep, yield_sleep_tick,
                     yield_success, yield_switch_thread, yield_wait)


class easytask:
    # it is like global import easytask, but keep local import for test.py

    Task = Task
    Thread = Thread
    TaskSet = TaskSet
    Section = Section
    ETaskDone = ETaskDone

    get_current_thread = get_current_thread
    get_current_task = get_current_task
    print_debug_info = print_debug_info
    taskmethod = taskmethod

    yield_enter = yield_enter
    yield_leave = yield_leave
    yield_cancel = yield_cancel
    yield_propagate = yield_propagate
    yield_add_to = yield_add_to
    yield_sleep = yield_sleep
    yield_sleep_tick = yield_sleep_tick
    yield_success = yield_success
    yield_switch_thread = yield_switch_thread
    yield_wait = yield_wait

@easytask.taskmethod()
def simple_return_task() -> easytask.Task:
    return 1

def simple_return():
    t = simple_return_task().wait()
    if not t.is_succeeded() or t.result() != 1:
        return False
    return True

@easytask.taskmethod()
def branch_true_false_task(b) -> easytask.Task:
    yield easytask.yield_sleep_tick()

    if b:
        yield easytask.yield_success(1)
    else:
        yield easytask.yield_cancel()

def branch_true_1():
    t = branch_true_false_task(True).wait()
    return t.is_succeeded() and t.result() == 1

def branch_false_cancel():
    t = branch_true_false_task(False).wait()
    return not t.is_succeeded()

@easytask.taskmethod()
def sleep_1_task() -> easytask.Task:
    yield easytask.yield_sleep(1.0)
    return 1

def sleep_1():
    t = sleep_1_task().wait()
    return t.is_succeeded() and t.result() == 1

@easytask.taskmethod()
def propagate_task_1() -> easytask.Task:
    yield easytask.yield_sleep_tick()
    return 1

@easytask.taskmethod()
def propagate_task() -> easytask.Task:
    yield easytask.yield_propagate( propagate_task_1() )

def propagate():
    t = propagate_task().wait()
    return t.is_succeeded() and t.result() == 1


@easytask.taskmethod()
def wait_multi_task_1() -> easytask.Task:
    yield easytask.yield_sleep( random.uniform(0.0, 1.0) )

@easytask.taskmethod()
def wait_multi_task() -> easytask.Task:
    yield easytask.yield_wait([wait_multi_task_1() for _ in range(8)])
    return 1

def wait_multi():
    t = sleep_1_task().wait()
    return t.is_succeeded() and t.result() == 1


@easytask.taskmethod()
def compute_in_single_thread_task_0(count) -> easytask.Task:
    result = 0
    for i in range(count):
        result += i
        yield easytask.yield_sleep_tick()
    return result

@easytask.taskmethod()
def compute_in_single_thread_task() -> easytask.Task:
    tasks = [ compute_in_single_thread_task_0(i) for i in range(128) ]
    yield easytask.yield_wait(tasks)

    return sum([ task.result() for task in tasks ])

def compute_in_single_thread():
    t = compute_in_single_thread_task().wait()
    return t.is_succeeded() and t.result() == 341376

@easytask.taskmethod()
def thread_task() -> easytask.Task:
    prev_t, new_t = easytask.get_current_thread(), easytask.Thread(name='temp')
    yield easytask.yield_switch_thread(new_t)

    yield easytask.yield_sleep( random.uniform(0.0, 1.0) )

    yield easytask.yield_switch_thread(prev_t)

    new_t.finalize()

    return 1

def thread():
    t = thread_task().wait()
    return t.is_succeeded() and t.result() == 1

@easytask.taskmethod()
def multi_thread_task(main_call=True, data = None) -> easytask.Task:
    if main_call:
        data = []
        tasks = [ multi_thread_task(main_call=False, data=data) for _ in range(8)]
        yield easytask.yield_wait(tasks)
        return sum(data)
    else:
        prev_t, new_t = get_current_thread(), easytask.Thread(name='temp')
        yield easytask.yield_switch_thread(new_t)
        yield easytask.yield_sleep( random.uniform(0.0, 1.0) )
        data.append(1)
        yield easytask.yield_switch_thread(prev_t)
        new_t.finalize()

def multi_thread():
    t = multi_thread_task().wait()
    return t.is_succeeded() and t.result() == 8

@easytask.taskmethod()
def taskset_fetch_task_0() -> easytask.Task:
    yield easytask.yield_sleep(1.0)
    return 1

@easytask.taskmethod()
def taskset_fetch_task() -> easytask.Task:
    ts = easytask.TaskSet()

    for _ in range(32):
        ts.add ( taskset_fetch_task_0() )

    while ts.count() != 0:
        for task in ts.fetch(done=True):
            if not task.is_succeeded() or task.result() != 1:
                ts.cancel_all()
                return False

        yield easytask.yield_sleep_tick()

    return True

def taskset_fetch():
    return taskset_fetch_task().wait().result()

@easytask.taskmethod()
def taskset_task(ts : easytask.TaskSet) -> easytask.Task:
    yield easytask.yield_add_to(ts)

    yield easytask.yield_sleep(999.0)

def taskset():
    ts = easytask.TaskSet('taskset_1')

    t = taskset_task(ts)

    if ts.count() != 1:
        return False

    t.cancel()

    if ts.count() != 0:
        return False

    t = taskset_task(ts)

    ts.finalize()

    if t.is_succeeded():
        return False
    if ts.count() != 0:
        return False

    t = taskset_task(ts)
    if t.is_succeeded():
        return False

    return True

@easytask.taskmethod()
def done_exception_task(ev) -> easytask.Task:
    try:
        yield easytask.yield_sleep(1.0)
        yield easytask.yield_success()
    except easytask.ETaskDone as e:
        ...
    ev.set()

def done_exception():
    ev = threading.Event()
    done_exception_task(ev).wait()
    if not ev.is_set():
        return False

    ev = threading.Event()
    t = done_exception_task(ev)
    t.cancel()
    if not ev.is_set():
        return False
    return True

@easytask.taskmethod()
def exclusive_section_task_0(thread, section, value, is_leave, N) -> easytask.Task:
    yield easytask.yield_switch_thread(thread)

    yield easytask.yield_enter(section)
    for _ in range(N):
        value[0] = value[0] + 1
        yield easytask.yield_sleep_tick()

    if is_leave:
        yield easytask.yield_leave(section)


@easytask.taskmethod()
def section_task() -> easytask.Task:
    value = [0]
    section = easytask.Section()

    I = 10
    N = 10
    threads = [ easytask.Thread(name=f'thread_{i}') for i in range(I) ]
    tasks = [ exclusive_section_task_0(threads[i], section, value, i % 2 == 0, N) for i in range(I) ]
    yield easytask.yield_wait(tasks)
    [thread.finalize() for thread in threads]
    return value[0] == I*N

def section():
    return section_task().wait().result()

@easytask.taskmethod()
def child_tasks_task_2() -> easytask.Task:
    yield easytask.yield_sleep(999)

@easytask.taskmethod()
def child_tasks_task_1(task_ar) -> easytask.Task:
    task_ar.append( child_tasks_task_2())
    yield easytask.yield_sleep(999)

@easytask.taskmethod()
def child_tasks_task_0(task_ar) -> easytask.Task:
    task_ar.append( child_tasks_task_1(task_ar))
    yield easytask.yield_sleep(999)

@easytask.taskmethod()
def child_tasks_task() -> easytask.Task:
    task_ar = []
    t =  child_tasks_task_0(task_ar)
    task_ar.append(t)
    yield easytask.yield_sleep(0.5)
    t.cancel()
    return all(task.is_done() for task in task_ar)

def child_tasks():
    return child_tasks_task().wait().result()

def run_test():
    """
    """
    log_level = get_log_level()
    set_log_level(2)

    clear()
    tests = [simple_return, branch_true_1, branch_false_cancel,
             sleep_1, propagate, wait_multi, child_tasks, taskset, taskset_fetch,
             compute_in_single_thread, thread, multi_thread,
             done_exception, section]

    tests_result = []

    for func in tests:
        print(f'Testing {func.__name__}...')
        result = func()
        tests_result.append( result )
        print(f"{func.__name__} {'OK' if result else 'FAIL'}" )
        if not result:
            break

    easytask.print_debug_info()

    clear()

    set_log_level(log_level)



