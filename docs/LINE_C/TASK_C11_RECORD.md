# Task C11 记录 - 真实 API 联调

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C11 要求，把 mock 数据切换到线 A 的真实后端，完成 CYD 与后端、Web 的三方联调闭环。

C11 本次重点：

- 新增 C11 联调切换指南注释（顶部配置区）
- 新增 `probe_api()` 函数，启动时测试后端连通性
- 更新 `main()` 打印完整启动诊断信息
- 真实 API 模式自动调用 `probe_api()`，mock 模式跳过
- 保持 `USE_MOCK_DATA = True` 提交，不提交真实密码和 IP

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `embedded/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C11_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |
| 是否提交真实 API IP | 否（保持 `192.168.137.1` 占位符） |

## C11 切换步骤（联调现场操作）

```text
步骤 1：在 laptop 上启动后端
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

步骤 2：查找 laptop 局域网 IP
  Windows : ipconfig  → 找 "IPv4 地址"（如 192.168.1.100）
  Mac/Linux: ifconfig → 找 "inet "

步骤 3：修改 scenelingo_dashboard.py 顶部 4 项（不提交到 Git）
  API_BASE          = "http://192.168.1.100:8000"
  WIFI_SSID         = "实际 Wi-Fi 名称"
  WIFI_PASSWORD     = "实际 Wi-Fi 密码"
  AUTO_CONNECT_WIFI = True
  USE_MOCK_DATA     = False

步骤 4：上传文件到 CYD
  mpremote connect COM7 fs cp embedded\scenelingo_dashboard.py :scenelingo_dashboard.py

步骤 5：运行并观察串口输出
  mpremote connect COM7 run embedded\scenelingo_dashboard.py
  看到 "--> API probe OK" 表示连通正常
  看到 "--> API probe FAILED" 按排查清单检查
```

## C11 联调验收步骤

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | CYD 进入 Dashboard，点 Refresh | 显示真实 `/dashboard` 数据，状态行显示 `"live"` |
| 2 | Web 保存一个 word | Web dashboard 显示新 word |
| 3 | CYD Refresh Dashboard | CYD 显示 Web 刚保存的 word |
| 4 | CYD Insight View 点击 keyword | 状态行显示 `"Saved: <keyword>"` |
| 5 | CYD Insight View 点击 phrase | 状态行显示 `"Saved: <phrase>"` |
| 6 | Web Refresh Dashboard | Web 显示 CYD 保存的 keyword 和 phrase |

## C11 新增字段说明

| 函数 / 配置 | 说明 |
| --- | --- |
| `probe_api()` | 发一次 `GET /dashboard` 测试后端可达性，结果打印到串口，不阻塞 UI |
| C11 联调切换指南 | 顶部配置区注释，列出 4 项需要修改的配置、后端启动命令、联调顺序 |
| `main()` 新增 `probe_api()` 调用 | `USE_MOCK_DATA=False` 时自动调用，mock 模式跳过 |
| `main()` 新增打印 `USE_MOCK_DATA` | 串口输出确认当前是 mock 还是真实 API 模式 |
| `main()` 新增打印 `AUTO_CONNECT_WIFI` | 串口输出确认 Wi-Fi 是否自动连接 |

## probe_api() 工作流程

```text
main()
  -> USE_MOCK_DATA=False → probe_api()
     -> api_get("/dashboard")
        -> _request_json("GET", "/dashboard")
           -> 成功：返回 dashboard data
              -> print("--> API probe OK")
              -> return True
           -> 失败（网络 / IP 错误）：返回 None
              -> print("--> API probe FAILED. Check: ...")
              -> return False
  -> show_home()  ← 无论 probe 结果如何，UI 正常启动
```

## 串口诊断输出示例

**mock 模式（默认）：**
```
--> SceneLingo CYD dashboard ready.
--> MicroPython: 1.23.0
--> LVGL: 9.3
--> API_BASE: http://192.168.137.1:8000
--> USE_MOCK_DATA: True
--> AUTO_CONNECT_WIFI: False
```

**真实 API 模式（联调时）：**
```
--> C11 probe: http://192.168.1.100:8000/dashboard
--> API probe OK
--> SceneLingo CYD dashboard ready.
--> MicroPython: 1.23.0
--> LVGL: 9.3
--> API_BASE: http://192.168.1.100:8000
--> USE_MOCK_DATA: False
--> AUTO_CONNECT_WIFI: True
```

**真实 API 连接失败：**
```
--> C11 probe: http://192.168.1.100:8000/dashboard
--> API probe FAILED. Check: API_BASE / Wi-Fi / firewall / --host 0.0.0.0
```

## 排查清单

| 问题 | 检查项 |
| --- | --- |
| API probe FAILED | 后端是否用 `--host 0.0.0.0` 启动 |
| API probe FAILED | `API_BASE` 是否是 laptop 局域网 IP（非 `localhost`） |
| API probe FAILED | CYD 和 laptop 是否在同一 Wi-Fi / hotspot |
| API probe FAILED | Windows 防火墙是否拦截 8000 端口 |
| API probe FAILED | URL 是否包含 `http://` |
| Dashboard 为空 | Web 是否已保存过 item |
| Dashboard 不更新 | 是否点击了 Refresh |
| 保存失败 | `POST /save_item` payload 是否包含全部字段 |

## C11 验收结果

| 验收项 | 结果 |
| --- | --- |
| 换 IP 只改 `API_BASE` 一处 | 通过，顶部配置区唯一配置 |
| `probe_api()` 存在 | 通过 |
| mock 模式跳过 probe | 通过，`main()` 中 `if not USE_MOCK_DATA` 判断 |
| 真实 API 模式自动 probe | 通过 |
| 串口输出包含 `USE_MOCK_DATA` | 通过 |
| 串口输出包含 `AUTO_CONNECT_WIFI` | 通过 |
| C11 联调切换指南注释完整 | 通过，含后端启动命令、IP 查找方法、联调顺序 |
| 不提交真实密码和 IP | 通过，Git 提交保持占位符 |

## 注意事项

- `probe_api()` 失败不会阻止 UI 启动，只打印串口提示。用户仍可使用 mock 模式浏览所有页面。
- 联调完成后记得把 `USE_MOCK_DATA` 改回 `True`，`WIFI_SSID` / `WIFI_PASSWORD` 改回 `CHANGE_ME`，再提交 Git。
- 若使用 hotspot，laptop 的 IP 通常是 `192.168.137.1`（Windows 移动热点默认值）。
