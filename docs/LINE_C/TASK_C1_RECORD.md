# Task C1 记录 - Wi-Fi / Network 确认

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C1 要求，确认 CYD 可以连接到和 laptop 可互通的网络，并记录 CYD IP。

本次采用路线：

```text
laptop -> eduroam
laptop Mobile Hotspot -> SceneLingo-CYD
CYD -> SceneLingo-CYD
CYD API_BASE -> http://192.168.137.1:8000
```

这样 laptop 仍然通过 `eduroam` 上网，但 CYD 不直接连接 `eduroam`，避免 WPA2-Enterprise / EAP 配置问题。

## 本次记录字段

| 字段 | 内容 |
| --- | --- |
| CYD 串口 | `COM7` |
| CYD USB 识别 | `1a86:7523 wch.cn` |
| laptop 主网络 | `eduroam` |
| laptop 主网络 IP | `10.83.6.63` |
| laptop 热点 SSID | `SceneLingo-CYD` |
| 热点密码 | 已隐藏，不写入仓库 |
| laptop 热点侧 IP | `192.168.137.1` |
| laptop 热点侧子网掩码 | `255.255.255.0` |
| CYD IP | `192.168.137.181` |
| CYD 子网掩码 | `255.255.255.0` |
| CYD 网关 | `192.168.137.1` |
| CYD DNS | `192.168.137.1` |
| 后端 API_BASE | `http://192.168.137.1:8000` |
| 热点客户端数量 | `1` |
| laptop ping CYD | 成功，2/2 received，0% loss |

## 执行命令记录

| 步骤 | 命令 | 做了什么 | 结果字段 |
| --- | --- | --- | --- |
| 1 | `mpremote connect list` | 查看可用串口，确认 CYD 端口 | `COM7 1a86:7523 wch.cn` |
| 2 | `ipconfig` | 查看 laptop 网络信息 | `WLAN IP = 10.83.6.63`，热点侧 IP = `192.168.137.1` |
| 3 | Windows `NetworkOperatorTetheringManager` | 检查 Mobile Hotspot 状态 | 初始状态为 `Off` |
| 4 | Windows `NetworkOperatorTetheringManager.StartTetheringAsync()` | 启动 laptop Mobile Hotspot | `StartStatus: Success`，`State: On` |
| 5 | `mpremote connect COM7 exec "print('raw repl ok')"` | 确认 CYD 可以进入 MicroPython raw REPL | `raw repl ok` |
| 6 | `mpremote connect COM7 exec "... w.scan() ... w.connect(ssid, password) ..."` | 扫描 Wi-Fi，并让 CYD 连接 `SceneLingo-CYD` | 扫描到 `SceneLingo-CYD`，连接成功 |
| 7 | `w.ifconfig()` | 读取 CYD 网络配置 | `('192.168.137.181', '255.255.255.0', '192.168.137.1', '192.168.137.1')` |
| 8 | `ping -n 2 192.168.137.181` | laptop 侧验证能访问 CYD | `Sent = 2, Received = 2, Lost = 0` |
| 9 | Windows `NetworkOperatorTetheringManager` | 再次确认热点状态和客户端数量 | `State: On`，`ClientCount: 1` |

说明：第 6 步实际运行时需要热点密码，但文档和仓库文件中只记录占位说明，不记录真实密码。

## C1 验收结果

| 验收项 | 结果 |
| --- | --- |
| 配置 Wi-Fi SSID / password | 已通过临时运行命令配置，密码未写入仓库 |
| CYD 连上 Wi-Fi / hotspot | 通过 |
| 记录 CYD IP | `192.168.137.181` |
| laptop 和 CYD 在同一网段 | 通过，均在 `192.168.137.x/24` |
| 后端地址使用 laptop 局域网 IP | `http://192.168.137.1:8000` |
| 不使用 `localhost` 作为 CYD API 地址 | 通过 |

## 后续使用方式

C2 之后的 CYD 业务文件顶部应使用：

```python
API_BASE = "http://192.168.137.1:8000"
```

FastAPI 后端需要用下面的方式启动，才能让 CYD 从热点侧访问：

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 注意事项

- CYD 不直接连接 `eduroam`，因为当前 MicroPython 固件不支持 WPA2-Enterprise / EAP 参数。
- 不要把真实 Wi-Fi 密码提交到 Git。
- CYD 访问 laptop 后端时必须使用 laptop 的局域网 IP，例如 `192.168.137.1`，不能使用 `localhost`。
- 如果 laptop 重启或热点关闭，需要重新打开 Mobile Hotspot，并重新确认 CYD IP。
