#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_web_samples · 把示例 md 内联为 web/samples.js
================================================================
纯静态 web 版在 file:// 下无法 fetch 本地 md（CORS），故把示例源稿内联进 JS。
新增 / 改动 examples 后重跑本脚本即可。只用标准库。

用法：python tools/build_web_samples.py
"""
import json, os
# 项目根 = 本脚本所在 tools/ 的上一级，不写死个人路径。
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SAMPLES = [
    ("共享示例（全模块）", os.path.join("examples", "demo.md")),
    ("蓝白杂志 · 主题示例", os.path.join("examples", "demo-蓝白杂志.md")),
    ("暖橙横向 · 主题示例", os.path.join("examples", "demo-暖橙横向.md")),
    ("暖棕手记 · 主题示例", os.path.join("examples", "demo-暖棕手记.md")),
    ("翠绿科技 · 主题示例", os.path.join("examples", "demo-翠绿科技.md")),
]

data = []
for label, rel in SAMPLES:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(p, encoding="utf-8") as f:
        data.append({"label": label, "path": rel, "md": f.read()})

out = "/* 自动生成，请勿手改；源：tools/build_web_samples.py */\n"
out += "window.WX_SAMPLES = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n"
wp = os.path.join(ROOT, "web", "samples.js")
with open(wp, "w", encoding="utf-8") as f:
    f.write(out)
print("已生成 web/samples.js（%d 个示例）" % len(data))
