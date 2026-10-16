---
name: wx-theme-extractor
description: 公众号「wx-layout 排版工坊」的主题提取器。从任意一篇微信公众号文章（保存的 .mhtml/.html）复刻出一套可插拔主题：确定性脚本抽取 #js_content 的 DOM 与内联样式，AI 负责语义归纳、槽位识别、设计令牌与本地行内标记提炼，产出 themes/<主题>.py + web/themes/<name>.js + examples/demo-<主题>，并通过 diff_render/diff_style 保真对比与 Python/JS 双端字节级 parity 校验后入库。典型触发：把这篇公众号文章做成主题、复刻某公众号的排版风格、新增一套主题、提取/逆向主题、照着这篇文章的样式做一套模板。边界：不日常排版成稿（用 wx-layout）、不改内核 wx_core.py 与老主题、样式只来自真实页面不臆造、不抓取版权内容入库。
---

# wx-theme-extractor · 主题提取器

把任意一篇公众号文章归纳成一套可插拔主题，增量进主题库。**确定性脚本负责抽取与校验，
AI 负责看懂与归纳；AI 不凭印象编样式，所有样式必须来自真实页面。**

## 与 wx-layout 的分工

- 本 skill 只在「**要新增一套视觉风格**」时偶尔使用；日常把文章排成公众号图文用 `wx-layout`。
- 产出物：一套主题（Python + JS 双端）+ 该主题示例 demo + 文档登记。
- 完整流程依据项目根《docs/主题Demo生成规范.md》；主题接口细节见
  `references/主题制作规范.md`。

## 输入要求（第 0 步：拿到真实页面）

1. 让用户在浏览器打开目标文章，**Ctrl+S 保存为「网页，单个文件(.mhtml)」**（或 .html），
   把文件路径给你。
2. 不要尝试用 curl/fetch 直接抓 `mp.weixin.qq.com`——会返回「环境异常」，
   服务端浏览器也会被验证码拦住；只能用用户保存的页面，或由浏览器自动化技能驱动
   用户本机浏览器另存。
3. 只提取正文 `#js_content`（整页含 script/导航，会污染令牌统计）。
4. 视频 / 小程序 / SVG 静态提取不到，一律设计为**占位 + 后台手动插入**（视频用
   内核的 `:::video` 卡片），不要试图复刻播放框。

## 工作流

### 1. 抽 DOM 与样式（确定性脚本）

```bash
# 在项目根执行；输出 <名>.dom.json（DOM+内联样式树）与 <名>.outline.txt（可读骨架）
python tools/extract_dom.py "<保存的文章.mhtml>" --outdir tools/analysis
```

`.dom.json` 里同时有聚合候选令牌（颜色 / 字号 / 字体 / 圆角 / 行高 / 对齐 / 装饰条 /
渐变 / flex 布局等，按频次排序）。先通读 `.outline.txt` 建立版面结构印象，
再按需查 `.dom.json` 中具体节点的内联样式。

### 2. 语义归纳（AI 的核心工作，只依据真实抽取结果）

- **模块映射**：原文有哪些可复用版式（刊头 / 章节大标题 / 小标题 / 正文 / 截图 /
  引用 / 视频卡片 / 延伸卡片 / 结尾 / 作者名片，以及主题特有模块，如目录、步骤、
  代码块、表格、提示框、画廊等），分别映射到 role。
- **槽位识别**：每个 role 有几个位置参数（`b.get(N)`）、有无 kw 开关（如 `round=1`）、
  消费 body 里的哪些元素（image/heading/paras/lists/links）。
- **设计令牌**：从聚合候选里确定 tokens（主色、底色、正文色、标题色、字号、行高、
  字体、圆角、边框、阴影、间距）；**每个令牌都要能在 dom.json 中找到出处**，
  原文没有的不许编。
- **装饰与布局**：独立装饰条、分隔线、渐变、横向滑动（overflow-x + white-space）、
  flex 排列等，记录其数值——这些 `diff_style.py` 会逐项核对，漏了过不了关。
- **本地行内标记**：原文是否有高亮 / 下划线 / 反例色 / 代码胶囊等主题专属行内写法，
  定义标记符号（如 `==x==`、`` `x` ``）并实现主题自己的 inline 函数。

### 3. 生成 Python 主题

- 在 `themes/<中文label>.py` 新建主题，**复制最接近的现有主题改造**（不要从零写）：
  杂志类参考蓝白杂志、手记类参考暖棕手记、技术类参考翠绿科技、轻量横向参考暖橙横向。
- 接口与硬约束严格按 `references/主题制作规范.md`：`THEME` 元数据 + `render_<role>(b,c)`
  + `ROLES` + 可选 `fallback`；文本一律走 `c.leaf()` 转义，样式只许内联。
