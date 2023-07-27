import requests
import re
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor
from utils.FixNameUtil import FixNameUtil
from threading import Lock
import yaml


class CarwlMajority:
    lock = Lock()
    config = yaml.load(open('application.yml'), yaml.Loader)

    def __init__(self):
        self.id = 0
        self.video_info_list = []  # 视频列表
        self.picture_info_list = []  # 图片列表
        self.author_name = ''
        self.sec_uid = ''
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; ''Nexus 5 Build/MRA58N) AppleWebKit/537.36 ('
                                      'KHTML, '
                                      'like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36',
                        'referer': 'https://www.douyin.com/',
                        'cookie': CarwlMajority.config['cookie']}

    # 生成自增id(线程安全)
    def acquire_id(self):
        CarwlMajority.lock.acquire()
        self.id += 1
        CarwlMajority.lock.release()
        return self.id

    def get_url(self, user_in):
        url = re.findall('v.douyin.com/(.*?)/', user_in)  # 分享链接形式(目前只在手机上发现2022/7/31)
        if url:
            url = 'https://v.douyin.com/' + str(url[0])  # 手机链接分享链接形式
            data = requests.get(url=url, headers=self.headers).url
            sec_uid = re.findall('sec_uid=(.*?)&', data)
            self.sec_uid = sec_uid[0]
        else:
            sec_uid = re.findall('douyin.com/user/(.*)\?', user_in)  # 电脑主页链接形式
            if len(sec_uid) == 0:
                sec_uid = re.findall('douyin.com/user/(.*)', user_in)
            if len(sec_uid) == 0:
                raise Exception("url格式异常,请查看README文档")
            self.sec_uid = sec_uid[0]

    def get_video_info(self):
        max_cursor = 0
        print('解析页面中...')
        while 1:
            # 原接口已失效
            # pageurl = f'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={self.sec_uid}&count=15&max_cursor={max_cursor}'
            pageurl = f'https://www.douyin.com/aweme/v1/web/aweme/post/?aid=6383&sec_user_id={self.sec_uid}&count=10&max_cursor={max_cursor}&publish_video_strategy_type=2'

            listpage = requests.get(url=pageurl, headers=self.headers).text
            listpage = json.loads(listpage)

            # if listpage["has_more"] == 0:
            #     break

            if max_cursor == 0:
                self.author_name = listpage['aweme_list'][0]['author']['nickname']  # 获取作者名称
                self.author_name = FixNameUtil.fixname(self.author_name)
            max_cursor = listpage["max_cursor"]  # 当页页码
            for i1 in listpage["aweme_list"]:
                #  视频收集
                if i1["images"] is None:
                    # name = FixNameUtil.fixname(i1["desc"])
                    url = i1["video"]["play_addr"]["url_list"][0]
                    self.video_info_list.append(url)
                #  图片收集
                else:
                    self.picture_info_list += list(map(lambda x: x["url_list"][-1], i1["images"]))

            if listpage["has_more"] == 0:
                break

        print('共解析到' + str(len(self.video_info_list)) + '个视频,' + str(len(self.picture_info_list)) + '张图片')

    def threadpooldown(self):
        with ThreadPoolExecutor(10) as executor:  # 创建一个容纳10个线程的线程池
            for i in self.video_info_list:
                executor.map(self.download, {i})
            for i in self.picture_info_list:
                executor.map(self.download_pic, {i})

    def download(self, url):
        data = requests.get(url=url, headers=self.headers).content
        with open(f'{self.acquire_id()}.mp4', 'wb') as f:  # 存入当前目录
            f.write(data)

    def download_pic(self, url):
        data = requests.get(url=url, headers=self.headers).content
        with open(f'{self.acquire_id()}.jpg', 'wb') as f:  # 存入当前目录
            f.write(data)

    def crawl_main(self, user_in):
        start_time = time.time()
        print('程序启动...')
        self.get_url(user_in)
        self.get_video_info()
        if not os.path.exists(self.author_name):
            os.mkdir(f'{self.author_name}')
        os.chdir(f'./{self.author_name}/')
        print('正在批量下载,请耐心等待...')
        self.threadpooldown()
        end_time = time.time()
        cost_time = format(end_time - start_time, '.2f')
        print('下次完成，共花费时间' + cost_time + 's')
        # os.chdir('..')


if __name__ == '__main__':
    userurl = input('---------------请在此粘贴您的链接---------------\n')
    a = CarwlMajority()
    a.crawl_main(userurl)
