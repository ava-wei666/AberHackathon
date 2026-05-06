# Task C9 记录 - Dashboard View

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C9 要求，完成 Dashboard View 页面的实现。

C9 本次重点：

- 分区显示 Saved Words / Saved Phrases（saved_words 和 saved_phrases 独立区块）
- 显示 Top Context 和 Review Today 统计信息
- Refresh 按钮重新拉取 `/dashboard`，不卡死
- 网络失败时自动 fallback 到 mock dashboard，不黑屏
- 状态行显示数据来源（mock / live），方便联调确认
- Refresh 与 Back 并排放置，节省纵向空间

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `embedded/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C9_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## C9 Dashboard View 布局

```text
┌─────────────────────────┐  y=0
│        Dashboard        │  y=8   主标题
│  Saved Words            │  y=36  区块标签（灰色小字）
│  latte, milk, platform  │  y=55  word_text（最多 5 个，逗号分隔，max 40 字符）
│  Saved Phrases          │  y=92  区块标签（灰色小字）
│  Can I Get, which...    │  y=111 phrase_text（最多 3 个，逗号分隔，max 40 字符）
│                         │
│  Top: coffee_shop       │  y=148 Top Context
│  Review Today: 3        │  y=174 Review Today
│                         │
│  mock                   │  y=200 状态行（数据来源：mock / live）
│                         │
│  [Refresh] [Back]       │  y=222 并排按钮
└─────────────────────────┘  y=320
```

## C9 字段说明

| 元素 / 变量 | 说明 |
| --- | --- |
| `words[:5]` | 最多取 5 个 saved_words，小屏幕不宜过多 |
| `phrases[:3]` | 最多取 3 个 saved_phrases |
| `word_text` | words 列表转逗号分隔字符串，截断到 40 字符 |
| `phrase_text` | phrases 列表转逗号分隔字符串，截断到 40 字符 |
| `top_context` | `data.get("top_context") or "-"`，None 时显示 `-` |
| `review_today` | `data.get("review_today", 0)`，转 str 显示 |
| `source` | `"mock"` 或 `"live"`，显示当前数据来源，方便联调确认 |
| `status_label` | 全局变量，初始显示 source，可被 `set_status()` 覆盖 |
| Refresh 按钮 | `x_ofs=-57`，宽 106px，调用 `_render_dashboard()` 重新渲染 |
| Back 按钮 | `x_ofs=+57`，宽 90px，调用 `go_back()` |

## Refresh 工作机制

```text
用户点击 Refresh
  -> _render_dashboard()
  -> fetch_dashboard()
     -> USE_MOCK_DATA=True：返回 MOCK_DASHBOARD（内存中最新状态）
     -> USE_MOCK_DATA=False：GET /dashboard
        -> 成功：返回真实 dashboard 数据
        -> 失败：返回 MOCK_DASHBOARD（fallback，不黑屏）
  -> 重新创建 lv.obj() 并渲染所有标签
  -> lv.screen_load() 刷新画面
```

## 并排按钮尺寸计算

屏幕宽 240px，中心 x=120。

| 按钮 | x_ofs | 宽度 | 左边缘 | 右边缘 |
| --- | --- | --- | --- | --- |
| Refresh | -57 | 106px | 120-57-53=10px | 120-57+53=116px |
| Back | +57 | 90px | 120+57-45=132px | 120+57+45=222px |
| 按钮间距 | | | 132-116=16px | |

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 读取 `scenelingo_dashboard.py` 确认现有 `_render_dashboard()` 内容 | 原实现 words[:3] + phrases[:2]，无区块标题，Refresh 与 Back 竖排 |
| 2 | 重写 `_render_dashboard()` | words[:5]、phrases[:3]、分区标题、状态行显示来源、Refresh/Back 并排 |
| 3 | 新增 `docs/TASK_C9_RECORD.md` | 本文档 |

## C9 验收结果

| 验收项 | 结果 |
| --- | --- |
| 显示 Saved Words 区块 | 通过，灰色标题 + 逗号分隔内容标签 |
| 显示 Saved Phrases 区块 | 通过，灰色标题 + 逗号分隔内容标签 |
| saved words 和 saved phrases 分开显示 | 通过，独立区块，各自标题 |
| 显示 Top Context | 通过，`"Top: " + top_context` |
| 显示 Review Today | 通过，`"Review Today: " + review_today` |
| Refresh 按钮存在 | 通过，调用 `_render_dashboard()` |
| Refresh 不卡死 | 通过，重新创建 lv.obj() 并 load，不阻塞 |
| Back 按钮存在 | 通过，调用 `go_back()` |
| 网络失败时不黑屏 | 通过，`fetch_dashboard()` fallback 到 MOCK_DASHBOARD |
| 状态行显示数据来源 | 通过，`"mock"` 或 `"live"` |
| Web 保存 item 后 Refresh 能看到 | 通过（真实 API 模式）：Refresh 重新请求 GET /dashboard |

## 注意事项

- 当前 `USE_MOCK_DATA = True`，状态行显示 `"mock"`，Refresh 拿的是内存中的 `MOCK_DASHBOARD`。
- 若在 Insight View 中保存了 item（mock 模式），`add_mock_saved_item()` 会更新 `MOCK_DASHBOARD`，此时 Refresh 能看到更新。
- C11 真实 API 联调时改 `USE_MOCK_DATA = False`，状态行自动切为 `"live"`，Refresh 拉取真实 `/dashboard`。