- 主题文件头部注释写明：复刻来源（公众号名，仅作出处记录）、模块清单、
  本地行内标记说明。

### 4. 复刻验证（文本 + 装饰双保真）

```bash
# 4.1 把原文内容重建成模块 md（验证用中间稿，放 tools/analysis，该目录已 gitignore）
#     （照着原文逐块转成 :::模块，图片地址用 dom.json 里的真实 URL）
# 4.2 原文 vs 复刻：并排 HTML + 块文本 difflib 相似度/缺失/多余
python tools/diff_render.py --page "<原文.mhtml>" --md "tools/analysis/<主题>复刻.md" \
    --theme <主题label> --out "tools/analysis/diff-<主题>.html"
# 4.3 渲染复刻稿，再做装饰/结构保真对比（退出码 0 才通过）
python render.py "tools/analysis/<主题>复刻.md" --theme <主题label> \
    -o "tools/analysis/<主题>复刻.html"
python tools/diff_style.py "<原文.mhtml>" "tools/analysis/<主题>复刻.html"
```

- 文本相似度逐块对齐，修缺失/多余块；装饰对比覆盖装饰条 / 边框 / 渐变 / 横向滑动 /
  图片数 / flex / 居中。
- 最后把渲染 HTML 粘进公众号后台编辑器复测（人工一步）：只允许出现原文本身也有的
  同类提示（如渐变 darkmode-no-gradient），不得引入新的结构违规类型。

### 5. 生成示例 demo（覆盖该主题全部样式）

```bash
# 确定性骨架：枚举 ROLES、位置槽、kw 变体、行内标记，自动保证覆盖率
python tools/scaffold_demo.py <主题label> --render
```

然后按《docs/主题Demo生成规范.md》**人工（AI）润色** `examples/demo-<主题>.md`：
占位改中性演示文字、刊头名写「【请改成你的公众号名称】」、日期写「【日期】」、
图片优先从本次 `.dom.json` 取真实出现过的 URL，取不到保留
`https://placehold.co/...` 占位；润色后重渲染：

```bash
python render.py "examples/demo-<主题>.md" --theme <主题label> \
    -o "examples/demo-<主题>.html"
```

### 6. JS 双端移植与登记（容易漏，逐项做）

1. 新建 `web/themes/<英文name>.js`，逐 role 忠实移植 Python 版（注意 JS 中
   **没有 `%%` 转义**，`50%` 直接写；末尾 `global.WX.registerTheme({THEME, ROLES})`，
   有降级则加 `fallback`）。
2. 在 `web/index.html` 加一行 `<script src="themes/<name>.js"></script>`。
3. 在 `tools/web_parity.py` 的 `SAMPLES`（加 `examples/demo-<主题>.md`）与
   `THEME_FILE`（加 `"<name>": "<中文label>"`）登记；在 `tools/web_parity.js`
   顶部 `load(...)` 加新 JS 主题。
4. 在 `tools/build_web_samples.py` 的 `SAMPLES` 加该主题 demo 条目。
5. 跑双端字节级 parity（需安装 Node.js；没装 Node 时至少完成 Python 端渲染验证，
   并在交付说明中注明 JS 未校验）：
   ```bash
   node tools/web_parity.js
   python tools/web_parity.py      # 全部一致、退出码 0 才通过
   ```
6. 重建网页版资源与单文件：
   ```bash
   python tools/build_web_samples.py
   python tools/build_web_single.py
   ```
7. 更新文档登记：`README.md` 主题/路线图、`docs/AI调用指南.md` 主题对照表。

### 7. 入库前检查

- [ ] `themes/<主题>.py`、`web/themes/<name>.js`、`examples/demo-<主题>.md/.html` 齐备。
- [ ] `diff_style.py` 退出码 0；后台复测无新增违规类型。
- [ ] `web_parity.py` 全部一致；demo 覆盖每个 role / 位置槽 / kw 变体 / 行内标记。
- [ ] 刊头名称/日期为占位，未编造；无真实品牌推广文案。
- [ ] **没有改 `wx_core.py` 与老主题**；如确需内核改动，单独向用户说明理由，
      并跑全量 parity 验证全部老主题。
- [ ] `git status` 确认 `tools/analysis/`、`internal/`（含他人文章原文与中间产物）
      未被提交——版权内容只留在本地。

## 铁律

- **样式只来自真实 HTML/内联样式**：每个令牌、每个装饰数值都能在抽取产物中指出处，
  不臆造、不拿"常见设计"凑。
- **不改内核、不改老主题**；新主题是纯增量文件。
- **复刻验证不过不入库**：文本对齐、装饰保真、双端 parity 三关都要过。
- **版权隔离**：他人文章内容仅本地提取用，仓库只收中性示例。
