# LINE_A Task A10 操作记录

## 记录字段

| 字段       | 内容                                                      |
| -------- | ------------------------------------------------------- |
| Line     | `LINE_A`                                                |
| Task     | `A10 - Save / Dashboard API`                            |
| 状态       | 已通过                                                     |
| 执行日期     | `2026-05-03`                                            |
| 工作目录     | `C:\hackathon`                                          |
| 后端地址     | `http://127.0.0.1:8000/`                                |
| 当前服务进程   | `48024`                                                 |
| 主要涉及文件   | `backend/main.py`、`backend/database.py`、`scenelingo.db` |
| 本次业务代码改动 | 无                                                       |
| 文档记录     | `docs/LINE_A_A10_STEPS.md`                              |
| 下一步      | A11 局域网联调准备                                             |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` 中详细拆分为 A12 `POST /save_item` 和 A13 `GET /dashboard`。

当前执行记录按 `docs/TASK_PHASES.md` 的阶段顺序推进：A10 记录 Save / Dashboard API。

## 任务目标

完成用户复习项保存和 Dashboard 汇总接口：

- `POST /save_item`：保存用户选择复习的 word / phrase。
- `GET /dashboard`：返回 CYD dashboard 可以直接展示的数据。

## 接口定义

`POST /save_item`

| 字段     | 内容                                 |
| ------ | ---------------------------------- |
| Method | `POST`                             |
| Path   | `/save_item`                       |
| 请求模型   | `SaveItemRequest`                  |
| 数据库写入  | SQLite `review_items` 表            |
| 成功返回   | `{"id": <item_id>, "saved": true}` |

请求字段：

| 字段               | 规则                    |
| ---------------- | --------------------- |
| `item_text`      | 必填，最短 1 个字符           |
| `item_type`      | 只能是 `word` 或 `phrase` |
| `source_context` | 可为空，建议传 context id    |

`GET /dashboard`

| 字段     | 内容                                  |
| ------ | ----------------------------------- |
| Method | `GET`                               |
| Path   | `/dashboard`                        |
| 用途     | 返回 CYD dashboard 汇总数据               |
| 数据来源   | `review_items` 和 `analysis_results` |
| 写数据库   | 否                                   |

Dashboard 重点字段：

```
saved_words
saved_phrases
top_context
recent_keywords
review_today
```

## 验收命令

保存 word / phrase 并检查 Dashboard：

```powershell
$before = .\.venv\Scripts\python.exe -c "import sqlite3; con=sqlite3.connect('scenelingo.db'); print(con.execute('SELECT COUNT(*) FROM review_items').fetchone()[0]); con.close()"
$wordPayload = @{ item_text = "espresso"; item_type = "word"; source_context = "coffee_shop" } | ConvertTo-Json
$phrasePayload = @{ item_text = "large size"; item_type = "phrase"; source_context = "coffee_shop" } | ConvertTo-Json
$wordResult = Invoke-RestMethod -Uri http://127.0.0.1:8000/save_item -Method Post -ContentType "application/json" -Body $wordPayload
$phraseResult = Invoke-RestMethod -Uri http://127.0.0.1:8000/save_item -Method Post -ContentType "application/json" -Body $phrasePayload
$after = .\.venv\Scripts\python.exe -c "import sqlite3; con=sqlite3.connect('scenelingo.db'); print(con.execute('SELECT COUNT(*) FROM review_items').fetchone()[0]); con.close()"
$dashboard = Invoke-RestMethod -Uri http://127.0.0.1:8000/dashboard
$wordVisible = @($dashboard.saved_words | Where-Object { $_.item_text -eq 'espresso' -and $_.source_context -eq 'coffee_shop' }).Count -gt 0
$phraseVisible = @($dashboard.saved_phrases | Where-Object { $_.item_text -eq 'large size' -and $_.source_context -eq 'coffee_shop' }).Count -gt 0
"before=$before"
"after=$after"
"inserted_count=$([int]$after - [int]$before)"
"word_saved=$($wordResult.saved),word_id=$($wordResult.id),word_visible=$wordVisible"
"phrase_saved=$($phraseResult.saved),phrase_id=$($phraseResult.id),phrase_visible=$phraseVisible"
$dashboard | ConvertTo-Json -Depth 8
```

非法 `item_type` 检查：

```powershell
try {
  $badPayload = @{ item_text = "latte"; item_type = "sentence"; source_context = "coffee_shop" } | ConvertTo-Json
  Invoke-RestMethod -Uri http://127.0.0.1:8000/save_item -Method Post -ContentType "application/json" -Body $badPayload -ErrorAction Stop
} catch {
  [int]$_.Exception.Response.StatusCode
}
```

空 `item_text` 检查：

```powershell
try {
  $badPayload = @{ item_text = ""; item_type = "word"; source_context = "coffee_shop" } | ConvertTo-Json
  Invoke-RestMethod -Uri http://127.0.0.1:8000/save_item -Method Post -ContentType "application/json" -Body $badPayload -ErrorAction Stop
} catch {
  [int]$_.Exception.Response.StatusCode
}
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

