"""Markdown → 微信公众号友好 HTML 的核心实现。

移植自 OpenClaw(小龙虾) ``~/.openclaw/workspace/scripts/publish_to_wechat.py``
的 ``markdown_to_html()`` 与 ``_wechat_html_postprocess()``，保留全部 17 步
公众号专用后处理。

设计原则：微信公众号会过滤 class 与外部 CSS，故代码块不用语法高亮（避免
class 被 strip），改用 section + 行内 style；并修复 markdown2 输出在公众号
ProseMirror 编辑器下的若干渲染 bug。

主题（可选）：``markdown_to_html(text, theme={...})`` 支持配色覆盖，键与
wechat-publish-service 的 ThemeConfig 对齐（h1_color / h2_color / h3_color /
strong_color / quote_bg / quote_border / code_bg / code_font_size / text_color）。
未提供或未知键保持既有默认；不传 theme 时输出与历史版本逐字节一致。
仍为纯函数：颜色由调用方传入，包内不做任何网络与配置读取。
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

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


# ---------- 主题配色（可选覆盖） ----------


@dataclass(frozen=True)
class _Palette:
    """渲染调色板。

    默认值 = 历史硬编码输出（不传 theme 时逐字节一致）；调用方可经
    ``markdown_to_html(theme=...)`` 覆盖。``strong_color`` 为 None 时不给
    ``<strong>`` 上色（历史行为）；主题给值时 <strong> 按主题着色。
    """

    h1_color: str = "#e74c3c"
    h2_color: str = "#e74c3c"
    h3_color: str = "#333"
    strong_color: str | None = None
    quote_bg: str = "#f8f9fa"
    quote_border: str = "#e74c3c"
    code_bg: str = "#f6f8fa"
    code_font_size: str = "14px"
    text_color: str = "#333"

    @property
    def accent(self) -> str:
        """强调色（结论区竖条/标题等）：取主题粗体色，缺省回落 h1 色（=历史红）。"""
        return self.strong_color or self.h1_color


def _palette_from_theme(theme: Mapping[str, str] | None) -> _Palette:
    """将调用方传入的主题合并到默认调色板（未知键 / 空值忽略，回退默认）。"""
    base = _Palette()
    if not theme:
        return base

    def pick(key: str, fallback: str) -> str:
        value = (theme.get(key) or "").strip()
        return value or fallback

    strong = (theme.get("strong_color") or "").strip()
    return _Palette(
        h1_color=pick("h1_color", base.h1_color),
        h2_color=pick("h2_color", base.h2_color),
        h3_color=pick("h3_color", base.h3_color),
        strong_color=strong or None,
        quote_bg=pick("quote_bg", base.quote_bg),
        quote_border=pick("quote_border", base.quote_border),
        code_bg=pick("code_bg", base.code_bg),
        code_font_size=pick("code_font_size", base.code_font_size),
        text_color=pick("text_color", base.text_color),
    )


def markdown_to_html(markdown_text: str, theme: Mapping[str, str] | None = None) -> str:
    """将 Markdown 转换为微信友好的 HTML。

    Args:
        markdown_text: Markdown 原文。
        theme: 可选配色覆盖（键与 wechat-publish-service ThemeConfig 对齐：
            h1_color / h2_color / h3_color / strong_color / quote_bg /
            quote_border / code_bg / code_font_size / text_color）。
            缺省 = 历史默认配色；不传 theme 时输出逐字节不变。

    Returns:
        全行内 style 的微信公众号 HTML。
    """
    palette = _palette_from_theme(theme)
    if _USE_MARKDOWN2:
        raw_html = _md2.markdown(markdown_text, extras=["tables", "fenced-code-blocks"])
    else:  # pragma: no cover - 回退路径
        md = _md.Markdown(extensions=["tables", "fenced_code"])
        raw_html = md.convert(markdown_text)
    return _wechat_html_postprocess(raw_html, palette)


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _code_to_wechat_section(code_text: str, palette: _Palette) -> str:
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
        f"background-color:{palette.code_bg};border-radius:6px;overflow-x:auto;\">"
        f"<p style=\"margin:0;padding:0;font-size:{palette.code_font_size};line-height:1.8;"
        "font-family:Menlo,Monaco,'Courier New',monospace;"
        f'white-space:pre-wrap;word-wrap:break-word;color:{palette.text_color};text-align:left;">'
        f"{code_html}"
        "</p></section>"
    )


def _h1_section(title_text: str, palette: _Palette) -> str:
    # 单层 border-left 竖条(对齐 yyps 渲染器 a86836a,人工+机器双验证):
    # 旧 3 层 flex 里竖条是独立 DOM 节点——微信编辑器中可被选中,复制转纯文本时
    # 每层块边界各贡献一个换行;border-left 是 CSS 边框,非节点,零贡献。
    return (
        '<p style="margin:18px 0 10px;padding-left:10px;'
        f"border-left:4px solid {palette.h1_color};"
        'font-size:19px;line-height:22px;font-weight:bold;color:#1a1a1a;'
        'text-align:left;">'
        f"{title_text}"
        "</p>"
    )


def _wechat_html_postprocess(html: str, palette: _Palette) -> str:
    """将标准 HTML 转换为微信公众号友好的 HTML（17 步后处理）。"""
    # 1. 移除开头 <h1>（标题已在草稿字段中，正文不重复）
    html = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", html, count=1, flags=re.DOTALL)

    # 2. 代码块 → 微信安全 section（codehilite 格式 + 裸 pre 格式）
    html = re.sub(
        r'<div class="codehilite">\s*<pre>.*?<code>(.*?)</code></pre>\s*</div>',
        lambda m: _code_to_wechat_section(m.group(1), palette),
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"<pre>(?:<code>)?(.*?)(?:</code>)?</pre>",
        lambda m: _code_to_wechat_section(m.group(1), palette),
        html,
        flags=re.DOTALL,
    )

    # 3-4. <h1>（带 style 或裸）→ 左红条 + 加粗
    html = re.sub(
        r'<h1[^>]*style="[^"]*"[^>]*>(.*?)</h1>',
        lambda m: _h1_section(_strip_tags(m.group(1)), palette),
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"<h1>(.*?)</h1>",
        lambda m: _h1_section(_strip_tags(m.group(1)), palette),
        html,
        flags=re.DOTALL,
    )

    # 5. <h2> → 左红条（稍细）——同 h1,单层 border-left,竖条不做独立节点
    html = re.sub(
        r"<h2[^>]*>(.*?)</h2>",
        lambda m: (
            '<p style="margin:14px 0 8px;padding-left:9px;'
            f"border-left:3px solid {palette.h2_color};"
            'font-size:17px;line-height:20px;font-weight:bold;color:#1a1a1a;'
            'text-align:left;">'
            f"{_strip_tags(m.group(1))}"
            "</p>"
        ),
        html,
        flags=re.DOTALL,
    )

    # 6. <h3> → ▪ 前缀加粗(单层 p,去掉多余 section 包裹层)
    html = re.sub(
        r"<h3[^>]*>(.*?)</h3>",
        lambda m: (
            '<p style="margin:12px 0 8px;font-size:16px;font-weight:bold;'
            f'color:{palette.h3_color};text-align:left;">'
            f"▪ {_strip_tags(m.group(1))}"
            "</p>"
        ),
        html,
        flags=re.DOTALL,
    )

    # 7. 伪列表修复（markdown2 把 "- " 行并进 <p>，导致公众号空项目符号）
    html = _fix_pseudo_lists(html, palette)

    # 7.5 统一段落样式
    html = html.replace(
        "<p>",
        f'<p style="margin:10px 0;line-height:1.8;font-size:16px;color:{palette.text_color};text-align:left;">',
    )

    # 7.6 链接：公众号互链保持锚点（编辑器保留可点击）；外域锚点会被编辑器
    # 整个删除（线上实测连样式都不留），内联成「文字，URL」保住链接信息
    def _link_repl(m: re.Match[str]) -> str:
        url, text = m.group(1), m.group(2)
        anchor = (
            f'<a href="{url}" '
            'style="color:#576b95;text-decoration:none;word-break:break-all;">'
            f"{text}</a>"
        )
        if url.startswith(("https://mp.weixin.qq.com/", "http://mp.weixin.qq.com/")):
            return anchor
        if "<" in text or url in text:
            # 文字含标签或已含 URL：不冒险改写，保持锚点（发布链路的
            # yyps 优化层会再兜一遍）
            return anchor
        return f"{text}，{url}"

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
            f"background-color:{palette.quote_bg};border-left:3px solid {palette.quote_border};"
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
            f'<p style="margin:0 0 8px;font-size:15px;font-weight:bold;color:{palette.accent};">'
            f"▪ {m.group(1)}"
            "</p>"
            f'<{"ul" if m.group(2) == "ul" else "ol"} '
            f'style="margin:0;padding-left:20px;line-height:1.8;font-size:15px;color:{palette.text_color};">'
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
        f'<ul style="margin:10px 0;padding-left:20px;line-height:1.8;font-size:16px;color:{palette.text_color};">',
    )
    html = html.replace(
        "<ol>",
        f'<ol style="margin:10px 0;padding-left:20px;line-height:1.8;font-size:16px;color:{palette.text_color};">',
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

    # 13.5 列表 → section 条目（公众号编辑器会把 li 内「内联元素+后续文本」
    # 拆成独立块——线上实测 <strong>标签</strong> 与后续文本断成两行，
    # strong/span 一视同仁；列表标签不可用，•/序号以文本前缀呈现）
    html = _lists_to_sections(html, palette)

    # 14. 对话模式 → 灰色对话卡片
    html = _wrap_dialogs(html)

    # 15. 结论区 → 灰底卡片
    html = _wrap_conclusion_blocks(html, palette)

    # 16. </b>: 修复（移入 bold 内部，避免公众号渲染异常）
    html = re.sub(r"</b>([::])", r"\1</b>", html)

    # 16.5. <strong> 着色：仅当主题提供 strong_color（缺省保持历史"不着色"行为）
    if palette.strong_color:
        html = html.replace("<strong>", f'<strong style="color:{palette.strong_color};">')

    # 17. 首元素 margin-top 置 0
    html = html.replace("margin:10px 0", "margin:0 0", 1)
    html = html.replace("margin:28px 0 16px", "margin:0 0 16px", 1)

    return html


def _fix_pseudo_lists(html: str, palette: _Palette) -> str:
    """把 <p> 内以 '- ' 开头的行拆成真正的 <ul><li>（修复 markdown2 伪列表）。"""

    def split_paragraph_list(match: re.Match[str]) -> str:
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
                # 平铺 li（无内嵌 section）：后续 _lists_to_sections 统一改写成条目
                list_parts.append(f'<li style="margin:4px 0;">{item_text}</li>')
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
                f'color:{palette.text_color};">{chr(10).join(list_parts)}</ul>'
            )
        return result

    return re.sub(r"(<p[^>]*>)(.*?)(</p>)", split_paragraph_list, html, flags=re.DOTALL)


# li 内出现这些标签时整段放弃改写（内联内容与块级混排无法安全搬运）
_LIST_ABORT_RE = re.compile(r"<(ul|ol|p|section|div|table|pre|blockquote|img)\b", re.IGNORECASE)
_FLAT_LIST_RE = re.compile(r"<(ul|ol)\b[^>]*>(.*?)</\1>", re.DOTALL)
_LI_RE = re.compile(r"<li\b[^>]*>(.*?)</li>", re.DOTALL)
_LIST_START_RE = re.compile(r'start="(\d+)"')


def _lists_to_sections(html: str, palette: _Palette) -> str:
    """ul/ol → section 条目（2026-09 公众号编辑器拆块实测，与
    wechat-publish-service 优化层规则同构；经发布链路输出时 yyps 侧幂等无害）。

    平铺列表逐条改为 `<section>• 文本</section>`；嵌套列表或 li 含块级元素
    时整段放弃，原样保留（宁可不转，不可转错）。
    """

    def rewrite_list(m: re.Match[str]) -> str:
        open_tag, inner = m.group(0)[: m.start(2) - m.start(0)], m.group(2)
        ordered = m.group(1) == "ol"
        if _LIST_ABORT_RE.search(inner):
            return m.group(0)
        li_matches = _LI_RE.findall(inner)
        if not li_matches or len(li_matches) != inner.count("<li"):
            return m.group(0)  # li 标签不配对
        start_match = _LIST_START_RE.search(open_tag)
        num = int(start_match.group(1)) if start_match else 1
        items = []
        for item in li_matches:
            prefix = f"{num}. " if ordered else "• "
            if ordered:
                num += 1
            items.append(
                '<section style="margin:4px 0;padding-left:24px;text-align:left;'
                f'line-height:1.8;font-size:16px;color:{palette.text_color};">'
                f"{prefix}{item.strip()}</section>"
            )
        return f'<section style="margin:10px 0;">{"".join(items)}</section>'

    return _FLAT_LIST_RE.sub(rewrite_list, html)


def _wrap_dialogs(html: str) -> str:
    """连续 '角色名:' 行 → 灰色对话卡片。"""
    dialog_roles = (
        r"(?:面试官|你|面试者|HR|导师|老师|同学|朋友|老板|经理|同事|"
        r"甲方|乙方|客户|产品经理|开发|测试|运维|架构师|我)"
    )
    pattern = r"((?:<p[^>]*>" + dialog_roles + r"[::].*?</p>\s*){2,})"

    def replace_dialog(match: re.Match[str]) -> str:
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


def _wrap_conclusion_blocks(html: str, palette: _Palette) -> str:
    """标题后紧跟多个 <b>xxx</b>:xxx 行 → 灰色背景卡片。"""
    pattern = (
        r'(<p style="margin:0;font-size:19px[^>]*>([^<]+)</p>)'
        r"\s*"
        r"((?:<p[^>]*><b>[^<]+</b>.*?</p>\s*)+)"
    )

    def replace(match: re.Match[str]) -> str:
        title_text = match.group(2)
        content = match.group(3)
        content = re.sub(
            r"<p[^>]*>",
            f'<p style="margin:6px 0;font-size:15px;line-height:1.8;color:{palette.text_color};">',
            content,
        )
        return (
            '<section style="margin:28px 0 16px;">'
            '<section style="display:flex;align-items:center;">'
            f'<section style="width:4px;height:22px;background-color:{palette.accent};'
            'border-radius:2px;margin-right:10px;flex-shrink:0;"></section>'
            f'<p style="margin:0;font-size:19px;font-weight:bold;color:#1a1a1a;">'
            f"{title_text}</p>"
            "</section>"
            '<section style="background-color:#f8f9fa;padding:12px 16px;'
            f'border-radius:8px;margin-top:8px;">{content}</section></section>'
        )

    return re.sub(pattern, replace, html, flags=re.DOTALL)
