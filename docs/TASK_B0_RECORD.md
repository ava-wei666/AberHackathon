# Task B0 记录 - Web 运行确认

日期：2026-05-03

## 目标

确认 Web 页面不依赖任何构建工具，直接打开即可运行。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |
| 是否引入 Node.js / npm | 否 |
| 是否引入前端框架 | 否 |

## 运行方式

电脑浏览器直接打开：

```
web/index.html
```

手机访问时，用 Python 内置静态服务：

```powershell
cd D:\web_cyd\AberHackathon-main
python -m http.server 5500 --directory web
```

手机浏览器访问：

```
http://你的电脑IP:5500
```

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 直接双击 `web/index.html` | 页面正常加载，不白屏 |
| 2 | 确认无 `package.json`、无 `node_modules` | 通过，无需安装依赖 |
| 3 | 确认 `API_BASE` 集中在一处 | 通过，`const API_BASE = "http://localhost:8000"` |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 电脑浏览器能直接打开页面 | 通过 |
| 不需要安装 Node.js 依赖 | 通过 |
| 不需要启动前端 dev server | 通过 |
| 手机能通过 Python http.server 访问 | 通过 |
