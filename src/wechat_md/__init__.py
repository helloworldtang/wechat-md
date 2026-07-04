"""wechat-md: Markdown → 微信公众号友好 HTML。

提供与 OpenClaw(小龙虾) 一致的、针对微信公众号 ProseMirror 编辑器实战
沉淀的 HTML 后处理（代码块 → section + 行内 style、伪列表修复、对话/
结论区卡片等 17 步）。微信公众号会过滤 class 与外部 CSS，故代码块不用
语法高亮（避免 class 被 strip），改用 section + 行内 style。

纯函数，仅依赖 markdown2。可作为小龙虾、exomind 及任何需要「公众号排版」
的系统的共享权威实现——一处修改，所有消费方自动跟进。
"""

from wechat_md.render import markdown_to_html

__all__ = ["markdown_to_html"]
__version__ = "0.1.0"
