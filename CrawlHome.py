import asyncio
import os
import re
import time

import requests
import aiohttp

import utils.XBogusUtil
import utils.Sleep

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
}


class CrawlHome(object):
    def __init__(self):
        self.session = requests.Session()
        # 防止开vpn了requests模块报ssl异常
        self.session.trust_env = False
        self.video_info_list = []
        self.picture_info_list = []
        self.author_name = ''

    def analyze_user_input(self, user_in):
        try:
            u = re.search('user/([-\w]+)', user_in)
            if u:
                return u.group(1)
            u = re.search('https://v.douyin.com/(\w+)/', user_in)
            if u:
                url = u.group(0)
                res = self.session.get(url=url, headers=headers).url
                uid = re.search('user/([-\w]+)', res)
                if uid:
                    return uid.group(1)

        except Exception as e:
            return

    # 默认开启睡眠
    def get_home_video(self, user_in, sleep=False):
        sec_uid = self.analyze_user_input(user_in)
        cursor = 0
        if sec_uid is None:
            exit("粘贴的用户主页地址格式错误")
        home_url = f'https://www.douyin.com/aweme/v1/web/aweme/post/?aid=6383&sec_user_id={sec_uid}&count=35&max_cursor={cursor}&cookie_enabled=true&platform=PC&downlink=10'

        xbs = utils.XBogusUtil.generate_url_with_xbs(home_url, headers.get('User-Agent'))
        url = home_url + '&X-Bogus=' + xbs
        json_str = self.session.get(url, headers=headers).json()
        # print(json_str)

        self.author_name = json_str['aweme_list'][0]['author']['nickname']  # 获取作者名称

        while 1:

            home_url = f'https://www.douyin.com/aweme/v1/web/aweme/post/?aid=6383&sec_user_id={sec_uid}&count=35&max_cursor={cursor}&cookie_enabled=true&platform=PC&downlink=10'
            xbs = utils.XBogusUtil.generate_url_with_xbs(home_url, headers.get('User-Agent'))
            url = home_url + '&X-Bogus=' + xbs
            json_str = self.session.get(url, headers=headers).json()
            cursor = json_str["max_cursor"]  # 当页页码
            for i1 in json_str["aweme_list"]:
                #  视频收集
                if i1["images"] is None:
                    name = i1["desc"]
                    url = i1["video"]["play_addr"]["url_list"][0]
                    # url = i1["video"]['bit_rate'][0]['play_addr']['url_list'][0]
                    self.video_info_list.append({'video_desc': name, 'video_url': url})
                #  图片收集
                else:
                    self.picture_info_list += list(map(lambda x: x["url_list"][-1], i1["images"]))

            if json_str["has_more"] == 0:
                break

            # 随机睡眠
            if sleep:
                utils.Sleep.random_sleep()


async def save_to_disk(video_list, picture_list):
    count = 1
    tasks = []
    async with aiohttp.ClientSession(headers=headers) as session:
        for i in video_list:
            url = i.get('video_url')
            task = asyncio.ensure_future(download_video(session, count, url))
            tasks.append(task)
            count += 1
        for i in picture_list:
            task = asyncio.ensure_future(download_pic(session, count, i))
            tasks.append(task)
            count += 1
        await asyncio.gather(*tasks)


async def download_video(session, filename, url):
    # await asyncio.sleep(0.5)
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.read()
            with open(f'{filename}.mp4', "wb") as f:
                f.write(data)


async def download_pic(session, filename, url):
    # await asyncio.sleep(0.3)
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.read()
            with open(f'{filename}.jpg', "wb") as f:
                f.write(data)


def download_main(author_name, video_list, picture_list):
    if not os.path.exists(author_name):
        os.mkdir(author_name)
    os.chdir(author_name)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(save_to_disk(video_list, picture_list))
    os.chdir("..")


if __name__ == '__main__':
    c = CrawlHome()
    user_in = input("在此粘贴用户主页的链接\n")
    print('开始解析请等待...')
    start_time = time.time()
    c.get_home_video(user_in)
    print('共解析到' + str(len(c.video_info_list)) + '个视频,' + str(len(c.picture_info_list)) + '张图片')
    print('开始下载,请稍等...')
    download_main(c.author_name, c.video_info_list, c.picture_info_list)
    end_time = time.time()
    cost_time = format(end_time - start_time, '.2f')
    print('下次完成，共花费时间' + cost_time + 's')
