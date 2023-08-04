import time
import random


# 生成随机睡眠时间
def random_sleep():
    sleep_time = random.randint(1, 3)
    time.sleep(sleep_time)
