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
    if filename is None:
        filename = str(time.time())  # 如果视频简介为空则将时间戳设为文件名
        return filename

    character = r'[\n\r\t?*/\\|:><"]'
    filename = re.sub(character, "", filename)  # 用正则表达式去除windows下的特殊字符，这些字符不能用在文件名

    if len(filename) <= limit:  # 防止文件名过长,linux 和 windows 文件名限制约为 255 个字符
        return filename
    else:
        filename = filename[:int(limit / 2) - 3] + '...' + filename[len(filename) - int(limit / 2):]
        return filename


def user_input():
    paste_url = input('请在此粘贴你的链接\n')
    return paste_url


def get_url(paste_url):
    url = re.findall('v.douyin.com/(.*?)/', paste_url)  # 分享链接形式(目前只在手机上发现2022/6/17)
    if url:
        url = 'https://v.douyin.com/' + str(url[0])
        a = requests.get(url=url, headers=headers).url
        sec_uid = re.findall('sec_uid=(.*?)&', a)
        return sec_uid[0]
    else:
        sec_uid = re.findall('douyin.com/user/(.*)', paste_url)  # 电脑主页链接形式
        return sec_uid[0]


def get_video_info(sec_uid):
    max_cursor = 0
    videourl = []
    videoname = []
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
                videoname.append(name)
                videourl.append(url)
        if max_cursor == 0:  # 当max_cursor重新变为0时意味着页面已全部加载完
            break
    videonumber = len(videoname)
    print('共解析到' + str(videonumber) + '个视频')
    return videonumber, videoname, videourl, authorname


def download(videourl, videoname):
    data = requests.get(url=videourl, headers=headers).content
    with open(f'{videoname}.mp4', 'wb') as f:  # 存入当前目录
        f.write(data)


def crawl_main(number):
    sec_uid1 = get_url(number)
    start_time = time.time()
    video_info = get_video_info(sec_uid1)

    video_number = video_info[0]
    video_url_list = video_info[2]
    video_name_list = video_info[1]
    author_name = video_info[3]

    os.mkdir(f'{author_name}')  # 新建下载文件夹
    os.chdir(f'./{author_name}/')

    print('正在批量下载,请耐心等待...')
    with ThreadPoolExecutor(100) as executor:  # 创建一个容纳100个线程的线程池
        for i in range(video_number):
            video_url = video_url_list[i]
            video_name = video_name_list[i]
            executor.map(download, {video_url}, {video_name})
    end_time = time.time()
    cost_time = format(end_time - start_time, '.2f')
    print(f'{video_number}个视频已全部下载完成,共花费时间 {cost_time} s')
    os.chdir('..')


if __name__ == '__main__':
    userinput = user_input()
    crawl_main(userinput)
