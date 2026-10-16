#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render · 公众号排版工坊入口
用法：
  python render.py 文章.md                         用默认主题渲染
  python render.py 文章.md --theme 蓝白杂志 --open  指定主题并打开
  python render.py --list-themes                   列出所有主题
"""

import argparse
import os
import webbrowser

import wx_core

DEFAULT_THEME = "蓝白杂志"


def resolve_theme(name):
    """支持用文件名 / label / name 代号匹配主题。"""
    # 直接命中文件名
    try:
        return wx_core.load_theme(name), name
    except FileNotFoundError:
        pass
    # 遍历按 label / name 匹配
    for fname, label in wx_core.list_themes():
        mod = wx_core.load_theme(fname)
        if label == name or mod.THEME.get("name") == name:
            return mod, fname
    raise SystemExit("找不到主题：%s。可用 `python render.py --list-themes` 查看。" % name)


def main():
    ap = argparse.ArgumentParser(description="公众号排版工坊 · 渲染入口")
    ap.add_argument("md", nargs="?", help="带模块标记的文章 .md")
    ap.add_argument("--theme", help="主题名（文件名 / 显示名 / 代号），不填用默认")
    ap.add_argument("-o", "--output", help="输出 HTML 路径")
    ap.add_argument("--open", action="store_true", help="渲染后在浏览器打开")
    ap.add_argument("--list-themes", action="store_true", help="列出所有可用主题")
    args = ap.parse_args()

    if args.list_themes or not args.md:
        themes = wx_core.list_themes()
        if not themes:
            print("themes\\ 目录下还没有主题。")
        for fname, label in themes:
            mark = "（默认）" if fname == DEFAULT_THEME else ""
            print("  %s \t%s%s" % (fname, label, mark))
        if not args.md:
            return
        if args.list_themes:
            return

    theme_name = args.theme or DEFAULT_THEME
    theme, real_name = resolve_theme(theme_name)

    with open(args.md, encoding="utf-8") as f:
        md_text = f.read()

    engine = wx_core.Engine(theme)
    body_html = engine.render(md_text)
    button = theme.THEME.get("tokens", {}).get("BLUE", "#2563eb")
    page = wx_core.build_page(body_html, title=real_name + " · 排版预览",
                              button_color=button)

    out_path = args.output or (os.path.splitext(args.md)[0] + "-wx.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print("已生成：%s（主题：%s）" % (out_path, real_name))
    if args.open:
        webbrowser.open("file://" + os.path.abspath(out_path))


if __name__ == "__main__":
    main()
