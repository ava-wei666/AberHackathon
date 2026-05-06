# Task C3 记录 - Mock 数据先行

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C3 要求，在后端或网络还没有准备好时，CYD UI 也能先开发和演示。

C3 本次重点：

- 不连接后端也能显示 Insight View
- 不连接后端也能显示 Dashboard View
- mock 数据结构和真实 API 字段保持接近，后续切换真实 API 时不重写 UI

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `embedded/scenelingo_dashboard.py` |
| 板端上传文件 | `:scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C3_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## 新增 / 确认的 mock 字段

| 字段 | 内容 |
| --- | --- |
| `USE_MOCK_DATA` | `True`，默认优先使用 mock 数据 |
| `MOCK_CONTEXTS` | 4 个 context 入口，分为 `real-world` 和 `story` |
| `MOCK_ANALYSES` | 每个 context 对应一组 Insight mock |
| `MOCK_ANALYSIS` | 默认 Coffee Shop mock，兼容已有函数 |
| `MOCK_DASHBOARD` | 复习 Dashboard mock 数据 |
| `saved_words` | mock word 列表，例如 `latte`, `milk`, `platform` |
| `saved_phrases` | mock phrase 列表，例如 `Can I Get`, `which platform` |
| `review_today` | mock 今日复习数量 |
| `top_context` | mock 高频 context |

## 4 个 context mock

| context id | title | keywords 数量 | phrases 数量 |
| --- | --- | --- | --- |
| `coffee_shop` | `Coffee Shop` | 5 | 3 |
| `doctor_pharmacy` | `Doctor / Pharmacy` | 5 | 3 |
| `kings_cross` | `King's Cross` | 5 | 3 |
| `baker_street` | `Baker Street` | 5 | 3 |

## 执行命令记录

| 步骤 | 命令 | 做了什么 | 结果字段 |
| --- | --- | --- | --- |
| 1 | `git status --short --branch` | 检查工作区状态 | 当前 C2 文件和 C2 文档还未提交 |
| 2 | `rg -n "MOCK|fetch_context|fetch_dashboard|api_get|AUTO_CONNECT|show_insight|Dashboard" embedded\scenelingo_dashboard.py` | 查找 C3 需要改动的 mock / fetch / dashboard 位置 | 找到 mock 数据和 fetch 函数位置 |
| 3 | `Get-Content -Raw -Encoding UTF8 embedded\scenelingo_dashboard.py` | 读取 C2 业务主文件 | 确认已有 C2 结构 |
| 4 | `python -m py_compile embedded\scenelingo_dashboard.py` | 本地语法检查 | 通过，无语法错误 |
| 5 | `mpremote connect COM7 fs cp embedded\scenelingo_dashboard.py :scenelingo_dashboard.py` | 上传更新后的 C3 业务文件到 CYD | 上传成功 |
| 6 | `mpremote connect COM7 fs ls` | 查看板端文件系统 | 存在 `boot.py`, `main.py`, `scenelingo_dashboard.py` |
| 7 | `Select-String -Path embedded\scenelingo_dashboard.py -Pattern ...` | 检查 C3 关键字段是否存在 | 找到 `USE_MOCK_DATA`, 4 个 context, dashboard 字段 |

## 本次实现说明

`scenelingo_dashboard.py` 增加了：

```text
USE_MOCK_DATA = True
MOCK_ANALYSES
add_mock_saved_item()
mock-first fetch_contexts()
mock-first fetch_context()
mock-first fetch_dashboard()
mock save_item()
```

当 `USE_MOCK_DATA = True` 时：

- `fetch_contexts()` 直接返回 `MOCK_CONTEXTS`
- `fetch_context(context_id)` 直接返回对应 `MOCK_ANALYSES[context_id]`
- `fetch_dashboard()` 直接返回 `MOCK_DASHBOARD`
- `api_get()` 不发真实请求，只打印 `Mock GET`
- `api_post()` 不发真实请求，只打印 `Mock POST`
- 点击 keyword / phrase 保存时，`add_mock_saved_item()` 会把 item 加到内存里的 mock dashboard

## C3 验收结果

| 验收项 | 结果 |
| --- | --- |
| 不连后端也能显示 Insight View | 通过，`fetch_context()` 默认返回 mock |
| 不连后端也能显示 Dashboard View | 通过，`fetch_dashboard()` 默认返回 mock |
| 至少 5 个 keywords | 通过，每个 context 5 个 |
| 至少 3 个 phrases | 通过，每个 context 3 个 |
| summary 控制在 1-2 句 | 通过 |
| 换真实 API 时不重写 UI 结构 | 通过，只需把 `USE_MOCK_DATA` 改为 `False` 并配置网络 |
| 网络失败时不黑屏 | 通过，默认 mock-first |

## 注意事项

- C3 阶段 mock 是默认模式，真实 API 联调属于 C11。
- 如果要测试真实 API，请先完成 C1 网络，再把 `USE_MOCK_DATA = False`。
- 真实 Wi-Fi 密码仍然不能写入 Git。
- 本次没有覆盖板端 `main.py`，只更新了 `:scenelingo_dashboard.py`。
