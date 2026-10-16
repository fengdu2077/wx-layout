#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_dom · 从保存的公众号文章抽取 #js_content 的 DOM 与内联样式
================================================================
wx-theme-extractor 的第 1 步（确定性脚本，只读真实页面，不臆造）：
  - 支持 .mhtml（MIME 网页存档）与 .html/.htm；
  - 定位 #js_content，逐元素输出 标签 + 内联样式（JSON 树）；
  - 生成可读骨架 outline.txt；
  - 聚合候选设计令牌（颜色 / 字号 / 字体 / 圆角 / 行高 / 对齐 等，按频次）。

用法：
  python extract_dom.py "文章.mhtml"
  python extract_dom.py 文章.html --outdir tools/analysis
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from email import policy
from html.parser import HTMLParser

VOID_TAGS = {"img", "br", "hr", "input", "meta", "link", "source", "col", "wbr"}

# 参与令牌聚合的样式属性
AGG_PROPS = ["color", "background-color", "font-size", "font-family", "line-height",
             "font-weight", "border-radius", "text-align", "letter-spacing",
             "padding", "margin", "border-left", "border-bottom",
             "width", "height", "display",
             # 布局 / 横向滑动 / 弹性容器（复刻时易漏，必须进聚合）
             "overflow", "overflow-x", "overflow-y", "white-space", "vertical-align",
             "flex-direction", "justify-content", "align-items", "gap", "box-sizing",
             "text-transform"]
HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
GRADIENT_RE = re.compile(r"(linear|radial)-gradient", re.I)

# 视频是公众号「素材库引用的播放框」，不能被 md→HTML 样式复刻，只能出占位（:::video）。
# 命中下列任一即视为视频节点：自定义元素、播放器外层 class、data-type=video、视频 iframe。
VIDEO_TAGS = {"mpvideo", "mp-common-videosnap", "mp-common-videov2",
              "mp-common-miniprogramvideo", "mpvideosnap"}
VIDEO_CLASS_HINTS = ("mpvideo_wrp", "video_iframe", "page_video", "mpvideo")


def is_video_record(r):
    tag = r["tag"].lower()
    if tag in VIDEO_TAGS:
        return True
    a = r.get("attrs", {})
    cls = a.get("class", "")
    if cls and any(k in cls for k in VIDEO_CLASS_HINTS):
        return True
    if a.get("data-type") == "video":
        return True
    if tag == "iframe":
        src = (a.get("data-src") or a.get("src") or "").lower()
        if "video" in src:
            return True
    return False


def decode_part(part):
    """取出 MIME part 的原始字节并按字符集解码（微信页面实际为 UTF-8，MIME 头常漏标）。"""
    raw = part.get_payload(decode=True)
    if raw is None:
        raw = b""
    cs = part.get_content_charset()
    for enc in [c for c in [cs, "utf-8", "gb18030"] if c]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


# ============================ 读取 HTML ============================

def read_html(path):
    """返回 (html字符串, 来源URL)。"""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".mhtml", ".mht"):
        from email import message_from_binary_file
        with open(path, "rb") as f:
            msg = message_from_binary_file(f, policy=policy.default)
        url = ""
        for part in msg.walk():
            loc = part.get("Content-Location", "") or ""
            if part.get_content_type() == "text/html" and "/s/" in loc:
                return decode_part(part), loc
        # 退化：取第一个 text/html
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return decode_part(part), part.get("Content-Location", "")
        sys.exit("MHTML 中没有 text/html 部分。")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(), ""


# ============================ 建树 ============================

class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs          # dict
        self.children = []          # Node 或 str
        self.parent = parent


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(n)
        if tag not in VOID_TAGS:
            self.stack.append(n)

    def handle_endtag(self, tag):
        # 闭合标签必须弹栈：从栈顶向下找最近的同名标签并弹出，找不到则忽略（容错）。
        # 不实现它，整棵树会退化成一条链（曾导致视频占位去重只认到第一个）。
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_startendtag(self, tag, attrs):
        n = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(n)

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(data)


def build_tree(html):
    tb = TreeBuilder()
    tb.feed(html)
    tb.close()
    return tb.root


def find_by_id(root, target):
    stack = [root]
    while stack:
        n = stack.pop()
        if n.tag != "#root" and n.attrs.get("id") == target:
            return n
        stack.extend(c for c in n.children if isinstance(c, Node))
    return None


# ============================ 样式 / 文本 ============================

def parse_style(raw):
    out = {}
    for decl in (raw or "").split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            k = k.strip().lower()
            if k:
                out[k] = v.strip()
    return out


def direct_text(n):
    parts = [c.strip() for c in n.children if isinstance(c, str) and c.strip()]
    return " ".join(parts)


