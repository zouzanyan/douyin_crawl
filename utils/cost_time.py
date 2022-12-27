import time
import functools


# 计算函数执行时间的装饰器
def cost_time(text):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            t = time.perf_counter()
            func(*args, **kwargs)
            print(f'{func.__name__} 函数执行了 {time.perf_counter() - t:.8f} s')
        return wrapper
    return decorator
