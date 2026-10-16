#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题：翠绿科技（green-tech）
================================
复刻自公众号「阿虎玩AI」技术长文（R2T2 真流式识别 / T3PO 流式同传）。
翠绿主色 + 圆角卡片 + 深色终端代码块；行内标记丰富（绿色加粗、黄/粉/绿下划线、代码胶囊）。

渲染函数签名：render_x(b, c)
  b = wx_core.Block（pos / kw / fields / blocks / bullet）
  c = wx_core.Engine（leaf / inline / esc_attr / t）

本主题行内扩展（green_inline，自定义，不依赖内核 ** / 链接默认样式）：
  **x**   绿色加粗（强调词）
  ==x==   绿色加粗 + 黄色 3px 下划线（关键术语）
  ~~x~~   粉色 2px 下划线（反例/风险词）
  ++x++   浅绿 2px 下划线（模型名/版本/参数）
  `x`     灰色代码胶囊
  @@x@@   琥珀代码胶囊（参考入口）
  [x](url) 绿色下划线链接
模块：
  issue 标签|日期|眉题|大标题行1|大标题行2|副说明|横幅文字|胶囊1|胶囊2
  part  编号|中文标题|英文标签（编号为 /// 时小标签自动变 LAST）
  sub   小标题（绿色左竖条）
  shot  图片|图注
  note/tip 绿色提示框（首段位置槽=可选标题）
  warning  琥珀警示框
  step  编号|标题（容器，可含一行说明，勿嵌套 code）
  code lang=bash 深色终端代码块
  table 简单竖线表格（绿色表头、首列浅绿）
  cta   三连卡片
