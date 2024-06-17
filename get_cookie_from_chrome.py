import configparser

import browser_cookie3
from loguru import logger


def write_cookie_from_browser_by_host(host):
    logger.info('开始获取Chrome浏览器的douyin Cookie')
    # 获取chrome浏览器下的douyin的 cookie
    cookie_data = ''
    try:
        cookie_data = browser_cookie3.chrome(domain_name=host)
    except Exception:
        logger.error('请先关闭Chrome浏览器!')
        exit(400)
    cookie_str = ""
    for cookie in cookie_data:
        cookie_str += f"{cookie.name}={cookie.value};"

    # 移除最后一个分号
    cookie_str = cookie_str.rstrip(";")
    # 把cookie写入config.ini文件中
    config = configparser.RawConfigParser()
    config.add_section('douyin')
    config.set('douyin', 'cookie', cookie_str)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    logger.success('douyin Cookie已保存在本目录下的config.ini文件中！')


if __name__ == '__main__':
    write_cookie_from_browser_by_host('douyin.com')
