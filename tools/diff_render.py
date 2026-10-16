#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_render · 原文 vs 新主题复刻：并排渲染 + 文本级差异
====================================================
wx-theme-extractor 的第 2 步（确定性；只读真实保存页 + 我们的渲染产物）：
  左：保存页 #js_content 的真实 innerHTML（原图原样式，不改动）；
  右：同一内容用新主题渲染的结果；
  顶部：把两侧按「块文本序列」做 difflib 对齐，给出相似度、缺失 / 多余块。

只用 Python 标准库。

用法：
  python diff_render.py --page "文章.mhtml" \
      --md "复刻.md" --theme 暖棕手记 --out "diff.html"
"""

import argparse
import difflib
import html as html_mod
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import wx_core                       # noqa: E402
import extract_dom as ed             # noqa: E402


# ---------------- 原始 Node 树 → HTML（仅用于并排展示） ----------------

def _render_attrs(x):
    a = dict(x.attrs)
    if x.tag == "img":
        # 微信懒加载：浏览器展示需要把 data-src 提到 src
        src = a.get("src") or a.get("data-src")
        if src:
            a["src"] = src
    parts = ['%s="%s"' % (k, html_mod.escape("" if v is None else v, quote=True))
             for k, v in a.items()]
    return (" " + " ".join(parts)) if parts else ""


def node_inner_html(container):
    out = []
    work = [("item", c) for c in reversed(list(container.children))]
    while work:
        kind, val = work.pop()
        if kind == "close":
            out.append("</%s>" % val)
            continue
        if isinstance(val, str):
            out.append(html_mod.escape(val, quote=False))
            continue
        if val.tag in ed.VOID_TAGS:
            out.append("<%s%s />" % (val.tag, _render_attrs(val)))
            continue
        out.append("<%s%s>" % (val.tag, _render_attrs(val)))
        work.append(("close", val.tag))
        for c in reversed(val.children):
            work.append(("item", c))
    return "".join(out)


# ---------------- 全文 → 句段序列（粒度无关，稳健对齐） ----------------

def _clean_md(t):
    return ed.collapse_ws(t.replace("**", "").replace("==", ""))


def _sentences(full):
    out = []
    for x in re.split(r"[\n。！？!?]+", full):
        x = ed.collapse_ws(x).strip(" ｜|，,、 ")
        if len(x) >= 2:
            out.append(x)
    return out


# 块级元素：取「自身文本」时遇到这些即停止（它们是新的逻辑块/分组）
BLOCKELS = {
    "section", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li",
    "table", "tbody", "thead", "tr", "td", "th", "img", "hr", "br", "blockquote",
    "figure", "figcaption", "form", "button", "input", "label", "select",
    "mp-style-type", "mp-common-profile", "mp-common-videosnap", "qqmusic",
    "mpvideosnap", "mp-miniprogram", "iframe", "canvas", "svg",
}


def own_text(n):
    """块级节点「自身」的文本：收集行内文本，遇到嵌套块级元素即止（不进入）。"""
    parts = []
    work = [c for c in reversed(n.children)]
    while work:
        x = work.pop()
        if isinstance(x, str):
            s = x.strip()
            if s:
                parts.append(s)
        elif x.tag in BLOCKELS:
            continue  # 嵌套块：不计入自身文本
        else:
            for c in reversed(x.children):  # 行内元素：继续找文本
                work.append(c)
    return ed.collapse_ws(" ".join(parts))


def walk_article(content):
    """把可见正文按逻辑块切成行，并统计可见图片。
    为每个块级节点取 own_text（不与嵌套块重复），随后继续遍历嵌套块；
    跳过 display:none / visibility:hidden（赞赏、小程序、关注二维码等 UI）。
    返回 (行列表, 可见图片数)。"""
    lines, imgs = [], 0
    work = [c for c in reversed(content.children)]
    while work:
        n = work.pop()
        if not isinstance(n, ed.Node):
            continue
        st = ed.parse_style(n.attrs.get("style", ""))
        if st.get("display") == "none" or st.get("visibility") == "hidden":
            continue  # 整棵子树是隐藏 UI
        tag = n.tag
        if tag == "img":
            imgs += 1
            lines.append("[图]")
            continue  # img 无内容
        if tag in BLOCKELS:
            t = own_text(n)
            if t:
                lines.append(t)
        for c in reversed(n.children):  # 继续遍历，找到嵌套逻辑块
            work.append(c)
    return lines, imgs


def ours_full_text(md, containers):
    """按文档顺序把复刻内容还原为纯文本；issue/part 各组件单独成行，与原文对齐。"""
    parts = []
    for b in wx_core.parse(md, containers):
        if b.role == "para":
            parts.append(_clean_md(b.fields.get("text", "")))
        elif b.role == "issue":
            parts.extend(x for x in (b.get(0), b.get(1), b.get(2)) if x)
        elif b.role == "part":
            parts.extend(x for x in (b.get(0), (b.get(2) or "").upper(),
                                     b.get(1)) if x)
        elif b.role == "shot":
            parts.append("[图]")
            if b.get(1):
                parts.append(_clean_md(b.get(1)))
        elif b.role == "end":
            parts.append("—The End—")
            parts.append(b.get(0) or "真诚感谢你的每一个❤️和👍")
    return "\n".join(p for p in parts if p)


# ---------------- 报告页 ----------------

def build_report(page_path, md_path, theme_name, out_path):
    html, url = ed.read_html(page_path)
    root = ed.build_tree(html)
    content = ed.find_by_id(root, "js_content")
    if content is None:
        sys.exit("未找到 #js_content。")
    orig_html = node_inner_html(content)

    theme = wx_core.load_theme(theme_name)
    eng = wx_core.Engine(theme)
    md = io.open(md_path, encoding="utf-8").read()
    ours_html = eng.render(md)

    # 块行 → 句段对齐（两侧同粒度）
    orig_lines, orig_imgs = walk_article(content)
    a = _sentences("\n".join(orig_lines))
    b = _sentences(ours_full_text(md, eng.containers()))
    sm = difflib.SequenceMatcher(None, a, b)
    ratio = sm.ratio()

    missing, extra = [], []
    eq = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            eq += (i2 - i1)
        if tag in ("delete", "replace"):
            missing.extend(a[i1:i2])
        if tag in ("insert", "replace"):
            extra.extend(b[j1:j2])

    ours_imgs = sum(1 for x in wx_core.parse(md, eng.containers())
                    if x.role == "shot")

    font = eng.t.get("FONT", "")

    def col(title, inner):
        return (
            '<div class="pane"><h3>%s</h3><div class="body">%s</div></div>'
            % (title, inner))

    orig_col = col(
        "原文 · 保存页 #js_content（真实样式）",
        '<section style="max-width:677px;margin:0 auto;padding:8px 16px;'
        'box-sizing:border-box;background:#ffffff;color:#383838;'
        'font-family:%s;line-height:1.75;">%s</section>' % (font, orig_html))
    ours_col = col("复刻 · 主题渲染（%s）" % theme_name, ours_html)

    def li(items, cls, limit=12):
        shown = items[:limit]
        more = ('<li class="%s">…另有 %d 条</li>' % (cls, len(items) - limit)) \
            if len(items) > limit else ""
        return "".join('<li class="%s">%s</li>' % (cls, html_mod.escape(x))
                       for x in shown) + more

    report = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>原文 vs 复刻（{theme}）</title>
<style>
 *{{box-sizing:border-box;}}
 body{{margin:0;background:#f2f1ef;color:#222;font-family:{font};}}
 .bar{{position:sticky;top:0;z-index:9;background:#fff;border-bottom:1px solid #e4e2de;
       padding:14px 20px;}}
 .bar h1{{margin:0 0 8px;font-size:15px;}}
 .ratio{{height:10px;background:#e9e7e3;border-radius:980px;overflow:hidden;}}
 .ratio i{{display:block;height:100%;background:#8f7373;}}
 .meta{{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:#666;margin-top:8px;}}
 .meta b{{color:#333;}}
 details{{margin-top:10px;font-size:12px;}}
 .cols{{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px;align-items:start;}}
 @media (max-width:920px){{.cols{{grid-template-columns:1fr;}}}}
 .pane{{background:#fff;border:1px solid #e4e2de;border-radius:10px;overflow:hidden;}}
 .pane h3{{margin:0;padding:10px 14px;font-size:13px;font-weight:600;background:#faf9f7;
       border-bottom:1px solid #eee;}}
 .body{{padding:8px 6px;max-height:78vh;overflow:auto;}}
 .miss{{color:#a23b3b;list-style:none;}} .add{{color:#5b6b3b;list-style:none;}}
 ul{{margin:6px 0;padding-left:4px;}}
</style></head><body>
 <div class="bar">
   <h1>原文 vs 复刻（{theme}）</h1>
   <div class="ratio"><i style="width:{pct:.1f}%"></i></div>
   <div class="meta">
     <span>文本相似度 <b>{pct:.1f}%</b></span>
     <span>对齐句段 <b>{eq}</b></span>
     <span>原文句段 <b>{na}</b></span>
     <span>复刻句段 <b>{nb}</b></span>
     <span>图片 原文<b>{oi}</b> / 复刻<b>{ni}</b></span>
     <span>缺失/不一致 <b>{nmiss}</b></span>
     <span>复刻新增 <b>{nadd}</b></span>
   </div>
   <details><summary>差异明细（缺失=原文有/复刻无；新增=复刻有/原文无）</summary>
     <ul>{miss}</ul><ul>{add}</ul>
   </details>
 </div>
 <div class="cols">{orig}{ours}</div>
</body></html>""".format(
        theme=html_mod.escape(theme_name), font=font, pct=ratio * 100, eq=eq,
        na=len(a), nb=len(b), oi=orig_imgs, ni=ours_imgs,
        nmiss=len(missing), nadd=len(extra),
        miss=li(missing, "miss"), add=li(extra, "add"),
        orig=orig_col, ours=ours_col)

    with io.open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("相似度 %.1f%%；对齐 %d；缺失 %d；新增 %d"
          % (ratio * 100, eq, len(missing), len(extra)))
    print("已写出：%s" % out_path)


def main():
    ap = argparse.ArgumentParser(description="原文 vs 新主题复刻并排对比")
    ap.add_argument("--page", required=True, help="原文存档：.mhtml / .html（含 #js_content）")
    ap.add_argument("--md", required=True, help="复刻稿 Markdown")
    ap.add_argument("--theme", default="暖棕手记")
    ap.add_argument("--out", default="diff.html")
    args = ap.parse_args()

    md_path = args.md if os.path.isabs(args.md) else os.path.join(HERE, args.md)
    out_path = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)
    build_report(args.page, md_path, args.theme, out_path)


if __name__ == "__main__":
    main()
