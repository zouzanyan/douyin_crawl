import requests
import re
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor

headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; ''Nexus 5 Build/MRA58N) AppleWebKit/537.36 ('
                         'KHTML, '
                         'like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36',
           'referer': 'https://www.douyin.com/'}


def fixname(filename, limit=100):
    character = r'[\n\r\t?*/\\|:><"]'
    filename = re.sub(character, "", filename)  # 用正则表达式去除windows下的特殊字符，这些字符不能用在文件名
    if filename is None or "":
        filename = str(time.time())  # 如果视频简介为空则将时间戳设为文件名
        return filename
    if len(filename) <= limit:  # 防止文件名过长,linux 和 windows 文件名限制约为 255 个字符
        return filename
    else:
        filename = filename[:int(limit / 2) - 3] + '...' + filename[len(filename) - int(limit / 2):]
        return filename


def user_input():
    paste_url = input('请在此粘贴你的链接\n')
    if not paste_url:
        raise Exception("url不能为空")
    return paste_url


def get_url(paste_url):
    url = re.findall('v.douyin.com/(.*?)/', paste_url)  # 分享链接形式(目前只在手机上发现2022/7/31)
    if url:
        url = 'https://v.douyin.com/' + str(url[0])  # 手机链接分享链接形式
        a = requests.get(url=url, headers=headers).url
        sec_uid = re.findall('sec_uid=(.*?)&', a)
        return sec_uid[0]
    else:
        sec_uid = re.findall('douyin.com/user/(.*)', paste_url)  # 电脑主页链接形式
        if not sec_uid:
            raise Exception("url格式异常,请查看README文档")
        return sec_uid[0]


def get_video_info(sec_uid):
    max_cursor = 0
    videoinfo_dict = {}
    authorname = 0
    print('解析页面中...')
    while 1:
        pageurl = f'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={sec_uid}&count=15&max_cursor={max_cursor}'
        listpage = requests.get(url=pageurl, headers=headers).text
        listpage = json.loads(listpage)
        if max_cursor == 0:
            authorname = listpage['aweme_list'][0]['author']['nickname']  # 获取作者名称
            authorname = fixname(authorname)
        max_cursor = listpage["max_cursor"]
        for i1 in listpage["aweme_list"]:
            if i1["image_infos"] is None:  # 将图集排除在外
                name = fixname(i1["desc"])
                url = i1["video"]["play_addr"]["url_list"][0]

                videoinfo_dict.update({name: url})
        if max_cursor == 0:  # 当max_cursor重新变为0时意味着页面已全部加载完
            break
    videonumber = len(videoinfo_dict)
    print('共解析到' + str(videonumber) + '个视频')
    return videonumber, videoinfo_dict, authorname


def threadpooldown(video_info_dict):

    with ThreadPoolExecutor(100) as executor:  # 创建一个容纳100个线程的线程池
        for i in video_info_dict:
            executor.map(download, {i}, {video_info_dict[i]})


def download(name, url):
    data = requests.get(url=url, headers=headers).content
    with open(f'{name}.mp4', 'wb') as f:  # 存入当前目录
        f.write(data)


def crawl_main(number):
    sec_uid1 = get_url(number)
    start_time = time.time()
    video_info = get_video_info(sec_uid1)

    video_number = video_info[0]
    video_info_dict = video_info[1]
    print(video_info_dict.values())
    author_name = video_info[2]

    os.mkdir(f'{author_name}')  # 新建下载文件夹
    os.chdir(f'./{author_name}/')

    print('正在批量下载,请耐心等待...')
    threadpooldown(video_info_dict)
    end_time = time.time()
    cost_time = format(end_time - start_time, '.2f')
    os.chdir('..')


if __name__ == '__main__':
    userinput = user_input()
    crawl_main(userinput)
