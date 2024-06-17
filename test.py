import time
import unittest

from tqdm import tqdm


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test111(self):
        invalid_chars = r'<>:"/\\|?*'
        sanitized_filename = ''.join('' if c in invalid_chars else c for c in '  . dwad[]::;;<>   ')
        print(sanitized_filename)

    def testjdu(self):
        # 模拟下载的总数据量（以字节为单位）
        total_size = 10  # 假设下载文件大小为1MB

        # 使用tqdm创建一个进度条，total参数设置总的数据量（这里是字节数）
        with tqdm(total=15, unit='个', unit_scale=False, desc='视频下载进度') as pbar:
            # 模拟下载过程
            for i in range(total_size):
                # 假设每次迭代代表下载了一个字节的数据
                # 在这里可以添加你的下载逻辑代码
                time.sleep(1)  # 模拟下载延迟

                # 更新进度条，增加已下载的数据量
                pbar.update(1)
        with tqdm(total=0, unit='个', unit_scale=False, desc='图片下载进度') as pbar:
            # 模拟下载过程
            for i in range(0):
                # 假设每次迭代代表下载了一个字节的数据
                # 在这里可以添加你的下载逻辑代码
                time.sleep(1)  # 模拟下载延迟

                # 更新进度条，增加已下载的数据量
                pbar.update(1)

            # 下载完成后，进度条将自动关闭
        # 如果需要在完成后显示一些信息，可以在with语句块之后添加代码
        print("下载完成！")



if __name__ == '__main__':
    unittest.main()
