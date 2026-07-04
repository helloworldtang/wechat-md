"""Markdown → 微信公众号友好 HTML 的核心实现。

移植自 OpenClaw(小龙虾) ``~/.openclaw/workspace/scripts/publish_to_wechat.py``
的 ``markdown_to_html()`` 与 ``_wechat_html_postprocess()``，保留全部 17 步
公众号专用后处理。

设计原则：微信公众号会过滤 class 与外部 CSS，故代码块不用语法高亮（避免
class 被 strip），改用 section + 行内 style；并修复 markdown2 输出在公众号
ProseMirror 编辑器下的若干渲染 bug。
"""

from __future__ import annotations

import re

try:
    import markdown2 as _md2

    _USE_MARKDOWN2 = True
except ImportError:  # pragma: no cover - 回退路径
    try:
        import markdown as _md

        _USE_MARKDOWN2 = False
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "wechat-md 需要 markdown2（或 markdown）依赖，请 pip install markdown2"
        ) from e


def markdown_to_html(markdown_text: str) -> str:
    """将 Markdown 转换为微信友好的 HTML。"""
    if _USE_MARKDOWN2:
        raw_html = _md2.markdown(markdown_text, extras=["tables", "fenced-code-blocks"])
    else:  # pragma: no cover - 回退路径
        md = _md.Markdown(extensions=["tables", "fenced_code"])
        raw_html = md.convert(markdown_text)
    return _wechat_html_postprocess(raw_html)


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _code_to_wechat_section(code_text: str) -> str:
    """将代码文本转为微信安全的 section（纯文本 + 行内 style + &nbsp; 保留缩进）。"""
    # 清理 span（高亮库生成的 class 会被微信过滤）
    code_text = re.sub(r"<span[^>]*>", "", code_text)
    code_text = code_text.replace("</span>", "")
    # HTML 实体解码
    code_text = code_text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    lines = code_text.split("\n")
    # 去掉首尾空行，但保留各行的前导空格（避免首行缩进被 strip 吞掉）
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    processed_lines = []
    for line in lines:
        if not line.strip():
            processed_lines.append("&nbsp;")
        else:
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            processed_lines.append("&nbsp;" * indent + stripped)
    code_html = "<br/>".join(processed_lines)
    return (
        '<section style="padding:16px;margin:16px 0;'
        "background-color:#f6f8fa;border-radius:6px;overflow-x:auto;\">"
        "<p style=\"margin:0;padding:0;font-size:14px;line-height:1.8;"
        "font-family:Menlo,Monaco,'Courier New',monospace;"
        'white-space:pre-wrap;word-wrap:break-word;color:#333;text-align:left;">'
        f"{code_html}"
        "</p></section>"
    )


def _h1_section(title_text: str) -> str:
    return (
        '<section style="margin:28px 0 16px;">'
        '<section style="display:flex;align-items:center;">'
        '<section style="width:4px;height:22px;background-color:#e74c3c;'
        'border-radius:2px;margin-right:10px;flex-shrink:0;"></section>'
        '<p style="margin:0;font-size:19px;font-weight:bold;color:#1a1a1a;">'
        f"{title_text}"
        "</p></section></section>"
    )


