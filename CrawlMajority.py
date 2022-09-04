import requests
import re
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor
from utils.FixNameUtil import FixNameUtil


class CarwlMajority:
    def __init__(self):
        self.video_number = 0  # 视频数量
        self.video_info_dict = {}  # 视频信息字典
        self.author_name = ''
        self.sec_uid = ''
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; ''Nexus 5 Build/MRA58N) AppleWebKit/537.36 ('
                                      'KHTML, '
                                      'like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36',
                        'referer': 'https://www.douyin.com/'}

    def get_url(self, user_in):
        url = re.findall('v.douyin.com/(.*?)/', user_in)  # 分享链接形式(目前只在手机上发现2022/7/31)
        if url:
            url = 'https://v.douyin.com/' + str(url[0])  # 手机链接分享链接形式
            a = requests.get(url=url, headers=self.headers).url
            sec_uid = re.findall('sec_uid=(.*?)&', a)
            self.sec_uid = sec_uid[0]
        else:
            sec_uid = re.findall('douyin.com/user/(.*)\?', user_in)  # 电脑主页链接形式
            if not sec_uid:
                raise Exception("url格式异常,请查看README文档")
            self.sec_uid = sec_uid[0]

    def get_video_info(self):
        max_cursor = 0
        fixnameutil = FixNameUtil()  # 实例化工具类
        print('解析页面中...')
        while 1:
            pageurl = f'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={self.sec_uid}&count=15&max_cursor={max_cursor}'
            listpage = requests.get(url=pageurl, headers=self.headers).text
            listpage = json.loads(listpage)
            if max_cursor == 0:
                self.author_name = listpage['aweme_list'][0]['author']['nickname']  # 获取作者名称
                self.author_name = fixnameutil.fixname(self.author_name)
            max_cursor = listpage["max_cursor"]  # 当页页码
            for i1 in listpage["aweme_list"]:
                if i1["image_infos"] is None:  # 将图集排除在外
                    name = fixnameutil.fixname(i1["desc"])
                    url = i1["video"]["play_addr"]["url_list"][0]

                    self.video_info_dict.update({name: url})
            if max_cursor == 0:  # 当max_cursor重新变为0时意味着页面已全部加载完
                break
        self.video_number = len(self.video_info_dict)
        print('共解析到' + str(self.video_number) + '个视频')

    def threadpooldown(self):
        with ThreadPoolExecutor(100) as executor:  # 创建一个容纳100个线程的线程池
            for i in self.video_info_dict:
                executor.map(self.download, {i}, {self.video_info_dict[i]})

    def download(self, name, url):
        data = requests.get(url=url, headers=self.headers).content
        with open(f'{name}.mp4', 'wb') as f:  # 存入当前目录
            f.write(data)

    def crawl_main(self, user_in):
        start_time = time.time()

        print('程序启动...')
        self.get_url(user_in)
        self.get_video_info()
        os.mkdir(f'{self.author_name}')  # 新建下载文件夹
        os.chdir(f'./{self.author_name}/')
        print('正在批量下载,请耐心等待...')
        self.threadpooldown()
        end_time = time.time()
        cost_time = format(end_time - start_time, '.2f')
        print('下次完成，共花费时间' + cost_time + 's')
        os.chdir('..')


if __name__ == '__main__':
    url = input('---------------请在此粘贴您的链接---------------\n')
    a = CarwlMajority()
    a.crawl_main(url)
