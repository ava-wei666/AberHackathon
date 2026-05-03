# LINE_A Task A0-A1 操作记录

本文档记录 LINE_A 前两个任务的执行方式、验收标准和本次实际检查结果。

## 总体原则

- 线 A 负责后端 API、NLP 管线、SQLite 数据存储和给 Web / CYD 使用的接口。
- A0-A1 阶段只做环境确认和健康检查，不新增业务功能。
- 后续凡是涉及代码新增或修改，函数、接口、关键逻辑和不直观的数据处理都使用中文注释说明。
- 不创建第二个虚拟环境，不把依赖安装到系统 Python，不新增重复的 requirements 文件。

## Task A0 - 环境确认

目标：确认本地后端开发环境可用。

推荐操作：

```powershell
cd C:\hackathon
.\.venv\Scripts\Activate.ps1
python --version
python -m pip list
python -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

验收标准：

- 可以使用项目已有的 `.venv`。
- `fastapi`、`uvicorn`、`pydantic` 已安装。
- 后端 Python 文件语法检查无报错。

本次实际检查结果：

- Python 版本：`Python 3.14.3`
- 已确认依赖：
  - `fastapi==0.136.1`
  - `uvicorn==0.46.0`
  - `pydantic==2.13.3`
- 已执行语法检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

结果：无报错，A0 通过。

## Task A1 - API 健康检查

目标：确认 FastAPI 后端服务可以启动，并且 Web / CYD / 队友能访问健康检查接口。

涉及文件：

```
backend/main.py
```

健康检查接口：

```http
GET /
```

期望返回：

```json
{
  "status": "ok",
  "service": "SceneLingo API"
}
```

推荐启动方式：

```powershell
cd C:\hackathon
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

如果需要让同一局域网里的手机、CYD 或队友电脑访问，可以使用：

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

本机测试方式：

```powershell
curl http://localhost:8000/
```

或在浏览器打开：

```
http://localhost:8000
```

本次实际检查方式：

当前 Codex shell 会在单次命令结束后清理后台子进程，因此我使用同一个 PowerShell 调用完成“启动服务 -> 请求接口 -> 关闭服务”的验收：

```powershell
$process = Start-Process -FilePath "C:\hackathon\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory "C:\hackathon" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 3
Invoke-RestMethod -Uri http://127.0.0.1:8000/
Stop-Process -Id $process.Id
```

实际返回：

```
status:  ok
service: SceneLingo API
```

结果：健康检查接口可用，A1 通过。

## 代码注释约定

- 本次 A0-A1 没有修改业务代码。
- 已查看 `backend/main.py`、`backend/database.py`、`backend/nlp_engine.py`，当前关键函数和接口已经采用中文注释风格。
- 后续从 A2 开始，如果新增或修改代码，统一使用中文注释解释接口职责、数据流、数据库写入、NLP 处理和异常分支。
- 注释只写在能帮助队友理解的位置，避免给显而易见的语句添加噪音注释。

## 2026-05-03 执行结论

- A0 已执行并通过：项目 `.venv` 可用，Python 版本为 `3.14.3`，`fastapi==0.136.1`、`uvicorn==0.46.0`、`pydantic==2.13.3` 均安装在项目虚拟环境中。
- A0 语法检查已通过：`backend/__init__.py`、`backend/main.py`、`backend/nlp_engine.py`、`backend/database.py` 均无编译错误。
- A1 已执行并通过：FastAPI 可启动，`GET http://127.0.0.1:8000/` 返回 `status=ok` 和 `service=SceneLingo API`。
- A1 后台服务已启动：当前 FastAPI 进程号为 `38300`，本机访问地址为 `http://127.0.0.1:8000/`。
- 当前阶段没有新增或修改业务代码，只记录操作步骤和验收结果。
