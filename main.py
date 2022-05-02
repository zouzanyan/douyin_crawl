import re
import json
import requests


# 去除文件名中的特殊字符
def fixname(filename):
    character = r'[?*/\|:><]'
    filename = re.sub(character, "", filename)  # 用正则表达式去除windows下的特殊字符，这些字符不能用在文件名
    return filename


# 爬取主程序
if __name__ == '__main__':
    while 1:
        number = input('请粘贴您的分享链接\n')

        # 请求头
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gec'
                                 'ko) Chrome/96.0.4664.110 Safari/537.36',
                   'referer': 'https://www.douyin.com/'}
        try:
            number_ = re.findall('douyin.com/(.*?)/', number)[0]  # 匹配粘贴目标包含的抖音视频id
        except Exception as e:
            print('粘贴链接错误,未匹配!!!\n', e)
            continue

        url = f'https://v.douyin.com/{number_}/'

        response = requests.head(url=url, headers=headers)
        url_1 = response.headers['location']  # 获取真实的视频源地址
        uid = re.findall('video/(.*?)/', url_1)[0]  # 获得抖音视频对应的唯一视频id
        src_url = f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={uid}'
        response_src = requests.get(url=src_url, headers=headers).text

        data = json.loads(response_src)

        video_content = data["item_list"][0]["video"]["play_addr"]["url_list"][0]  # 获取抖音视频的直接地址
        video_name = data["item_list"][0]["desc"]  # 获取视频名称
        video_name_fix = fixname(video_name)  # 修复(去除)windows下非法的字符

        video_content_rmwm = video_content.replace("playwm", "play", 1)  # 链接去水印
        print('下载中.......\n')
        video_response = requests.get(url=video_content_rmwm, headers=headers, stream=True)  # 获取视频的数据流

        with open(f'{video_name_fix}.mp4', 'wb') as f:  # 存入当前目录
            for i in video_response.iter_content(10000):  # 边下边存入硬盘
                f.write(i)
        print('下载完成!!!\n')
