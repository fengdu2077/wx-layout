#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
serve · 公众号排版工坊 · 本地可视化工作台（P3）
================================================
仅用标准库、完全离线。启动一个只监听 127.0.0.1 的本地服务，
在浏览器里提供三栏工作台：
  左：Markdown 源码编辑（可载入 examples / tools\analysis 里的 .md，可保存）
  中：主题选择 + 渲染 / 一键复制 / 保存
  右：实时预览（与 render.py 同一套 Python 内核渲染，结果一致）

用法：
  python serve.py                 默认端口 8899，占用则自动顺延，并自动打开浏览器
  python serve.py --port 9000 --no-open
"""

import argparse
import json
import os
import pathlib
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import wx_core

ROOT = pathlib.Path(wx_core.HERE).resolve()


# ============================ 路径与数据 ============================

def safe_rel(p):
    """把前端给的相对路径约束在项目根内、且为 .md；非法返回 None。"""
    rel = pathlib.PurePosixPath((p or "").replace("\\", "/"))
    parts = [x for x in rel.parts if x not in ("", ".")]
    if not parts or any(x == ".." for x in parts):
        return None
    if not parts[-1].lower().endswith(".md"):
        return None
    return pathlib.Path(*parts)


def list_md_files():
    """枚举可载入 / 保存的 md：examples、tools\analysis、drafts。"""
    out = []
    for sub in ("examples", os.path.join("tools", "analysis"), "drafts"):
        d = ROOT / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            out.append(f.relative_to(ROOT).as_posix())
    return out


def theme_list():
    items = []
    for fname, label in wx_core.list_themes():
        name = fname
        try:
            name = wx_core.load_theme(fname).THEME.get("name", fname)
        except Exception:
            pass
        items.append({"file": fname, "label": label, "name": name})
    return items


def render_md(md, theme_file):
    theme = wx_core.load_theme(theme_file)
    return wx_core.Engine(theme).render(md)


# ============================ 前端页面 ============================

APP_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>公众号排版工坊 · 工作台</title>
<style>
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body { font-family: system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         color: #1f2937; background: #f3f4f6; display: flex; flex-direction: column; }
  header { display: flex; align-items: center; gap: 10px; padding: 10px 14px;
           background: #fff; border-bottom: 1px solid #e5e7eb; flex: 0 0 auto; flex-wrap: wrap; }
  header .brand { font-weight: 800; font-size: 16px; margin-right: 6px; }
  header label { font-size: 13px; color: #4b5563; display: flex; align-items: center; gap: 6px; }
  select, button, input[type=text] { font-size: 13px; padding: 7px 10px; border: 1px solid #d1d5db;
           border-radius: 8px; background: #fff; color: #1f2937; }
  button { cursor: pointer; }
  button.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
  button.good { background: #16a34a; color: #fff; border-color: #16a34a; }
  button:hover { filter: brightness(1.05); }
  .spacer { flex: 1; }
  #status { font-size: 12px; color: #6b7280; min-width: 90px; }
  main { flex: 1 1 auto; display: flex; min-height: 0; }
  .pane { display: flex; flex-direction: column; min-height: 0; min-width: 0; }
  .pane.left { flex: 0 0 42%; background: #fff; border-right: 1px solid #e5e7eb; }
  .pane.right { flex: 1 1 auto; background: #eceef1; }
  .pane-bar { flex: 0 0 auto; display: flex; align-items: center; gap: 8px; padding: 8px 12px;
              border-bottom: 1px solid #eef0f2; background: #fafafa; }
  .pane-bar .title { font-size: 12px; color: #6b7280; font-weight: 700; }
  #fileSel { flex: 1 1 auto; min-width: 120px; }
  #editor { flex: 1 1 auto; width: 100%; border: none; outline: none; resize: none;
            padding: 14px; font-family: ui-monospace, Consolas, "Courier New", monospace;
            font-size: 13px; line-height: 1.6; color: #111827; }
  #previewWrap { flex: 1 1 auto; overflow: auto; padding: 18px 10px 40px; }
  #preview { width: 100%; min-height: 100%; border: none; background: transparent; }
</style>
</head>
<body>
<header>
  <span class="brand">公众号排版工坊</span>
  <label>主题
    <select id="themeSel"></select>
  </label>
  <button id="themeDemoBtn" title="载入展示当前主题全部样式的示例 demo">本主题示例</button>
  <button class="primary" id="renderBtn">渲染</button>
  <button class="good" id="copyBtn">一键复制</button>
  <button id="saveBtn">保存</button>
  <span class="spacer"></span>
  <span id="status">就绪</span>
</header>
<main>
  <section class="pane left">
    <div class="pane-bar">
      <span class="title">源码</span>
      <select id="fileSel"></select>
      <button id="loadBtn">载入</button>
    </div>
    <textarea id="editor" spellcheck="false"></textarea>
  </section>
  <section class="pane right">
    <div class="pane-bar">
      <span class="title">预览（复制后到公众号后台 Ctrl+V）</span>
    </div>
    <div id="previewWrap"><iframe id="preview" title="预览"></iframe></div>
  </section>
</main>
<script>
var editor = document.getElementById('editor');
var themeSel = document.getElementById('themeSel');
var fileSel = document.getElementById('fileSel');
var statusEl = document.getElementById('status');
var preview = document.getElementById('preview');
var lastHtml = '', lastText = '', curPath = '', timer = null;

function setStatus(t, bad){ statusEl.textContent = t; statusEl.style.color = bad ? '#dc2626' : '#6b7280'; }

function api(path, opts){
  return fetch(path, opts).then(function(r){ return r.json().then(function(j){ return j; }); });
}

function init(){
  api('/api/themes').then(function(d){
    themeSel.innerHTML = '';
    d.themes.forEach(function(t){
      var o = document.createElement('option');
      o.value = t.file; o.textContent = t.label + '（' + t.name + '）';
      themeSel.appendChild(o);
    });
    ['蓝白杂志','暖棕手记'].forEach(function(f){
      if (themeSel.value !== f) { Array.prototype.forEach.call(themeSel.options, function(o){ if(o.value===f) themeSel.value=f; }); }
    });
  });
  refreshFiles();
}

function refreshFiles(){
  return api('/api/files').then(function(d){
    fileSel.innerHTML = '';
    var ph = document.createElement('option'); ph.value=''; ph.textContent='— 选择文件载入 —'; fileSel.appendChild(ph);
    d.files.forEach(function(f){
      var o = document.createElement('option'); o.value=f; o.textContent=f; fileSel.appendChild(o);
    });
  });
}

function loadFile(){
  var p = fileSel.value;
  if (!p) return;
  api('/api/file?path=' + encodeURIComponent(p)).then(function(d){
    if (!d.ok){ setStatus(d.error, true); return; }
    curPath = p; editor.value = d.md; setStatus('已载入 ' + p); doRender();
  });
}

function doRender(){
  var body = { md: editor.value, theme: themeSel.value };
  setStatus('渲染中…');
  return api('/api/render', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }).then(function(d){
    if (!d.ok){ setStatus('渲染失败：' + d.error, true); return; }
    lastHtml = d.html;
    var doc = '<!doctype html><html><head><meta charset="utf-8"></head>' +
              '<body style="margin:0;padding:0;">' + lastHtml + '</body></html>';
    preview.onload = function(){
      try { lastText = preview.contentDocument.body.innerText; } catch(e){ lastText = ''; }
    };
    preview.srcdoc = doc;
    setStatus('已渲染 · ' + themeSel.options[themeSel.selectedIndex].textContent);
  });
}

function scheduleRender(){
  if (timer) clearTimeout(timer);
  timer = setTimeout(doRender, 500);
}

function copyArticle(){
  function ok(){ setStatus('已复制！去公众号后台 Ctrl+V'); }
  function fail(){ setStatus('复制失败，请手动全选复制', true); }
  if (!lastHtml){ setStatus('请先渲染', true); return; }
  if (navigator.clipboard && window.ClipboardItem){
    var data = new ClipboardItem({
      'text/html': new Blob([lastHtml], { type: 'text/html' }),
      'text/plain': new Blob([lastText || editor.value], { type: 'text/plain' })
    });
    navigator.clipboard.write([data]).then(ok).catch(selectFallback);
  } else { selectFallback(); }
  function selectFallback(){
    try {
      var doc = preview.contentDocument, range = doc.createRange();
      range.selectNodeContents(doc.body);
      var sel = doc.getSelection(); sel.removeAllRanges(); sel.addRange(range);
      doc.execCommand('copy') ? ok() : fail();
    } catch(e){ fail(); }
  }
}

function saveFile(){
  var p = window.prompt('保存到（相对项目根的 .md 路径）', curPath || 'drafts/新文章.md');
  if (!p) return;
  api('/api/save', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: p, md: editor.value })
  }).then(function(d){
    if (!d.ok){ setStatus('保存失败：' + d.error, true); return; }
    curPath = d.path; setStatus('已保存 ' + d.path); refreshFiles();
  });
}

document.getElementById('themeDemoBtn').onclick = function(){
  var p = 'examples/demo-' + themeSel.value + '.md';
  api('/api/file?path=' + encodeURIComponent(p)).then(function(d){
    if (!d.ok){ setStatus('该主题还没有示例（见 docs/主题Demo生成规范.md）', true); return; }
    curPath = p; editor.value = d.md; fileSel.value = p;
    setStatus('已载入主题示例 ' + p); doRender();
  });
};
document.getElementById('renderBtn').onclick = doRender;
document.getElementById('copyBtn').onclick = copyArticle;
document.getElementById('saveBtn').onclick = saveFile;
document.getElementById('loadBtn').onclick = loadFile;
themeSel.onchange = doRender;
editor.addEventListener('input', scheduleRender);

init();
// 首屏放一份最小示例提示
editor.value = '# 在左侧写 Markdown，或从上方下拉载入 examples\\demo.md\n\n用 :::模块 标记，右侧实时预览，点「一键复制」即可。';
doRender();
</script>
</body>
</html>
"""