def _wechat_html_postprocess(html: str) -> str:
    """将标准 HTML 转换为微信公众号友好的 HTML（17 步后处理）。"""
    # 1. 移除开头 <h1>（标题已在草稿字段中，正文不重复）
    html = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", html, count=1, flags=re.DOTALL)

    # 2. 代码块 → 微信安全 section（codehilite 格式 + 裸 pre 格式）
    html = re.sub(
        r'<div class="codehilite">\s*<pre>.*?<code>(.*?)</code></pre>\s*</div>',
        lambda m: _code_to_wechat_section(m.group(1)),
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"<pre>(?:<code>)?(.*?)(?:</code>)?</pre>",
        lambda m: _code_to_wechat_section(m.group(1)),
        html,
        flags=re.DOTALL,
    )

    # 3-4. <h1>（带 style 或裸）→ 左红条 + 加粗
    html = re.sub(
        r'<h1[^>]*style="[^"]*"[^>]*>(.*?)</h1>',
        lambda m: _h1_section(_strip_tags(m.group(1))),
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"<h1>(.*?)</h1>",
        lambda m: _h1_section(_strip_tags(m.group(1))),
        html,
        flags=re.DOTALL,
    )

    # 5. <h2> → 左红条（稍细）
    html = re.sub(
        r"<h2[^>]*>(.*?)</h2>",
        lambda m: (
            '<section style="margin:22px 0 12px;">'
            '<section style="display:flex;align-items:center;">'
            '<section style="width:3px;height:18px;background-color:#e74c3c;'
            'border-radius:2px;margin-right:8px;flex-shrink:0;"></section>'
            '<p style="margin:0;font-size:17px;font-weight:bold;color:#1a1a1a;">'
            f"{_strip_tags(m.group(1))}"
            "</p></section></section>"
        ),
        html,
        flags=re.DOTALL,
    )

    # 6. <h3> → ▪ 前缀加粗
    html = re.sub(
        r"<h3[^>]*>(.*?)</h3>",
        lambda m: (
            '<section style="margin:18px 0 10px;">'
            '<p style="margin:0;font-size:16px;font-weight:bold;color:#333;">'
            f"▪ {_strip_tags(m.group(1))}"
            "</p></section>"
        ),
        html,
        flags=re.DOTALL,
    )

    # 7. 伪列表修复（markdown2 把 "- " 行并进 <p>，导致公众号空项目符号）
    html = _fix_pseudo_lists(html)

    # 7.5 统一段落样式
    html = html.replace(
        "<p>",
        '<p style="margin:10px 0;line-height:1.8;font-size:16px;color:#333;text-align:left;">',
    )

    # 7.6 链接样式（蓝字、可点击）
    def _link_repl(m):
        return (
            f'<a href="{m.group(1)}" '
            'style="color:#576b95;text-decoration:none;word-break:break-all;">'
            f"{m.group(2)}</a>"
        )

    html = re.sub(
        r'<a href="([^"]+)"[^>]*style="[^"]*"[^>]*>(.*?)</a>', _link_repl, html, flags=re.DOTALL
    )
    html = re.sub(r'<a href="([^"]+)">(.*?)</a>', _link_repl, html, flags=re.DOTALL)

    # 8. 移除 <hr/>（ProseMirror 会渲染成冗余灰线）
    html = html.replace("<hr />", "").replace("<hr/>", "")

    # 9. 引用块 → 灰底 + 左红边
    html = re.sub(
        r"<blockquote>\s*(.*?)\s*</blockquote>",
        lambda m: (
            '<section style="margin:12px 0;padding:10px 16px;'
            "background-color:#f8f9fa;border-left:3px solid #e74c3c;"
            'border-radius:0 4px 4px 0;">'
            f"{m.group(1)}"
            "</section>"
        ),
        html,
        flags=re.DOTALL,
    )

    # 10. <p><b>标题</b></p> + 紧跟列表 → 灰色卡片
    html = re.sub(
        r"<p[^>]*><b>([^<]+)</b></p>\s*<(ul|ol)([^>]*)>(.*?)</\2>",
        lambda m: (
            '<section style="margin:14px 0;padding:12px 16px;background-color:#fafafa;'
            'border-radius:6px;">'
            '<p style="margin:0 0 8px;font-size:15px;font-weight:bold;color:#e74c3c;">'
            f"▪ {m.group(1)}"
            "</p>"
            f'<{"ul" if m.group(2) == "ul" else "ol"} '
            'style="margin:0;padding-left:20px;line-height:1.8;font-size:15px;color:#333;">'
            f"{m.group(4)}"
            f'</{"ul" if m.group(2) == "ul" else "ol"}>'
            "</section>"
        ),
        html,
        flags=re.DOTALL,
    )

    # 11. 普通列表样式
    html = html.replace(
        "<ul>",
        '<ul style="margin:10px 0;padding-left:20px;line-height:1.8;font-size:16px;color:#333;">',
    )
    html = html.replace(
        "<ol>",
        '<ol style="margin:10px 0;padding-left:20px;line-height:1.8;font-size:16px;color:#333;">',
    )
    html = html.replace("<li>", '<li style="margin:4px 0;">')

    # 12. 表格样式
    html = html.replace(
        "<table>",
        '<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:15px;">',
    )
    html = html.replace(
        "<th>",
        '<th style="border:1px solid #ddd;padding:8px 12px;background-color:#f6f8fa;'
        'font-weight:bold;text-align:left;">',
    )
    html = html.replace("<td>", '<td style="border:1px solid #ddd;padding:8px 12px;">')

    # 13. 压缩列表内空白（ProseMirror 把 \n 渲染成空 <li>）
    html = re.sub(
        r"<(ul|ol)([^>]*)>(.*?)</\1>",
        lambda m: f"<{m.group(1)}{m.group(2)}>"
        + re.sub(r">\s+<", "><", m.group(3)).strip()
        + f"</{m.group(1)}>",
        html,
        flags=re.DOTALL,
    )

    # 14. 对话模式 → 灰色对话卡片
    html = _wrap_dialogs(html)

    # 15. 结论区 → 灰底卡片
    html = _wrap_conclusion_blocks(html)

    # 16. </b>: 修复（移入 bold 内部，避免公众号渲染异常）
    html = re.sub(r"</b>([::])", r"\1</b>", html)

    # 17. 首元素 margin-top 置 0
    html = html.replace("margin:10px 0", "margin:0 0", 1)
    html = html.replace("margin:28px 0 16px", "margin:0 0 16px", 1)

    return html


