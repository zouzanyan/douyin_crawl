import re

import requests

from utils.FixNameUtil import FixNameUtil
from utils.cost_time import cost_time


def user_input():
    userinput = input('-------请在此粘贴您的分享链接------\n')
    return userinput


# 爬取主程序
@cost_time('')
def crawl_main(number):
    # 请求头
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; ''Nexus 5 Build/MRA58N) AppleWebKit/537.36 ('
                             'KHTML, '
                             'like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36',
               'referer': 'https://www.douyin.com/'}

    number = re.findall('v.douyin.com/(.*?)/', number)  # 匹配粘贴目标包含的抖音视频id
    number = number[0]

    url = f'https://v.douyin.com/{number}/'

    response = requests.get(url=url, headers=headers).url  # 获取重定向后的地址
    uid = re.findall('video/(.*?)/', response)[0]  # 获得抖音视频对应的唯一视频id
    src_url = f'https://www.iesdouyin.com/aweme/v1/web/aweme/detail/?aweme_id={uid}&aid=1128&version_name=23.5.0&device_platform=android&os_version=2333'

    response_src = requests.get(url=src_url, headers=headers).json()
    desc = FixNameUtil.fixname(response_src["aweme_detail"]["desc"])

    if response_src["aweme_detail"]["images"] is None:
        print('您粘贴的是抖音视频资源')
        video_src = response_src["aweme_detail"]["video"]["play_addr"]["url_list"][0]
        video_data = requests.get(url=video_src, headers=headers).content
        with open(desc + '.mp4', 'wb') as file:
            file.write(video_data)
    if response_src["aweme_detail"]["images"] is not None:
        print('您粘贴的是抖音图集资源')
        pic_src_list = list(map(lambda x: x["url_list"][0], response_src["aweme_detail"]["images"]))
        for i in range(len(pic_src_list)):
            pic_data = requests.get(pic_src_list[i], headers=headers).content
            with open(str(i) + '.webp', 'wb') as file:
                file.write(pic_data)


if __name__ == '__main__':
    user = user_input()
    crawl_main(user)
