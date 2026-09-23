"""wechat-md 渲染基础测试：覆盖公众号适配的关键转换。"""

from wechat_md import markdown_to_html


def test_strips_leading_h1():
    """开头 H1 应被移除（标题在草稿字段中，正文不重复）。"""
    md = "# 我的标题\n\n正文内容"
    html = markdown_to_html(md)
    assert "我的标题</h1>" not in html
    assert "正文内容" in html


def test_code_block_uses_inline_style_no_class():
    """代码块应是 section + 行内 style，且无 class（公众号会过滤 class）。"""
    md = "```python\nprint('hi')\n```\n"
    html = markdown_to_html(md)
    assert "<section" in html
    assert "background-color:#f6f8fa" in html
    assert "class=" not in html  # 关键：无 class


def test_code_indent_preserved_with_nbsp():
    """代码行首缩进用 &nbsp; 保留。"""
    md = "```\n  indented\n```\n"
    html = markdown_to_html(md)
    assert "&nbsp;&nbsp;indented" in html


def test_h2_has_red_bar():
    """H2 应转成左红条 + 加粗——单层 border-left(竖条不做独立节点,防复制多换行)。"""
    md = "## 子标题\n\n正文"
    html = markdown_to_html(md)
    assert "border-left:3px solid #e74c3c" in html
    assert "font-weight:bold" in html
    assert "display:flex" not in html  # 竖条不得是独立 flex 子节点


def test_h1_midarticle_single_layer():
    """正文中间 H1 应转成单层 border-left 竖条(旧 3 层嵌套会在复制时多换行)。"""
    md = "开头段\n\n# 中间大标题\n\n后文"
    html = markdown_to_html(md)
    assert 'border-left:4px solid #e74c3c' in html
    assert "display:flex" not in html
    assert "中间大标题" in html


def test_link_inline_styled():
    """外域链接内联成「文字，URL」（公众号编辑器会删外链锚点丢 URL）。"""
    md = "[例子](https://example.com)\n"
    html = markdown_to_html(md)
    assert "例子，https://example.com" in html
    assert "<a href" not in html


def test_weixin_link_keeps_anchor():
    """公众号互链保持真锚点（编辑器保留可点击）。"""
    md = "[旧文](https://mp.weixin.qq.com/s/abc)\n"
    html = markdown_to_html(md)
    assert '<a href="https://mp.weixin.qq.com/s/abc"' in html


def test_complex_link_keeps_anchor():
    """链接文字含标签或已含 URL 时不冒险改写，保持锚点。"""
    md = "[**加粗**](https://example.com) 与 [https://example.com](https://example.com)\n"
    html = markdown_to_html(md)
    assert html.count("<a href") == 2


def test_blockquote_styled():
    """引用块应是灰底 + 左红边。"""
    md = "> 这是引用\n"
    html = markdown_to_html(md)
    assert "border-left:3px solid #e74c3c" in html
    assert "background-color:#f8f9fa" in html


def test_list_styled():
    """列表 → section 条目（公众号编辑器会拆块 li 内联内容，列表标签不可用）。"""
    md = "- 项目一\n- 项目二\n"
    html = markdown_to_html(md)
    assert "<ul" not in html
    assert "<li" not in html
    assert "• 项目一" in html
    assert "• 项目二" in html
    # 条目内联内容整体在同一 section（不触发拆块）
    assert '<section style="margin:4px 0;padding-left:24px;' in html


def test_ordered_list_keeps_numbering():
    """有序列表序号以文本前缀保留。"""
    md = "1. 第一\n2. 第二\n"
    html = markdown_to_html(md)
    assert "<ol" not in html
    assert "1. 第一" in html
    assert "2. 第二" in html


def test_list_with_bold_label_inline():
    """「- **标签**:说明」必须整条内联（2026-09 线上拆块事故回归）。"""
    md = "- **命中率**：跌破40%说明问法漂移；\n"
    html = markdown_to_html(md)
    assert "<li" not in html
    assert "• <strong>命中率</strong>：跌破40%" in html or "• <strong>命中率" in html


def test_hr_removed():
    """<hr/> 应被移除（ProseMirror 会渲染成冗余灰线）。"""
    md = "上文\n\n---\n\n下文\n"
    html = markdown_to_html(md)
    assert "<hr" not in html


def test_table_styled():
    """表格应有边框样式。"""
    md = "\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    html = markdown_to_html(md)
    assert "<table" in html
    assert "border:1px solid #ddd" in html


def test_dialog_card():
    """连续 '角色名:' 行应被包成对话卡片。"""
    md = "面试官: Redis 为什么快?\n\n我: 基于内存。\n"
    html = markdown_to_html(md)
    # 对话卡片有圆角灰底
    assert "border-radius:8px" in html
    assert "面试官" in html
    assert "基于内存" in html


def test_plain_text_gets_paragraph_style():
    """纯文本段落应被加行内 style。"""
    md = "这是一段普通文字。\n"
    html = markdown_to_html(md)
    assert "line-height:1.8" in html


# ---------- 主题（可选配色覆盖） ----------


def test_theme_colors_applied():
    """主题覆盖：标题竖条 / 粗体 / 引用边框按主题着色。"""
    md = "## 子标题\n\n**重点** 和引用：\n\n> 引用\n"
    theme = {"h2_color": "#3498db", "strong_color": "#3498db", "quote_border": "#ddd"}
    html = markdown_to_html(md, theme=theme)
    assert "border-left:3px solid #3498db" in html
    assert '<strong style="color:#3498db;">' in html
    assert "border-left:3px solid #ddd" in html
    assert "#e74c3c" not in html


def test_theme_absent_keeps_legacy_output():
    """不传 theme 保持历史默认输出（红 + 粗体不上色）——回归护栏。"""
    md = "开头段\n\n# 中间标题\n\n**重点**\n\n> 引用\n"
    assert markdown_to_html(md) == markdown_to_html(md, theme=None)
    html = markdown_to_html(md)
    assert "border-left:4px solid #e74c3c" in html  # 正文中间 H1 竖条
    assert "border-left:3px solid #e74c3c" in html  # 引用边框
    assert "<strong>" in html
    assert "<strong style=" not in html


def test_theme_partial_override_and_unknown_keys():
    """部分覆盖：未给字段保持默认；未知键 / 空值忽略。"""
    md = "## 标题\n\n**重点**\n"
    html = markdown_to_html(
        md, theme={"strong_color": "#27ae60", "unknown": "#000000", "h2_color": ""}
    )
    assert "border-left:3px solid #e74c3c" in html  # h2 空值 → 默认红
    assert '<strong style="color:#27ae60;">' in html
    assert "#000000" not in html


def test_theme_h3_and_code():
    """H3 与代码块取主题色 / 底色 / 字号。"""
    md = "### 小节\n\n```\ncode\n```\n"
    html = markdown_to_html(
        md, theme={"h3_color": "#3498db", "code_bg": "#eeeeee", "code_font_size": "13px"}
    )
    assert "color:#3498db" in html
    assert "background-color:#eeeeee" in html
    assert "font-size:13px" in html


def test_theme_text_color():
    """正文字色随主题。"""
    md = "普通段落文字。\n"
    html = markdown_to_html(md, theme={"text_color": "#444444"})
    assert "color:#444444" in html


def test_theme_empty_inputs_equal_none():
    """theme={} 或全空值时等价于不传。"""
    md = "**重点**\n"
    assert markdown_to_html(md, theme={}) == markdown_to_html(md)
    assert markdown_to_html(md, theme={"strong_color": ""}) == markdown_to_html(md)
