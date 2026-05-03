# LINE_A Task A8 操作记录

## 记录字段

| 字段       | 内容                                                                              |
| -------- | ------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                        |
| Task     | `A8 - 完成 /analyze_text`                                                         |
| 状态       | 已通过                                                                             |
| 执行日期     | `2026-05-03`                                                                    |
| 工作目录     | `C:\hackathon`                                                                  |
| 后端地址     | `http://127.0.0.1:8000/`                                                        |
| 当前服务进程   | `48024`                                                                         |
| 主要涉及文件   | `backend/main.py`、`backend/nlp_engine.py`、`backend/database.py`、`scenelingo.db` |
| 本次业务代码改动 | 无                                                                               |
| 文档记录     | `docs/LINE_A_A8_STEPS.md`                                                       |
| 下一步      | A9 Context API                                                                  |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` 中详细拆分为 A9 `POST /analyze_text`。

当前执行记录按 `docs/TASK_PHASES.md` 的阶段顺序推进：A8 记录 `/analyze_text`。

## 任务目标

打通核心分析接口：接收用户文本，调用 NLP pipeline，保存分析结果，并返回完整 API response。

## 接口定义

| 字段     | 内容                   |
| ------ | -------------------- |
| Method | `POST`               |
| Path   | `/analyze_text`      |
| 请求模型   | `AnalyzeTextRequest` |
| 返回模型   | `id + NLP result`    |
| 数据库写入  | `analysis_results`   |

请求字段：

| 字段                 | 规则                                     |
| ------------------ | -------------------------------------- |
| `raw_text`         | 必填，最短 1 个字符                            |
| `source_type`      | `real-world` 或 `story`，默认 `real-world` |
| `optional_context` | 可为空；传入时 NLP 分类优先使用该 context            |

返回必须包含：

```
id
cleaned_text
keywords
phrases
detected_context
summary
suggested_review_items
```

## 测试文本

```
Hi, can I get a latte with milk to go?
```

## 验收命令

数据库写入前后计数 + API 检查：

```powershell
$before = .\.venv\Scripts\python.exe -c "import sqlite3; con=sqlite3.connect('scenelingo.db'); print(con.execute('SELECT COUNT(*) FROM analysis_results').fetchone()[0]); con.close()"
$payload = @{ raw_text = "Hi, can I get a latte with milk to go?"; source_type = "real-world"; optional_context = $null } | ConvertTo-Json
$response = Invoke-RestMethod -Uri http://127.0.0.1:8000/analyze_text -Method Post -ContentType "application/json" -Body $payload
$after = .\.venv\Scripts\python.exe -c "import sqlite3; con=sqlite3.connect('scenelingo.db'); print(con.execute('SELECT COUNT(*) FROM analysis_results').fetchone()[0]); con.close()"
$required = @('id', 'cleaned_text', 'keywords', 'phrases', 'detected_context', 'summary', 'suggested_review_items')
$fields = @($response.PSObject.Properties.Name)
$missing = @($required | Where-Object { $_ -notin $fields })
"before=$before"
"after=$after"
"inserted_count=$([int]$after - [int]$before)"
"status=HTTP_200"
"missing_fields=$($missing -join ',')"
"detected_context_id=$($response.detected_context.id)"
"keywords_is_array=$($response.keywords -is [System.Array])"
"phrases_is_array=$($response.phrases -is [System.Array])"
"suggested_review_items_is_array=$($response.suggested_review_items -is [System.Array])"
$response | ConvertTo-Json -Depth 8
```

Dashboard 检查：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/dashboard
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

## 验收结果

| 检查项                         | 结果            |
| --------------------------- | ------------- |
| Python 编译检查                 | 通过            |
| HTTP 状态                     | `200`         |
| 返回字段完整性                     | 通过，无缺失字段      |
| `detected_context.id`       | `coffee_shop` |
| `keywords` 类型               | array / list  |
| `phrases` 类型                | array / list  |
| `suggested_review_items` 类型 | array / list  |
| 写入前 `analysis_results`      | `11`          |
| 写入后 `analysis_results`      | `12`          |
| 新增写入数量                      | `1`           |
| 最新 analysis id              | `12`          |
| Dashboard `top_context`     | `coffee_shop` |

API 返回核心字段：

| 字段                       | 当前结果                                                                                            |
| ------------------------ | ----------------------------------------------------------------------------------------------- |
| `id`                     | `12`                                                                                            |
| `cleaned_text`           | `hi get latte milk go`                                                                          |
| `keywords`               | `["get", "latte", "milk"]`                                                                      |
| `phrases`                | `["Can I Get", "to go", "with milk"]`                                                           |
| `detected_context.id`    | `coffee_shop`                                                                                   |
| `summary`                | `This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.` |
| `suggested_review_items` | `["get", "latte", "milk", "Can I Get", "to go"]`                                                |

数据库最新行：

```
(12, 'coffee_shop', 'hi get latte milk go', "This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.")
```

## 代码和数据影响

| 字段                  | 内容                                                |
| ------------------- | ------------------------------------------------- |
| 业务代码                | 未修改，现有实现已满足 A8                                    |
| 中文注释                | `backend/main.py` 的 `/analyze_text` 路由已有中文注释      |
| 数据库                 | A8 验收通过 `/analyze_text` 写入 1 条 `analysis_results` |
| analysis_results 总数 | `12`                                              |
| 最新 analysis id      | `12`                                              |
| review_items        | 未新增，`review_today` 仍为 `4`                         |

## 当前 Dashboard 记录

| 字段              | 当前结果                                                                          |
| --------------- | ----------------------------------------------------------------------------- |
| saved words     | `receipt`、`latte`                                                             |
| saved phrases   | `for here`、`to go`                                                            |
| top context     | `coffee_shop`                                                                 |
| recent keywords | `get`、`latte`、`milk`、`how`、`much`、`detective`、`found`、`clue`、`baker`、`street` |
| review_today    | `4`                                                                           |

## 服务状态记录

| 字段   | 内容                       |
| ---- | ------------------------ |
| 当前进程 | `48024`                  |
| 本机访问 | `http://127.0.0.1:8000/` |
| 停止命令 | `Stop-Process -Id 48024` |

## 结论

- A8 已通过。
- `/analyze_text` 可以接收 `raw_text`、`source_type`、`optional_context`。
- 接口会调用 NLP pipeline，返回完整分析结果。
- 接口会把结果写入 `analysis_results`。
- Dashboard 可以读取分析结果并更新 `top_context`。
