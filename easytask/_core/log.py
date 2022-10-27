_LOG_LEVEL = 1

def set_log_level(level : int):
    """
    set console log level
    
    ```
        0   prints nothing
        1   only critical errors/warning
        2   more details for debugging
    ```
    """
    global _LOG_LEVEL
    _LOG_LEVEL = level
    
def get_log_level() -> int:
    global _LOG_LEVEL
    return _LOG_LEVEL