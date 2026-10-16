<!--
  主题示例 demo · 暖棕手记（warm-brown-journal）
  本文件由 tools/scaffold_demo.py 依据主题源码自动生成，展示该主题的全部模块与写法。
  用法：在工作台打开本文件，对照下方 HTML 注释里的语法，替换占位内容；图片必须是 https://。
  本主题未实现、走内核 fallback 的 role：sub、quote、video、author、card。跨主题降级示例见 examples/demo.md。
-->

<!-- 写法：:::issue 主标签|副标签|文章标题（容器，本主题此模块不使用 body，直接用单独一行 ::: 闭合）。
     主标签是公众号/栏目名，没提供就写【请改成你的公众号名称】，发布前替换。 -->
:::issue 【请改成你的公众号名称】|副标签|文章标题
:::

<!-- 写法：:::part 01|章节中文标题|ENGLISH LABEL（单行，无需闭合） -->
:::part 01|章节中文标题|ENGLISH LABEL

<!-- 写法：正文直接写；**加粗**、[文字](https链接)；主题本地标记 ==；列表用 - 开头 -->
这是正文演示段落，包含**加粗强调**，还有[链接](https://example.com)，还有==行内标记==。

<!-- 写法：列表项以 - 开头（• 由内核自动处理） -->
- 列表项一，可含**加粗**
- 列表项二

<!-- 写法：:::shot https://placehold.co/600x400?text=Demo|图注文字（单行，无需闭合） -->
:::shot https://placehold.co/600x400?text=Demo|图注文字

<!-- 变体写法：:::shot https://placehold.co/600x400?text=Demo|图注文字|round=1（开关 round 打开后的效果） -->
:::shot https://placehold.co/600x400?text=Demo|图注文字|round=1

<!-- 写法：:::end 一句致谢（可省略）（单行，无需闭合） -->
:::end 一句致谢（可省略）
