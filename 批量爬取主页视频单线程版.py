import requests
import re
import json
import time
#  单线程的批量爬取视频,还没做图集的批量爬取


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


def get_video_info(u):
    print('开始解析作者主页作品...')
    a = requests.get(url=u, headers=headers).url
    sec_uid = re.findall('sec_uid=(.*?)&', a)[0]
    max_cursor = 0
    videourl = []
    videoname = []
    while 1:
        pageurl = f'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={sec_uid}&count=15&max_cursor={max_cursor}'
        listpage = requests.get(url=pageurl, headers=headers).content
        listpage = listpage.decode('utf-8')
        listpage = json.loads(listpage)
        max_cursor = listpage["max_cursor"]
        for i in listpage["aweme_list"]:
            if i["image_infos"] is None:  # 将图集排除在外
                name = fixname(i["desc"])
                url = i["video"]["play_addr"]["url_list"][0]
                videoname.append(name)
                videourl.append(url)
        if max_cursor == 0:  # 当max_cursor重新变为0时意味着页面已全部加载完
            break
    videonumber = len(videoname)
    print('共解析到' + str(videonumber) + '个视频\n')
    return videonumber, videoname, videourl


def download(videoname, videourl):
    count = 0
    for (name, url) in zip(videoname, videourl):
        count += 1
        print(f'第{count}个视频正在下载')
        data = requests.get(url=url, headers=headers).content
        with open(f'{name}.mp4', 'wb') as f:  # 存入当前目录
            f.write(data)
        print(f'第{count}个视频下载完成')


if __name__ == '__main__':
    url1 = input('请粘贴用户主页地址\n')
    start_time = time.time()
    video_info = get_video_info(url1)
    video_name = video_info[1]
    video_url = video_info[2]
    download(video_name, video_url)
    end_time = time.time()
    cost_time = format(end_time - start_time, '.2f')
    print(f'{video_info[0]}全部下载完成,共花费时间 {cost_time} s')
