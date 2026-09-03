# wechat-md

Markdown → 微信公众号友好 HTML。**单一权威实现**，供小龙虾(OpenClaw)、exomind 及任何需要「公众号排版」的系统共享。

## 为什么独立成包

微信公众号会过滤 `class` 与外部 CSS，通用 Markdown 渲染器（pulldown-cmark + syntect 等）生成的高亮 class 会被 strip，导致代码块高亮失效、排版错乱。本包移植自 OpenClaw 实战沉淀的 **17 步公众号专用后处理**（代码块 → `<section>` + 行内 style、伪列表修复、ProseMirror `\n` bug 修复、对话/结论区卡片等），是经过大量真实发文验证的成熟逻辑。

独立成包避免在多个系统里各拷一份（DRY）：任何一方修复 bug 或增强排版，所有消费方 `pip install -e` 后自动跟进。

## 安装

```bash
# 版本化安装（生产推荐：升级=显式改版本号）
pip install https://github.com/helloworldtang/wechat-md/archive/refs/tags/v0.2.0.tar.gz

# editable 安装（开发期推荐，改即生效）
pip install -e ~/workspace/github/wechat-md
```

> pyproject 依赖引用请锁 tag（`.../refs/tags/vX.Y.Z.tar.gz`），**不要引 `main.tar.gz`**——main 是滚动的，`uv sync`/`pip install` 会隐性升级到未审阅的代码。

## 使用

```python
from wechat_md import markdown_to_html

html = markdown_to_html("# 标题\n\n正文...")
# html 已是公众号可直接粘贴的格式（全部行内 style，无 class）
```

## 依赖

仅 `markdown2`。回退支持 `markdown`。

## 测试

```bash
pip install -e ".[dev]"
pytest
```

## 溯源

移植自 `~/.openclaw/workspace/scripts/publish_to_wechat.py` 的 `markdown_to_html()` 与 `_wechat_html_postprocess()`。若发现排版 bug，在本包修复后，小龙虾与 exomind 同步生效。
