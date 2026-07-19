"""
抖音下载器 -- 轻量交互菜单 (纯标准库, 无额外依赖)。

运行:
    python __main__.py                 # 交互菜单
    python __main__.py "<分享文本>"     # 单次: 解析并下载
"""

from __future__ import annotations

import datetime as _dt
import os
import sys
from typing import Optional

from parser import parse_douyin
from user import fetch_user_video_page, get_user_profile, resolve_sec_uid
from download import download_album, download_video


# ----------------------------------------------------------------------
# 会话内设置
# ----------------------------------------------------------------------

class _Settings:
    def __init__(self) -> None:
        self.out_dir: str = "./downloads"
        self.cookie: Optional[str] = None


_SETTINGS = _Settings()


# ----------------------------------------------------------------------
# IO 工具
# ----------------------------------------------------------------------

def _ensure_utf8() -> None:
    """Windows 控制台默认 GBK, 强制 UTF-8 以正确显示 emoji / 中文作者名。"""
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    n = n / 1024.0
    for unit in ("KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def _prompt(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _pause() -> None:
    _prompt("\n按回车返回...")


def _make_progress_cb(label: str):
    """返回 progress(bytes) 回调, 行内 \\r 刷新, 每 ~256KB 更新一次。"""
    last = [0]

    def cb(downloaded: int) -> None:
        # downloaded 回退(如图集切下一张)或增量足够才刷新
        if downloaded < last[0] or downloaded - last[0] >= 256 * 1024:
            line = f"\r{label} {_fmt_bytes(downloaded)}".ljust(40)
            sys.stdout.write(line)
            sys.stdout.flush()
            last[0] = downloaded

    return cb


def _friendly_error(e: Exception) -> str:
    """把常见底层报错翻译成中文提示。"""
    msg = str(e)
    if "响应不是合法 JSON" in msg or "412" in msg:
        return f"{msg} (可能触发风控, 稍后重试或在「设置」里填 cookie)"
    return msg


# ----------------------------------------------------------------------
# 结果展示
# ----------------------------------------------------------------------

def _print_result(result) -> None:
    print(f"  类型     : {'视频' if result.type == 'video' else '图集'}")
    print(f"  aweme_id : {result.aweme_id}")
    print(f"  标题     : {result.title}")
    print(f"  作者     : {result.author}")
    if result.type == "video":
        print(f"  播放地址 : {result.video_url}")
    else:
        print(f"  图片数   : {len(result.image_urls)}")


def _print_profile(p) -> None:
    print(f"  昵称     : {p.nickname}")
    print(f"  short_id : {p.short_id}")
    print(f"  作品数   : {p.aweme_count}")
    if p.signature:
        sig = p.signature.replace("\n", " ")
        print(f"  签名     : {sig[:60]}{'...' if len(sig) > 60 else ''}")


def _show_video_page(page, page_no: int) -> None:
    print(f"\n--- 作品列表 (第 {page_no} 页, has_more={page.has_more}) ---")
    for idx, it in enumerate(page.items, 1):
        date = _dt.datetime.fromtimestamp(it.create_time).strftime("%m-%d") if it.create_time else "  -  "
        desc = (it.desc[:28] + "…") if len(it.desc) > 28 else (it.desc or "(无描述)")
        print(f"  {idx:2d}. [{date}] {desc}  ({it.duration}s)")


# ----------------------------------------------------------------------
# 下载
# ----------------------------------------------------------------------

def _download_result(result) -> None:
    os.makedirs(_SETTINGS.out_dir, exist_ok=True)
    try:
        if result.type == "video":
            cb = _make_progress_cb("下载中")
            path = download_video(result.video_url, result.title or result.aweme_id,
                                   out_dir=_SETTINGS.out_dir, force=True, progress=cb)
            sys.stdout.write("\n")
            print(f"[完成] {path}  ({_fmt_bytes(os.path.getsize(path))})")
        else:
            def album_cb(i: int, total: int, b: int) -> None:
                line = f"\r图 {i}/{total} 下载中 {_fmt_bytes(b)}".ljust(40)
                sys.stdout.write(line)
                sys.stdout.flush()
            paths = download_album(result, out_dir=_SETTINGS.out_dir, force=True, progress=album_cb)
            sys.stdout.write("\n")
            d = os.path.dirname(paths[0]) if paths else _SETTINGS.out_dir
            print(f"[完成] 图集 {len(paths)} 张 -> {d}")
    except Exception as e:
        sys.stdout.write("\n")
        print(f"[失败] 下载失败: {_friendly_error(e)}")


def _download_one_item(it) -> None:
    if not it.play_url:
        print(f"  [跳过] {it.aweme_id} 无播放地址")
        return
    name = it.desc or it.aweme_id
    os.makedirs(_SETTINGS.out_dir, exist_ok=True)
    cb = _make_progress_cb(f"  下载中 {name[:16]}")
    try:
        path = download_video(it.play_url, name, out_dir=_SETTINGS.out_dir, force=False, progress=cb)
        sys.stdout.write("\n")
        print(f"  [完成] {os.path.basename(path)}  ({_fmt_bytes(os.path.getsize(path))})")
    except Exception as e:
        sys.stdout.write("\n")
        print(f"  [失败] {name}: {_friendly_error(e)}")


# ----------------------------------------------------------------------
# 流程 1: 解析分享链接
# ----------------------------------------------------------------------

def action_parse_link() -> None:
    print("\n--- 解析分享链接 ---")
    text = _prompt("粘贴分享文本或链接: ")
    if not text:
        return
    try:
        result = parse_douyin(text)
    except Exception as e:
        print(f"[失败] 解析失败: {e}")
        _pause()
        return
    _print_result(result)
    if _prompt("\n是否下载? (y/n, 默认 n): ").lower() in ("y", "yes"):
        _download_result(result)
    _pause()


# ----------------------------------------------------------------------
# 流程 2: 用户主页 / 浏览作品
# ----------------------------------------------------------------------

def _parse_indices(sel: str, n: int) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for part in sel.replace("，", ",").split(","):
        part = part.strip()
        if part.isdigit():
            i = int(part)
            if 1 <= i <= n and i not in seen:
                out.append(i)
                seen.add(i)
    return out


def _browse_videos(sec_uid: str) -> None:
    cursor = 0
    page_no = 0
    while True:
        try:
            page = fetch_user_video_page(sec_uid, cursor=cursor, count=20, cookie=_SETTINGS.cookie)
        except Exception as e:
            print(f"\n[失败] 获取作品列表失败: {_friendly_error(e)}")
            _pause()
            return
        if not page.items:
            print("\n  (无作品或已到底)")
            _pause()
            return
        page_no += 1
        _show_video_page(page, page_no)
        while True:  # 在当前页处理输入
            sel = _prompt("\n输入序号下载(逗号多选) / n 下一页 / b 返回: ").lower()
            if not sel or sel in ("b", "back", "q", "quit"):
                return
            if sel in ("n", "next"):
                if not page.has_more:
                    print("  (已到最后一页)")
                    continue
                cursor = page.max_cursor
                break  # 外层 fetch 下一页
            indices = _parse_indices(sel, len(page.items))
            if not indices:
                print("  无有效选择")
                continue
            for i in indices:
                _download_one_item(page.items[i - 1])
            _pause()
            _show_video_page(page, page_no)  # 重显当前页继续操作


def action_user() -> None:
    print("\n--- 用户主页 / 浏览作品 ---")
    text = _prompt("主页链接 / sec_uid / 抖音号: ")
    if not text:
        return
    try:
        sec_uid = resolve_sec_uid(text, cookie=_SETTINGS.cookie)
    except Exception as e:
        print(f"[失败] 解析用户失败: {e}")
        _pause()
        return
    try:
        profile = get_user_profile(sec_uid, cookie=_SETTINGS.cookie)
    except Exception as e:
        print(f"[失败] 获取资料失败: {_friendly_error(e)}")
        _pause()
        return
    _print_profile(profile)
    _browse_videos(sec_uid)


# ----------------------------------------------------------------------
# 流程 3: 设置
# ----------------------------------------------------------------------

def action_settings() -> None:
    print("\n--- 设置 ---")
    print(f"  当前输出目录: {_SETTINGS.out_dir}")
    d = _prompt("  新输出目录 (回车保持): ")
    if d:
        _SETTINGS.out_dir = d
    print(f"  当前 cookie: {'(已设置)' if _SETTINGS.cookie else '(未设置)'}")
    c = _prompt("  新 cookie (回车保持, 输入 clear 清除): ")
    if c:
        _SETTINGS.cookie = None if c.lower() == "clear" else c
    print(f"  -> 输出目录: {_SETTINGS.out_dir}")
    print(f"  -> cookie: {'已设置' if _SETTINGS.cookie else '未设置'}")
    _pause()


# ----------------------------------------------------------------------
# 主循环
# ----------------------------------------------------------------------

def _interactive() -> None:
    while True:
        try:
            print()
            print("=" * 42)
            print("  抖音无水印下载器")
            print(f"  输出目录: {_SETTINGS.out_dir}")
            print("=" * 42)
            print("  1. 解析分享链接 (视频/图集)")
            print("  2. 用户主页 / 浏览作品")
            print("  3. 设置 (输出目录 / cookie)")
            print("  0. 退出")
            choice = _prompt("> ")
            if choice in ("0", "q", "quit", "exit"):
                print("再见")
                break
            elif choice == "1":
                action_parse_link()
            elif choice == "2":
                action_user()
            elif choice == "3":
                action_settings()
            else:
                print("无效选择")
        except KeyboardInterrupt:
            print("\n再见")
            break


def _run_single(text: str) -> None:
    """单次模式: 解析 + 自动下载。"""
    try:
        result = parse_douyin(text)
    except Exception as e:
        print(f"[失败] 解析失败: {e}")
        return
    _print_result(result)
    _download_result(result)


def main(argv: Optional[list[str]] = None) -> None:
    _ensure_utf8()
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        _run_single(" ".join(argv))
    else:
        _interactive()


if __name__ == "__main__":
    main()


# 8.76 lcA:/ 02/06 x@S.Lw :1pm 装酷中 # Order秩序# djosama# DJosama秩序停滞舞挑战 # 驼背老大爷 # 暮蝶  https://v.douyin.com/Zvp8DKvLZSY/ 复制此链接，打开Dou音搜索，直接观看视频！