def subtree_text(n):
    parts = []
    items = [n]
    while items:
        x = items.pop()
        if isinstance(x, str):
            s = x.strip()
            if s:
                parts.append(s)
        else:
            for c in reversed(x.children):
                items.append(c)
    return " ".join(parts)


def collapse_ws(s):
    return re.sub(r"\s+", " ", s).strip()


# ============================ 抽取 ============================

def collect_meta(root):
    metas = {}
    stack = [root]
    while stack:
        n = stack.pop()
        if n.tag == "meta":
            prop = n.attrs.get("property") or n.attrs.get("name")
            if prop and prop not in metas:
                metas[prop] = n.attrs.get("content", "")
        for c in n.children:
            if isinstance(c, Node):
                stack.append(c)
    return metas


def serialize(content):
    """把 js_content 子树序列化为带 id 的扁平记录列表，同时聚合令牌（迭代式，任意深度）。"""
    records = []
    counters = {p: Counter() for p in AGG_PROPS}
    hex_counter = Counter()
    gradient_blocks = 0

    def add_node(n, parent_id, depth):
        idx = len(records)
        style = parse_style(n.attrs.get("style", ""))
        rec = {
            "id": idx, "parent": parent_id, "depth": depth,
            "tag": n.tag, "style": style,
        }
        #关键属性
        for a in ("src", "data-src", "alt", "href", "class", "data-w",
                  "data-ratio", "data-type"):
            if n.attrs.get(a):
                rec.setdefault("attrs", {})[a] = n.attrs[a]
        t = direct_text(n)
        if t:
            rec["text"] = t
        records.append(rec)

        for k, v in style.items():
            if k in counters:
                counters[k][v] += 1
        for hx in HEX_RE.findall(n.attrs.get("style", "")):
            hex_counter[hx.lower()] += 1
        if GRADIENT_RE.search(n.attrs.get("style", "")):
            nonlocal_grad[0] += 1
        return idx

    nonlocal_grad = [0]
    stack = []
    for c in reversed(content.children):
        if isinstance(c, Node):
            stack.append((c, None, 0))
    while stack:
        n, parent_id, depth = stack.pop()
        idx = add_node(n, parent_id, depth)
        kids = [c for c in n.children if isinstance(c, Node)]
        for c in reversed(kids):
            stack.append((c, idx, depth + 1))

    candidates = {
        "colors_hex": dict(hex_counter.most_common()),
        "gradients_blocks": nonlocal_grad[0],
    }
    for p in AGG_PROPS:
        if counters[p]:
            candidates[p] = dict(counters[p].most_common(15))

    # 专项：横向/纵向滑动容器（复刻时必须保留 overflow-x:auto/scroll + white-space:nowrap，
    # 否则会从「可滑动」退化成「溢出裁切」）。
    scroll_containers = []
    for r in records:
        ox = r["style"].get("overflow-x")
        oy = r["style"].get("overflow-y")
        ov = r["style"].get("overflow")

        def _scrollable(v):
            return v in ("auto", "scroll") or (v and "scroll" in v)
        hit = None
        if _scrollable(ox):
            hit = "overflow-x"
        elif _scrollable(oy):
            hit = "overflow-y"
        elif _scrollable(ov) and not _scrollable(ox):
            hit = "overflow"
        if hit:
            scroll_containers.append({
                "id": r["id"], "depth": r["depth"], "axis": hit,
                "value": r["style"].get(hit),
                "white-space": r["style"].get("white-space", ""),
                "padding-bottom": r["style"].get("padding-bottom", ""),
                "text": r.get("text", "")[:30],
            })
    candidates["scroll_containers"] = scroll_containers

    # 专项：视频占位。视频无法被 HTML 样式复刻，只标记最外层视频节点，
    # 供 AI 在 md 里写 :::video <标题>|<说明>。嵌套视频节点只保留最外层，避免重复。
    by_id = {r["id"]: r for r in records}
    flagged = [r for r in records if is_video_record(r)]
    flag_ids = {r["id"] for r in flagged}
    video_placeholders = []
    for r in flagged:
        p, outer = r["parent"], True
        while p is not None:
            if p in flag_ids:
                outer = False
                break
            p = by_id[p]["parent"]
        if outer:
            video_placeholders.append({
                "id": r["id"], "depth": r["depth"], "tag": r["tag"],
                "class": r.get("attrs", {}).get("class", "")[:60],
                "text": r.get("text", "")[:30],
            })
    candidates["video_placeholders"] = video_placeholders
    return records, candidates


