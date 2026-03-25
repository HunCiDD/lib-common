# 常用装饰器

import time
from functools import wraps
from ..logger.configs import loggers


run_logger = loggers.get_logger("run")


# 重试装饰器
def retry(max_retries=3, delay=1, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    run_logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                    time.sleep(delay * (attempt + 1))
            return None

        return wrapper

    return decorator
