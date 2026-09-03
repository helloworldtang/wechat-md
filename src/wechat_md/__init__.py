"""wechat-md: Markdown → 微信公众号 HTML 渲染器。

输出全部行内 style、零 class、零外部 CSS 的 HTML——微信公众号编辑器会
过滤 class 与外部样式表，通用渲染器的输出会被 strip 成裸文本。本包针对
公众号编辑器逐项适配：标题竖条、代码块卡片（等宽 + 缩进保留）、表格、
引用块、对话/结论区卡片等。

纯函数、无网络、无配置，仅依赖 markdown2。一个入口：markdown_to_html(text)。
"""

from wechat_md.render import markdown_to_html

__all__ = ["markdown_to_html"]
__version__ = "0.2.1"
