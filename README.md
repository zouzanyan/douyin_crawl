# douyin_crawl
抖音视频批量爬取

开发工具
windows10

pycharm

### 编译环境
Python 3.10.4 (tags/v3.10.4:9d38120, Mar 23 2022, 23:13:41) [MSC v.1929 64 bit (AMD64)] on win32

### 简介
除requests模块,其他模块均为内置模块

pip install requests  (安装requests模块)
批量爬取暂不支持图集

GUI.py依赖于其他两个模块,另两个模块互相独立



### 使用说明
运行主函数main.py,根据终端提示进行操作.爬取的视频放在项目目录的的文件夹下
##### 单视频粘贴例子(支持模糊)
4.69 bAT:/ “相遇不一定有结局，但一定会有意义，在追逐月亮的途中，我也曾被月光照亮过.”  https://v.douyin.com/YJVajNq/ 复制此链接，打开Dou音搜索，直接观看视频！


##### 用户主页链接例子(支持模糊)
######以下两种链接均支持
######手机端
https://v.douyin.com/YJqwKvm/
######电脑端
https://www.douyin.com/user/MS4wLjABAAAAMWnCuaM1kNwVyN5P1f9OL5w1zWVuCGImgfF8j4rYv0Y
***
### 进度

22/6/1  加入对抖音图集爬取的功能 <br>
22/6/5  加入对抖音用户作品的批量爬取  <br>
22/6/7  加入多线程下载，简化代码，函数式编程<br>
22/6/18     优化代码,解耦合,尝试使用tkinter做界面

***

其他疑问请加qq1406823510