## 验收结果

| 检查项                         | 结果                              |
| --------------------------- | ------------------------------- |
| Python 编译检查                 | 通过                              |
| 保存 word                     | `espresso` 保存成功，`word_id=5`     |
| 保存 phrase                   | `large size` 保存成功，`phrase_id=6` |
| review_items 写入前            | `4`                             |
| review_items 写入后            | `6`                             |
| 新增写入数量                      | `2`                             |
| Dashboard saved_words       | 包含 `espresso`                   |
| Dashboard saved_phrases     | 包含 `large size`                 |
| Dashboard `top_context`     | `coffee_shop`                   |
| Dashboard `recent_keywords` | 返回 10 个且不重复                     |
| Dashboard `review_today`    | `6`                             |
| 非法 `item_type`              | HTTP `422`                      |
| 空 `item_text`               | HTTP `422`                      |

写入检查输出：

```
before=4
after=6
inserted_count=2
word_saved=True,word_id=5,word_visible=True
phrase_saved=True,phrase_id=6,phrase_visible=True
has_dashboard_fields=True
top_context=coffee_shop
recent_keywords_count=10
recent_keywords_unique=True
review_today=6
```

数据库统计：

```
contexts=4
analysis_results=12
review_items=6
words=3
phrases=3
```

## 代码和数据影响

| 字段                  | 内容                                                                    |
| ------------------- | --------------------------------------------------------------------- |
| 业务代码                | 未修改，现有实现已满足 A10                                                       |
| 中文注释                | `backend/main.py` 和 `backend/database.py` 的 save / dashboard 逻辑已有中文注释 |
| 数据库写入               | 通过 `/save_item` 新增 2 条 `review_items`                                 |
| 新增 word             | `espresso`，source_context `coffee_shop`                               |
| 新增 phrase           | `large size`，source_context `coffee_shop`                             |
| review_items 总数     | `6`                                                                   |
| analysis_results 总数 | `12`                                                                  |

## 当前 Dashboard 记录

| 字段              | 当前结果                                                                          |
| --------------- | ----------------------------------------------------------------------------- |
| saved words     | `espresso`、`receipt`、`latte`                                                  |
| saved phrases   | `large size`、`for here`、`to go`                                               |
| top context     | `coffee_shop`                                                                 |
| recent keywords | `get`、`latte`、`milk`、`how`、`much`、`detective`、`found`、`clue`、`baker`、`street` |
| review_today    | `6`                                                                           |

## 给线 B / 线 C 的联调信息

| 使用方     | 接口                | 用途                                             |
| ------- | ----------------- | ---------------------------------------------- |
| 线 B Web | `POST /save_item` | 用户点击保存 word / phrase                           |
| 线 B Web | `GET /dashboard`  | Web dashboard 或 fallback demo 展示               |
| 线 C CYD | `GET /dashboard`  | CYD dashboard 展示 saved items 和 recent keywords |

稳定返回字段：

```
saved_words
saved_phrases
top_context
recent_keywords
review_today
```

## 服务状态记录

| 字段   | 内容                       |
| ---- | ------------------------ |
| 当前进程 | `48024`                  |
| 本机访问 | `http://127.0.0.1:8000/` |
| 停止命令 | `Stop-Process -Id 48024` |

## 结论

- A10 已通过。
- `/save_item` 可以保存 word 和 phrase。
- `/save_item` 对非法 `item_type` 和空 `item_text` 会返回校验错误。
- `/dashboard` 能分开返回 saved words 和 saved phrases。
- `/dashboard` 能返回 `top_context`、去重后的 `recent_keywords` 和 `review_today`。
