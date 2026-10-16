#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
theme_contract · 读取 wx-layout 某套主题的「真实模块契约」
================================================================
供 wx-layout skill 在排版前调用：role / 字段 / 令牌全部直接从 themes/<主题>.py
的真实代码抽取，禁止凭记忆臆造样式。

项目根（含 wx_core.py 的目录）解析优先级：
  1. --root 参数
  2. WX_LAYOUT_ROOT 环境变量
  3. 自动探测：本脚本位于 <ROOT>/skills/wx-layout/scripts/ 下，逐级向上查找 wx_core.py

用法：
  python theme_contract.py 蓝白杂志
  python theme_contract.py blue-editorial --root /path/to/wx-layout
  python theme_contract.py 蓝白杂志 --json
"""

import argparse
import json
import os
import re
import sys

_FUNC_RE = re.compile(r"^def\s+render_(\w+)\s*\(")
_ALIAS_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*b\.fields\b")


def _detect_root():
    """从脚本所在目录逐级向上，找含 wx_core.py 的目录（wx-layout 项目根）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(6):
        if os.path.isfile(os.path.join(cur, "wx_core.py")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def resolve_root(cli_root):
    root = cli_root or os.environ.get("WX_LAYOUT_ROOT") or _detect_root()
    if not root or not os.path.isfile(os.path.join(root, "wx_core.py")):
        sys.exit(
            "找不到内核 wx_core.py。请用 --root 指定 wx-layout 项目根"
            "（含 wx_core.py 的目录），或设置环境变量 WX_LAYOUT_ROOT。"
        )
    return root


def load_theme(root, name):
    """按文件名 / label / name 代号解析主题，返回 (模块, 文件名)。"""
    sys.path.insert(0, root)
    import wx_core
    try:
        return wx_core.load_theme(name), name
    except FileNotFoundError:
        pass
    for cand, label in wx_core.list_themes():
        mod = wx_core.load_theme(cand)
        if label == name or mod.THEME.get("name") == name or mod.THEME.get("label") == name:
            return mod, cand
    sys.exit("找不到主题：%s。可用 `python render.py --list-themes` 查看。" % name)


def extract_role_contract(src):
    """从主题源码抽取每个 render_<role> 的位置槽与字段名（只读真实代码）。"""
    lines = src.splitlines()
    out = {}
    i = 0
    while i < len(lines):
        m = _FUNC_RE.match(lines[i])
        if not m:
            i += 1
            continue
        role = m.group(1)
        body = []
        i += 1
        while i < len(lines):
            ln = lines[i]
            if ln.strip() == "" or ln[:1] in (" ", "\t"):
                body.append(ln)
                i += 1
            else:
                break
        btext = "\n".join(body)

        # b.fields 的别名（如 f = b.fields）
        aliases = {"fields"}
        for ln in body:
            am = _ALIAS_RE.match(ln)
            if am:
                aliases.add(am.group(1))
        base = "(?:b\\.fields|%s)" % "|".join(re.escape(a) for a in aliases)
        fre = base + r"""(?:\.get\(\s*['"]([\w]+)['"]|\[\s*['"]([\w]+)['"]\s*\])"""

        field_names = set()
        for mm in re.finditer(fre, btext):
            field_names.add(mm.group(1) or mm.group(2))

        pos = {int(x) for x in re.findall(r"b\.get\(\s*(\d+)\s*\)", btext)}
        pos |= {int(x) for x in re.findall(r"(?<![A-Za-z0-9_.])\.get\(\s*(\d+)\s*\)", btext)}

        out[role] = {
            "pos_slots": sorted(pos),
            "fields": sorted(field_names),
            "uses_blocks": "b.blocks" in btext,
            "uses_bullet": "b.bullet" in btext,
        }
    return out


def build_data(root, name):
    mod, fname = load_theme(root, name)
    theme = mod.THEME
    src_path = os.path.join(root, "themes", fname + ".py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    contracts = extract_role_contract(src)
    roles = list(getattr(mod, "ROLES", {}).keys())
    return {
        "file": fname,
        "name": theme.get("name"),
        "label": theme.get("label"),
        "version": theme.get("version"),
        "containers": theme.get("containers", []),
        "has_fallback": hasattr(mod, "fallback"),
        "tokens": theme.get("tokens", {}),
        "roles": roles,
        "role_contract": {r: contracts.get(r, {"pos_slots": [], "fields": [],
                                               "uses_blocks": False, "uses_bullet": False})
                          for r in roles},
    }


def print_human(d):
    print("主题：%s（%s） v%s" % (d["label"], d["name"], d["version"]))
    print("文件：themes/%s.py" % d["file"])
    extra = d["containers"] or "无"
    print("追加容器 role：%s；自定义 fallback：%s" % (extra, "有" if d["has_fallback"] else "无"))
    print("\n设计令牌 tokens（真实值）：")
    for k, v in d["tokens"].items():
        print("  %-12s = %s" % (k, v))
    print("\n已实现 roles（%d）：%s" % (len(d["roles"]), ", ".join(d["roles"])))
    print("\n各 role 字段契约（源码自动抽取；位置槽/字段语义见 references/模块速查.md，细节以源文件为准）：")
    for r in d["roles"]:
        c = d["role_contract"][r]
        flags = []
        if c["uses_blocks"]:
            flags.append("遍历blocks")
        if c["uses_bullet"]:
            flags.append("bullet前缀")
        print("  %-7s 位置槽:%s 字段:[%s]%s"
              % (r, c["pos_slots"], ", ".join(c["fields"]),
                 ("  " + "、".join(flags)) if flags else ""))


def main():
    ap = argparse.ArgumentParser(description="读取 wx-layout 主题的真实模块契约")
    ap.add_argument("theme", help="主题文件名 / label / name 代号")
    ap.add_argument("--root", help="wx-layout 项目根（含 wx_core.py；默认自动探测）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    root = resolve_root(args.root)
    data = build_data(root, args.theme)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_human(data)


if __name__ == "__main__":
    main()