"""

import html as html_mod
import re

THEME = {
    "name": "green-tech",
    "label": "翠绿科技",
    "version": "1.0",
    "containers": ["step"],
    "tokens": {
        "BLUE": "#059669",
        "BOLD_INK": "#059669",
        "INK": "#111827",
        "TEXT": "#374151",
        "MUTED": "#9ca3af",
        "LIGHT": "#d1d5db",
        "PAGE_BG": "#ffffff",
        "FONT": ('-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",'
                 '"Microsoft YaHei",sans-serif'),
        "MONO": '"SF Mono",Consolas,Monaco,monospace',
        "AMBER": "#f59e0b",
        "GREEN_BG": "#ecfdf5",
        "GREEN_BG2": "#f0fdf4",
        "AMBER_BG": "#fffbeb",
        "CODE_BG": "#f3f4f6",
        "TERM_BG": "#1e293b",
        "TERM_HEAD": "#0f172a",
        "TERM_FG": "#e2e8f0",
        "HL_GREEN": "#a7f3d0",
        "HL_YELLOW": "#fde68a",
        "HL_PINK": "#fecaca",
        "BORDER_GRAY": "#e5e7eb",
    },
}


# ---------------- 行内（主题本地扩展） ----------------

def green_inline(text, c):
    text = html_mod.escape(text, quote=False)
    stash = {}

    def keep(frag):
        k = "\x01%d\x01" % len(stash)
        stash[k] = frag
        return k

    t = c.t

    def chip(inner, bg, weight):
        return ('<code style="font-family:%s;font-size:13px;color:#1f2937;background:%s;'
                'font-weight:%s;border-radius:4px;padding:2px 6px;">%s</code>'
                % (t["MONO"], bg, weight, inner))

    # 代码胶囊（先抽，内部符号不被后续规则处理）
    text = re.sub(r"`([^`\n]+)`",
                  lambda m: keep(chip(m.group(1), "#f3f4f6", "600")), text)
    text = re.sub(r"@@([^@\n]+)@@",
                  lambda m: keep(chip(m.group(1), "#fde68a", "700")), text)
    # 关键术语：绿粗 + 黄下划线
    text = re.sub(r"==([^=\n]+)==",
                  lambda m: keep('<strong style="color:%s;font-weight:bold;'
                                 'border-bottom:3px solid %s;">%s</strong>'
                                 % (t["BLUE"], t["HL_YELLOW"], m.group(1))), text)
    # 粉色下划线（反例）
    text = re.sub(r"~~([^~\n]+)~~",
                  lambda m: keep('<span style="border-bottom:2px solid %s;">%s</span>'
                                 % (t["HL_PINK"], m.group(1))), text)
    # 浅绿下划线（模型/版本/参数）
    text = re.sub(r"\+\+([^+\n]+)\+\+",
                  lambda m: keep('<span style="font-weight:600;border-bottom:2px solid %s;">%s</span>'
                                 % (t["HL_GREEN"], m.group(1))), text)
    # 绿色加粗
    text = re.sub(r"\*\*([^*]+)\*\*",
                  lambda m: keep('<strong style="color:%s;">%s</strong>'
                                 % (t["BLUE"], m.group(1))), text)
    # 链接
    text = re.sub(r"\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)",
                  lambda m: keep('<a href="%s" style="color:%s;text-decoration:underline;">%s</a>'
                                 % (m.group(2), t["BLUE"], m.group(1))), text)

    for k, frag in stash.items():
        text = text.replace(k, frag)
    return text


def green_leaf(text, c):
    return '<span leaf="">' + green_inline(text, c) + "</span>"


# ---------------- 正文 ----------------

def render_para(b, c):
    text = ("• " if b.bullet else "") + b.fields.get("text", "")
    return (
        '<section style="margin:0 0 8px;"><p style="margin:0;font-size:14px;'
        'line-height:1.9;text-align:justify;color:%s;letter-spacing:0;">%s</p></section>'
    ) % (c.t["TEXT"], green_leaf(text, c))


# ---------------- 刊头（大封面卡） ----------------

def render_issue(b, c):
    t = c.t
    tag, date = b.get(0), b.get(1)
    small, line1, line2 = b.get(2), b.get(3), b.get(4)
    subtitle, banner = b.get(5), b.get(6)
    pill1, pill2 = b.get(7), b.get(8)

    top = (
        '<section style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">'
        '<span style="font-size:11px;color:%s;font-weight:700;">%s</span>'
        '<span style="height:1px;flex:1;background:linear-gradient(to right,rgba(5,150,105,0.6),rgba(5,150,105,0));"></span>'
        '<span style="font-size:10px;color:%s;font-weight:600;">%s</span></section>'
        % (t["BLUE"], green_leaf(tag, c), t["LIGHT"], green_leaf(date, c)))
    eyebrow = ('<p style="margin:0 0 6px;font-size:15px;color:%s;">%s</p>'
               % (t["LIGHT"], green_leaf(small, c))) if small else ""
    h = (
        '<p style="margin:0;font-size:24px;color:%s;font-weight:900;line-height:1.05;">%s</p>'
        '<p style="margin:0 0 16px;font-size:24px;color:%s;font-weight:900;line-height:1.05;">%s</p>'
        % (t["INK"], green_inline(line1, c), t["BLUE"], green_inline(line2, c)))
    bar = '<section style="width:48px;height:3px;border-radius:2px;margin-bottom:16px;background:linear-gradient(to right,rgb(5,150,105),rgba(5,150,105,0));"></section>'
    sub = ('<p style="margin:0 0 18px;font-size:13px;color:%s;line-height:1.7;">%s</p>'
           % (t["MUTED"], green_leaf(subtitle, c))) if subtitle else ""

    def model_pill(x):
        return ('<span style="font-size:8px;color:#ffffff;background:rgba(255,255,255,0.2);'
                'font-weight:600;border-radius:3px;padding:1px 6px;margin-right:6px;">%s</span>'
                % green_leaf(x, c))
    banner_h = (
        '<section style="display:flex;align-items:center;gap:8px;padding:12px 0;margin-top:4px;">'
        '<span style="font-size:12px;color:rgba(255,255,255,0.9);font-weight:600;margin-right:6px;">%s</span>'
        '%s%s</section>'
        % (green_leaf(banner, c), model_pill(pill1), model_pill(pill2)))
    banner_wrap = ('<section style="background:linear-gradient(135deg,#059669,#10b981);'
                   'border-radius:10px;padding:0 20px;">%s</section>' % banner_h)

    return (
        '<section style="width:677px;max-width:100%%;box-sizing:border-box;background:#ffffff;'
        'border-radius:20px;margin:0 0 32px;padding:32px 28px 28px;">%s%s%s%s%s%s</section>'
        % (top, eyebrow, h, bar, sub, banner_wrap))


# ---------------- 横向滑动目录 ----------------

def _toc_card(num, title, sub, active):
    if active:
        return (
            '<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;'
            'background:linear-gradient(135deg,#059669,#10b981);'
            'border-radius:12px;padding:12px;margin-right:8px;">'
            '<p style="margin:0 0 5px;font-size:9px;color:rgba(255,255,255,0.7);font-weight:700;'
            'letter-spacing:1px;">PART %s</p>'
            '<p style="margin:0 0 3px;font-size:13px;color:#ffffff;font-weight:800;">%s</p>'
            '<p style="margin:0;font-size:10px;color:rgba(255,255,255,0.7);">%s</p></section>'
            % (num, title, sub))
    return (
        '<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;'
        'background:#ffffff;border-radius:12px;padding:12px;margin-right:8px;">'
        '<p style="margin:0 0 5px;font-size:9px;color:#9ca3af;font-weight:700;letter-spacing:1px;">PART %s</p>'
        '<p style="margin:0 0 3px;font-size:13px;color:#111827;font-weight:800;">%s</p>'
        '<p style="margin:0;font-size:10px;color:#9ca3af;">%s</p></section>'
        % (num, title, sub))


def render_toc(b, c):
    entries = []
    for ln in b.body_lines:
        if not ln.strip():
            continue
        cells = [x.strip() for x in ln.split("|")]
        if len(cells) >= 2:
            entries.append((cells[0], cells[1], cells[2] if len(cells) > 2 else ""))
    n_parts = sum(1 for e in entries if e[0] != "///")
    head = (
        '<section style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">'
        '<p style="margin:0;font-size:10px;color:#9ca3af;font-weight:600;text-transform:uppercase;'
        'letter-spacing:2px;">📦 %d Parts + Conclusion</p>'
        '<p style="margin:0;font-size:10px;color:#9ca3af;">👉 滑动</p></section>' % n_parts)
    cards = "".join(_toc_card(num, title, sub, i == 0)
                    for i, (num, title, sub) in enumerate(entries))
    # 关键：外层 overflow-x:auto（仅内容超出时才出现滚动条）+ white-space:nowrap；
    # 用 scroll 会常驻滚动条，auto 是「需要时才出现」。卡片自身 white-space:normal 让文字换行。
    return ('<section style="margin:0 20px 32px;">%s'
            '<section style="overflow-x:auto;white-space:nowrap;padding-bottom:8px;">%s</section>'
            '</section>' % (head, cards))


# ---------------- 章节标题 ----------------

def render_part(b, c):
    t = c.t
    num, title, en = b.get(0), b.get(1), b.get(2)
    small = "LAST" if num == "///" else "PART"
    return (
        '<section style="padding:0 20px;margin:24px 0 12px;">'
        '<section style="display:flex;align-items:center;gap:16px;">'
        '<section style="text-align:center;flex-shrink:0;">'
        '<p style="margin:0;font-size:28px;color:%s;font-weight:900;line-height:1;">%s</p>'
        '<p style="margin:2px 0 0;font-size:8px;color:%s;font-weight:700;">%s</p></section>'
        '<span style="width:1px;height:36px;background:%s;"></span>'
        '<section style="min-width:0;">'
        '<p style="margin:0 0 1px;font-size:17px;color:%s;font-weight:900;">%s</p>'
        '<p style="margin:0;font-size:11px;color:%s;font-weight:600;">%s</p>'
        '</section></section></section>'
        % (t["BLUE"], green_leaf(num, c), t["LIGHT"], small, t["BORDER_GRAY"],
           t["INK"], green_leaf(title, c), t["MUTED"], green_leaf(en.upper(), c)))


# ---------------- 小标题（绿色左竖条） ----------------

def render_sub(b, c):
    t = c.t
    return (
        '<section style="margin:28px 0 14px;"><p style="margin:0;font-size:16px;'
        'color:#1c1917;font-weight:800;line-height:1.5;padding-left:10px;'
        'border-left:4px solid %s;">%s</p></section>'
        % (t["BLUE"], green_leaf(b.get(0), c)))


# ---------------- 截图（居中） ----------------

def render_shot(b, c):
    t = c.t
    src, caption = b.get(0), b.get(1)
    img = ('<section style="text-align:center;margin:8px 0;"><span leaf="">'
           '<img src="%s" style="max-width:100%%;height:auto;border-radius:8px;display:block;margin:0 auto;" />'
           '</span></section>' % c.esc_attr(src))
    cap = ('<p style="margin:6px 0 12px;font-size:12px;color:%s;text-align:center;line-height:1.6;">%s</p>'
           % (t["MUTED"], green_leaf(caption, c))) if caption else ""
    return img + cap


# ---------------- 提示框 / 警示框 ----------------

def _callout(b, c, bg, border, label_bg, label_fg):
    title = b.get(0)
    paras = b.fields.get("paras", [])
    head = ('<p style="margin:0 0 8px;"><span style="display:inline-block;font-size:11px;'
            'color:%s;background:%s;font-weight:700;border-radius:4px;padding:2px 10px;">%s</span></p>'
            % (label_fg, label_bg, green_leaf(title, c))) if title else ""
    body = "".join(
        '<p style="margin:0 0 6px;font-size:14px;color:%s;line-height:1.8;">%s</p>'
        % (c.t["TEXT"], green_leaf(p, c)) for p in paras)
    return ('<section style="background:%s;border-radius:0 8px 8px 0;padding:14px 18px;'
            'margin:14px 0;border-left:4px solid %s;">%s%s</section>'
            % (bg, border, head, body))


def render_note(b, c):
    t = c.t
    return _callout(b, c, t["GREEN_BG"], t["BLUE"], t["BLUE"], "#ffffff")


def render_tip(b, c):
    return render_note(b, c)


def render_warning(b, c):
    t = c.t
    return _callout(b, c, t["AMBER_BG"], t["AMBER"], t["AMBER"], "#ffffff")


# ---------------- 步骤 ----------------

def render_step(b, c):
    t = c.t
    num, title = b.get(0), b.get(1)
    paras = b.fields.get("paras", [])
    body = "".join(
        '<p style="margin:6px 0 0;font-size:14px;color:%s;line-height:1.8;">%s</p>'
        % (t["TEXT"], green_leaf(p, c)) for p in paras)
    return (
        '<section style="margin:18px 0 6px;">'
        '<section style="display:flex;align-items:center;gap:10px;">'
        '<span style="display:inline-block;font-size:10px;color:#ffffff;background:%s;'
        'font-weight:700;border-radius:12px;padding:2px 8px;">STEP %s</span>'
        '<h4 style="margin:0;font-size:15px;color:%s;font-weight:800;">%s</h4>'
        '</section>%s</section>'
        % (t["INK"], green_leaf(num, c), t["INK"], green_leaf(title, c), body))


# ---------------- 深色终端代码块 ----------------

def render_code(b, c):
    t = c.t
    lang = b.kw.get("lang") or (b.get(0) if b.pos else "") or "bash"
    lines = b.body_lines
    dots = ('<span style="display:inline-block;width:10px;height:10px;border-radius:50%%;'
            'background:%s;margin-right:6px;"></span>' % "#ff5f56")
    dots += ('<span style="display:inline-block;width:10px;height:10px;border-radius:50%%;'
             'background:%s;margin-right:6px;"></span>' % "#ffbd2e")
    dots += ('<span style="display:inline-block;width:10px;height:10px;border-radius:50%%;'
             'background:%s;margin-right:8px;"></span>' % "#27c93f")
    head = (
        '<section style="display:flex;align-items:center;background:%s;padding:9px 14px;">'
        '%s<span style="font-size:12px;color:#64748b;letter-spacing:1px;">%s</span></section>'
        % (t["TERM_HEAD"], dots, green_leaf(lang, c)))
    code = "".join(
        '<p style="margin:0;font-size:13px;color:%s;line-height:1.6;font-family:%s;white-space:pre;">%s</p>'
        % (t["TERM_FG"], t["MONO"], html_mod.escape(ln, quote=False)) for ln in lines)
    # 正文区 overflow-x:auto：长命令可横向滚动（与原文一致）；外层 margin-bottom:24px。
    return (
        '<section style="background:%s;border-radius:8px;margin:0 0 24px;overflow:hidden;">%s'
        '<section style="padding:11px 14px;overflow-x:auto;">%s</section></section>'
        % (t["TERM_BG"], head, code))


# ---------------- 表格（简单竖线表） ----------------

def _split_row(line):
    return [x.strip() for x in line.strip().strip("|").split("|")]


def render_table(b, c):
    t = c.t
    rows = [ln for ln in b.body_lines if ln.strip()]
    if not rows:
        return ""
    header = _split_row(rows[0])
    body_rows = [r for r in rows[1:] if not re.match(r"^[\s|:\-]+$", r)]
    th = "".join(
        '<th style="color:#ffffff;background:%s;font-weight:700;text-align:left;'
        'padding:8px 10px;border-bottom:1px solid %s;">%s</th>'
        % (t["BLUE"], t["BLUE"], green_leaf(h, c)) for h in header)
    trs = ""
    for r in body_rows:
        cells = _split_row(r)
        tds = ""
        for ci, cell in enumerate(cells):
            first_bg = ("background:%s;" % t["GREEN_BG2"]) if ci == 0 else ""
            tds += ('<td style="padding:8px 10px;border-bottom:1px solid %s;%s">%s</td>'
                    % (t["BORDER_GRAY"], first_bg, green_leaf(cell, c)))
        trs += "<tr>%s</tr>" % tds
    return (
        '<section style="margin:14px 0;"><table style="width:100%%;border-collapse:collapse;'
        'font-size:12px;"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></section>'
        % (th, trs))


# ---------------- 三连 CTA ----------------

def render_cta(b, c):
    t = c.t
    lead = b.fields.get("paras", [""])[0]
    items = [("👍", "点赞", "#ffffff", "#4b5563"),
             ("👀", "在看", "#ffffff", "#4b5563"),
             ("➦", "转发", t["GREEN_BG"], t["BLUE"])]
    cols = "".join(
        '<section style="flex:1;text-align:center;"><section style="display:flex;width:40px;'
        'height:40px;background:%s;border-radius:12px;margin:0 auto 6px;align-items:center;'
        'justify-content:center;font-size:18px;color:%s;">%s</section>'
        '<span style="font-size:10px;font-weight:600;color:%s;">%s</span></section>'
        % (bg, fg, icon, fg, label) for icon, label, bg, fg in items)
    lead_h = ('<p style="margin:0 0 18px;font-size:13px;color:%s;font-weight:bold;line-height:1.6;">%s</p>'
              % (t["INK"], green_leaf(lead, c))) if lead else ""
    return (
        '<section style="background:radial-gradient(circle,#f9fafb 0%%,#f1f5f9 100%%);'
        'text-align:center;border-radius:16px;margin:24px 0;padding:32px 20px;">%s'
        '<section style="display:flex;gap:12px;">%s</section>'
        '<p style="margin:18px 0 0;font-size:10px;color:%s;">%s</p></section>'
        % (lead_h, cols, t["MUTED"], green_leaf("THANKS FOR READING", c)))


ROLES = {
    "para": render_para,
    "issue": render_issue,
    "toc": render_toc,
    "part": render_part,
    "sub": render_sub,
    "shot": render_shot,
    "note": render_note,
    "tip": render_tip,
    "warning": render_warning,
    "step": render_step,
    "code": render_code,
    "table": render_table,
    "cta": render_cta,
}
