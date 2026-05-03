# LINE_A Task A7 操作记录

## 记录字段

| 字段       | 内容                                                        |
| -------- | --------------------------------------------------------- |
| Line     | `LINE_A`                                                  |
| Task     | `A7 - Summary`                                            |
| 状态       | 已通过                                                       |
| 执行日期     | `2026-05-03`                                              |
| 工作目录     | `C:\hackathon`                                            |
| 后端地址     | `http://127.0.0.1:8000/`                                  |
| 当前服务进程   | `48024`                                                   |
| 主要涉及文件   | `backend/nlp_engine.py`、`backend/main.py`、`scenelingo.db` |
| 本次业务代码改动 | 优化 summary 模板为一句话                                         |
| 文档记录     | `docs/LINE_A_A7_STEPS.md`                                 |
| 下一步      | A8 完成 `/analyze_text`                                     |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` 中详细拆分为 A8 Summary 生成。

当前执行记录按 `docs/TASK_PHASES.md` 的阶段顺序推进：A7 记录 Summary。

## 任务目标

用本地模板生成简短学习建议，保证没有外网和 LLM 时也能演示。

## Summary 规则记录

| 规则            | 当前实现                                   |
| ------------- | -------------------------------------- |
| 生成方式          | `_build_summary()` 使用本地字符串模板           |
| 外部依赖          | 不依赖 LLM，不依赖外网                          |
| context title | summary 中包含 detected context 的 `title` |
| 关键词           | summary 中包含前 2-3 个 keywords            |
| phrase 提示     | 有 phrases 时提示第一个 phrase                |
| 句子长度          | 当前模板压缩为 1 句话                           |
| CYD 小屏幕       | 保持单句、短字符串，便于显示                         |

## 测试文本

```
Hi, can I get a latte with milk to go? How much is the large size?
```

## 验收命令

直接函数检查：

```powershell
.\.venv\Scripts\python.exe -c "from backend.database import init_db, list_contexts; from backend.nlp_engine import analyze_text; init_db(); result=analyze_text('Hi, can I get a latte with milk to go? How much is the large size?', source_type='real-world', optional_context='coffee_shop', contexts=list_contexts()); summary=result['summary']; print(summary); print(type(summary).__name__); print('length=' + str(len(summary))); print('period_count=' + str(summary.count('.'))); print('has_title=' + str('Coffee Shop' in summary)); print('has_keyword=' + str(('latte' in summary) or ('milk' in summary)))"
```

多 context 函数检查：

```powershell
@'
from backend.database import init_db, list_contexts
from backend.nlp_engine import analyze_text

init_db()
contexts = list_contexts()
cases = [
    ("coffee_shop", "real-world", "coffee_shop", "Hi, can I get a latte with milk to go? How much is the large size?"),
    ("doctor_pharmacy", "real-world", "doctor_pharmacy", "I have a headache and a cough. Do I need medicine from the pharmacy?"),
    ("kings_cross", "story", "kings_cross", "Which platform should I use to catch the train to the magic school at King's Cross?"),
    ("baker_street", "story", "baker_street", "The detective found a clue on Baker Street and tried to solve the case."),
]
for expected, source_type, context_id, text in cases:
    result = analyze_text(text, source_type=source_type, optional_context=context_id, contexts=contexts)
    print(f"{expected}: {result['summary']}")
'@ | .\.venv\Scripts\python.exe -
```

API 端到端检查：

```powershell
$payload = @{ raw_text = "Hi, can I get a latte with milk to go? How much is the large size?"; source_type = "real-world"; optional_context = "coffee_shop" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri http://127.0.0.1:8000/analyze_text -Method Post -ContentType "application/json" -Body $payload
$response.summary
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

## 验收结果

| 检查项                | 结果                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| Python 编译检查        | 通过                                                                                              |
| summary 类型         | `String` / `str`                                                                                |
| summary 文本         | `This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.` |
| 字符长度               | `93`                                                                                            |
| 句号数量               | `1`                                                                                             |
| 包含 context title   | 通过，包含 `Coffee Shop`                                                                             |
| 包含关键词              | 通过，包含 `latte` / `milk`                                                                          |
| 不依赖 LLM            | 通过，纯本地模板                                                                                        |
| API 最新 analysis id | `11`                                                                                            |

多 context summary 输出：

```
coffee_shop: This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.
doctor_pharmacy: This looks like Doctor / Pharmacy: focus on headache, cough, need and practice phrases like 'I Have a'.
kings_cross: This looks like Harry Potter - King's Cross: focus on which, platform, should and practice phrases like 'Which Platform'.
baker_street: This looks like Sherlock Holmes - Baker Street: focus on detective, found, clue and practice phrases like 'Solve the Case'.
```

## 代码和数据影响

| 字段                  | 内容                                                                                              |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| 业务代码                | 修改 `backend/nlp_engine.py`                                                                      |
| 修改位置                | `_build_summary()`                                                                              |
| 修改原因                | 将原来的 3 句模板压缩为 1 句，更适合 CYD 小屏幕                                                                   |
| 中文注释                | 已更新中文注释说明本地模板和小屏幕用途                                                                             |
| 数据库                 | A7 验收过程中通过 `/analyze_text` 写入多条 `analysis_results`                                              |
| analysis_results 总数 | `11`                                                                                            |
| 最新 analysis id      | `11`                                                                                            |
| 最新 summary          | `This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.` |
| review_items        | 未新增，`review_today` 仍为 `4`                                                                       |

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

- A7 已通过。
- Summary 现在由本地模板生成，不依赖外网或 LLM。
- Summary 包含 context title、2-3 个关键词和一个 phrase 提示。
- Summary 已压缩成一句话，更适合 CYD 小屏幕展示。
