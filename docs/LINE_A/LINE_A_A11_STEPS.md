# LINE_A Task A11 操作记录

## 记录字段

| 字段        | 内容                                                              |
| --------- | --------------------------------------------------------------- |
| Line      | `LINE_A`                                                        |
| Task      | `A11 - 局域网联调准备`                                                 |
| 状态        | 已通过，本机局域网 IP 连通；跨设备仍需手机 / CYD 实测                                |
| 执行日期      | `2026-05-03`                                                    |
| 工作目录      | `C:\hackathon`                                                  |
| 本地 API    | `http://localhost:8000`                                         |
| 本机 IP API | `http://127.0.0.1:8000`                                         |
| 局域网 API   | `http://10.88.0.183:8000`                                       |
| 启动进程      | `48024`                                                         |
| 监听子进程     | `14136`                                                         |
| 主要涉及文件    | `backend/main.py`、`backend/database.py`、`backend/nlp_engine.py` |
| 本次业务代码改动  | 无                                                               |
| 文档记录      | `docs/LINE_A_A11_STEPS.md`                                      |
| 下一步       | A12 线 A 完成标准                                                    |

## 任务目标

让线 B 的 Web 页面、线 C 的 CYD 设备和队友电脑可以通过同一个局域网地址访问线 A 后端。

## 服务启动记录

当前服务以局域网监听方式运行：

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

监听检查结果：

```
LocalAddress=0.0.0.0
LocalPort=8000
State=Listen
OwningProcess=14136
```

进程关系：

```
48024 -> "C:\hackathon\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
14136 -> child process, owns the TCP listener
```

说明：停止服务时优先停启动进程：

```powershell
Stop-Process -Id 48024
```

如果端口仍被占用，再停监听子进程：

```powershell
Stop-Process -Id 14136
```

## 局域网 IP 记录

当前有效网络：

```
Wireless LAN adapter WiFi
DNS suffix: aber.ac.uk
IPv4 Address: 10.88.0.183
Subnet Mask: 255.255.0.0
Default Gateway: 10.88.255.254
```

给线 B / 线 C 使用：

```
本地 API：http://localhost:8000
本机 IP API：http://127.0.0.1:8000
局域网 API：http://10.88.0.183:8000
```

## 可用接口清单

| Method | Path            | 用途              |
| ------ | --------------- | --------------- |
| `GET`  | `/`             | 健康检查            |
| `GET`  | `/contexts`     | 获取 context 列表   |
| `GET`  | `/context/{id}` | 获取单个 context 卡片 |
| `POST` | `/analyze_text` | 文本分析            |
| `POST` | `/save_item`    | 保存复习项           |
| `GET`  | `/dashboard`    | Dashboard 数据    |

可用 context ids：

```
coffee_shop
doctor_pharmacy
kings_cross
baker_street
```

## 验收命令

监听端口检查：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object LocalAddress,LocalPort,State,OwningProcess
```

局域网 IP 检查：

```powershell
ipconfig
```

端口连通性检查：

```powershell
Test-NetConnection -ComputerName 10.88.0.183 -Port 8000 -InformationLevel Detailed
```

局域网 API 检查：

```powershell
Invoke-RestMethod -Uri http://10.88.0.183:8000/
Invoke-RestMethod -Uri http://10.88.0.183:8000/contexts
Invoke-RestMethod -Uri http://10.88.0.183:8000/dashboard
```

防火墙 profile 检查：

```powershell
netsh advfirewall show allprofiles
```

防火墙规则添加尝试：

```powershell
netsh advfirewall firewall add rule name="SceneLingo FastAPI 8000" dir=in action=allow protocol=TCP localport=8000
```

## 验收结果

| 检查项                | 结果                                           |
| ------------------ | -------------------------------------------- |
| 服务监听地址             | `0.0.0.0:8000`                               |
| 本地健康检查             | 通过                                           |
| 局域网 IP 健康检查        | 通过，`http://10.88.0.183:8000/` 返回 `status=ok` |
| 端口连通性              | `TcpTestSucceeded=True`                      |
| `/contexts` 局域网访问  | 通过，返回 4 个 context                            |
| `/dashboard` 局域网访问 | 通过，返回 saved items 和 dashboard 字段             |
| 防火墙状态              | Domain / Private / Public profiles 均为 ON     |
| 防火墙默认入站策略          | `BlockInbound,AllowOutbound`                 |
| 防火墙规则添加            | 失败，需要管理员 PowerShell                          |

端口连通性输出：

```
ComputerName=10.88.0.183
RemoteAddress=10.88.0.183
RemotePort=8000
NameResolutionResults=10.88.0.183, Siwen.aber.ac.uk
TcpTestSucceeded=True
```

防火墙规则添加结果：

```
No rules match the specified criteria.
The requested operation requires elevation (Run as administrator).
```

## 防火墙说明

当前本机使用局域网 IP 访问 `10.88.0.183:8000` 已经成功，但这只能证明服务监听和本机网络路径正常。

如果手机、CYD 或队友电脑访问失败，请在管理员 PowerShell 中执行：

```powershell
netsh advfirewall firewall add rule name="SceneLingo FastAPI 8000" dir=in action=allow protocol=TCP localport=8000
```

如果校园网或公司网开启客户端隔离，即使防火墙允许，跨设备访问也可能失败。此时可以改用同一热点、同一路由器 WiFi，或用 Web 本机 demo 作为 fallback。

## 给线 B 的交付信息

线 B Web 调用：

```
Base URL：http://10.88.0.183:8000
GET  /contexts
POST /analyze_text
POST /save_item
GET  /dashboard
```

Web 闭环：

```
输入文本 -> POST /analyze_text -> 显示结果 -> POST /save_item -> GET /dashboard
```

## 给线 C 的交付信息

线 C CYD 调用：

```
Base URL：http://10.88.0.183:8000
GET /contexts
GET /context/{id}
GET /dashboard
```

CYD 建议优先显示：

```
context title
summary
saved_words
saved_phrases
recent_keywords
review_today
```

## 当前 Dashboard 记录

| 字段              | 当前结果                                                                          |
| --------------- | ----------------------------------------------------------------------------- |
| saved words     | `espresso`、`receipt`、`latte`                                                  |
| saved phrases   | `large size`、`for here`、`to go`                                               |
| top context     | `coffee_shop`                                                                 |
| recent keywords | `get`、`latte`、`milk`、`how`、`much`、`detective`、`found`、`clue`、`baker`、`street` |
| review_today    | `6`                                                                           |

## 代码和数据影响

| 字段                  | 内容             |
| ------------------- | -------------- |
| 业务代码                | 未修改            |
| 数据库写入               | 无，A11 只做网络联调检查 |
| contexts 总数         | `4`            |
| analysis_results 总数 | `12`           |
| review_items 总数     | `6`            |

## 结论

- A11 已完成局域网联调准备。
- 后端已监听 `0.0.0.0:8000`。
- 本机局域网 IP 为 `10.88.0.183`。
- 局域网 API `http://10.88.0.183:8000` 在本机验证可访问。
- 防火墙默认入站策略是 BlockInbound；如果外部设备访问失败，需要管理员权限添加 TCP 8000 入站规则。
