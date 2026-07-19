# 抖音无水印解析下载器 (Python)

> **单视频/图集解析无需 cookie、无需签名** -- 走移动端分享页,粘贴分享链接即可下载,稳定且匿名。

纯标准库交互菜单,仅依赖 `requests` + `gmssl`。用户主页/作品列表走 web 接口(自带 a_bogus 签名),cookie 可选。

## 功能

- **单视频/图集** -- 从分享文本提取无水印直链并下载(图集原图存子目录)。**无需 cookie**。
- **用户主页** -- 解析 sec_uid、浏览资料、分页多选下载作品。
- **交互菜单** -- 纯标准库 UI,Windows 控制台自动转 UTF-8。
- **单次模式** -- 命令行直接传分享文本,解析后自动下载。

## 安装

- Python ≥ 3.9(推荐 3.12)
- 依赖见 `requirements.txt`

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# .venv/bin/python -m pip install -r requirements.txt        # macOS / Linux
```

## 用法

```bash
python __main__.py                       # 交互菜单
python __main__.py "分享文本或链接"        # 单次:解析并下载
```

## Cookie

单视频/图集解析**不需要** cookie,仅用户主页相关功能受影响:

| 场景 | 匿名 | 带 cookie |
|---|---|---|
| 作品列表 | 最多约 41 条,无法翻页 | 可翻页拿全部 |
| 抖音号 / short_id 反查 sec_uid | 常触发风控 | 正常 |

优先用主页长链或裸 sec_uid,避免用抖音号(必须走搜索,匿名基本失败)。

## 目录结构

```
douyin_crawl/
├── __main__.py     # 入口
├── cli.py          # 交互菜单 / 单次模式
├── parser.py       # 单视频/图集解析 (分享页,无需签名)
├── sign.py         # a_bogus 签名的 web 接口客户端
├── user.py         # 用户资料 + 作品列表
├── download.py     # 下载
└── util/abogus.py  # a_bogus 签名算法
```

## 常见问题

- **`ImportError: attempted relative import`** -- 在本目录内直接 `python __main__.py`,勿当包导入。
- **`412` / 风控** -- web 接口被风控,稍后重试或填登录 cookie;单视频走分享页不受影响。
- **作品只能看 41 条** -- 匿名限制,带 cookie 即可翻页。
- **中文/emoji 乱码** -- 确认终端为 UTF-8(`chcp 65001`)。

## 法律与使用须知

仅供个人学习与研究,下载内容版权归原作者所有。使用本工具产生的法律责任由使用者自行承担。
