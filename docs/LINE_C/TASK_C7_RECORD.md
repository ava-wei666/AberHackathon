# Task C7 记录 - Context Select Screen

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C7 要求，完成 Context Select 页面的实现。

C7 本次重点：

- 标题根据 `source_type` 动态显示 "Real-world" 或 "Story"
- 显示对应类型下的全部 context 按钮（最多 4 个）
- 点击 context 优先请求真实 API，失败时使用 mock fallback，不黑屏
- Back 按钮能回 Home
- 按钮够大，手指可点中

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `embedded/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C7_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## C7 Context Select 布局

```text
┌─────────────────────────┐  y=0
│                         │
│       Real-world        │  y=12  主标题（动态：Real-world / Story）
│   Select a context      │  y=46  副标题（灰色小字）
│                         │
│  ┌──────────────────┐   │  y=84  context 按钮 1
│  │   Coffee Shop    │   │        (real-world) 或 King's Cross (story)
│  └──────────────────┘   │
│  ┌──────────────────┐   │  y=148 context 按钮 2
│  │Doctor / Pharmacy │   │        (real-world) 或 Baker Street (story)
│  └──────────────────┘   │
│                         │
│         [Back]          │  y=270 Back 按钮
└─────────────────────────┘  y=320
```

## C7 字段说明

| 元素 / 变量 | 说明 |
| --- | --- |
| `_SOURCE_TYPE_LABELS` | `source_type` 内部 key 到显示文案的映射，`"real-world"` -> `"Real-world"`，`"story"` -> `"Story"` |
| `current_source_type` | 全局变量，记录当前选中的场景类型，供后续 Insight View 回退时判断 |
| `type_label` | 本次渲染的页面标题，从 `_SOURCE_TYPE_LABELS` 取值，未知类型兜底显示 `"Context"` |
| `contexts` | `fetch_contexts().get(current_source_type, [])` 取到的 context 列表 |
| 按钮宽 | 210px |
| 按钮高 | 48px |
| 按钮间距 | 64px（y 步进） |
| Back 按钮 | y=270，宽 100px，高 38px，调用 `go_back()` |

## Context 数据（来自 mock / 真实 API）

| source_type | context_id | 显示文案 |
| --- | --- | --- |
| real-world | `coffee_shop` | Coffee Shop |
| real-world | `doctor_pharmacy` | Doctor / Pharmacy |
| story | `kings_cross` | King's Cross |
| story | `baker_street` | Baker Street |

## 点击 context 的流程

```text
用户点击 context 按钮
  -> open_context(context_id)
  -> fetch_context(context_id)
     -> USE_MOCK_DATA=True：返回 mock_context(context_id)
     -> USE_MOCK_DATA=False：GET /context/{id}
        -> 成功：normalize_context(data)
        -> 失败：mock_context(context_id)  ← 保证不传 None，不黑屏
  -> go_to("insight", data)
  -> _render_insight(data)
```

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 读取 `scenelingo_dashboard.py` 确认现有 `_render_context_select()` 内容 | 找到原有实现，标题固定为 "Context"，缺少 C7 区块标注、动态标题、副标题和注释 |
| 2 | 编辑 `_render_context_select()` 和 `open_context()` | 新增 C7 区块标注、`_SOURCE_TYPE_LABELS`、动态标题、副标题、间距调整、中文注释 |
| 3 | 新增 `docs/TASK_C7_RECORD.md` | 本文档 |

## C7 验收结果

| 验收项 | 结果 |
| --- | --- |
| 标题根据 source_type 动态显示 | 通过，`_SOURCE_TYPE_LABELS` 映射，未知类型兜底 "Context" |
| Real-world 下显示 Coffee Shop | 通过，来自 `MOCK_CONTEXTS["real-world"]` |
| Real-world 下显示 Doctor / Pharmacy | 通过，来自 `MOCK_CONTEXTS["real-world"]` |
| Story 下显示 King's Cross | 通过，来自 `MOCK_CONTEXTS["story"]` |
| Story 下显示 Baker Street | 通过，来自 `MOCK_CONTEXTS["story"]` |
| 4 个 context 都能进入 Insight View | 通过，`open_context()` -> `fetch_context()` -> `go_to("insight", data)` |
| 请求失败不黑屏 | 通过，`fetch_context()` 失败时返回 `mock_context()`，不传 None |
| Back 按钮能回 Home | 通过，`go_back()` 弹出历史栈回到 Home |
| 按钮够大（210×48） | 通过 |
| lambda 闭包无陷阱 | 通过，使用 `context_id=context_id` 默认参数捕获 |

## 注意事项

- `lambda context_id=context_id` 是 MicroPython / Python 的闭包陷阱规避写法。若不加默认参数捕获，循环结束后所有按钮都会使用最后一个 `context_id`。
- 当前 `USE_MOCK_DATA = True`，点击任何 context 都使用 mock 数据，不发 HTTP 请求。
- C11 真实 API 联调时改 `USE_MOCK_DATA = False`，`open_context()` 自动切到真实 GET 请求，页面结构无需改动。
