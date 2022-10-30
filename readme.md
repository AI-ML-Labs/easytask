## Easytask library. 

Work with tasks in multiple threads easily.
    
    
## Installation

```
pip install git+https://github.com/iperov/easytask/archive/refs/heads/master.zip
```
Requirement: Python 3.6+


## Learn quickly from examples.
    
```python
import easytask
import time

@easytask.taskmethod()  # turns the method into easytask.Task
def main_task() -> easytask.Task[str]: # annotate that Task returns str
    caller_time = time.time()
    # ^ code above run seamlessly from caller until first switch or wait
    
    yield easytask.yield_sleep(1.0) # while Task sleep, other Tasks in Thread will work
    return f'Hello world. Caller time {caller_time}'
    
if __name__ == '__main__':
    t = main_task().wait() # wait Task in non-Task method
    print( t.result() ) # Hello world. Caller time 1667033110.0105093
```

```python
import easytask

@easytask.taskmethod() 
def compute_task(i) -> easytask.Task:
    if i == 0:
        # This task will finish immediately
        return i
        
    # Sleep minimal amount of time.
    yield easytask.yield_sleep_tick() 
    
    return i*i

@easytask.taskmethod() 
def main_task() -> easytask.Task: 
    # Run multiple tasks
    tasks = [ compute_task(i) for i in range(4) ]
    
    # Wait for all tasks in current task
    yield easytask.yield_wait(tasks)
    
    for task in tasks:
        print(f'Result: {task.result()}')
    """
    Result: 0
    Result: 1
    Result: 4
    Result: 9
    """
```
    
```python
import easytask

@easytask.taskmethod() 
def compute_task(i) -> easytask.Task:
    # Sleep minimal amount of time.
    yield easytask.yield_sleep_tick() 
    
    if i == 0:
        # Cancelling Task with optional exception
        yield easytask.yield_cancel( ValueError('0 is not allowed') )
    
    yield easytask.yield_success(i*i) # same as return i*i
    

@easytask.taskmethod() 
def main_task() -> easytask.Task: 
    # Run multiple tasks
    tasks = [ compute_task(i) for i in range(4) ]
    
    # Waiting for Tasks by checking them directly
    while not all(task.is_done() for task in tasks):
        yield easytask.yield_sleep_tick()
        
    for task in tasks:
        if task.is_succeeded():
            print(f'Success result: {task.result()}')
        else:
            print(f'Error. Exception: {task.exception()}')
    """
    Error. Exception: 0 is not allowed
    Success result: 1
    Success result: 4
    Success result: 9
    """    
```

### Tasks can be cancelled for any reason.
### If you have an external resource, such as a file, it must be closed correctly when you cancel/success a task for any reason.
```python
import easytask
import io

@easytask.taskmethod() 
def file_task() -> easytask.Task:
    file = None
    
    try:
        # Do some work
        yield easytask.yield_sleep_tick()
        ...
        yield easytask.yield_sleep_tick()
        ...
        
        # Now we decide to open a file
        file = io.StringIO()
        
        # Work with file ...
        yield easytask.yield_sleep(100.0)
        
        if 'something' == 'wrong':
            # Something goes wrong? Cancel this task.
            yield easytask.yield_cancel()
        
        if 'enough':
            # Done this task at any place.
            yield easytask.yield_success()
    
    except easytask.ETaskDone:
        # Handling Task done event. 
        # After that, you will no longer be able to use yield
        ...
        
    # Code below will be executed in any case.
    # Close file gracefully.
    if file is not None:
        file.close()

@easytask.taskmethod() 
def main_task() -> easytask.Task: 
    t = file_task()
        
    # Cancel file task after 1 sec
    yield easytask.yield_sleep(1)
    t.cancel()
```

```python

import easytask

@easytask.taskmethod() 
def compute_task(n : int) -> easytask.Task[int]:
    # Each compute_task spawns its own physical python thread and switches to it
    sub_thread = easytask.Thread()
    
    try:
        yield easytask.yield_switch_thread(sub_thread)
        
        # Compute in sub thread and in a single task in this thread.
        
        yield easytask.yield_success(n*n)
    except easytask.ETaskDone:
        ...
        
    sub_thread.finalize()
    
@easytask.taskmethod() 
def main_task() -> easytask.Task: 
    # Run multiple tasks
    tasks = [ compute_task(i) for i in range(4) ]
    
    # Wait for all tasks in current task
    yield easytask.yield_wait(tasks)
    
    for task in tasks:
        print(f'Result: {task.result()}')
    """
    Result: 0
    Result: 1
    Result: 4
    Result: 9
    """
```

### Only one task in a thread is executed at a time

<img src="doc\slide_0.png"></img>

### In this way, you can use a thread to access shared data securely.

```python
...

yield easytask.yield_switch_thread(data_thread)
shared_data += 1

...
```

## Using in class.

```python
## Using in Classes.

class Bar():
    def __init__(self):
        # Taskset is used to collect tasks.
        self._ts = easytask.Taskset()
        
        # Spawn worker thread
        self._worker_thread = easytask.Thread()
        
    def finalize(self):
        # explicit Bar finalization
        
        # all tasks in Taskset will be cancelled
        self._ts.finalize()
        
        # Tasks attached to worker_thread will also be cancelled.
        self._worker_thread.finalize()
        
    @easytask.taskmethod()
    def computation(self) -> easytask.Task:
        # adding task to class taskset
        yield easytask.yield_add_to(self._ts)
        yield easytask.yield_switch_thread(self._worker_thread)
        
        while True:
            # do some continuous work
            yield easytask.yield_sleep_tick()
        

@easytask.taskmethod() 
def main_task() -> easytask.Task: 
    bar = Bar()
    bar.computation()
    
    yield easytask.yield_sleep(2.0)

    # After 2 sec we decide to finalize Bar
    bar.finalize()
```