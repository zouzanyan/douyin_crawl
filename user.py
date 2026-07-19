"""
抖音用户解析 —— 解析各种输入为 sec_uid, 拉取用户资料和作品列表。

输入格式:
  1. 主页长链: https://www.douyin.com/user/MS4w...
  2. 裸 sec_uid: MS4w...
  3. v.douyin.com 短链
  4. 数字 short_id / 抖音号 (需登录态)
"""

import re
from typing import Any, Optional

import requests

from parser import MOBILE_UA, extract_url
from sign import signed_request

# ----------------------------------------------------------------------
# sec_uid 解析
# ----------------------------------------------------------------------

SEC_UID_RE = re.compile(r"(MS4wLjABAAAA[A-Za-z0-9_-]+)")
USER_PATH_RE = re.compile(r"/user/(MS4w[A-Za-z0-9_-]+)")
SEC_UID_QUERY_RE = re.compile(r"[?&]sec_us(?:er_)?id=([A-Za-z0-9_.-]+)")

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": MOBILE_UA})


def _extract_sec_uid_from_url(u: str) -> Optional[str]:
    m = SEC_UID_RE.search(u) or USER_PATH_RE.search(u)
    if m and m.group(1):
        return m.group(1)
    q = SEC_UID_QUERY_RE.search(u)
    if q and q.group(1):
        return q.group(1)
    return None


def resolve_sec_uid(input_text: str, cookie: Optional[str] = None) -> str:
    """从任意输入解析出 sec_uid。cookie 可选 (用于搜索反查)。"""
    text = (input_text or "").strip()
    if not text:
        raise ValueError("输入为空")

    direct = _extract_sec_uid_from_url(text)
    if direct:
        return direct

    link = extract_url(text) if re.search(r"https?://", text) else None
    if link:
        try:
            resp = _SESSION.get(link, headers={"User-Agent": MOBILE_UA}, allow_redirects=True, timeout=10)
            final_url = resp.url
        except requests.RequestException:
            final_url = link
        sec = _extract_sec_uid_from_url(final_url)
        if sec:
            return sec
        raise ValueError("无法从链接解析 sec_uid，请确认是用户主页链接")

    if re.match(r"^\d{6,20}$", text) or re.match(r"^[A-Za-z][A-Za-z0-9_]{5,19}$", text):
        sec = search_user_sec_uid(text, cookie)
        if sec:
            return sec
        raise ValueError(f"无法解析「{text}」：抖音匿名搜索需登录态，请提供 cookie 或改用主页链接")

    raise ValueError(f"无法识别的输入: {text}")


# ----------------------------------------------------------------------
# 用户资料
# ----------------------------------------------------------------------

class UserProfile:
    __slots__ = ("sec_uid", "short_id", "nickname", "avatar_url", "aweme_count", "signature")

    def __init__(self, sec_uid: str, short_id: str, nickname: str,
                 avatar_url: Optional[str], aweme_count: int, signature: str):
        self.sec_uid = sec_uid
        self.short_id = short_id
        self.nickname = nickname
        self.avatar_url = avatar_url
        self.aweme_count = aweme_count
        self.signature = signature


def get_user_profile(sec_uid: str, cookie: Optional[str] = None) -> UserProfile:
    """拉取用户资料。"""
    r = signed_request(
        path="/aweme/v1/web/user/profile/other/",
        params={
            "sec_user_id": sec_uid,
            "source": "channel_pc_web",
            "publish_video_strategy_type": 2,
        },
        cookie=cookie,
    )
    if not r["ok"] or not r["data"]:
        raise ValueError(r.get("error") or "获取用户资料失败")
    user = (r["data"] or {}).get("user")
    if not user:
        sc = (r["data"] or {}).get("status_code")
        raise ValueError(f"获取用户资料失败 (status_code={sc if sc is not None else '?'})")
    avatar = user.get("avatar_thumb") or {}
    avatar_urls = avatar.get("url_list") or []
    return UserProfile(
        sec_uid=sec_uid,
        short_id=str(user.get("short_id") or user.get("uid") or ""),
        nickname=user.get("nickname") or "未知用户",
        avatar_url=avatar_urls[0] if avatar_urls else None,
        aweme_count=int(user.get("aweme_count") or 0),
        signature=user.get("signature") or "",
    )


