## Easytask library. 

Work with tasks in multiple threads easily.
    
    
## Installation

```
pip install git+https://github.com/iperov/easytask/archive/refs/heads/master.zip
```
Requirement: Python 3.6+


## Learn quickly from examples.
    
```python
@easytask.taskmethod()  # makes method easytask.Task
def main_task() -> easytask.Task[str]: # annotate that Task returns str
    yield easytask.yield_sleep(1.0) # while Task sleep, other Tasks in Thread will work
    return 'Hello world'
    
if __name__ == '__main__':
    t = main_task().wait() # wait Task in non-Task method
    print( t.result() ) # Hello world
```