# AI Skills · 排版工具的两个 AI 助手

本目录是「公众号排版工坊（wx-layout）」配套的两个 AI skill。它们不是独立程序，
而是给 AI Agent 用的**操作手册 + 辅助脚本**：AI 负责看懂与组织，渲染等确定性工作
始终由项目里的程序完成。

> 排版器 skill 与项目同名（**wx-layout**）：项目名是 wx-layout，日常排版调用的
> 主 skill 也叫 wx-layout；另一个 skill 是 wx-theme-extractor。

| Skill | 用途 | 使用频率 |
|---|---|---|
| **wx-layout**（排版器） | 把你**已经写好的文章**排成公众号图文：保留原文、只加 `:::模块` 标记，调用 `render.py` 渲染 | 高频，日常 |
| **wx-theme-extractor**（主题提取器） | 从任意一篇公众号文章复刻出一套新主题（`themes/` + `web/themes/` + 示例），过保真与双端校验后入库 | 偶尔，加风格时 |

两者边界：

- **wx-layout 只排版、不代写**：不扩写、不缩写、不润色、不删改原文；没有成稿请先写完。
- **wx-theme-extractor 只造主题**：样式只从真实保存页面抽取，不臆造；不改内核、不改老主题。
- 两个 skill **都不自己渲染 HTML**，最终网页只由 `render.py / wx_core`（浏览器端为
  `web/core.js`）生成。

## 目录结构

```
skills/
├─ wx-layout/
│  ├─ SKILL.md                  # 排版流程（AI 入口）
│  ├─ references/模块速查.md     # role ↔ 字段语义速查
│  └─ scripts/theme_contract.py  # 读主题真实契约（role/字段/令牌，从源码抽取）
└─ wx-theme-extractor/
   ├─ SKILL.md                  # 主题复刻流程（AI 入口）
   └─ references/主题制作规范.md  # 双端主题接口、登记清单、验证命令
```

## 安装

### 方式一：安装到支持 Skill 的 AI Agent

把对应目录（或整个 `skills/` 下两个目录）复制到你的 Agent 平台的技能目录：

- 豆包办公（Doubao Work）：复制到用户技能目录 `.doubaowork/agent_mode/workspace/.user_skills/`
  下（例如 `…/workspace/.user_skills/wx-layout/`），重启/刷新会话后即可被识别。
- 其他 Agent（Claude Code / Cursor / 各类兼容 Agent Skills 约定的平台）：
  复制到该平台约定的 skills 目录，保持 `SKILL.md` 文件名与目录结构不变。

注意：`wx-layout/scripts/theme_contract.py` 会自动从 skill 所在位置向上探测
wx-layout 项目根（也可用 `--root` 或环境变量 `WX_LAYOUT_ROOT` 指定），
**复制安装后请保持 wx-layout 项目目录完整、不要只移动 skill 文件夹**；
如果 skill 与项目分开存放，运行时用 `--root` 指向项目根。

### 方式二：不安装，直接让 AI 照做

任意 AI（ChatGPT / Claude / Gemini / Kimi / DeepSeek / 文心 / 通义 / 豆包等）
都能直接读取本目录的 `SKILL.md` 后按流程执行，无需任何插件：

- 日常排版：把《docs/AI排版手册.md》或 `skills/wx-layout/SKILL.md` 连同你写好的文章
  发给 AI；更通用的可复制规则见 `docs/AI调用指南.md`。
- 复刻主题：把 `skills/wx-theme-extractor/SKILL.md` 连同目标文章的保存页交给 AI。

## 环境要求

- 两个 skill 调用的脚本只用 **Python 3.8+ 标准库**，无需 `pip install`、无需联网。
- 双端 parity 校验（仅新增主题时）需要可选的 **Node.js**；未安装时至少完成
  Python 端验证。
- 普通用户若不使用 AI / Python，直接双击 `dist/公众号排版工坊.html` 即可排版，
  与本目录无关。
