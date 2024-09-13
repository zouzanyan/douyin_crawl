import threading
import time
import random
import uuid


# 生成随机睡眠时间
def random_sleep():
    sleep_time = random.randint(1, 3)
    time.sleep(sleep_time)


def sanitize_filename(filename, max_length=100, ellipsis='...'):
    """ 去除操作系统不支持的文件名字符 """
    if filename.__len__() == 0:
        return uuid.uuid4()
    invalid_chars = '<>:"/\\|?*\n\t\r'
    sanitized_filename = ''.join('' if c in invalid_chars else c for c in filename)
    sanitized_filename = sanitized_filename.strip(' .')
    if len(sanitized_filename) > max_length:
        head_length = (max_length - len(ellipsis)) // 2
        tail_length = max_length - len(ellipsis) - head_length
        sanitized_filename = (sanitized_filename[:head_length] + ellipsis +
                              sanitized_filename[-tail_length:])
    if sanitized_filename.__len__() == 0:
        return uuid.uuid4()
    return sanitized_filename


class IDGenerator:
    # 类变量，作为全局自增ID的计数器
    _last_id = 0
    # 锁，确保线程安全
    _lock = threading.Lock()

    @classmethod
    def generate_unique_id(cls):
        """线程安全地生成并返回一个新的全局自增ID"""
        with cls._lock:
            cls._last_id += 1
            return cls._last_id


if __name__ == '__main__':
    print(IDGenerator.generate_unique_id())

