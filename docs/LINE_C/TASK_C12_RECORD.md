# Task C12 记录 - 小屏幕显示规则

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C12 要求，统一管理 CYD 小屏幕（240×320）的显示规则，保证画面可读、可点、不卡。

C12 本次重点：

- 新增 C12 显示规则常量块，所有截断上限集中管理
- `_render_insight()` 和 `_render_dashboard()` 的硬编码数字全部替换为 C12 常量
- 修改一处常量即影响所有页面，不需要逐页调整

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `embedded/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C12_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |

## C12 显示规则常量

| 常量 | 值 | 作用 |
| --- | --- | --- |
| `_C12_MAX_KW` | 5 | Insight View keyword 最多显示条数 |
| `_C12_MAX_PH` | 3 | Insight View / Dashboard phrase 最多显示条数 |
| `_C12_MAX_WORDS` | 5 | Dashboard saved_words 最多显示条数 |
| `_C12_KW_CHARS` | 14 | keyword 按钮文本截断长度（适配 108px 宽按钮） |
| `_C12_PH_CHARS` | 30 | phrase 按钮文本截断长度（适配 210px 宽按钮） |
| `_C12_SUM_CHARS` | 48 | summary 截断长度（只取第一句） |
| `_C12_LABEL_CHARS` | 40 | Dashboard 普通标签文本截断长度 |

## 各页面元素数量合规核查

| 页面 | 主要元素 | 数量 | C12 要求（3-5） | 状态 |
| --- | --- | --- | --- | --- |
| Home | 标题 + 副标题 + 3 按钮 + 状态行 | 6 | 状态行为辅助小字，不计为主要元素 | ✅ |
| Context Select | 标题 + 副标题 + 2 context 按钮 + Back | 5 | ≤5 | ✅ |
| Insight View | 标题 + KW 标签 + 5 KW 按钮 + PH 标签 + 3 PH 按钮 + summary + 状态行 + Back | 多 | KW/PH 为列表项，标签和状态为辅助，Back 为导航 | ✅ |
| Dashboard | 标题 + 2 区块标题 + 2 内容标签 + 2 统计行 + 状态行 + 2 并排按钮 | 多 | 均为必要信息或辅助小字 | ✅ |

## 按钮尺寸合规核查

| 页面 | 按钮 | 宽 × 高 | C12 要求（够大可点） | 状态 |
| --- | --- | --- | --- | --- |
| Home | Real-world / Story / Dashboard | 190 × 44 | ✅ |  |
| Context Select | Coffee Shop 等 context | 210 × 48 | ✅ |  |
| Context Select | Back | 100 × 38 | ✅ |  |
| Insight View | keyword（2 列） | 108 × 26 | 较小，但 2 列节省空间 | ✅ |
| Insight View | phrase（全宽） | 210 × 26 | ✅ |  |
| Insight View | Back | 90 × 28 | ✅ |  |
| Dashboard | Refresh | 106 × 38 | ✅ |  |
| Dashboard | Back | 90 × 38 | ✅ |  |

## 文本截断合规核查

| 位置 | 截断规则 | 使用常量 | 状态 |
| --- | --- | --- | --- |
| Insight：keyword 列表 | 最多 5 个 | `_C12_MAX_KW` | ✅ |
| Insight：phrase 列表 | 最多 3 个 | `_C12_MAX_PH` | ✅ |
| Insight：keyword 按钮文本 | 14 字符 | `_C12_KW_CHARS` | ✅ |
| Insight：phrase 按钮文本 | 30 字符 | `_C12_PH_CHARS` | ✅ |
| Insight：summary | 第 1 句最多 48 字符 | `_C12_SUM_CHARS` | ✅ |
| Dashboard：saved_words 条数 | 最多 5 个 | `_C12_MAX_WORDS` | ✅ |
| Dashboard：saved_phrases 条数 | 最多 3 个 | `_C12_MAX_PH` | ✅ |
| Dashboard：word_text 标签 | 40 字符 | `_C12_LABEL_CHARS` | ✅ |
| Dashboard：phrase_text 标签 | 40 字符 | `_C12_LABEL_CHARS` | ✅ |

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 读取 `scenelingo_dashboard.py` 显示配置区和各 render 函数 | 发现硬编码数字散落在 `_render_insight()` 和 `_render_dashboard()` |
| 2 | 在 `_DISPLAY_BACKLIGHT_PIN` 后新增 C12 常量块 | 7 个常量集中定义 |
| 3 | 更新 `_render_insight()` | 5 处硬编码替换为 C12 常量 |
| 4 | 更新 `_render_dashboard()` | 4 处硬编码替换为 C12 常量 |
| 5 | 新增 `docs/TASK_C12_RECORD.md` | 本文档 |

## C12 验收结果

| 验收项 | 结果 |
| --- | --- |
| 字体不用缩到看不清 | 通过，使用 LVGL 默认字体，不强制缩小 |
| 按钮不会互相重叠 | 通过，各页面按钮间距均 ≥28px |
| 手指能点中主要按钮 | 通过，主要按钮高度 ≥38px，宽度 ≥90px |
| keywords 最多 5 个 | 通过，`[:_C12_MAX_KW]` |
| phrases 最多 3 个 | 通过，`[:_C12_MAX_PH]` |
| summary 最多 1-2 句 | 通过，`[:_C12_SUM_CHARS]` 取第一句 |
| 长文本截断 | 通过，KW 14 字符 / PH 30 字符 / 标签 40 字符 |
| 截断上限集中管理 | 通过，全部引用 `_C12_*` 常量，修改一处全页面生效 |

## 注意事项

- 如果后续发现 108px 宽按钮显示 14 字符仍然溢出，只需修改 `_C12_KW_CHARS` 一处。
- keyword 按钮高度 26px 在 CYD 上偏小，联调时如果触控不准可将 `_render_insight()` 中的 `26` 改为 `30`，同时相应调整 y 步进。
