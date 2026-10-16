#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题：暖棕手记（warm-brown-journal）
================================
复刻自公众号「角落里的AI世界 / 角落实验室 · 旅行手记」。
暖调旅行杂志风：暖棕 / 淡粉 / 奶油配色，渐变标题字、圆角胶囊标签与序号牌。

渲染函数签名：render_x(b, c)
  b = wx_core.Block（pos / kw / fields / blocks / bullet）
  c = wx_core.Engine（c.leaf / c.inline / c.esc_attr / c.t 令牌）

本主题用到的模块（见 references 或 tools\\analysis 的真实抽取）：
  issue 角落实验室|旅行手记|文章标题
  part  编号|中文标题|英文标签
  shot  图片地址|图注（可加 |round=1 走圆角）
  end   （可给一句致谢，默认已内置）
  正文 15px/1.85/justify；**橙色强调**；==卡其高亮（引用语句）==
其余 role（sub/quote/video/author/card）由内核 fallback 降级。
"""

import html as html_mod
import re

_MARK_RE = re.compile(r"==([^=\n]+)==")


THEME = {
    "name": "warm-brown-journal",
    "label": "暖棕手记",
    "version": "1.0",
    "containers": [],
    "tokens": {
        # 通用槽位（内核 / render 使用）
        "BLUE": "rgb(250,124,33)",       # 链接 / 主强调色（橙）
        "BOLD_INK": "rgb(250,124,33)",   # ** 加粗 → 橙色
        "INK": "#383838",
        "TEXT": "#383838",
        "MUTED": "#888888",
        "PAGE_BG": "#ffffff",
        "FONT": ('"PingFang SC NEW",system-ui,-apple-system,"Helvetica Neue",'
                 '"Hiragino Sans GB","Microsoft YaHei UI","Microsoft YaHei",'
                 'Arial,sans-serif'),
        # 暖棕配色（真实值）
        "KHAKI": "#6E6248",
        "SLATE": "#2F3840",
        "MAUVE": "#8F7373",
        "DUSTY": "#A89090",
        "PINK": "#E8D5D5",
        "PINK_DEEP": "#CFB7B7",
        "CREAM": "#F4ECD7",
        "TAG1_BG": "#F0E4E4",
        "TAG1_FG": "#6E5353",
        # 渐变（真实值）
        "TITLE_GRAD": "linear-gradient(90deg,#2d2d2d 0%,#6e6248 58%,#a89090 100%)",
        "PART_GRAD": "linear-gradient(90deg,#2f3840 0%,#8f7373 58%,#cfb7b7 100%)",
        "BADGE_GRAD": "linear-gradient(135deg,#8f7373 0%,#cfb7b7 100%)",
        "HIGHLIGHT": "linear-gradient(transparent 62%,#e8d5d5 62%,#e8d5d5 90%,transparent 90%)",
    },
}


# ---------------- 行内（主题本地扩展：== 卡其高亮） ----------------

def warm_inline(text, c):
    """先抽出 ==x==（卡其字+粉色高亮），其余交给内核 inline（**橙色 / 链接）。"""
    stash = {}

    def keep(m):
        k = "\x01%d\x01" % len(stash)
        stash[k] = m.group(1)
        return k

    tmp = _MARK_RE.sub(keep, text)
    out = c.inline(tmp)
    for k, inner in stash.items():
        frag = (
            '<strong style="margin:0;padding:0 2px;font-weight:700;color:%s;'
            'background-image:%s;background-repeat:no-repeat;">%s</strong>'
        ) % (c.t["KHAKI"], c.t["HIGHLIGHT"], html_mod.escape(inner, quote=False))
        out = out.replace(k, frag)
    return out


def warm_leaf(text, c):
    return '<span leaf="">%s</span>' % warm_inline(text, c)


# ---------------- 正文 ----------------

def render_para(b, c):
    text = ("• " if b.bullet else "") + b.fields.get("text", "")
    return (
        '<section style="margin:0 0 20px;"><p style="margin:0;font-size:15px;'
        'line-height:1.85;text-align:justify;color:%s;letter-spacing:0;">%s</p></section>'
    ) % (c.t["INK"], warm_leaf(text, c))


# ---------------- 刊头：双胶囊标签 + 渐变标题 + 分隔点 ----------------

def _pill(txt, bg, fg, margin, c):
    if not txt:
        return ""
    return (
        '<span style="display:inline-block;background:%s;color:%s;border-radius:980px;'
        'padding:4px 10px;font-size:11px;line-height:1.4;margin:%s;">%s</span>'
        % (bg, fg, margin, c.leaf(txt)))


def render_issue(b, c):
    t = c.t
    tag1, tag2, title = b.get(0), b.get(1), b.get(2)
    pills = (
        '<section style="margin:0 0 18px;line-height:1;">'
        + _pill(tag1, t["TAG1_BG"], t["TAG1_FG"], "0 6px 0 0", c)
        + _pill(tag2, t["CREAM"], t["KHAKI"], "0", c)
        + '</section>')
    h1 = (
        '<h1 style="margin:0 0 26px;font-size:29px;line-height:1.34;font-weight:780;'
        'letter-spacing:-0.02em;color:%s;background-image:%s;background-repeat:no-repeat;'
        '-webkit-background-clip:text;background-clip:text;'
        '-webkit-text-fill-color:transparent;">%s</h1>'
        % (t["INK"], t["TITLE_GRAD"], c.leaf(title)))
    dot = (
        '<section style="width:64px;height:4px;margin:0 0 26px;border-radius:980px;'
        'background-color:%s;"></section>'
        % t["PINK_DEEP"])
    return (
        '<section style="margin:0 10px 34px;padding:26px 10px 4px;">%s%s%s</section>'
        % (pills, h1, dot))


# ---------------- 章节标题：序号牌 + 英文标签 + 渐变中文标题 ----------------

def render_part(b, c):
    t = c.t
    num, title, en = b.get(0), b.get(1), b.get(2)
    badge = (
        '<span style="display:inline-block;background-color:%s;background-image:%s;color:%s;'
        'font-size:18px;font-weight:900;padding:4px 14px;border-radius:6px;margin-right:14px;'
        'line-height:1.3;">%s</span>'
        % (t["DUSTY"], t["BADGE_GRAD"], t["CREAM"], c.leaf(num)))
    head = (
        '<span style="min-width:0;">'
        '<p style="margin:0 0 2px;font-size:10px;font-weight:700;letter-spacing:0;color:%s;">%s</p>'
        '<span style="display:block;font-size:18px;font-weight:800;line-height:1.5;color:%s;'
        'background-image:%s;background-repeat:no-repeat;-webkit-background-clip:text;'
        'background-clip:text;-webkit-text-fill-color:transparent;">%s</span>'
        '</span>'
        % (t["KHAKI"], c.leaf(en.upper()), t["SLATE"], t["PART_GRAD"], c.leaf(title)))
    return (
        '<section style="display:flex;align-items:center;margin:18px 0 20px;'
        'padding-bottom:14px;border-bottom:3px solid %s;">%s%s</section>'
        % (t["PINK_DEEP"], badge, head))


# ---------------- 截图：居中图片 + 居中灰色图注 ----------------

def render_shot(b, c):
    t = c.t
    src, caption = b.get(0), b.get(1)
    rounded = b.kw.get("round", "") in ("1", "true", "yes", "圆角")
    if rounded:
        wrap_m, img_style = "28px 0 30px", ("max-width:100%;height:auto;display:block;"
                                            "margin:0 auto;border-radius:12px;")
    else:
        wrap_m, img_style = "0 0 8px", ("max-width:100%;height:auto;display:block;"
                                        "margin:0 auto;")
    fig = (
        '<section style="text-align:center;margin:%s;"><span leaf="">'
        '<img src="%s" style="%s" /></span></section>'
        % (wrap_m, c.esc_attr(src), img_style))
    cap = (
        '<p style="margin:10px 0 20px;font-size:11px;line-height:1.65;text-align:center;'
        'color:%s;">%s</p>' % (t["MUTED"], c.leaf(caption))) if caption else ""
    return fig + cap


# ---------------- END：The End + 致谢 ----------------

def render_end(b, c):
    thanks = b.get(0) or "真诚感谢你的每一个❤️和👍"
    the_end = (
        '<section style="text-align:center;margin:28px 0 16px;">'
        '<p style="margin:0;font-size:16px;letter-spacing:0;">%s</p></section>'
        % c.leaf("—The End—"))
    thanks_html = (
        '<p style="margin:0 0 18px;font-size:14px;line-height:1.85;text-align:center;'
        'color:rgb(102,102,102);">%s</p>' % c.leaf(thanks))
    return the_end + thanks_html


ROLES = {
    "para": render_para,
    "issue": render_issue,
    "part": render_part,
    "shot": render_shot,
    "end": render_end,
}
