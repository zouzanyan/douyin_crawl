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
pip install pyyaml (安装yaml模块,配置文件)




### 使用说明
crawl_one是爬取单个视频或图集程序

crawlMajority是批量爬取所有视频程序,application.yml下粘贴抖音cookie

根据终端提示进行操作.爬取的视频放在项目目录的的文件夹下


##### 单视频粘贴例子(支持模糊)
4.69 bAT:/ “相遇不一定有结局，但一定会有意义，在追逐月亮的途中，我也曾被月光照亮过.”  https://v.douyin.com/YJVajNq/ 复制此链接，打开Dou音搜索，直接观看视频！


##### 用户主页链接例子(支持模糊)
######以下两种链接均支持
######手机端
https://v.douyin.com/YJqwKvm/
######电脑端
https://www.douyin.com/user/MS4wLjABAAAAK8yyhMzdNAtyWqupVvVBXB_4bmr6DMAZ0zpGn91qlJU?vid=7124859220079561995
https://www.douyin.com/user/MS4wLjABAAAAK8yyhMzdNAtyWqupVvVBXB_4bmr6DMAZ0zpGn91qlJU
***
### 进度

22/6/1  加入对抖音图集爬取的功能 <br>
22/6/5  加入对抖音用户作品的批量爬取  <br>
22/6/7  加入多线程下载，简化代码，函数编程<br>
22/7/31 维护 <br>
22/11/4 代码修改维护
23/1/5 代码维护,主页批量爬取修复(目前批量爬取方案需要使用用户cookie)
23/2/12 目前单视频和主页批量爬取都需要cookie

***

其他疑问请加qq1406823510
