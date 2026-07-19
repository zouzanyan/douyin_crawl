"""
下载 —— 视频/图片/图集下载到本地磁盘。

抖音 play 地址需带 Referer: https://www.iesdouyin.com/ 才会正常响应。
"""

import os
import re
from typing import Callable, Optional

import requests

from parser import MOBILE_UA, HOMEPAGE_URL, sanitize_filename, AlbumResult

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": MOBILE_UA})


def _download_stream(url: str, save_path: str, headers: dict[str, str], timeout: int,
                     progress: Optional[Callable[[int], None]] = None) -> int:
    """流式下载到文件, 返回写入字节数。progress 在每块写入后收到累计字节数。"""
    resp = _SESSION.get(url, headers=headers, allow_redirects=True, timeout=timeout, stream=True)
    if resp.status_code not in (200, 206):
        raise ValueError(f"源返回 HTTP {resp.status_code}")

    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    downloaded = 0
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            f.write(chunk)
            downloaded += len(chunk)
            if progress is not None:
                progress(downloaded)
    return downloaded


def download_video(url: str, filename: str, out_dir: str = ".",
                   force: bool = False, timeout: int = 60,
                   progress: Optional[Callable[[int], None]] = None) -> str:
    """下载视频到本地。已存在则跳过 (除非 force=True)。返回保存路径。"""
    safe_name = sanitize_filename(filename)
    if not safe_name.lower().endswith(".mp4"):
        safe_name += ".mp4"
    save_path = os.path.join(out_dir, safe_name)
    if os.path.exists(save_path) and not force:
        return save_path
    _download_stream(url, save_path, {
        "User-Agent": MOBILE_UA,
        "Referer": HOMEPAGE_URL,
    }, timeout, progress=progress)
    return save_path


def download_image(url: str, filename: str, out_dir: str = ".",
                   force: bool = False, timeout: int = 30,
                   progress: Optional[Callable[[int], None]] = None) -> str:
    """下载图片到本地。扩展名从 URL 推断。"""
    safe_name = sanitize_filename(filename)
    if not re.search(r"\.(jpe?g|png|webp|heic|bmp)$", safe_name, re.I):
        ext = ".jpg"
        m = re.search(r"\.(jpe?g|png|webp|heic|bmp)", url, re.I)
        if m:
            ext = m.group(0).lower()
        safe_name += ext
    save_path = os.path.join(out_dir, safe_name)
    if os.path.exists(save_path) and not force:
        return save_path
    _download_stream(url, save_path, {
        "User-Agent": MOBILE_UA,
        "Referer": HOMEPAGE_URL,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }, timeout, progress=progress)
    return save_path


def download_album(result: AlbumResult, out_dir: str = ".",
                   force: bool = False, timeout: int = 30,
                   progress: Optional[Callable[[int, int, int], None]] = None) -> list[str]:
    """下载图集所有原图到 <out_dir>/<title>/ 目录。

    progress(index, total, downloaded) 回调每张图下载过程中收到累计字节数。
    """
    album_dir = os.path.join(out_dir, sanitize_filename(result.title) or "album")
    os.makedirs(album_dir, exist_ok=True)
    saved: list[str] = []
    total = len(result.image_urls)
    for i, url in enumerate(result.image_urls, 1):
        def per_image_cb(downloaded: int, idx: int = i) -> None:
            if progress is not None:
                progress(idx, total, downloaded)
        path = download_image(url, f"{i:02d}", album_dir, force=force, timeout=timeout,
                               progress=per_image_cb)
        saved.append(path)
    return saved
