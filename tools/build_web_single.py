#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_web_single · 把离线网页版打包成「零依赖单 HTML 文件」
================================================================
把 web/index.html 里的本地 <script src>（core/themes/samples）与
<link rel="stylesheet" href> 全部内联进同一个文件，生成可任意托管、
可直接发文件的单页应用。只用标准库、完全离线。

用法：
    python tools/build_web_single.py
    python tools/build_web_single.py -o dist/排版工坊.html
"""
import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
DEFAULT_OUT = os.path.join(ROOT, "dist", "公众号排版工坊.html")

# <script src="..."></script>（src 为属性，带或不带其它属性）
_SCRIPT_RE = re.compile(
    r'<script\b[^>]*\bsrc\s*=\s*"(?P<src>[^"]+)"[^>]*>\s*</script>',
    re.IGNORECASE)
# <link rel="stylesheet" href="...">
_LINK_RE = re.compile(
    r'<link\b[^>]*\brel\s*=\s*["\']stylesheet["\'][^>]*\bhref\s*=\s*"(?P<href>[^"]+)"[^>]*/?>',
    re.IGNORECASE)


def _is_remote(url):
    return url.startswith(("http://", "https://", "//", "data:", "blob:"))


def _read(rel):
    p = os.path.join(WEB, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        raise FileNotFoundError("web 下找不到被引用的文件：%s" % rel)
    with open(p, encoding="utf-8") as f:
        return f.read()


def _inline_script(match):
    src = match.group("src")
    if _is_remote(src):
        return match.group(0)  # 外链原样保留
    code = _read(src).replace("</script>", "<\\/script>")  # 防止提前闭合 <script>
    return '<script>\n/* ===== inlined: %s ===== */\n%s\n</script>' % (src, code)


def _inline_link(match):
    href = match.group("href")
    if _is_remote(href):
        return match.group(0)
    css = _read(href).replace("</style>", "<\\/style>")
    return '<style>\n/* ===== inlined: %s ===== */\n%s\n</style>' % (href, css)


def build():
    index = os.path.join(WEB, "index.html")
    html = open(index, encoding="utf-8").read()

    inlined = []

    def collect_script(m):
        if not _is_remote(m.group("src")):
            inlined.append(m.group("src"))
        return _inline_script(m)

    def collect_link(m):
        if not _is_remote(m.group("href")):
            inlined.append(m.group("href"))
        return _inline_link(m)

    html = _SCRIPT_RE.sub(collect_script, html)
    html = _LINK_RE.sub(collect_link, html)

    # 兜底自检：不允许再残留「带本地 src/href 的外链标签」（漏内联会导致单文件打不开）。
    # 只查真实标签，避免匹配到内联 JS 里拼接的 src=" 字符串。
    def _local(attr):
        return re.compile(r'<%s\b[^>]*\b%s\s*=\s*"(?!https?:|//|data:|blob:|#)([^"]+)"'
                          % (attr[0], attr[1]), re.IGNORECASE)
    leftover = _SCRIPT_RE.findall(html) + _LINK_RE.findall(html)
    leftover = [u for u in leftover if not _is_remote(u)]
    if leftover:
        raise SystemExit("仍有未内联的本地引用：%s" % ", ".join(sorted(set(leftover))))

    return html, inlined


def main():
    ap = argparse.ArgumentParser(description="打包离线网页版为零依赖单 HTML")
    ap.add_argument("-o", "--out", default=DEFAULT_OUT, help="输出文件路径")
    args = ap.parse_args()

    html, inlined = build()
    out = args.out
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print("已生成单文件：%s" % out)
    print("体积：%.1f KB" % (len(html.encode("utf-8")) / 1024))
    print("内联资源（%d）：" % len(inlined))
    for r in inlined:
        print("  - %s" % r)


if __name__ == "__main__":
    main()
