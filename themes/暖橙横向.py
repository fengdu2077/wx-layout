#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题：暖橙横向（warm-horizontal）
================================
对照主题，用于验证「role + 字段契约」机制：
  - card 只取 title / summary，不渲染封面图与按钮，且为横向布局；
  - 只实现 card 与 para，其余 role 由 wx_core 默认 fallback 降级（不报错）。
"""

THEME = {
    "name": "warm-horizontal",
    "label": "暖橙横向",
    "version": "1.0",
    "containers": [],
    "tokens": {
        "BLUE": "#ea8a2e",          # 该主题主色用暖橙
        "BLUE_BRIGHT": "#f59e0b",
        "BORDER_BLUE": "#fed7aa",
        "INK": "#7c2d12",
        "BOLD_INK": "rgb(124,45,18)",
        "TEXT": "#78350f",
        "MUTED": "#b45309",
        "PAGE_BG": "#fffaf3",
        "FONT": ("-apple-system,system-ui,'PingFang SC','Microsoft YaHei',sans-serif"),
    },
}


def render_para(b, c):
    t = c.t
    text = ("• " if b.bullet else "") + b.fields.get("text", "")
    return (
        '<section style="margin-top:20px;"><p style="margin:0;font-size:15px;line-height:1.95;'
        'text-align:justify;color:%s;letter-spacing:0;">%s</p></section>'
    ) % (t["TEXT"], c.leaf(text))


def render_card(b, c):
    """横向：左侧小色块 + 右侧标题/摘要；明确不渲染图片与按钮。"""
    t = c.t
    f = b.fields
    title = f.get("heading") or (f["paras"][0] if f["paras"] else "")
    paras = f["paras"]
    summary = paras if f.get("heading") else (paras[1:] if paras else [])

    sum_html = "".join(
        '<p style="margin:%s;font-size:13.5px;line-height:1.8;color:%s;">%s</p>'
        % ("0 0 6px" if j < len(summary) - 1 else "0", t["TEXT"], c.leaf(p))
        for j, p in enumerate(summary))
    return (
        '<section style="margin-top:24px;"><section style="display:flex;align-items:center;gap:14px;'
        'background:#fffaf3;border:1px solid %s;border-radius:12px;padding:15px 16px;">'
        # 左侧色块（横向布局标志，替代封面图）
        '<span style="width:40px;height:40px;border-radius:9px;background:#fed7aa;flex-shrink:0;'
        'display:flex;align-items:center;justify-content:center;">'
        '<span style="width:14px;height:14px;border-radius:4px;background:%s;display:inline-block;"></span></span>'
        # 右侧标题 + 摘要
        '<span style="flex:1;min-width:0;">'
        '<p style="margin:0 0 6px;font-size:16px;font-weight:900;color:%s;">%s</p>'
        '%s</span>'
        # 注意：fields.image / link / action 在此主题下被有意忽略，不输出任何图与按钮
        '</section></section>'
    ) % (t["BORDER_BLUE"], t["BLUE"], t["INK"], c.leaf(title), sum_html)


ROLES = {
    "para": render_para,
    "card": render_card,
}
