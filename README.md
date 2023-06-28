# douyin_crawl
抖音视频批量爬取

开发工具
windows10

pycharm

### 编译环境
```text
Python 3.9.0 (tags/v3.9.0:9cf6752, Oct  5 2020, 15:34:40) [MSC v.1927 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
```


### 简介
```text
除requests模块,其他模块均为内置模块

pip install requests  (安装requests模块)
pip install pyyaml (安装yaml模块,配置文件)

```

### 使用说明
```text
crawl_one是爬取单个视频或图集程序的启动程序 (已失效2023/6/28)
crawlMajority是批量爬取个人主页所有视频和图片的启动程序,必须在application.yml下粘贴抖音cookie (2023/6/28正常)
根据终端提示进行操作.爬取的视频放在项目目录的的文件夹下
```

```text
单视频示例(支持模糊)
4.69 bAT:/ “相遇不一定有结局，但一定会有意义，在追逐月亮的途中，我也曾被月光照亮过.”  https://v.douyin.com/YJVajNq/ 复制此链接，打开Dou音搜索，直接观看视频！


用户主页链接示例(支持模糊),以下两种链接均支持
1.手机端分享格式
https://v.douyin.com/YJqwKvm/
2.电脑端的浏览器url
https://www.douyin.com/user/MS4wLjABAAAAK8yyhMzdNAtyWqupVvVBXB_4bmr6DMAZ0zpGn91qlJU?vid=7124859220079561995
https://www.douyin.com/user/MS4wLjABAAAAK8yyhMzdNAtyWqupVvVBXB_4bmr6DMAZ0zpGn91qlJU
```
***
### 进度
```text
22/6/1  加入对抖音图集爬取的功能
22/6/5  加入对抖音用户作品的批量爬取
22/6/7  加入多线程下载，简化代码，函数编程
22/7/31 维护 
22/11/4 代码修改维护
23/1/5 代码维护,主页批量爬取修复(目前批量爬取方案需要使用用户cookie)
23/2/12 目前单视频和主页批量爬取都需要cookie
23/6/28 主页视频图片批量爬取接口正常,单个视频爬取接口暂时停止维护

```
***
cookie获取方式，登陆网页版抖音后，f12网页调试，任意粘贴一个数据请求体里面的cookie(很长一串),注意yml文件中cookie冒号后面有一个空格
***
其他疑问请加qq1406823510
