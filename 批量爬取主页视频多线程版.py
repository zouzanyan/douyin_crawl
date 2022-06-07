import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor

#  单线程的批量爬取视频,还没做图集的批量爬取
import 批量爬取主页视频单线程版

headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; ''Nexus 5 Build/MRA58N) AppleWebKit/537.36 ('
                         'KHTML, '
                         'like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36',
           'referer': 'https://www.douyin.com/'}


def fixname(filename):
    if filename is None:
        filename = str(time.time())  # 如果视频简介为空则将时间戳设为文件名
    character = r'[\n\r\t?*/\\|:><"]'
    filename = re.sub(character, "", filename)  # 用正则表达式去除windows下的特殊字符，这些字符不能用在文件名
    return filename


def download(videourl, videoname):
    data = requests.get(url=videourl, headers=headers, stream=True)
    with open(f'{videoname}.mp4', 'wb') as f:  # 存入当前目录
        for i1 in data.iter_content(10000):  # 边下边存入硬盘
            f.write(i1)


if __name__ == '__main__':
    url1 = input('请粘贴用户主页地址\n')
    start_time = time.time()
    video_info = 批量爬取主页视频单线程版.get_video_info(url1)
    video_number = video_info[0]
    video_url_list = video_info[2]
    video_name_list = video_info[1]
    with ThreadPoolExecutor(video_number) as executor:
        for i in range(video_number):
            video_url = video_url_list[i]
            video_name = video_name_list[i]
            task = executor.map(download, {video_url}, {video_name})
    end_time = time.time()
    cost_time = format(end_time - start_time, '.2f')
    print(f'{video_info[0]}全部下载完成,共花费时间 {cost_time} s')
