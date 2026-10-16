#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
scaffold_demo · 为指定主题生成「覆盖全部样式」的示例 demo（骨架）
==================================================================
依据《docs/主题Demo生成规范.md》。只读主题真实源码，确定性地保证覆盖率：
  - 该主题 ROLES 里每个 role 各出一个示例（容器 role 配演示 body）；
  - 每个位置槽用占位文字，HTML 注释里写明该行写法；
  - 带 kw 开关的 role（如 shot round=1）额外给一个变体；
  - 正文段落演示 ** 加粗、[链接] 与主题本地行内标记（如 ==高亮==）；
  - 顶部注释列出本主题未实现、走内核 fallback 的 role。

输出：examples\demo-<主题文件>.md（再用 render.py 渲染成同名 .html）。

用法：
  python tools\scaffold_demo.py 暖棕手记
  python tools\scaffold_demo.py 蓝白杂志 --render
"""

import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import wx_core

# 占位图片（https，符合内核要求）；正式 demo 建议替换成该主题 dom.json 里的真实图片
PLACEHOLDER_IMG = "https://placehold.co/600x400?text=Demo"

FUNC_RE = re.compile(r"^def\s+render_(\w+)\s*\(")

# 常见模块的展示顺序（未列出的 role 排在 author/end 之前）
ORDER = ["issue", "part", "sub", "para", "shot", "quote", "video",
         "gallery", "callout", "faq", "timeline", "compare", "steps",
         "highlights", "profile", "toc", "stats", "keyvalue", "note",
         "tip", "warning", "code", "table", "cta", "audio", "card",
         "author", "divider", "image", "end"]

# 向用户演示的“常用 role”（用于统计哪些未实现 → fallback）
COMMON = ["issue", "part", "sub", "shot", "quote", "video", "end", "author", "card"]

SLOT_LABELS = {
    "issue": {2: ["【请改成你的公众号名称】", "【日期】"],
              3: ["【请改成你的公众号名称】", "副标签", "文章标题"]},
    "part": {3: ["01", "章节中文标题", "ENGLISH LABEL"]},
    "sub": {1: ["小标题"]},
    "shot": {2: [PLACEHOLDER_IMG, "图注文字"]},
    "video": {2: ["视频标题", "视频说明（后台手动替换成视频）"]},
    "author": {2: ["作者名", "作者身份 / 头衔"]},
    "quote": {1: ["出处 / 作者"]},
    "end": {1: ["一句致谢（可省略）"]},
}


def slot_labels(role, n):
    d = SLOT_LABELS.get(role, {})
    if n in d:
        return d[n]
    return ["占位%d" % (i + 1) for i in range(n)]


def func_bodies(src):
    """切出每个 render_<role> 的函数体源码。"""
    lines = src.splitlines()
    out, i = {}, 0
    while i < len(lines):
        m = FUNC_RE.match(lines[i])
        if not m:
            i += 1
            continue
        role = m.group(1)
        body, i = [], i + 1
        while i < len(lines):
            ln = lines[i]
            if ln.strip() == "" or ln[:1] in (" ", "\t"):
                body.append(ln)
                i += 1
            else:
                break
        out[role] = "\n".join(body)
    return out


def role_info(body):
    pos = {int(x) for x in re.findall(r"b\.get\(\s*(\d+)\s*\)", body)}
    pos |= {int(x) for x in re.findall(r"(?<![A-Za-z0-9_.])\.get\(\s*(\d+)\s*\)", body)}
    kw = re.findall(r"b\.kw\.get\(\s*['\"]([\w]+)['\"]", body)

    def has(*needles):
        return any(x in body for x in needles)

    return {
        "npos": (max(pos) + 1) if pos else 0,
        "kw": sorted(set(kw)),
        "image": has('["image"]', "['image']", '.get("image"', ".get('image'",
                     '["images"]', "['images']"),
        "heading": has('["heading"]', "['heading'", '["headings"]', "['headings']"),
        "lists": has('["lists"]', "['lists']"),
        "links": has('["links"]', "['links']", '["link"]', "['link']"),
        "paras": has('["paras"]', "['paras']"),
        "blocks": has("b.blocks"),
        "bullet": has("b.bullet"),
    }


def local_markers(src):
    """检测主题在源码里用 re.compile 定义的成对行内分隔符（如 ==）。"""
    out = set()
    for m in re.finditer(r"re\.compile\(\s*r?[\"']([=~+*_])\1", src):
        out.add(m.group(1) * 2)
    return sorted(out)


def container_body(role, info):
    L = []
    if role == "card":
        if info["image"]:
            L.append("![卡片封面](%s)" % PLACEHOLDER_IMG)
        L.append("## 卡片标题占位")
        L.append("这是卡片摘要演示文字，替换成你的简介内容。")
        if info["links"]:
            L.append("[阅读原文](https://example.com)")
        return L
    if role == "issue":
        if info["image"]:
            L.append("![刊头封面](%s)" % PLACEHOLDER_IMG)
        L.append("EDITOR'S NOTE")
        L.append("这是刊头导语演示，可替换成本期要点。")
        return L
    if info["heading"]:
        L.append("## 小标题占位")
    L.append("这是「%s」模块的正文演示段落，可替换成你的内容。" % role)
    if info["image"]:
        L.append("![图片占位](%s)" % PLACEHOLDER_IMG)
    if info["lists"]:
        L += ["- 列表项一", "- 列表项二"]
    if info["links"]:
        L.append("[链接 / 按钮文字](https://example.com)")
    return L


def build_demo(theme_file):
    mod = wx_core.load_theme(theme_file)
    label = mod.THEME.get("label", theme_file)
    name = mod.THEME.get("name", "")
    src_path = os.path.join(wx_core.THEMES_DIR, theme_file + ".py")
    src = open(src_path, encoding="utf-8").read()

    bodies = func_bodies(src)
    roles = list(getattr(mod, "ROLES", {}).keys())
    containers = wx_core.Engine(mod).containers()
    infos = {r: role_info(bodies.get(r, "")) for r in roles}
    markers = local_markers(src)
    missing_fb = [r for r in COMMON if r not in roles]

    L = []
    L.append("<!--")
    L.append("  主题示例 demo · %s（%s）" % (label, name))
    L.append("  本文件由 tools/scaffold_demo.py 依据主题源码自动生成，展示该主题的全部模块与写法。")
    L.append("  用法：在工作台打开本文件，对照下方 HTML 注释里的语法，替换占位内容；图片必须是 https://。")
    L.append("  本主题未实现、走内核 fallback 的 role：%s。跨主题降级示例见 examples/demo.md。"
             % ("、".join(missing_fb) if missing_fb else "无"))
    L.append("-->")
    L.append("")

    ordered = [r for r in ORDER if r in roles]
    ordered += [r for r in roles if r not in ordered]

    for role in ordered:
        info = infos[role]

        if role == "para":
            seg = ["这是正文演示段落，包含**加粗强调**",
                   "[链接](https://example.com)"]
            for mk in markers:
                ch = mk[0]
                seg.append("%s行内标记%s" % (mk, mk))
            L.append("<!-- 写法：正文直接写；**加粗**、[文字](https链接)；"
                     + ("主题本地标记 %s；" % "、".join(markers) if markers else "")
                     + "列表用 - 开头 -->")
            L.append("，还有".join(seg) + "。")
            L.append("")
            L.append("<!-- 写法：列表项以 - 开头（• 由内核自动处理） -->")
            L.append("- 列表项一，可含**加粗**")
            L.append("- 列表项二")
            L.append("")
            continue

        labels = slot_labels(role, info["npos"])
        is_container = role in containers

        if is_container:
            head = ":::" + role + ((" " + "|".join(labels)) if labels else "")
            uses_body = (info["image"] or info["heading"] or info["lists"]
                         or info["links"] or info["paras"] or info["blocks"])
            note = "容器，内容另起行，最后用单独一行 ::: 闭合" if uses_body \
                else "容器，本主题此模块不使用 body，直接用单独一行 ::: 闭合"
            L.append("<!-- 写法：%s（%s） -->" % (head, note))
            L.append(head)
            if uses_body:
                L.extend(container_body(role, info))
            L.append(":::")
            L.append("")
        else:
            head = ":::" + role + ((" " + "|".join(labels)) if labels else "")
            L.append("<!-- 写法：%s（单行，无需闭合） -->" % head)
            L.append(head)
            L.append("")

        # kw 开关变体（如 shot round=1）
        for k in info["kw"]:
            variant_labels = list(labels)
            variant = ":::" + role + " " + "|".join(variant_labels) + "|" + k + "=1"
            L.append("<!-- 变体写法：%s（开关 %s 打开后的效果） -->" % (variant, k))
            L.append(variant)
            L.append("")

    return "\n".join(L).rstrip() + "\n", label


def main():
    ap = argparse.ArgumentParser(description="为主题生成覆盖全部样式的示例 demo")
    ap.add_argument("theme", help="主题文件名 / label / name")
    ap.add_argument("--render", action="store_true", help="生成后用 render.py 渲染成 .html")
    args = ap.parse_args()

    # 允许用 label / name 解析成文件名
    theme_file = args.theme
    if not os.path.exists(os.path.join(wx_core.THEMES_DIR, theme_file + ".py")):
        for fname, label in wx_core.list_themes():
            mod = wx_core.load_theme(fname)
            if label == args.theme or mod.THEME.get("name") == args.theme:
                theme_file = fname
                break

    text, label = build_demo(theme_file)
    out_md = os.path.join(ROOT, "examples", "demo-%s.md" % theme_file)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(text)
    print("已生成 demo 源稿：%s" % os.path.relpath(out_md, ROOT))

    if args.render:
        out_html = os.path.splitext(out_md)[0] + ".html"
        subprocess.run([sys.executable, os.path.join(ROOT, "render.py"), out_md,
                        "--theme", theme_file, "-o", out_html], check=True)
        print("已渲染示例：%s" % os.path.relpath(out_html, ROOT))


if __name__ == "__main__":
    main()