def make_outline(records, content_style, video_ids=None):
    """生成缩进骨架行。video_ids 为最外层视频节点，会醒目标注为视频占位。"""
    video_ids = video_ids or set()
    by_id = {r["id"]: r for r in records}
    lines = []
    sig_props = ["display", "width", "height",
                 "flex-direction", "justify-content", "align-items", "gap",
                 "overflow", "overflow-x", "overflow-y", "white-space",
                 "vertical-align", "box-sizing", "font-size", "color",
                 "background", "background-color",
                 "font-weight", "line-height", "text-align", "text-transform",
                 "letter-spacing", "border-radius",
                 "margin", "padding", "border-left", "border-bottom", "border-top"]

    for r in records:
        st = r["style"]
        sig = []
        for p in sig_props:
            if p in st:
                v = st[p]
                if len(v) > 46:
                    v = v[:46] + "…"
                sig.append("%s:%s" % (p, v))
        # 子树文本片段
        snippet = r.get("text", "")
        if not snippet:
            snippet = ""
        if len(snippet) > 50:
            snippet = snippet[:50] + "…"
        indent = "  " * min(r["depth"], 18)
        extra = ""
        if r["tag"] == "img":
            extra = " " + (r.get("attrs", {}).get("data-src")
                           or r.get("attrs", {}).get("src", ""))[:70]
        video_mark = ""
        if r["id"] in video_ids:
            video_mark = "★[VIDEO 占位] 在 md 里写「:::video <标题>|<说明>」，后台手动替换素材库视频 "
        lines.append("%s%s<%s> %s%s %s"
                     % (indent, video_mark, r["tag"], "；".join(sig), extra,
                        ("| " + snippet) if snippet else ""))
    head = "#js_content style: " + json.dumps(content_style, ensure_ascii=False)
    return head + "\n" + "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="抽取 #js_content DOM 与内联样式")
    ap.add_argument("page", help="保存的文章 .mhtml/.html")
    ap.add_argument("--outdir", help="输出目录（默认与输入同目录）")
    ap.add_argument("--outline-limit", type=int, default=80,
                    help="终端打印 outline 的行数（完整内容仍写入文件）")
    args = ap.parse_args()

    html, url = read_html(args.page)
    root = build_tree(html)
    content = find_by_id(root, "js_content")
    if content is None:
        sys.exit("未找到 #js_content，可能不是公众号文章页面。")

    metas = collect_meta(root)
    js_name = find_by_id(root, "js_name")
    account = collapse_ws(subtree_text(js_name)) if js_name else ""
    account = account or metas.get("og:nickname", "")
    title = metas.get("og:title", "")
    if not title:
        t = find_by_id(root, "activity-name")
        title = collapse_ws(subtree_text(t)) if t else ""

    content_style = parse_style(content.attrs.get("style", ""))
    records, candidates = serialize(content)

    outdir = args.outdir or os.path.dirname(os.path.abspath(args.page))
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.page))[0]
    json_path = os.path.join(outdir, base + ".dom.json")
    outline_path = os.path.join(outdir, base + ".outline.txt")

    payload = {
        "source": os.path.basename(args.page),
        "url": url,
        "account": account,
        "title": title,
        "js_content_style": content_style,
        "node_count": len(records),
        "candidates": candidates,
        "blocks": records,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    video_ids = {v["id"] for v in candidates["video_placeholders"]}
    with open(outline_path, "w", encoding="utf-8") as f:
        f.write(make_outline(records, content_style, video_ids))

    # 终端摘要
    print("来源：%s（%s）" % (account or "未知公众号", title))
    print("URL：%s" % url)
    print("元素节点数：%d" % len(records))
    print("含渐变块：%d；不同 hex 色：%d"
          % (candidates["gradients_blocks"], len(candidates["colors_hex"])))
    sc = candidates.get("scroll_containers", [])
    print("可滑动容器：%d" % len(sc))
    for s in sc:
        print("  - id=%s %s:%s；white-space:%s；padding-bottom:%s"
              % (s["id"], s["axis"], s["value"], s["white-space"] or "-",
                 s["padding-bottom"] or "-"))
    vp = candidates.get("video_placeholders", [])
    print("视频占位：%d（视频无法样式化，md 里写 :::video，后台替换素材库视频）" % len(vp))
    for v in vp:
        print("  - id=%s <%s>%s" % (v["id"], v["tag"],
              (" class=" + v["class"]) if v["class"] else ""))
    print("\n候选令牌（按频次，节选）：")
    for key in ("colors_hex", "font-size", "font-family", "color",
                "background-color", "line-height", "font-weight",
                "border-radius", "text-align"):
        vals = candidates.get(key)
        if vals:
            items = list(vals.items())[:6]
            shown = ", ".join("%s×%s" % (k, v) for k, v in items)
            print("  %-16s %s" % (key, shown))
    print("\n已写出：\n  %s\n  %s" % (json_path, outline_path))


if __name__ == "__main__":
    main()