def _fix_pseudo_lists(html: str) -> str:
    """把 <p> 内以 '- ' 开头的行拆成真正的 <ul><li>（修复 markdown2 伪列表）。"""

    def split_paragraph_list(match):
        p_tag = match.group(1)
        p_content = match.group(2)
        close_tag = match.group(3)

        lines = p_content.split("\n")
        has_list = any(line.strip().startswith("- ") for line in lines[1:])
        if not has_list:
            return match.group(0)

        text_parts: list[str] = []
        list_parts: list[str] = []
        in_list = False
        for line in lines:
            if line.strip().startswith("- "):
                in_list = True
                item_text = line.strip()[2:].strip()
                list_parts.append(
                    f'<li style="margin:4px 0;"><section style="text-align: left;">'
                    f"{item_text}</section></li>"
                )
            else:
                if in_list:
                    text_parts.append(line)
                    in_list = False
                else:
                    text_parts.append(line)

        result = ""
        text_content = "\n".join(text_parts).strip()
        if text_content:
            result += f"{p_tag}{text_content}{close_tag}\n"
        if list_parts:
            result += (
                '<ul style="margin:6px 0;padding-left:20px;line-height:1.8;font-size:15px;'
                f'color:#333;">{chr(10).join(list_parts)}</ul>'
            )
        return result

    return re.sub(r"(<p[^>]*>)(.*?)(</p>)", split_paragraph_list, html, flags=re.DOTALL)


def _wrap_dialogs(html: str) -> str:
    """连续 '角色名:' 行 → 灰色对话卡片。"""
    dialog_roles = (
        r"(?:面试官|你|面试者|HR|导师|老师|同学|朋友|老板|经理|同事|"
        r"甲方|乙方|客户|产品经理|开发|测试|运维|架构师|我)"
    )
    pattern = r"((?:<p[^>]*>" + dialog_roles + r"[::].*?</p>\s*){2,})"

    def replace_dialog(match):
        content = match.group(1)
        content = re.sub(
            r"<p[^>]*>",
            '<p style="margin:6px 0;font-size:15px;line-height:1.7;color:#444;">',
            content,
        )
        return (
            '<section style="background-color:#f8f9fa;padding:14px 16px;'
            f'border-radius:8px;margin:14px 0;">{content}</section>'
        )

    return re.sub(pattern, replace_dialog, html, flags=re.DOTALL)


def _wrap_conclusion_blocks(html: str) -> str:
    """标题后紧跟多个 <b>xxx</b>:xxx 行 → 灰色背景卡片。"""
    pattern = (
        r'(<p style="margin:0;font-size:19px[^>]*>([^<]+)</p>)'
        r"\s*"
        r"((?:<p[^>]*><b>[^<]+</b>.*?</p>\s*)+)"
    )

    def replace(match):
        title_text = match.group(2)
        content = match.group(3)
        content = re.sub(
            r"<p[^>]*>",
            '<p style="margin:6px 0;font-size:15px;line-height:1.8;color:#333;">',
            content,
        )
        return (
            '<section style="margin:28px 0 16px;">'
            '<section style="display:flex;align-items:center;">'
            '<section style="width:4px;height:22px;background-color:#e74c3c;'
            'border-radius:2px;margin-right:10px;flex-shrink:0;"></section>'
            f'<p style="margin:0;font-size:19px;font-weight:bold;color:#1a1a1a;">'
            f"{title_text}</p>"
            "</section>"
            '<section style="background-color:#f8f9fa;padding:12px 16px;'
            f'border-radius:8px;margin-top:8px;">{content}</section></section>'
        )

    return re.sub(pattern, replace, html, flags=re.DOTALL)
