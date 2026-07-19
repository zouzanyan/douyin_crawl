"""
抖音无水印解析 —— 核心爬取逻辑。

流程: 分享链接 → 提取 aweme_id → 请求分享页 → 提取 JSON → 解析视频/图集信息
"""

import json
import re
from typing import Any, Optional, Union

import requests

# ----------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/16.6 Mobile/15E148 Safari/604.1"
)
HOMEPAGE_URL = "https://www.iesdouyin.com/"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": MOBILE_UA})

_URL_RE = re.compile(r"https?://[^\s，。]+")
_VIDEO_ID_RE = re.compile(r"/video/(\d+)")
_LONG_DIGIT_RE = re.compile(r"(\d{15,})")


# ----------------------------------------------------------------------
# URL / ID 提取
# ----------------------------------------------------------------------

def extract_url(text: str) -> str:
    """从分享文本中提取 http(s) 链接。"""
    if not text:
        raise ValueError("输入为空")
    m = _URL_RE.search(text)
    if not m:
        raise ValueError(f"未在输入中找到链接: {text}")
    return m.group(0)


def get_aweme_id(url: str) -> str:
    """从抖音链接解析 aweme_id (支持短链重定向)。"""
    m = _VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)

    resp = _SESSION.get(url, headers={"User-Agent": MOBILE_UA}, allow_redirects=True, timeout=10)
    final_url = resp.url
    m = _VIDEO_ID_RE.search(final_url)
    if m:
        return m.group(1)
    m = _LONG_DIGIT_RE.search(final_url)
    if m:
        return m.group(1)
    raise ValueError(f"无法从链接解析视频 ID: {url}")


# ----------------------------------------------------------------------
# 页面抓取与 JSON 提取
# ----------------------------------------------------------------------

def fetch_share_page(aweme_id: str) -> str:
    """请求移动端分享页 HTML。"""
    url = f"https://www.iesdouyin.com/share/video/{aweme_id}/"
    resp = _SESSION.get(url, headers={
        "User-Agent": MOBILE_UA,
        "Referer": HOMEPAGE_URL,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }, allow_redirects=True, timeout=10)
    if resp.status_code != 200 or not resp.text:
        raise ValueError(f"分享页请求失败: HTTP {resp.status_code}")
    return resp.text


def extract_router_data(html: str) -> Any:
    """括号深度匹配提取 _ROUTER_DATA JSON。"""
    marker = "window._ROUTER_DATA = "
    idx = html.find(marker)
    if idx < 0:
        idx = html.find("_ROUTER_DATA")
        if idx < 0:
            return None
        eq = html.find("=", idx)
        if eq < 0:
            return None
        start = eq + 1
    else:
        start = idx + len(marker)

    while start < len(html) and html[start].isspace():
        start += 1
    if start >= len(html) or html[start] != "{":
        return None

    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(html)):
        c = html[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start : i + 1])
                except (ValueError, json.JSONDecodeError):
                    return None
    return None


# ----------------------------------------------------------------------
# JSON 遍历提取
# ----------------------------------------------------------------------

class _VideoMeta:
    """_walk_find 的累加器。"""
    __slots__ = ("play_urls", "video_id", "title", "author")

    def __init__(self):
        self.play_urls: list[str] = []
        self.video_id: Optional[str] = None
        self.title: Optional[str] = None
        self.author: Optional[str] = None


def _walk_find(obj: Any, found: _VideoMeta) -> None:
    """递归在 JSON 树中提取视频信息。"""
    if isinstance(obj, list):
        for v in obj:
            _walk_find(v, found)
        return
    if not isinstance(obj, dict):
        return

    # url_list (play_addr / download_addr) → 播放地址
    url_list = obj.get("url_list")
    if isinstance(url_list, list) and url_list:
        urls = [u for u in url_list if isinstance(u, str) and u]
        if urls and any("play" in u for u in urls):
            found.play_urls.extend(urls)

    # uri → video_id
    uri = obj.get("uri")
    if isinstance(uri, str) and not found.video_id:
        if re.match(r"^v[0-9a-f]+$", uri):
            found.video_id = uri

    # 标题 / 作者
    if isinstance(obj.get("desc"), str) and not found.title:
        found.title = obj["desc"]
    if isinstance(obj.get("nickname"), str) and not found.author:
        found.author = obj["nickname"]

    for v in obj.values():
        _walk_find(v, found)


# ----------------------------------------------------------------------
# 播放地址构造
# ----------------------------------------------------------------------

