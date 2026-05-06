# Task C2 记录 - 新建 CYD 业务主文件

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C2 要求，新建 CYD 业务主文件，不把 SceneLingo 业务 UI 写进 C0 的硬件测试文件。

本次新增：

```text
embedded/scenelingo_dashboard.py
```

## 本次记录字段

| 字段 | 内容 |
| --- | --- |
| 新增业务文件 | `embedded/scenelingo_dashboard.py` |
| 板端上传文件 | `:scenelingo_dashboard.py` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否覆盖板端 `main.py` | 否 |
| API_BASE | `http://192.168.137.1:8000` |
| Wi-Fi SSID / password | 保持 `CHANGE_ME` 占位，不提交真实密码 |
| AUTO_CONNECT_WIFI | `False`，C2 阶段默认不自动联网 |
| mock contexts | `coffee_shop`, `doctor_pharmacy`, `kings_cross`, `baker_street` |
| mock dashboard | `saved_words`, `saved_phrases`, `top_context`, `recent_keywords`, `review_today` |
| 页面入口函数 | `show_home`, `show_context_select`, `show_insight`, `show_dashboard`, `go_back` |
| HTTP helper | `api_get`, `api_post`, `fetch_contexts`, `fetch_context`, `fetch_dashboard`, `save_item` |

## 执行命令记录

| 步骤 | 命令 | 做了什么 | 结果字段 |
| --- | --- | --- | --- |
| 1 | `Get-Content -Raw -Encoding UTF8 embedded\touch_color_test.py` | 读取 C0 测试文件，复用显示/触摸初始化参数 | 确认引脚、屏幕方向、触摸配置 |
| 2 | `Get-Content -Raw -Encoding UTF8 lvgl9_examples\lvgl_multiscreen_example.py` | 查看项目已有 LVGL 多页面写法 | 确认使用 `lv.button`、`lv.screen_load` |
| 3 | `Get-Content -Raw -Encoding UTF8 backend\main.py` | 查看后端 API 路由和字段 | 确认 `/contexts`, `/context/{id}`, `/dashboard`, `/save_item` |
| 4 | `Get-Content -Raw -Encoding UTF8 backend\seed_data.json` | 查看 4 个 MVP context 的 id/title/keywords/phrases | 确认业务 mock 数据字段 |
| 5 | `git status --short --branch` | 确认工作区状态 | 开始前为 `main...origin/main`，无未提交改动 |
| 6 | `python -m py_compile embedded\scenelingo_dashboard.py` | 本地 Python 语法检查 | 通过，无语法错误 |
| 7 | `mpremote connect COM7 fs cp embedded\scenelingo_dashboard.py :scenelingo_dashboard.py` | 上传业务文件到 CYD 文件系统 | 上传成功 |
| 8 | `mpremote connect COM7 fs ls` | 查看板端文件系统 | 存在 `boot.py`, `main.py`, `scenelingo_dashboard.py` |

## 文件结构说明

`scenelingo_dashboard.py` 当前包含以下结构：

```text
API / Wi-Fi config
CYD display / touch config
mock data
global UI state
connect_wifi()
HTTP helper
mock / normalize helper
display initialization
LVGL style helper
screen navigation
Home screen
Context Select screen
Insight View
Dashboard View
Save interaction
main()
```

## C2 验收结果

| 验收项 | 结果 |
| --- | --- |
| `scenelingo_dashboard.py` 可以单独上传 | 通过，已上传到 `:scenelingo_dashboard.py` |
| `API_BASE` 在文件顶部 | 通过 |
| Wi-Fi 配置集中在文件顶部 | 通过 |
| 有 mock 数据入口 | 通过 |
| 有 HTTP helper | 通过 |
| 有 LVGL style/helper | 通过 |
| 有页面导航结构 | 通过 |
| 有 Home / Context / Insight / Dashboard 结构 | 通过 |
| 有保存交互函数 | 通过，`handle_save()` + `save_item()` |
| 未删除或修改 `touch_color_test.py` | 通过 |

## 注意事项

- C2 阶段只建立业务主文件结构；真实 API 联调属于 C11。
- 当前 `AUTO_CONNECT_WIFI = False`，所以即使没有网络，页面也应该先使用 mock 数据启动。
- 真实 Wi-Fi 密码不要写入 `scenelingo_dashboard.py` 或 Git。
- 如果要让板子开机直接运行 C2 业务文件，可以后续把它复制为板端 `main.py`，但本次没有覆盖 C0 的 `main.py`。
