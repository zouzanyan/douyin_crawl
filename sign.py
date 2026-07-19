"""
抖音 web 接口客户端 —— 提供 a_bogus 签名后的接口请求能力。

用于走 www.douyin.com 的 web 接口 (用户资料、作品列表等需签名的接口),
与 douyin.py (单视频分享页路径, 无需签名) 互补。
"""

from __future__ import annotations

import random
from typing import Any, Mapping, Optional

import requests

from util.abogus import ABogus, BrowserFingerprintGenerator

# ----------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------

WEB_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
)

HOME_URL = "https://www.douyin.com/"
TTWID_ENDPOINT = "https://ttwid.bytedance.com/ttwid/union/register/"

COMMON_PARAMS: dict[str, str] = {
    "device_platform": "webapp",
    "aid": "6383",
    "channel": "channel_pc_web",
    "update_version_code": "170400",
    "pc_client_type": "1",
    "pc_libra_divert": "Windows",
    "support_h265": "1",
    "support_dash": "0",
    "version_code": "290100",
    "version_name": "29.1.0",
    "cookie_enabled": "true",
    "screen_width": "1920",
    "screen_height": "1080",
    "browser_language": "zh-CN",
    "browser_platform": "Win32",
    "browser_name": "Edge",
    "browser_version": "130.0.0.0",
    "browser_online": "true",
    "engine_name": "Blink",
    "engine_version": "130.0.0.0",
    "os_name": "Windows",
    "os_version": "10",
    "cpu_core_num": "12",
    "device_memory": "8",
    "platform": "PC",
    "downlink": "10",
    "effective_type": "4g",
    "round_trip_time": "50",
}

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": WEB_UA})
_ABOGUS = ABogus(user_agent=WEB_UA, fp=BrowserFingerprintGenerator.generate_fingerprint("Edge"))


# ----------------------------------------------------------------------
# Token 获取 (每次请求实时获取, 不做缓存)
# ----------------------------------------------------------------------

def _gen_ms_token(length: int = 107) -> str:
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def _fetch_ttwid() -> str:
    """匿名获取 ttwid。失败返回空串 (部分接口仍可用)。"""
    body = {
        "region": "cn",
        "aid": 1768,
        "needFid": False,
        "service": HOME_URL,
        "mip": "0.0.0.0",
        "cbUrlProtocol": "https",
        "union": True,
    }
    try:
        resp = _SESSION.post(
            TTWID_ENDPOINT,
            json=body,
            headers={"Content-Type": "application/json", "User-Agent": WEB_UA},
            timeout=10,
        )
        return resp.cookies.get("ttwid") or ""
    except requests.RequestException:
        return ""


def _make_cookie(user_cookie: Optional[str] = None) -> str:
    """组装请求 Cookie。传 user_cookie 时用它 (登录态), 否则用匿名 ttwid+msToken。"""
    if user_cookie:
        return user_cookie
    ttwid = _fetch_ttwid()
    ms_token = _gen_ms_token()
    parts = ["msToken=" + ms_token, "odin_tt=1"]
    if ttwid:
        parts.insert(0, "ttwid=" + ttwid)
    return "; ".join(parts)


# ----------------------------------------------------------------------
# 签名请求
# ----------------------------------------------------------------------

def signed_request(
    path: str,
    params: Mapping[str, Any],
    method: str = "GET",
    body: str = "",
    cookie: Optional[str] = None,
) -> dict[str, Any]:
    """
    发起签名后的抖音 web 接口请求。

    Args:
        path: 接口路径, 如 "/aweme/v1/web/aweme/post/"
        params: 业务参数
        method: HTTP 方法
        body: POST body
        cookie: 可选登录 cookie (不传则匿名)

    Returns:
        {"ok": bool, "status": int, "data": Any, "error": Optional[str]}
    """
    # 组装参数 + 签名
    all_params: dict[str, str] = {
        **COMMON_PARAMS,
        **{k: str(v) for k, v in params.items()},
    }
    query = "&".join(f"{k}={v}" for k, v in all_params.items())
    # generate_abogus 返回 (signed_query, a_bogus, ua, body)
    signed_query, _a_bogus, ua, _body = _ABOGUS.generate_abogus(query, body)

    url = f"https://www.douyin.com{path}?{signed_query}"
    headers: dict[str, str] = {
        "User-Agent": ua,
        "Referer": HOME_URL,
        "Cookie": _make_cookie(cookie),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    try:
        resp = _SESSION.request(
            method,
            url,
            headers=headers,
            data=body if method == "POST" else None,
            timeout=15,
        )
    except requests.RequestException as e:
        return {"ok": False, "status": 0, "data": None, "error": f"请求失败: {e}"}

    if not resp.ok:
        text = resp.text[:120]
        if resp.status_code == 412 or "<html" in text.lower():
            hint = "触发风控 (可能签名失效或缺少有效 cookie)"
        else:
            hint = f"HTTP {resp.status_code}"
        return {"ok": False, "status": resp.status_code, "data": None, "error": f"{hint}{f': {text}' if text else ''}"}

    try:
        data = resp.json()
    except ValueError:
        return {"ok": False, "status": resp.status_code, "data": None, "error": "响应不是合法 JSON"}
    return {"ok": True, "status": resp.status_code, "data": data}
