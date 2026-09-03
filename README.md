# wechat-md

[![PyPI](https://img.shields.io/pypi/v/wechat-md)](https://pypi.org/project/wechat-md/)
[![Python](https://img.shields.io/pypi/pyversions/wechat-md)](https://pypi.org/project/wechat-md/)
[![License: MIT](https://img.shields.io/pypi/l/wechat-md)](LICENSE)
[![CI](https://github.com/helloworldtang/wechat-md/actions/workflows/ci.yml/badge.svg)](https://github.com/helloworldtang/wechat-md/actions/workflows/ci.yml)

Markdown → 微信公众号 HTML 渲染器。

输出**全部行内 style、零 class、零外部 CSS** 的 HTML，粘贴进微信公众号编辑器即为最终排版——标题、代码块、表格、引用、列表样式完整保留，不依赖任何外部资源。

## 为什么需要它

微信公众号编辑器会过滤 `class` 属性与外部样式表。通用 Markdown 渲染器输出的高亮 class 会被 strip，导致代码块排版错乱；依赖外部 CSS 的主题在公众号里整体失效。

wechat-md 针对公众号编辑器逐项适配，所有样式内联在元素上，输出即终稿。

## 安装

```bash
pip install wechat-md
```

生产环境锁定版本（升级是显式决策，不隐性漂移）：

```bash
pip install wechat-md==0.2.1
```

引用 GitHub 源时锁 tag（`.../archive/refs/tags/vX.Y.Z.tar.gz`），不要引滚动的 `main`。

## 快速开始

```python
from wechat_md import markdown_to_html

html = markdown_to_html("# 标题\n\n正文…")
```

返回的 HTML 可直接作为公众号草稿正文提交，或粘贴进编辑器。

## 排版规则

| Markdown 元素 | 公众号渲染效果 |
| --- | --- |
| 文首 H1 | 移除（标题由草稿字段承载，正文不重复） |
| H1 / H2 | 加粗 + 左侧红色竖条（`border-left`，复制时不产生多余换行） |
| H3 | ▪ 前缀加粗 |
| 代码块 | 灰底圆角卡片、等宽字体、缩进以 `&nbsp;` 保留 |
| 引用块 | 灰底 + 左红边卡片 |
| 表格 | 全边框、表头灰底 |
| 链接 | 公众号蓝（`#576b95`）、可点击 |
| 列表 | 行内样式，并修复渲染器把 `- ` 行并进段落的伪列表问题 |
| `---` 分隔线 | 移除（编辑器渲染为冗余灰线） |
| 连续「角色名:」行 | 自动聚合成对话卡片 |
| 标题后紧跟加粗小节 | 自动聚合成结论区卡片 |

## 设计约束

- 纯函数、无网络、无配置——`markdown_to_html(text: str) -> str` 一个入口。
- 唯一运行时依赖 `markdown2`（未安装时自动回退 `markdown`）。
- 兼容 Python 3.9+。

## 开发

```bash
pip install -e ".[dev]"
pytest
```

质量门：ruff（E,W,F,I,B,C4,UP,SIM）+ mypy --strict + pytest 全绿后才发版。

## License

MIT