def build_play_url(video_id: str, ratio: str = "default", base_url: Optional[str] = None) -> str:
    """构造无水印播放地址。"""
    if base_url:
        m = re.search(r"(https?://[^/]+/aweme/v1/play(?:wm)?/)", base_url)
        if m:
            prefix = m.group(1).replace("playwm", "play")
        else:
            prefix = "https://aweme.snssdk.com/aweme/v1/play/"
        extra = ""
        em = re.search(r"&(line=\d+)", base_url)
        if em:
            extra = "&" + em.group(1)
        return f"{prefix}?video_id={video_id}&ratio={ratio}{extra}"
    return f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio={ratio}&line=0"


# ----------------------------------------------------------------------
# 图集解析
# ----------------------------------------------------------------------

def _find_album_node(data: Any) -> Optional[dict]:
    """递归查找含 images 数组的节点 (图集)。"""
    if not isinstance(data, (dict, list)):
        return None
    if isinstance(data, list):
        for v in data:
            r = _find_album_node(v)
            if r:
                return r
        return None
    images = data.get("images")
    if isinstance(images, list) and len(images) > 0:
        return data
    for v in data.values():
        r = _find_album_node(v)
        if r:
            return r
    return None


def _is_album(data: Any) -> bool:
    node = _find_album_node(data)
    if not node:
        return False
    images = node.get("images")
    return isinstance(images, list) and len(images) > 0


def _get_album_image_urls(data: Any) -> list[str]:
    """提取图集无水印原图 URL 列表。"""
    node = _find_album_node(data)
    if not node:
        return []
    images = node.get("images")
    if not isinstance(images, list):
        return []
    urls: list[str] = []
    for img in images:
        if not isinstance(img, dict):
            continue
        dl = img.get("download_url_list")
        ul = img.get("url_list")
        url = ""
        if isinstance(dl, list) and dl and isinstance(dl[0], str):
            url = dl[0]
        elif isinstance(ul, list) and ul and isinstance(ul[0], str):
            url = ul[0]
        if url:
            urls.append(url)
    return urls


# ----------------------------------------------------------------------
# 解析结果
# ----------------------------------------------------------------------

class ParseResult:
    """视频解析结果。"""
    __slots__ = ("aweme_id", "title", "author", "video_url", "source_url", "type")

    def __init__(self, aweme_id: str, title: str, author: str, video_url: str, source_url: str):
        self.aweme_id = aweme_id
        self.title = title
        self.author = author
        self.video_url = video_url
        self.source_url = source_url
        self.type = "video"


class AlbumResult:
    """图集解析结果。"""
    __slots__ = ("aweme_id", "title", "author", "source_url", "image_urls", "type")

    def __init__(self, aweme_id: str, title: str, author: str, source_url: str, image_urls: list[str]):
        self.aweme_id = aweme_id
        self.title = title
        self.author = author
        self.source_url = source_url
        self.image_urls = image_urls
        self.type = "album"


# ----------------------------------------------------------------------
# 主解析入口
# ----------------------------------------------------------------------

def parse_douyin(text: str) -> Union[ParseResult, AlbumResult]:
    """解析抖音分享链接, 返回视频或图集信息。"""
    url = extract_url(text)
    aweme_id = get_aweme_id(url)
    html = fetch_share_page(aweme_id)
    data = extract_router_data(html)
    if data is None:
        raise ValueError("无法解析页面数据, 抖音接口可能已变更")

    # 提取标题/作者
    meta = _VideoMeta()
    _walk_find(data, meta)
    title = meta.title or aweme_id
    author = meta.author or ""

    # 图集
    if _is_album(data):
        image_urls = _get_album_image_urls(data)
        if image_urls:
            return AlbumResult(aweme_id, title, author, url, image_urls)
        raise ValueError("未能从页面提取图集图片")

    # 视频
    video_id = meta.video_id
    if not video_id:
        for u in meta.play_urls:
            m = re.search(r"video_id=([0-9a-zA-Z]+)", u)
            if m:
                video_id = m.group(1)
                break
    if not video_id:
        raise ValueError("未能从页面找到视频地址")

    template = next((u for u in meta.play_urls if "video_id=" in u), None)
    video_url = build_play_url(video_id, "default", template)
    return ParseResult(aweme_id, title, author, video_url, url)


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """清洗文件名中的非法字符。"""
    n = re.sub(r'[\\/:*?"<>|\n\r\t]', " ", name).strip()
    n = re.sub(r"\s+", " ", n)
    if len(n) > max_len:
        n = n[:max_len].strip()
    return n or "douyin_video"
