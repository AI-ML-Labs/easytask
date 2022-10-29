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

    yield easytask.yield_success(i*i)
    # ^ same as return i*i, but you can finish Task at any place
    

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