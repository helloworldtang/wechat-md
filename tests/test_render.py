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
    """H2 应转成左红条 + 加粗 section。"""
    md = "## 子标题\n\n正文"
    html = markdown_to_html(md)
    assert "background-color:#e74c3c" in html
    assert "font-weight:bold" in html


def test_link_inline_styled():
    """链接应是蓝字 + 行内 style。"""
    md = "[例子](https://example.com)\n"
    html = markdown_to_html(md)
    assert 'color:#576b95' in html
    assert "https://example.com" in html


def test_blockquote_styled():
    """引用块应是灰底 + 左红边。"""
    md = "> 这是引用\n"
    html = markdown_to_html(md)
    assert "border-left:3px solid #e74c3c" in html
    assert "background-color:#f8f9fa" in html


def test_list_styled():
    """列表应有行内 style。"""
    md = "- 项目一\n- 项目二\n"
    html = markdown_to_html(md)
    assert "<ul" in html
    assert "padding-left:20px" in html


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
