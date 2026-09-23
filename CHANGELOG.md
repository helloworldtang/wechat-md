# Changelog

本文件记录 wechat-md 的显著变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.4.0] - 2026-09-23

### Fixed

- **粗体尾部标点后紧跟文字时不再输出字面 `**`**：markdown2（含最新 2.5.5）对
  `**X。**后缀` 这类写法（粗体内部以标点结尾、关闭 `**` 外侧紧跟汉字/字母）
  不做强调转换，字面 `**` 直接进 HTML（早报「1. **标签句。**说明」模式实测踩中；
  CommonMark 规范应为 strong，段落与列表行为一致）。渲染前把粗体尾部标点移出
  粗体（`**X。**` → `**X**。`）后正常转换，视觉几乎无差；尾部标点串（如 `%。`）
  整串移出是转换成立的必要代价。围栏代码块与行内代码内容不改。属输出行为变更
  （受影响写法的渲染结果改变），按约定升 minor。

## [0.3.0] - 2026-09-23

### Added

- **可选主题（配色覆盖）**：`markdown_to_html(text, theme={...})` 支持按主题着色，
  键与 wechat-publish-service 的 ThemeConfig 对齐（h1_color / h2_color / h3_color /
  strong_color / quote_bg / quote_border / code_bg / code_font_size / text_color）。
  未提供或未知键保持默认；不传 theme 时**配色**与历史版本一致（回归测试保障）。
- 渲染器仍为纯函数：主题由调用方传入，包内不做网络与配置读取。

### Changed

- **列表 → section 条目**：公众号编辑器会把 li 内「内联元素+后续文本」拆成
  独立块（2026-09 线上实测，`<strong>标签</strong>` 与「：内容」断成两行），
  列表标签不可用。ul/ol 逐条改为 `<section>• 文本</section>`（有序列表保留
  `N.` 序号前缀）。嵌套列表或 li 含块级元素时整段放弃改写、原样保留。
  与 wechat-publish-service 优化层规则同构，经发布链路输出时幂等无害。
- **外域链接内联成「文字，URL」**：公众号编辑器会把外链锚点整个删除
  （连样式都不留），URL 信息丢失。`mp.weixin.qq.com` 互链保持真锚点
  （编辑器保留可点击）；链接文字含标签或已含 URL 时不冒险改写。

### Notes

- 配套 wechat-publish-service `GET /api/mp/account-theme`（账号默认主题查询）上线后，
  发文侧可先取账号主题再本地渲染，实现「账号配置主题 → 生成文章生效」。


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

[Unreleased]: https://github.com/helloworldtang/wechat-md/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/helloworldtang/wechat-md/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/helloworldtang/wechat-md/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/helloworldtang/wechat-md/compare/1043379...v0.2.0
[0.1.0]: https://github.com/helloworldtang/wechat-md/tree/1043379