def search_user_sec_uid(keyword: str, cookie: Optional[str] = None) -> Optional[str]:
    """用 short_id / 抖音号 搜索用户的 sec_uid。匿名大概率返回 2483 (需登录)。"""
    r = signed_request(
        path="/aweme/v1/web/general/search/single/",
        params={
            "keyword": keyword,
            "search_channel": "aweme_user_web",
            "search_source": "normal",
            "query_correct_type": "1",
            "is_filter_search": "0",
            "offset": "0",
            "count": "10",
            "sort_type": "0",
            "publish_time": "0",
        },
        cookie=cookie,
    )
    if not r["ok"] or not r["data"]:
        return None
    sc = (r["data"] or {}).get("status_code")
    if sc and sc != 0:
        return None
    items = (r["data"] or {}).get("data") or []
    for item in items:
        sec = (item.get("user") or {}).get("sec_uid")
        if sec:
            return sec
    return None


# ----------------------------------------------------------------------
# 作品列表
# ----------------------------------------------------------------------

class VideoListItem:
    __slots__ = ("aweme_id", "desc", "create_time", "play_url", "video_id", "duration")

    def __init__(self, aweme_id: str, desc: str, create_time: int,
                 play_url: Optional[str], video_id: Optional[str], duration: int):
        self.aweme_id = aweme_id
        self.desc = desc
        self.create_time = create_time
        self.play_url = play_url
        self.video_id = video_id
        self.duration = duration


class VideoPage:
    __slots__ = ("items", "max_cursor", "has_more")

    def __init__(self, items: list[VideoListItem], max_cursor: int, has_more: bool):
        self.items = items
        self.max_cursor = max_cursor
        self.has_more = has_more


def fetch_user_video_page(
    sec_uid: str,
    cursor: int = 0,
    count: int = 50,
    cookie: Optional[str] = None,
) -> VideoPage:
    """
    拉取用户作品列表。

    注意: 匿名访问下抖音最多返回 ~41 条且无法翻页;
    传登录 cookie 可正常翻页拿到全部作品。
    """
    r = signed_request(
        path="/aweme/v1/web/aweme/post/",
        params={
            "sec_user_id": sec_uid,
            "count": count if count > 0 else 50,
            "max_cursor": cursor,
            "locate_query": "false",
            "publish_video_strategy_type": 2,
            "need_time_list": 1,
            "time_list_query": 0,
            "whale_cut_token": "",
            "cut_version": 1,
            "from_user_page": 1,
        },
        cookie=cookie,
    )
    if not r["ok"] or not r["data"]:
        raise ValueError(r.get("error") or "获取作品列表失败")
    d = r["data"]
    raw_list = d.get("aweme_list")
    items = [_parse_aweme(a) for a in (raw_list if isinstance(raw_list, list) else [])]
    return VideoPage(
        items=items,
        max_cursor=int(d.get("max_cursor") or 0),
        has_more=bool(d.get("has_more")),
    )


def _parse_aweme(a: Any) -> VideoListItem:
    video = a.get("video") or {}
    play_addr = video.get("play_addr") or video.get("download_addr") or {}
    url_list = play_addr.get("url_list") or []
    play_url = next((u for u in url_list if "play" in u), None) or (url_list[0] if url_list else None)
    video_id = video.get("video_id")
    if not video_id and isinstance(play_url, str):
        m = re.search(r"video_id=([0-9a-zA-Z]+)", play_url)
        if m:
            video_id = m.group(1)
    return VideoListItem(
        aweme_id=str(a.get("aweme_id") or ""),
        desc=str(a.get("desc") or "")[:200],
        create_time=int(a.get("create_time") or 0),
        play_url=play_url,
        video_id=video_id,
        duration=round(int(video.get("duration") or 0) / 1000),
    )
