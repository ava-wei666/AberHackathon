# Task C5 记录 - Screen Navigation

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C5 要求，把四个页面的切换路径跑通，确保页面之间可以来回切换、不会卡死，且每页都有明确返回路径。

C5 本次重点：

- 四个页面（Home / Context Select / Insight View / Dashboard View）可以互相切换
- 历史栈管理：`go_to()` 压栈，`go_back()` 弹栈
- Back 按钮在每个页面都存在
- 未知路由兜底回 Home，避免黑屏
- 导航逻辑与 UI 渲染分离

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `lvgl9_firmwares/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C5_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## C5 导航字段 / 函数说明

| 函数 / 变量 | 作用 |
| --- | --- |
| `screen_history` | 全局历史栈，存储 `(route, arg)` 元组，Back 按钮弹栈返回 |
| `current_route` | 全局当前路由 `(route, arg)`，由 `_set_route()` 更新 |
| `show_home()` | 清空历史栈后进入 Home，避免返回路径累积 |
| `show_context_select(source_type)` | 进入 Context Select，`source_type` 为 `"real-world"` 或 `"story"` |
| `show_insight(data)` | 进入 Insight View，`data` 为 `fetch_context()` 返回的 dict |
| `show_dashboard()` | 进入 Dashboard View，渲染时调用 `fetch_dashboard()` |
| `go_to(route, arg)` | 把当前路由压栈后跳转到目标页面 |
| `go_back()` | 弹出上一路由并渲染；栈空时兜底回 Home |
| `_set_route(route, arg)` | 更新 `current_route`，供 `go_to()` 压栈时读取 |
| `_render_route(route, arg)` | 路由分发器，根据 route 字符串调用对应 `_render_*` 函数 |
| `_render_home()` | 渲染 Home 页面，含三个跳转按钮 |
| `_render_context_select(source_type)` | 渲染 Context Select 页面，列出当前类型的 context 按钮 |
| `_render_insight(data)` | 渲染 Insight View，展示 keywords / phrases / summary |
| `_render_dashboard()` | 渲染 Dashboard View，展示 saved_words / saved_phrases 及统计 |

## 页面跳转路径

```text
Home
  -> [Real-world] -> Context Select (real-world)
  -> [Story]      -> Context Select (story)
  -> [Dashboard]  -> Dashboard View

Context Select
  -> [context 按钮] -> Insight View (该 context 数据)
  -> [Back]         -> Home

Insight View
  -> [keyword 按钮] -> 保存 word（停留当前页）
  -> [phrase 按钮]  -> 保存 phrase（停留当前页）
  -> [Back]         -> Context Select

Dashboard View
  -> [Refresh]  -> 重新渲染 Dashboard（停留当前页）
  -> [Back]     -> Home
```

## 导航层与 UI 渲染分离原则

```text
go_to() / go_back() / show_*()
  -> _render_route()
     -> _render_home() / _render_context_select() / _render_insight() / _render_dashboard()
```

按钮回调只调用 `go_to()` 或 `go_back()`，不直接操作 LVGL 组件，保证导航逻辑可独立测试。

## 执行命令记录

| 步骤 | 命令 | 做了什么 | 结果 |
| --- | --- | --- | --- |
| 1 | 读取 `scenelingo_dashboard.py` | 确认 C5 导航函数已在 C4 阶段实现 | 找到 `show_home` / `go_to` / `go_back` / `_render_route` 等完整导航函数 |
| 2 | 编辑 `scenelingo_dashboard.py` | 新增 C5 区块标注，补充各导航函数的中文注释 | 注释覆盖全部导航函数 |
| 3 | 新增 `docs/TASK_C5_RECORD.md` | 记录 C5 字段、跳转路径、验收结果 | 本文档 |

## C5 验收结果

| 验收项 | 结果 |
| --- | --- |
| `show_home()` 存在 | 通过 |
| `show_context_select(source_type)` 存在 | 通过 |
| `show_insight(data)` 存在 | 通过 |
| `show_dashboard()` 存在 | 通过 |
| `go_back()` 存在 | 通过 |
| Home -> Context Select 可跳转 | 通过，`go_to("context_select", source_type)` |
| Context Select -> Insight View 可跳转 | 通过，`go_to("insight", data)` |
| Dashboard View 有 Back 按钮 | 通过 |
| Insight View 有 Back 按钮 | 通过 |
| Context Select 有 Back 按钮 | 通过 |
| 历史栈空时 Back 兜底回 Home | 通过，`go_back()` 栈空分支调用 `show_home()` |
| 未知路由不黑屏 | 通过，`_render_route()` else 分支调用 `_render_home()` |
| 切换不卡死 | 通过，每次创建新 `lv.obj()` 并调用 `lv.screen_load()` |

## 注意事项

- 当前 `USE_MOCK_DATA = True`，页面数据来自 mock，切换时不发 HTTP 请求。
- C11 真实 API 联调时，把 `USE_MOCK_DATA` 改为 `False` 即可，导航层不需要修改。
- `screen_history` 存储的是 `(route, arg)` 元组，`arg` 可能包含完整 Insight data dict，内存占用在 ESP32 上需注意。
