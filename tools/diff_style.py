#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_style · 原文 vs 复刻渲染 的「装饰 / 结构保真」对比
================================================================
diff_render.py 只比对文字，看不见边框 / 分隔线 / 间距这类纯视觉元素；
本工具补齐这一维：从两份 HTML 中抽取装饰清单并逐项对齐，报告缺失 / 多余。

对比维度：
  - bars    独立装饰条（显式宽高 + 底色 + 无文字）：宽/高/色/圆角/对齐
  - borders 容器边框（border-bottom/top）：宽/样式/色
  - gradients 渐变数量与签名（方向 + 色标）
  - scroll  可滑动容器（overflow-x/y auto/scroll + white-space），防止横向滑动退化成溢出裁切
  - images  图片数；flex 弹性行数；center 居中块数

用法：
  python diff_style.py <原文 .mhtml/.html> <我方渲染 .html>
退出码：0 = 关键维度一致；1 = 存在差异（可用于合并前把关）。
"""

import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_dom as ed

RGB_RE = re.compile(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)\)")
PX_RE = re.compile(r"^(\d+(?:\.\d+)?)px$")
BORDER_RE = re.compile(r"(\d+(?:\.\d+)?)px\s+(\w+)\s+(.+)$")


def norm_color(s):
    def sub(m):
        return "#%02x%02x%02x" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return RGB_RE.sub(sub, s).lower().replace(" ", "")


def get_content(path):
    html, _ = ed.read_html(path)
    root = ed.build_tree(html)
    for tid in ("js_content", "article"):
        n = ed.find_by_id(root, tid)
        if n is not None:
            return n
    sys.exit("找不到 #js_content / #article：%s" % path)


def hidden_ids(records):
    """返回自身或祖先被 display:none / visibility:hidden 的节点集合。"""
    byid = {r["id"]: r for r in records}
    hide = set()
    for r in records:
        st = r["style"]
        if st.get("display") == "none" or st.get("visibility") == "hidden":
            # 标记自身及其全部后代
            stack = [r["id"]]
            while stack:
                x = stack.pop(); hide.add(x)
                for c in records:
                    if c["parent"] == x:
                        stack.append(c["id"])
    return hide


def cascade_text_style(r, byid):
    """沿祖先链取文字节点实际生效的字号/颜色/字重/行高（子级优先，父级兜底）。"""
    merged = {}
    x = r["id"]
    while x is not None:
        st = byid[x]["style"]
        for k in ("font-size", "color", "font-weight", "line-height"):
            if k not in merged and k in st:
                merged[k] = st[k]
        x = byid[x]["parent"]
    return merged


def align_of(r, byid):
    x = r["id"]
    while x is not None:
        a = byid[x]
        ta = a["style"].get("text-align")
        if ta:
            return ta
        x = a["parent"]
    return "left"


def grad_signature(st):
    raw = " ".join(str(st.get(k, "")) for k in
                   ("background", "background-image"))
    sigs = []
    for m in re.finditer(r"((?:linear|radial)-gradient\([^;]*\))", raw):
        g = norm_color(m.group(1))   # 先把 rgb() 归一化为 hex，保证两侧可比
        kind = "linear" if g.startswith("linear") else "radial"
        ang = re.match(r"\w+-gradient\(\s*([^,]+)", g)
        ang = ang.group(1).strip() if ang else ""
        colors = HEX.findall(g)
        sigs.append("%s|%s|%s" % (kind, ang, ",".join(colors)))
    return sigs


HEX = ed.HEX_RE


def inventory(path):
    content = get_content(path)
    records, _ = ed.serialize(content)
    byid = {r["id"]: r for r in records}
    hide = hidden_ids(records)

    bars, borders, grads, headings, scroll = [], [], [], [], []
    images = flex = center = 0
    for r in records:
        if r["id"] in hide:
            continue
        st = r["style"]

        # 可滑动容器（横向/纵向）：缺了 overflow-x 会从「可滑动」退化成「溢出裁切」
        for axis, prop in (("x", "overflow-x"), ("y", "overflow-y")):
            if st.get(prop) in ("auto", "scroll"):
                scroll.append("%s|%s|ws:%s" % (axis, st.get(prop),
                                              st.get("white-space", "")))

        # 标题文字样式签名：直接承载文字的节点，按级联得到字号>=16 且 字重>=700
        if (r.get("text") or "").strip():
            cs = cascade_text_style(r, byid)
            fsm = PX_RE.match(str(cs.get("font-size", "")))
            fwd = re.sub(r"\D", "", str(cs.get("font-weight", "")))
            if fsm and float(fsm.group(1)) >= 16 and fwd and int(fwd) >= 700:
                lh = str(cs.get("line-height", ""))
                headings.append("%s|%s|w%s|lh%s" % (
                    fsm.group(1), norm_color(str(cs.get("color", ""))), fwd, lh))

        if r["tag"] == "img":
            images += 1
        if st.get("display") == "flex":
            flex += 1
        if st.get("text-align") == "center":
            center += 1

        # 独立装饰条
        wm, hm = PX_RE.match(str(st.get("width", ""))), PX_RE.match(str(st.get("height", "")))
        bg = st.get("background-color", "")
        if not bg:
            bg0 = st.get("background", "")
            if bg0 and "gradient" not in bg0:
                bg = bg0
        if wm and hm and bg and int(float(hm.group(1))) <= 12 and not (r.get("text") or "").strip():
            bars.append("%sx%s|%s|r%s|%s" % (
                wm.group(1), hm.group(1), norm_color(bg),
                st.get("border-radius", "0"), align_of(r, byid)))

        # 容器边框
        for side in ("border-bottom", "border-top"):
            bm = BORDER_RE.match(st.get(side, ""))
            if bm and bm.group(2) != "none" and float(bm.group(1)) >= 1:
                borders.append("%s|%spx|%s" % (side.split("-")[1], bm.group(1),
                                               norm_color(bm.group(3))))

        grads.extend(grad_signature(st))

    return {"bars": sorted(bars), "borders": sorted(borders),
            "gradients": sorted(grads), "headings": sorted(headings),
            "scroll": sorted(scroll),
            "images": images, "flex": flex, "center": center}


def multiset_diff(a, b):
    from collections import Counter
    ca, cb = Counter(a), Counter(b)
    missing = ca - cb   # 原文有、我方缺
    extra = cb - ca     # 我方多
    return missing, extra


def main():
    if len(sys.argv) != 3:
        sys.exit("用法：python diff_style.py <原文> <我方渲染.html>")
    orig, mine = inventory(sys.argv[1]), inventory(sys.argv[2])

    print("维度          原文 / 我方")
    ok = True
    for key in ("images", "flex"):
        match = orig[key] == mine[key]
        ok &= match
        print("%-12s  %s / %s   %s" % (key, orig[key], mine[key],
                                       "OK" if match else "✗"))
    # center 仅作参考：原文常因未闭合标签对同一内容多层居中包裹，我方更干净，计数不必相等
    print("%-12s  %s / %s   参考（冗余嵌套，不作为门槛）"
          % ("center", orig["center"], mine["center"]))
    for key in ("scroll", "headings", "bars", "borders", "gradients"):
        missing, extra = multiset_diff(orig[key], mine[key])
        match = not missing and not extra
        ok &= match
        print("%-12s  %d / %d   %s" % (key, len(orig[key]), len(mine[key]),
                                       "OK" if match else "✗"))
        for item, n in missing.items():
            print("    缺失 ×%d  %s" % (n, item))
        for item, n in extra.items():
            print("    多余 ×%d  %s" % (n, item))

    print("\n结论：%s" % ("装饰/结构保真一致" if ok else "存在装饰差异，需修正后再合并"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