# ============================ HTTP 处理 ============================

class Handler(BaseHTTPRequestHandler):
    server_version = "WxLayoutWorkbench/1.0"

    def _send(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, text):
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send_html(APP_HTML)
        if u.path == "/api/themes":
            return self._send({"ok": True, "themes": theme_list()})
        if u.path == "/api/files":
            return self._send({"ok": True, "files": list_md_files()})
        if u.path == "/api/file":
            q = parse_qs(u.query)
            rel = safe_rel(q.get("path", [""])[0])
            if not rel:
                return self._send({"ok": False, "error": "非法路径"}, 400)
            f = (ROOT / rel).resolve()
            if not f.is_relative_to(ROOT) or not f.is_file():
                return self._send({"ok": False, "error": "文件不存在"}, 404)
            return self._send({"ok": True, "path": rel.as_posix(),
                               "md": f.read_text(encoding="utf-8")})
        return self._send({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception as e:
            return self._send({"ok": False, "error": "请求解析失败: %s" % e}, 400)

        if u.path == "/api/render":
            try:
                html = render_md(payload.get("md", ""), payload.get("theme", ""))
                return self._send({"ok": True, "html": html})
            except Exception as e:
                return self._send({"ok": False, "error": str(e)}, 500)

        if u.path == "/api/save":
            rel = safe_rel(payload.get("path", ""))
            if not rel:
                return self._send({"ok": False, "error": "非法路径（需项目根内 .md）"}, 400)
            f = (ROOT / rel).resolve()
            if not f.is_relative_to(ROOT):
                return self._send({"ok": False, "error": "路径越界"}, 400)
            try:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(payload.get("md", ""), encoding="utf-8")
            except Exception as e:
                return self._send({"ok": False, "error": str(e)}, 500)
            return self._send({"ok": True, "path": rel.as_posix()})

        return self._send({"ok": False, "error": "not found"}, 404)

    def log_message(self, fmt, *args):
        sys.stderr.write("[workbench] %s\n" % (fmt % args))


def main():
    ap = argparse.ArgumentParser(description="公众号排版工坊 · 本地可视化工作台")
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    port = args.port
    httpd = None
    for cand in range(port, port + 20):
        try:
            httpd = ThreadingHTTPServer((args.host, cand), Handler)
            port = cand
            break
        except OSError:
            continue
    if httpd is None:
        raise SystemExit("找不到可用端口（%s 起 20 个均被占用）" % args.port)

    url = "http://%s:%d/" % (args.host, port)
    print("公众号排版工坊 · 工作台已启动：%s" % url)
    print("按 Ctrl+C 停止。")
    if not args.no_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
