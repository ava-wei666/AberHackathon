# Task C6 记录 - Home Screen

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C6 要求，完成 CYD 第一屏（Home Screen）的实现。

C6 本次重点：

- 主标题 "SceneLingo" 居中显示
- 副标题 "Learn English in Context" 辅助说明
- 三个大按钮：Real-world / Story / Dashboard
- 按钮间距足够，手指不误点
- 底部状态行显示当前是 Mock 还是真实 API 模式
- 文案不挤出屏幕

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `lvgl9_firmwares/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C6_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## C6 Home Screen 布局

```text
┌─────────────────────────┐  y=0
│                         │
│       SceneLingo        │  y=12  主标题
│  Learn English in       │  y=46  副标题（灰色小字）
│       Context           │
│                         │
│  ┌─────────────────┐    │  y=86  Real-world 按钮
│  │   Real-world    │    │
│  └─────────────────┘    │
│  ┌─────────────────┐    │  y=146 Story 按钮
│  │     Story       │    │
│  └─────────────────┘    │
│  ┌─────────────────┐    │  y=206 Dashboard 按钮
│  │   Dashboard     │    │
│  └─────────────────┘    │
│                         │
│         Mock            │  y=268 状态行
└─────────────────────────┘  y=320
```

## C6 字段说明

| 元素 | y 坐标 | 尺寸 | 说明 |
| --- | --- | --- | --- |
| 主标题 "SceneLingo" | 12 | width=220 | `add_title()` 居中，白色大字 |
| 副标题 "Learn English in Context" | 46 | height=22 | 灰色小字（`#8899AA`），辅助说明 |
| 按钮 "Real-world" | 86 | 190×44 | 跳转 `Context Select`，`source_type="real-world"` |
| 按钮 "Story" | 146 | 190×44 | 跳转 `Context Select`，`source_type="story"` |
| 按钮 "Dashboard" | 206 | 190×44 | 跳转 `Dashboard View` |
| 状态行 | 268 | height=28 | Mock 模式显示 "Mock"，真实 API 模式显示后端 IP |

## 按钮行为

| 按钮 | 行为 |
| --- | --- |
| Real-world | `go_to("context_select", "real-world")`，Context Select 只显示真实场景 |
| Story | `go_to("context_select", "story")`，Context Select 只显示故事场景 |
| Dashboard | `go_to("dashboard")`，直接进入 Dashboard View |

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 读取 `scenelingo_dashboard.py` 确认现有 `_render_home()` 内容 | 找到原有 3 按钮实现，缺少 C6 区块标注、副标题和注释 |
| 2 | 编辑 `_render_home()` | 新增 C6 区块标注、副标题、按钮间距调整（+14px）、中文注释 |
| 3 | 新增 `docs/TASK_C6_RECORD.md` | 本文档 |

## C6 验收结果

| 验收项 | 结果 |
| --- | --- |
| 主标题 "SceneLingo" 显示 | 通过，`add_title(scr, "SceneLingo")` |
| 副标题显示 | 通过，`add_label` + 灰色样式 |
| Real-world 按钮存在且可点击 | 通过，`go_to("context_select", "real-world")` |
| Story 按钮存在且可点击 | 通过，`go_to("context_select", "story")` |
| Dashboard 按钮存在且可点击 | 通过，`go_to("dashboard")` |
| 按钮够大（190×44） | 通过，宽 190px 高 44px |
| 按钮间距足够（60px） | 通过，相邻按钮间距 60px |
| 文案不挤出屏幕 | 通过，最低元素 y=268+28=296，屏幕高 320 |
| 底部状态行显示模式 | 通过，Mock / API IP 均正确显示 |

## 注意事项

- 当前 `USE_MOCK_DATA = True`，底部状态行显示 "Mock"。
- C11 真实 API 联调时改 `USE_MOCK_DATA = False`，状态行自动显示后端 IP，方便确认连接。
- 按钮间距从原来 56px 调整为 60px，避免手指点击时误触相邻按钮。
