import re
import time


class FixNameUtil:
    def __init__(self):
        self.limit = 100

    def fixname(self, filename):
        character = r'[\n\r\t?*/\\|:><"]'
        newname = re.sub(character, "", filename)  # 用正则表达式去除windows下的特殊字符，这些字符不能用在文件名
        if newname is None or "":
            newname = str(time.time())  # 如果视频简介为空则将时间戳设为文件名
            return newname
        if len(newname) <= self.limit:  # 防止文件名过长,linux 和 windows 文件名限制约为 255 个字符
            return newname
        else:
            newname = newname[:int(self.limit / 2) - 3] + '...' + newname[len(newname) - int(self.limit / 2):]
            return newname
