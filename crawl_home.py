import configparser
import os
import re
import sys

from loguru import logger

from utils import xbogus_util
from utils import my_util
from utils.crawler_request import CrawlerRequest


class DouYinCrawler:
    def __init__(self):
        self.crawler_request = self._initialize_crawler_request()
        self.video_list = []
        self.picture_list = []

    @staticmethod
    def _initialize_crawler_request():
        """初始化爬虫请求对象"""
        try:
            # 创建爬虫请求对象
            crawler = CrawlerRequest(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                    'Referer': 'https://www.douyin.com/'
                },
                min_sleep=3.0,
                max_sleep=10.0,
                max_retries=3,
                timeout=30,
                max_workers=1
            )
            
            # 设置Cookie
            cookie = DouYinCrawler._read_cookie_from_file()
            if cookie:
                crawler.set_cookies(DouYinCrawler._parse_cookie_string(cookie))
            else:
                logger.warning("未能成功加载Cookie，继续初始化爬虫请求对象。")
            
            return crawler
            
        except Exception as e:
            logger.error(f"初始化爬虫请求对象时发生错误: {e}")
            raise RuntimeError("无法创建爬虫请求对象，请检查配置或网络环境。")

    @staticmethod
    def _read_cookie_from_file():
        """读取Cookie配置"""
        try:
            config = configparser.RawConfigParser()
            config.read('config.ini')
            return config.get('douyin', 'cookie')
        except (FileNotFoundError, configparser.Error, KeyError) as e:
            logger.error(f"读取Cookie失败: {e}")
            return None

    @staticmethod
    def _parse_cookie_string(cookie_str):
        """解析Cookie字符串为字典"""
        cookie_dict = {}
        for item in cookie_str.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookie_dict[key] = value
        return cookie_dict

    def analyze_user_input(self, user_in: str):
        """分析用户输入，提取用户ID"""
        # 直接匹配用户ID
        match = re.search(r'user/([-\w]+)', user_in)
        if match:
            return match.group(1)
        
        # 处理短链接
        match = re.search(r'https://v.douyin.com/(\w+)/', user_in)
        if match:
            try:
                response = self.crawler_request.get(url=match.group(0), allow_redirects=True)
                uid_match = re.search(r'user/([-\w]+)', response.url)
                return uid_match.group(1) if uid_match else None
            except Exception as e:
                logger.error(f"处理短链接失败: {e}")
                return None
        
        logger.error("输入格式无效，无法提取用户ID")
        return None

    def crawl_media(self, user_in: str):
        """爬取用户媒体文件"""
        os.environ['NO_PROXY'] = 'douyin.com'
        sec_uid = self.analyze_user_input(user_in)
        if sec_uid is None:
            exit("粘贴的用户主页地址格式错误")

        logger.info(f"开始爬取用户 {sec_uid} 的媒体文件...")
        
        cursor = 0
        page_count = 0
        
        while True:
            page_count += 1
            logger.info(f"正在爬取第 {page_count} 页...")
            
            # 构建API URL
            home_url = f'https://www.douyin.com/aweme/v1/web/aweme/post/?aid=6383&sec_user_id={sec_uid}&count=18&max_cursor={cursor}&cookie_enabled=true&platform=PC&downlink=6.9'
            xbs = xbogus_util.generate_url_with_xbs(home_url, self.crawler_request.session.headers.get('User-Agent'))
            url = home_url + '&X-Bogus=' + xbs
            
            try:
                json_str = self.crawler_request.get_json(url)
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

            cursor = json_str["max_cursor"]
            
            # 处理媒体数据
            video_count, picture_count = self._process_media_data(json_str["aweme_list"])
            logger.info(f"第 {page_count} 页: 发现 {video_count} 个视频, {picture_count} 张图片")

            if json_str["has_more"] == 0:
                break

        logger.info(f"解析完成！总共发现 {len(self.video_list)} 个视频, {len(self.picture_list)} 张图片")
        
        # 显示统计信息
        # self._show_crawler_stats()
        
        print('视频数量: ' + str(len(self.video_list)))
        print('图片数量: ' + str(len(self.picture_list)))
        print(f'开始下载到本地文件 {sec_uid}...')
        self.download_media(sec_uid)

    def _process_media_data(self, aweme_list):
        """处理媒体数据"""
        video_count = 0
        picture_count = 0
        
        for item in aweme_list:
            if item["images"] is None:
                # 视频
                description = item["desc"]
                url = item["video"]["play_addr"]["url_list"][0]
                self.video_list.append([description, url])
                video_count += 1
            else:
                # 图片
                picture_urls = [img["url_list"][-1] for img in item["images"]]
                self.picture_list.extend(picture_urls)
                picture_count += len(picture_urls)
        
        return video_count, picture_count

    def _show_crawler_stats(self):
        """显示爬虫统计信息"""
        stats = self.crawler_request.get_stats()
        logger.info("爬虫统计信息:")
        logger.info(f"  总请求数: {stats['total_requests']}")
        logger.info(f"  成功请求: {stats['successful_requests']}")
        logger.info(f"  失败请求: {stats['failed_requests']}")
        logger.info(f"  成功率: {stats['success_rate']:.1f}%")

    def download_media(self, sec_uid):
        """下载媒体文件"""
        # 创建下载目录
        download_dir = os.path.join(os.getcwd(), sec_uid)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)

        # 准备下载列表
        download_pairs = []
        
        # 添加视频下载任务
        for des, url in self.video_list:
            file_name = my_util.sanitize_filename(des)
            file_path = os.path.join(download_dir, f'{file_name}.mp4')
            download_pairs.append((url, file_path))
        
        # 添加图片下载任务
        for url in self.picture_list:
            file_name = my_util.IDGenerator.generate_unique_id()
            file_path = os.path.join(download_dir, f'{file_name}.jpg')
            download_pairs.append((url, file_path))

        logger.info(f"开始批量下载 {len(download_pairs)} 个文件到目录: {download_dir}")
        
        # 批量下载
        results = self.crawler_request.download_files_batch(download_pairs)
        
        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        failed_count = len(results) - success_count
        
        logger.info(f"下载完成！成功: {success_count}, 失败: {failed_count}")
        
        # 显示失败的下载
        if failed_count > 0:
            logger.warning("以下文件下载失败:")
            for file_path, success in results.items():
                if not success:
                    logger.warning(f"  {file_path}")

        logger.info(f'用户视频图片已全部下载完成，保存在目录: {download_dir}')

    def __del__(self):
        """析构函数，确保关闭爬虫请求对象"""
        if hasattr(self, 'crawler_request'):
            self.crawler_request.close()


if __name__ == '__main__':
    logger.remove()  # 先移除默认的 sink
    logger.add(sys.stdout, level='INFO')

    crawler = DouYinCrawler()
    try:
        while True:
            user_input = input("请在此填入用户链接（输入exit退出）: \n")
            if user_input.lower() == "exit":
                break
            crawler.crawl_media(user_input)
    finally:
        crawler.crawler_request.close()
        logger.info("程序已退出")
        
