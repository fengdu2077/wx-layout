#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_parity · 对比浏览器 JS 内核与 Python 内核的渲染结果
================================================================
先跑：node tools/web_parity.js  （生成 tools/analysis/web_parity.json）
再跑：python tools/web_parity.py
逐「示例 × 主题」字节级比对；一致退出码 0，有差异 1。只用标准库。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import wx_core

SAMPLES = [
    os.path.join("examples", "demo.md"),
    os.path.join("examples", "demo-蓝白杂志.md"),
    os.path.join("examples", "demo-暖橙横向.md"),
    os.path.join("examples", "demo-暖棕手记.md"),
    os.path.join("examples", "demo-翠绿科技.md"),
]
THEME_FILE = {
    "blue-editorial": "蓝白杂志",
    "warm-horizontal": "暖橙横向",
    "warm-brown-journal": "暖棕手记",
    "green-tech": "翠绿科技",
}

with open(os.path.join(ROOT, "tools", "analysis", "web_parity.json"), encoding="utf-8") as f:
    js = json.load(f)

bad = 0
for i, rel in enumerate(SAMPLES):
    with open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8") as f:
        md = f.read()
    for name, fname in THEME_FILE.items():
        mod = wx_core.load_theme(fname)
        py_html = wx_core.Engine(mod).render(md)
        js_html = js["%d|%s" % (i, name)]
        key = "%s × %s" % (rel, name)
        if py_html == js_html:
            print("  OK   " + key)
        else:
            bad += 1
            n = min(len(py_html), len(js_html))
            pos = next((k for k in range(n) if py_html[k] != js_html[k]), n)
            print("  DIFF " + key + "（首个差异位置 %d；Py长%d / JS长%d）"
                  % (pos, len(py_html), len(js_html)))
            print("       Py: ...%s" % py_html[max(0, pos - 60):pos + 60].replace("\n", " "))
            print("       JS: ...%s" % js_html[max(0, pos - 60):pos + 60].replace("\n", " "))

print("\n结果：%s" % ("全部一致 ✅" if bad == 0 else "%d 组不一致 ❌" % bad))
sys.exit(1 if bad else 0)
