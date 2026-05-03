# Task B8 记录 - 手机浏览器联调

日期：2026-05-03

## 目标

让手机也可以作为输入端，访问 laptop 上的后端和 Web 页面。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |
| 需配合线 A | 后端用 `--host 0.0.0.0` 启动 |

## 联调前置条件

1. 线 A 后端用以下命令启动：

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. laptop 和手机连接同一 Wi-Fi 或 hotspot。

3. 查看 laptop 局域网 IP：

```powershell
ipconfig
# 找 IPv4 Address，例如 192.168.1.100
```

## Web 页面静态服务

```powershell
cd D:\web_cyd\AberHackathon-main
python -m http.server 5500 --directory web
```

手机浏览器访问：`http://laptop局域网IP:5500`

## API 地址修改

`web/index.html` 第一行 JS 配置：

```js
// 手机访问时改成 laptop 的局域网 IP
const API_BASE = "http://192.168.x.x:8000";
```

只改这一处，整页生效。

## 注意事项

- 手机里的 `localhost` 指手机自己，不是 laptop。必须改成 laptop 的局域网 IP。
- 演示结束后把 `API_BASE` 改回 `http://localhost:8000`，避免提交错误地址。

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 确认 `API_BASE` 只有一处 | 通过，`web/index.html` 顶部第一行 JS |
| 2 | 手机访问 Web 页面 | 通过，5500 端口 |
| 3 | 手机提交 `/analyze_text` | 通过 |
| 4 | 手机保存 item | 通过 |
| 5 | 手机刷新 dashboard | 通过 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 手机能加载 contexts | 通过 |
| 手机能提交 `/analyze_text` | 通过 |
| 手机能保存 item | 通过 |
| 手机能刷新 dashboard | 通过 |
| 换 API 地址只改一处 | 通过 |
