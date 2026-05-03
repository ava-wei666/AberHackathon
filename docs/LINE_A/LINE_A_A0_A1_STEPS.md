# LINE_A Task A0-A1 操作记录

## 记录字段

| 字段       | 内容                                                                                                       |
| -------- | -------------------------------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                                                 |
| Task     | `A0 - 环境确认` / `A1 - API 健康检查`                                                                            |
| 状态       | 已通过                                                                                                      |
| 执行日期     | `2026-05-03`                                                                                             |
| 工作目录     | `C:\hackathon`                                                                                           |
| 虚拟环境     | `C:\hackathon\.venv`                                                                                     |
| 后端地址     | `http://127.0.0.1:8000/`                                                                                 |
| 当前服务进程   | A7 后已重启为 `48024`                                                                                         |
| 主要涉及文件   | `backend/main.py`、`backend/__init__.py`、`backend/nlp_engine.py`、`backend/database.py`、`requirements.txt` |
| 本次业务代码改动 | 无                                                                                                        |
| 文档记录     | `docs/LINE_A_A0_A1_STEPS.md`                                                                             |
| 下一步      | A2 Seed Data 管理                                                                                          |

## 任务目标

A0 目标：确认本地后端开发环境可用。

A1 目标：确认 FastAPI 后端服务可以启动，并且 Web / CYD / 队友可以访问健康检查接口。

## 统一约定

- 使用项目已有 `.venv`，不创建第二个虚拟环境。
- 依赖只使用项目虚拟环境，不安装到系统 Python。
- 不新增重复的 requirements 文件。
- 后续凡是涉及代码新增或修改，函数、接口、关键逻辑和不直观的数据处理都使用中文注释说明。
- 注释写在能帮助队友理解的位置，避免给显而易见的语句添加噪音注释。

## 验收命令

A0 环境检查：

```powershell
cd C:\hackathon
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip show fastapi uvicorn pydantic
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

A1 服务检查推荐本地启动：

```powershell
cd C:\hackathon
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

局域网联调启动：

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

本机测试：

```powershell
curl http://localhost:8000/
```

本次 Codex 验收方式：

```powershell
$process = Start-Process -FilePath "C:\hackathon\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory "C:\hackathon" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 3
Invoke-RestMethod -Uri http://127.0.0.1:8000/
Stop-Process -Id $process.Id
```

## 验收结果

A0 环境检查：

| 检查项         | 结果                 |
| ----------- | ------------------ |
| Python 版本   | `Python 3.14.3`    |
| FastAPI     | `fastapi==0.136.1` |
| Uvicorn     | `uvicorn==0.46.0`  |
| Pydantic    | `pydantic==2.13.3` |
| Python 编译检查 | 通过，无报错             |

A1 接口定义：

| 字段     | 内容                                           |
| ------ | -------------------------------------------- |
| Method | `GET`                                        |
| Path   | `/`                                          |
| 用途     | 后端健康检查                                       |
| 期望返回   | `{"status":"ok","service":"SceneLingo API"}` |

A1 接口检查：

| 检查项        | 结果                       |
| ---------- | ------------------------ |
| FastAPI 启动 | 通过                       |
| 健康检查接口     | 通过                       |
| 返回 status  | `ok`                     |
| 返回 service | `SceneLingo API`         |
| 浏览器访问地址    | `http://localhost:8000`  |
| 本机 API 地址  | `http://127.0.0.1:8000/` |

## 代码和数据影响

| 字段        | 内容                  |
| --------- | ------------------- |
| 业务代码      | 未修改                 |
| 数据库       | 未修改                 |
| Seed data | 未修改                 |
| 文档        | 已整理 A0-A1 环境和接口验收记录 |
| 中文注释要求    | 后续新增或修改代码时继续执行      |

## 服务状态记录

| 时间点    | 进程号     | 说明                          |
| ------ | ------- | --------------------------- |
| A1 执行后 | `38300` | A1 阶段启动的后台服务                |
| A3 执行后 | `19644` | A3 修改数据库连接后重启的服务            |
| A5 执行后 | `42864` | A5 修改 NLP phrase 展示格式后重启的服务 |
| A7 执行后 | `48024` | A7 修改 summary 模板后重启，当前使用此进程 |

停止当前服务：

```powershell
Stop-Process -Id 48024
```

## 结论

- A0 已通过：项目 `.venv` 可用，依赖完整，后端 Python 文件语法检查无报错。
- A1 已通过：FastAPI 可以启动，`GET /` 返回健康检查 JSON。
- A0-A1 阶段未修改业务代码，只记录环境、命令和验收结果。
