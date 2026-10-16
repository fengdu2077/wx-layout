#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
wx_core · 公众号排版工坊共享内核
================================

职责（与具体主题无关、全系统只此一份）：
  1. 解析：Markdown + `:::模块` → IR（块列表；每块 = role + 字段 fields + 原始元素 blocks）
  2. 微信适配：leaf / textstyle 内部格式、行内 inline（加粗 / 链接）
  3. 主题加载：从 themes\*.py 动态加载；主题只提供「视觉模板 + 模块契约」
  4. 路由渲染：每个 role 交给主题对应渲染函数；主题未实现则 fallback 降级
  5. 复制页：ClipboardItem 直写原始 HTML

主题接口（themes\xxx.py）：
  THEME = {"name":..., "label":..., "tokens":{...}, "containers":[...(额外容器 role)]}
  def render_<role>(b, c): ...      # b=IRBlock, c=Engine（c.leaf/c.inline/c.t）
  ROLES = {role: fn, ...}
  def fallback(b, c): ...           # 可选
"""

import glob
import html as html_mod
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
THEMES_DIR = os.path.join(HERE, "themes")

# 默认带 body 的容器 role（以单独一行 `:::` 闭合）；主题可用 THEME["containers"] 追加
DEFAULT_CONTAINERS = {
    "issue", "quote", "author", "card", "gallery", "callout", "faq", "timeline",
    "compare", "steps", "highlights", "profile", "toc", "stats", "keyvalue",
    "note", "tip", "warning", "code", "table", "cta", "audio",
}
# 明确的单行 role（不带 body）
SINGLETON_ROLES = {"part", "sub", "shot", "video", "end", "divider", "image"}


# ============================ IR 数据结构 ============================

class Block:
    """一个语义块。"""
    def __init__(self, role, pos=None, kw=None, body_lines=None, bullet=False):
        self.role = role
        self.pos = pos or []          # 指令行 `|` 分割的位置参数
        self.kw = kw or {}           # key=value 参数
        self.body_lines = body_lines or []
        self.bullet = bullet         # 正文是否为列表项
        self.blocks = []             # body 解析出的通用元素
        self.fields = {}             # 抽取的命名字段

    def get(self, i, default=""):
        return self.pos[i] if i < len(self.pos) else default


# ============================ Markdown 元素解析 ============================

_IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_URL_RE = re.compile(r"^(https?://\S+|[\w\-./\\]+\.(?:png|jpe?g|gif|webp|bmp))\s*$", re.I)
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_LINK_ONLY_RE = re.compile(r"^\[([^\]]+)\]\((https?://[^)\s]+)\)\s*$")


def parse_body_elements(lines):
    """把 body 行解析成通用 markdown 元素，并抽取便捷字段。"""
    elements = []
    # 先按空行分段
    paras, buf = [], []
    for ln in lines + [""]:
        if ln.strip() == "":
            if buf:
                paras.append(buf); buf = []
        else:
            buf.append(ln)
    if buf:
        paras.append(buf)

    for plines in paras:
        # 纯列表段
        if all(re.match(r"^\s*[-*]\s+", x) for x in plines):
            items = [re.sub(r"^\s*[-*]\s+", "", x).strip() for x in plines]
            elements.append({"type": "list", "items": items})
            continue
        for x in plines:
            s = x.strip()
            m = _IMG_RE.match(s)
            if m:
                elements.append({"type": "image", "alt": m.group(1), "src": m.group(2)})
                continue
            m = _HEADING_RE.match(s)
            if m:
                elements.append({"type": "heading", "level": len(m.group(1)),
                                 "text": m.group(2).strip()})
                continue
            if _URL_RE.match(s):
                elements.append({"type": "image", "alt": "", "src": s})
                continue
            ml = _LINK_ONLY_RE.match(s)
            if ml:
                elements.append({"type": "link", "text": ml.group(1), "href": ml.group(2)})
                continue
            elements.append({"type": "para", "text": s})

    links = [{"text": e["text"], "href": e["href"]}
             for e in elements if e["type"] == "link"]
    links += [{"text": m.group(1), "href": m.group(2)}
              for e in elements if e["type"] == "para"
              for m in _LINK_RE.finditer(e["text"])]
    fields = {
        "images": [e["src"] for e in elements if e["type"] == "image"],
        "paras": [e["text"] for e in elements if e["type"] == "para"],
        "headings": [e["text"] for e in elements if e["type"] == "heading"],
        "lists": [e["items"] for e in elements if e["type"] == "list"],
        "links": links,
    }
    fields["image"] = fields["images"][0] if fields["images"] else ""
    fields["link"] = fields["links"][0]["href"] if fields["links"] else ""
    fields["heading"] = fields["headings"][0] if fields["headings"] else ""
    return elements, fields


# ============================ 顶层解析（md → IR） ============================

def _parse_head(head):
    """`a | b | k=v` → 位置参数 + 键值。"""
    pos, kw = [], {}
    for part in [x.strip() for x in head.split("|")]:
        if not part:
            continue
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*=\s*(.+)$", part)
        if m:
            kw[m.group(1)] = m.group(2).strip()
        else:
            pos.append(part)
    return pos, kw


def parse(md_text, containers):
    # 先剥离 HTML 注释（写法说明 / 文档注释不进入内容；注释行随之变空行，保证正确分段）
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)
    lines = md_text.splitlines()
    out, i = [], 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        if not s.startswith(":::"):
            buf = []
            while i < len(lines) and not lines[i].strip().startswith(":::"):
                buf.append(lines[i]); i += 1
            text = "\n".join(buf)
            chunks = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            for chunk in chunks:
                clines = [ln for ln in chunk.split("\n") if ln.strip()]
                items = [ln for ln in clines if re.match(r"^\s*[-*]\s+", ln)]
                if items and len(items) == len(clines):
                    for it in items:
                        b = Block("para", bullet=True)
                        b.blocks, b.fields = parse_body_elements([it])
                        b.fields["text"] = re.sub(r"^\s*[-*]\s+", "", it).strip()
                        out.append(b)
                else:
                    b = Block("para")
                    b.blocks, b.fields = parse_body_elements(clines)
                    b.fields["text"] = " ".join(x.strip() for x in clines)
                    out.append(b)
            continue

        m = re.match(r"^:::([A-Za-z_][\w\-]*)\s*(.*)$", s)
        if not m:
            i += 1; continue
        role, head = m.group(1), m.group(2)
        pos, kw = _parse_head(head)

        if role in containers:
            body, j = [], i + 1
            while j < len(lines) and lines[j].strip() != ":::":
                body.append(lines[j]); j += 1
            b = Block(role, pos, kw, body)
            b.blocks, b.fields = parse_body_elements(body)
            out.append(b)
            i = j + 1
        else:
            b = Block(role, pos, kw)
            out.append(b)
            i += 1
    return out


# ============================ 主题加载 ============================

def list_themes():
    themes = []
    for path in sorted(glob.glob(os.path.join(THEMES_DIR, "*.py"))):
        if os.path.basename(path).startswith("_"):
            continue
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            mod = load_theme(name)
            label = mod.THEME.get("label", name)
            themes.append((name, label))
        except Exception:
            themes.append((name, name))
    return themes


def load_theme(name):
    path = os.path.join(THEMES_DIR, name + ".py")
    if not os.path.exists(path):
        # 允许用 label / 代号模糊匹配
        for cand, _ in list_themes():
            pass
        raise FileNotFoundError("主题不存在：%s（%s）" % (name, path))
    spec = importlib.util.spec_from_file_location("theme_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ============================ 渲染引擎 ============================

class Engine:
    def __init__(self, theme):
        self.theme = theme
        self.t = theme.THEME.get("tokens", {})

    # -- 微信适配 / 行内 --
    def inline(self, text):
        text = html_mod.escape(text, quote=False)
        stash = {}

        def keep(frag):
            k = "\x00%d\x00" % len(stash); stash[k] = frag; return k

        text = re.sub(
            r"\*\*([^*]+)\*\*",
            lambda m: keep('<span textstyle="" style="color:%s;font-weight:600;">%s</span>'
                           % (self.t.get("BOLD_INK", "rgb(17,24,39)"), m.group(1))),
            text)
        text = re.sub(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
            lambda m: keep('<a href="%s" style="color:%s;text-decoration:underline;">%s</a>'
                           % (m.group(2), self.t.get("BLUE", "#2563eb"), m.group(1))),
            text)
        for k, v in stash.items():
            text = text.replace(k, v)
        return text

    def leaf(self, text):
        return '<span leaf="">%s</span>' % self.inline(text)

    def esc_attr(self, text):
        return html_mod.escape(text, quote=True)

    # -- 渲染 --
    def containers(self):
        extra = set(self.theme.THEME.get("containers", []))
        return (DEFAULT_CONTAINERS | extra) - SINGLETON_ROLES

    def render(self, md_text):
        blocks = parse(md_text, self.containers())
        roles = getattr(self.theme, "ROLES", {})
        pieces = []
        for b in blocks:
            fn = roles.get(b.role)
            if fn:
                pieces.append(fn(b, self))
            elif hasattr(self.theme, "fallback"):
                pieces.append(self.theme.fallback(b, self))
            else:
                pieces.append(self._default_fallback(b))
        body = "".join(pieces)
        t = self.t
        return (
            '<section style="max-width:677px;margin:0 auto;padding:8px 16px;box-sizing:border-box;'
            'background:%s;color:%s;font-family:%s;line-height:1.75;">%s</section>'
        ) % (t.get("PAGE_BG", "#ffffff"), t.get("TEXT", "#374151"),
             t.get("FONT", ""), body)

    def video_placeholder(self, b):
        """视频卡片：上方「视频位」（后台把素材库视频插进来），下方保留标题/说明文字。

        视频本身是公众号素材库引用的播放框，无法用网页样式生成；但它可以放进一个卡片框里
        （实测粘贴到后台后，视频留在框内、下方文字不丢失）。因此渲染成「视频位 + 下方文字」：
        作者把光标放进上方视频位、插入视频，下方标题/说明保持不变。
        """
        title = b.get(0)
        desc = b.get(1)
        # 上方视频位：提示文字会被后台插入的视频替换
        slot = (
            '<section style="width:100%;aspect-ratio:16/9;min-height:180px;background:#0f172a;'
            'display:flex;flex-direction:column;align-items:center;justify-content:center;'
            'text-align:center;padding:16px;box-sizing:border-box;">'
            '<p style="margin:0;font-size:14px;font-weight:800;color:#e2e8f0;letter-spacing:0;">'
            '▶ 视频位置｜在此插入视频</p>'
            '<p style="margin:8px 0 0;font-size:11px;line-height:1.7;color:#94a3b8;letter-spacing:0;">'
            '将光标放本框，点后台工具栏「视频」，从素材库上传/选择对应视频，替换本提示。</p>'
            '</section>'
        )
        # 下方文字说明（视频插入后保留）
        cap = ""
        if title:
            cap += ('<p style="margin:12px 14px 0;font-size:14px;font-weight:800;color:#1e293b;'
                    'letter-spacing:0;">%s</p>') % self.leaf(title)
        if desc:
            cap += ('<p style="margin:5px 14px 13px;font-size:12px;line-height:1.7;color:#64748b;'
                    'letter-spacing:0;">%s</p>') % self.leaf(desc)
        return ('<section style="margin:24px 0;"><section style="border:1px solid #e2e8f0;'
                'border-radius:12px;overflow:hidden;background:#ffffff;">%s%s'
                '</section></section>') % (slot, cap)

    def _default_fallback(self, b):
        if b.role == "video":
            return self.video_placeholder(b)
        if b.role == "para":
            text = ("• " if b.bullet else "") + b.fields.get("text", "")
            return (
                '<section style="margin-top:20px;"><p style="margin:0;font-size:15px;'
                'line-height:1.95;text-align:justify;color:%s;letter-spacing:0;">%s</p></section>'
            ) % (self.t.get("TEXT", "#374151"), self.leaf(text))
        # 未知块：降级为普通文本，不报错留白
        txt = " ".join(b.fields.get("paras", [])) or " ".join(b.pos)
        return (
            '<section style="margin-top:16px;padding:10px 12px;background:#f8fafc;'
            'border-radius:8px;"><p style="margin:0;font-size:14px;color:%s;">%s%s</p></section>'
        ) % (self.t.get("TEXT", "#374151"),
             ("[" + b.role + "] ") if not txt else "", self.leaf(txt))


# ============================ 预览 / 复制页 ============================

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
  body { margin:0; background:#eceef1; }
  .toolbar { position:sticky; top:0; z-index:9; text-align:center; padding:12px;
             background:#fff; border-bottom:1px solid #e5e5e5; }
  .toolbar button { border:none; background:__BLUE__; color:#fff; font-size:15px;
             padding:10px 26px; border-radius:8px; cursor:pointer; }
  #article { max-width:677px; margin:24px auto; background:#fff; padding:20px 8px 50px;
             box-shadow:0 2px 16px rgba(0,0,0,.08); border-radius:4px; }
  #tip { font-size:13px; color:#666; margin-left:14px; }
</style>
</head>
<body>
<div class="toolbar">
  <button onclick="copyArticle()">一键复制排版结果</button>
  <span id="tip">复制后，到公众号后台正文编辑区 Ctrl+V</span>
</div>
<div id="article">__BODY__</div>
<script>
function copyArticle(){
  var node=document.getElementById('article'), tip=document.getElementById('tip');
  function ok(){ tip.textContent='已复制！现在去公众号后台 Ctrl+V'; tip.style.color='#1a9e54'; }
  function fail(){ tip.textContent='复制失败，请手动选中正文复制'; tip.style.color='#d33'; }
  if(navigator.clipboard&&window.ClipboardItem){
    var data=new ClipboardItem({
      'text/html':new Blob([node.innerHTML],{type:'text/html'}),
      'text/plain':new Blob([node.innerText],{type:'text/plain'})
    });
    navigator.clipboard.write([data]).then(ok).catch(selectFallback);
  } else { selectFallback(); }
  function selectFallback(){
    var range=document.createRange(); range.selectNodeContents(node);
    var sel=window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
    try{ document.execCommand('copy')?ok():fail(); }catch(e){ fail(); }
  }
}
</script>
</body>
</html>
"""


def build_page(body_html, title="公众号排版预览", button_color="#2563eb"):
    return (PAGE_TEMPLATE.replace("__BODY__", body_html)
            .replace("__TITLE__", html_mod.escape(title))
            .replace("__BLUE__", button_color))
