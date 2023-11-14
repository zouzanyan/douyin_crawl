import configparser

import browser_cookie3
import requests


def write_cookie_from_browser_by_host(host):
    # 获取chrome浏览器下的douyin的 cookie
    cj = browser_cookie3.chrome(domain_name=host)
    cookie_str = ""
    for cookie in cj:
        cookie_str += f"{cookie.name}={cookie.value};"
    # 移除最后一个分号
    cookie_str = cookie_str.rstrip(";")
    # 把cookie写入config.ini文件中
    config = configparser.RawConfigParser()
    config.add_section('douyin')
    config.set('douyin', 'cookie', cookie_str)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)


if __name__ == '__main__':
    write_cookie_from_browser_by_host('douyin.com')
