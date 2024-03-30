# douyin_crawl
抖音视频,图片批量爬取

开发工具
windows10

pycharm

### 编译环境
```text
Python 3.12.2 (tags/v3.12.2:6abddd9, Feb  6 2024, 21:26:36) [MSC v.1937 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
```


### 简介
```text
系统需要安装node环境(https://nodejs.org/)

pip install PyExecJS (python调用js)
pip install requests  (同步http客户端)
pip install aiohttp (异步http客户端)

```

### 使用说明

```text
1. 运行前请先关闭chrome浏览器!!!否则卡住无法获取浏览器里面的cookie
2. 从chrome浏览器中获取cookie保存为config.ini文件
python get_cookie_from_chrome.py
3. 爬取主程序,按照命令行操作进行
python CrawlHome.py
```

```text
CrawlHome是批量爬取个人主页所有视频和图片的启动程序
根据终端提示进行操作.爬取的视频放在项目目录的的文件夹下
```

```text
用户主页链接示例(支持模糊),以下两种链接均支持

1.分享格式
长按复制此条消息，打开抖音搜索，查看TA的更多作品。 https://v.douyin.com/iJLb8V4y/

2.电脑端的浏览器url
https://www.douyin.com/user/MS4wLjABAAAAK8yyhMzdNAtyWqupVvVBXB_4bmr6DMAZ0zpGn91qlJU?vid=7124859220079561995
https://www.douyin.com/user/MS4wLjABAAAAK8yyhMzdNAtyWqupVvVBXB_4bmr6DMAZ0zpGn91qlJU
```

其他疑问请加qq1406823510
