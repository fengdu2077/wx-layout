#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题：蓝白杂志（blue-editorial）
=============================
默认主题。视觉参数提取自目标公众号原文；每个 role 一个渲染函数。
渲染函数签名：render_x(b, c)
  b = wx_core.Block（pos / fields / blocks / bullet）
  c = wx_core.Engine（c.leaf / c.inline / c.esc_attr / c.t 令牌）
"""

THEME = {
    "name": "blue-editorial",
    "label": "蓝白杂志",
    "version": "1.0",
    "containers": [],
    "tokens": {
        "BLUE": "#2563eb",
        "BLUE_BRIGHT": "#3b82f6",
        "BORDER_BLUE": "#dbeafe",
        "INK": "#111827",
        "BOLD_INK": "rgb(17,24,39)",
        "TEXT": "#374151",
        "MUTED": "#9ca3af",
        "PAGE_BG": "#ffffff",
        "FONT": ("'IBM Plex Sans',-apple-system,system-ui,'PingFang SC',"
                 "'Hiragino Sans GB','Microsoft YaHei',sans-serif"),
    },
}


# ---------------- 正文 ----------------

def render_para(b, c):
    t = c.t
    text = ("• " if b.bullet else "") + b.fields.get("text", "")
    return (
        '<section style="margin-top:20px;font-family:%s;">'
        '<p style="margin:0;font-size:15px;line-height:1.95;text-align:justify;'
        'color:%s;letter-spacing:0;">%s</p></section>'
    ) % (t["FONT"], t["TEXT"], c.leaf(text))


# ---------------- 刊头 ----------------

def render_issue(b, c):
    t = c.t
    column, date = b.get(0), b.get(1)
    cover = b.fields.get("image", "")
    texts = [e["text"] for e in b.blocks if e["type"] in ("para", "heading")]
    label = texts[0] if texts else "EDITOR'S NOTE"
    leads = texts[1:]
    lead_html = "".join(
        '<p style="margin:%s;font-size:15px;font-weight:900;line-height:1.7;color:%s;">%s</p>'
        % ("0 0 7px" if j < len(leads) - 1 else "0", t["INK"], c.leaf(p))
        for j, p in enumerate(leads))
    return (
        '<section style="background:#ffffff;border:1px solid %s;border-radius:12px;'
        'overflow:hidden;box-shadow:0 4px 14px rgba(37,99,235,0.06);">'
        '<section style="padding:13px 16px 12px;display:flex;align-items:center;gap:8px;">'
        '<span style="width:7px;height:7px;background:%s;border-radius:50%%;display:inline-block;overflow:hidden;">'
        '<span leaf="">&nbsp;</span></span>'
        '<span style="font-size:9px;font-weight:800;letter-spacing:0;color:%s;">%s</span>'
        '<span style="height:1px;background:linear-gradient(90deg,#bfdbfe,rgba(191,219,254,0));'
        'flex:1;display:inline-block;"><span leaf="">&nbsp;</span></span>'
        '<span style="font-size:9px;font-weight:700;color:%s;">%s</span></section>'
        '<figure style="margin:0;line-height:0;"><span leaf="">'
        '<img src="%s" style="max-width:100%%;height:auto;display:block;margin:0 auto;" />'
        '</span></figure>'
        '<section style="padding:15px 17px 17px;background:linear-gradient(135deg,#eff6ff,#ffffff);'
        'border-top:1px solid %s;">'
        '<p style="margin:0 0 8px;font-size:9px;font-weight:800;letter-spacing:0;color:%s;">%s</p>'
        '%s</section></section>'
    ) % (t["BORDER_BLUE"], t["BLUE"], t["BLUE"], c.leaf(column), t["MUTED"], c.leaf(date),
         c.esc_attr(cover), t["BORDER_BLUE"], t["BLUE"], c.leaf(label), lead_html)


# ---------------- 章节标题 ----------------

def render_part(b, c):
    t = c.t
    num, title, en = b.get(0), b.get(1), b.get(2)
    return (
        '<section style="margin-top:60px;font-family:%s;">'
        '<section style="display:flex;align-items:center;gap:16px;">'
        '<section style="text-align:center;flex-shrink:0;">'
        '<p style="margin:0;font-size:34px;font-weight:800;color:%s;line-height:1;letter-spacing:0;">%s</p>'
        '<p style="margin:3px 0 0;font-size:8px;font-weight:700;color:%s;letter-spacing:0;">%s</p>'
        '</section><section style="flex:1;min-width:0;">'
        '<p style="margin:0 0 3px;font-size:22px;font-weight:800;color:%s;line-height:1.35;'
        'letter-spacing:0;word-break:break-word;">%s</p>'
        '<p style="margin:0;font-size:10px;font-weight:700;color:%s;letter-spacing:0;">%s</p>'
        '</section></section></section>'
    ) % (t["FONT"], t["BLUE"], c.leaf(num), t["MUTED"], c.leaf("PART"),
         t["BLUE"], c.leaf(title), t["BLUE_BRIGHT"], c.leaf(en.upper()))


# ---------------- 小标题 ----------------

def render_sub(b, c):
    t = c.t
    title = b.get(0)
    return (
        '<section style="margin-top:32px;"><p style="margin:0;font-size:16px;font-weight:800;'
        'color:%s;letter-spacing:0;line-height:1.8;">'
        '<span style="width:4px;height:14px;background:%s;border-radius:2px;display:inline-block;'
        'vertical-align:-2px;margin-right:9px;"></span>%s</p></section>'
    ) % (t["BLUE"], t["BLUE"], c.leaf(title))


# ---------------- 截图卡片 ----------------

def render_shot(b, c):
    t = c.t
    src, caption = b.get(0), b.get(1)
    cap = ('<figcaption style="margin-top:9px;font-size:12px;color:%s;text-align:center;'
           'letter-spacing:0;line-height:1.6;">%s</figcaption>'
           % (t["MUTED"], c.leaf(caption))) if caption else ""
    return (
        '<section style="margin-top:24px;"><figure style="margin:0;">'
        '<section style="background:#ffffff;border:1px solid %s;border-radius:12px;padding:6px;'
        'overflow:hidden;box-shadow:0 3px 12px rgba(37,99,235,0.06);">'
        '<span leaf=""><img src="%s" style="max-width:100%%;height:auto;display:block;'
        'margin:0 auto;border-radius:8px;" /></span></section>%s</figure></section>'
    ) % (t["BORDER_BLUE"], c.esc_attr(src), cap)


# ---------------- 引用 ----------------

def render_quote(b, c):
    t = c.t
    who = b.get(0)
    tag = ('<p style="margin:0 0 6px;font-size:11px;font-weight:800;letter-spacing:0;color:%s;">%s</p>'
           % (t["BLUE"], c.leaf(who))) if who else ""
    paras = b.fields["paras"]
    body = "".join(
        '<p style="margin:%s;font-size:14px;line-height:1.85;color:%s;letter-spacing:0;">%s</p>'
        % ("0 0 7px" if j < len(paras) - 1 else "0", t["TEXT"], c.leaf(p))
        for j, p in enumerate(paras))
    return (
        '<section style="margin-top:20px;padding:12px 14px;background:#f8fafc;'
        'border-left:3px solid %s;border-radius:0 8px 8px 0;">%s%s</section>'
    ) % (t["BLUE"], tag, body)


# ---------------- 视频位 ----------------

def render_video(b, c):
    # 视频只能在公众号后台从素材库引用、是播放框，无法样式化；统一走内核占位块（虚线框 + 替换提示）。
    return c.video_placeholder(b)


# ---------------- END ----------------

def render_end(b, c):
    t = c.t
    return (
        '<section style="margin:26px 4px 22px;display:flex;align-items:center;gap:12px;">'
        '<span style="height:1px;background:linear-gradient(90deg,rgba(37,99,235,0),#93c5fd);'
        'flex:1;display:inline-block;"><span leaf="">&nbsp;</span></span>'
        '<span style="font-size:9px;font-weight:800;letter-spacing:0;color:%s;">%s</span>'
        '<span style="height:1px;background:linear-gradient(90deg,#93c5fd,rgba(37,99,235,0));'
        'flex:1;display:inline-block;"><span leaf="">&nbsp;</span></span></section>'
    ) % (t["BLUE"], c.leaf("END"))


# ---------------- 作者卡片 ----------------

def render_author(b, c):
    t = c.t
    name, role = b.get(0), b.get(1)
    intro = " ".join(b.fields["paras"])
    avatar = name.strip()[0] if name.strip() else "?"
    return (
        '<section style="margin:0 4px 24px;padding:18px;'
        'background:linear-gradient(135deg,#f0f7ff,#ffffff);border:1px solid %s;border-radius:12px;">'
        '<section style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">'
        '<section style="width:38px;height:38px;border-radius:50%%;background:%s;text-align:center;'
        'line-height:38px;flex-shrink:0;"><span style="font-size:17px;font-weight:900;color:#ffffff;">%s</span></section>'
        '<section style="min-width:0;"><p style="margin:0 0 2px;font-size:14px;font-weight:900;color:%s;">%s</p>'
        '<p style="margin:0;font-size:9px;color:%s;letter-spacing:0;">%s</p></section></section>'
        '<p style="margin:0 0 10px;font-size:13px;line-height:1.8;color:%s;">%s</p>'
        '<p style="font-size:9px;color:%s;letter-spacing:0;margin:14px 0 0;text-align:center;">%s</p>'
        '</section>'
    ) % (t["BORDER_BLUE"], t["BLUE"], avatar, t["INK"], c.leaf(name),
         t["MUTED"], c.leaf(role.upper()), t["TEXT"], c.leaf(intro.strip()),
         t["MUTED"], c.leaf("THANKS FOR READING"))


# ---------------- Card（全字段 / 纵向，机制样板） ----------------

def render_card(b, c):
    t = c.t
    f = b.fields
    image = f.get("image", "")
    title = f.get("heading") or (f["paras"][0] if f["paras"] else "")
    paras = f["paras"]
    if f.get("heading") and paras:
        summary = paras
    elif paras:
        summary = paras[1:]
    else:
        summary = []
    link = f.get("link", "")
    action = f["links"][0]["text"] if f["links"] else "阅读更多"

    img = ('<span leaf=""><img src="%s" style="width:100%%;height:160px;object-fit:cover;display:block;" /></span>'
           % c.esc_attr(image)) if image else ""
    sum_html = "".join(
        '<p style="margin:%s;font-size:13.5px;line-height:1.8;color:%s;">%s</p>'
        % ("0 0 7px" if j < len(summary) - 1 else "0", t["TEXT"], c.leaf(p))
        for j, p in enumerate(summary))
    btn = ('<a href="%s" style="display:inline-block;margin-top:10px;background:%s;color:#ffffff;'
           'font-size:12px;font-weight:700;border-radius:7px;padding:6px 16px;text-decoration:none;">%s</a>'
           % (link, t["BLUE"], c.leaf(action))) if link else ""
    return (
        '<section style="margin-top:24px;"><section style="background:#ffffff;border:1px solid %s;'
        'border-radius:12px;overflow:hidden;box-shadow:0 4px 14px rgba(37,99,235,0.06);">'
        '%s<section style="padding:16px 17px 17px;">'
        '<p style="margin:0 0 8px;font-size:17px;font-weight:900;color:%s;">%s</p>'
        '%s%s</section></section></section>'
    ) % (t["BORDER_BLUE"], img, t["INK"], c.leaf(title), sum_html, btn)


ROLES = {
    "para": render_para,
    "issue": render_issue,
    "part": render_part,
    "sub": render_sub,
    "shot": render_shot,
    "quote": render_quote,
    "video": render_video,
    "end": render_end,
    "author": render_author,
    "card": render_card,
}
