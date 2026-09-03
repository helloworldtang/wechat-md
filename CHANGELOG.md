# Changelog

本文件记录 wechat-md 的显著变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.2.1] - 2026-09-03

### Added

- **PyPI 首发**：`pip install wechat-md==0.2.1`（[pypi.org/project/wechat-md](https://pypi.org/project/wechat-md/)；
  Trusted Publishing，push tag 触发 CI 自动过质量门并上传）
- CI：push(main)/PR 触发质量门（ruff / mypy strict / pytest × Python 3.9–3.13 五版本矩阵）
- README 徽章（PyPI version / Python versions / License / CI）

### Changed

- README 专业化重写：面向「公众号排版」目标，新增排版规则一览表
- 版本单一来源：pyproject 经 hatch 动态读 `__init__.py`，根治版本号双处维护不同步
- 发版元数据补全（classifiers / Project-URLs / 作者）；ruff 配置固化进 pyproject（CI 去命令行重复参数）

## [0.2.0] - 2026-09-03

### Changed

- **行为变更**：h1/h2 标题竖条改为单层 `border-left`——旧 3 层 flex 竖条是独立可选中
  DOM 节点，从草稿箱复制文字到微信聊天时各层块边界各贡献一个换行；单层 CSS 边框
  不可选中、零贡献。h3 同步拍扁为单层 `<p>`（去多余 section 包裹）

## [0.1.0] - 2026-07-04

### Added

- 首个版本：`markdown_to_html(text)`——Markdown → 微信公众号友好 HTML，全行内样式、
  零 class/外部 CSS；含标题竖条、代码块卡片（等宽 + `&nbsp;` 缩进保留）、表格、
  引用块、链接、伪列表修复、对话卡片、结论区卡片等 17 步公众号专用后处理。
  唯一运行时依赖 markdown2（缺省自动回退 markdown）

[Unreleased]: https://github.com/helloworldtang/wechat-md/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/helloworldtang/wechat-md/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/helloworldtang/wechat-md/compare/1043379...v0.2.0
[0.1.0]: https://github.com/helloworldtang/wechat-md/tree/1043379
