# LINE_A Task A5 操作记录

## 记录字段

| 字段       | 内容                                                        |
| -------- | --------------------------------------------------------- |
| Line     | `LINE_A`                                                  |
| Task     | `A5 - Keyword / Phrase Extraction`                        |
| 状态       | 已通过                                                       |
| 执行日期     | `2026-05-03`                                              |
| 工作目录     | `C:\hackathon`                                            |
| 后端地址     | `http://127.0.0.1:8000/`                                  |
| 当前服务进程   | `42864`                                                   |
| 主要涉及文件   | `backend/nlp_engine.py`、`backend/main.py`、`scenelingo.db` |
| 本次业务代码改动 | 优化 seed phrase 展示格式                                       |
| 文档记录     | `docs/LINE_A_A5_STEPS.md`                                 |
| 下一步      | A6 Context Classification                                 |

## 任务目标

从 cleaned tokens 中提取最多 5 个关键词，并从当前 context 中优先提取最多 3 个学习短语。

## 提取规则记录

| 类型            | 规则                               |
| ------------- | -------------------------------- |
| Keywords      | 基于 cleaned tokens 做词频统计          |
| Keyword 长度    | 长度小于等于 2 的词不作为 keyword           |
| Keyword 数量    | 默认最多 5 个                         |
| Phrases 优先级 1 | 优先匹配当前 context 的 `seed_phrases`  |
| Phrases 优先级 2 | 不够时从 cleaned tokens 拼 3 词短语      |
| Phrases 优先级 3 | 仍不够时再拼 2 词短语                     |
| Phrase 数量     | 默认最多 3 个                         |
| 返回格式          | `keywords` 和 `phrases` 都必须是 list |

## 测试文本

后端详细任务文档 A5 测试文本：

```
Can I get a latte with milk? I want a large latte to go.
```

阶段总览 A5 测试文本：

```
Hi, can I get a latte with milk to go? How much is the large size?
```

## 验收命令

直接函数检查：

```powershell
.\.venv\Scripts\python.exe -c "from backend.database import init_db, list_contexts; from backend.nlp_engine import analyze_text; init_db(); result=analyze_text('Can I get a latte with milk? I want a large latte to go.', source_type='real-world', optional_context='coffee_shop', contexts=list_contexts()); print(result['keywords']); print(result['phrases']); print('first_keyword=' + result['keywords'][0]); print('keywords_is_list=' + str(isinstance(result['keywords'], list))); print('phrases_is_list=' + str(isinstance(result['phrases'], list))); print('keyword_count=' + str(len(result['keywords']))); print('phrase_count=' + str(len(result['phrases'])))"
```

阶段总览文本检查：

```powershell
.\.venv\Scripts\python.exe -c "from backend.database import init_db, list_contexts; from backend.nlp_engine import analyze_text; init_db(); result=analyze_text('Hi, can I get a latte with milk to go? How much is the large size?', source_type='real-world', optional_context='coffee_shop', contexts=list_contexts()); print(result['keywords']); print(result['phrases']); print('has_latte_or_milk=' + str(('latte' in result['keywords']) or ('milk' in result['keywords']))); print('has_expected_phrase=' + str(('Can I Get' in result['phrases']) or ('to go' in result['phrases'])))"
```

API 端到端检查：

```powershell
$payload = @{ raw_text = "Can I get a latte with milk? I want a large latte to go."; source_type = "real-world"; optional_context = "coffee_shop" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri http://127.0.0.1:8000/analyze_text -Method Post -ContentType "application/json" -Body $payload
$response.keywords
$response.phrases
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\nlp_engine.py backend\main.py
```

## 验收结果

| 检查项                | 结果                                  |
| ------------------ | ----------------------------------- |
| Python 编译检查        | 通过                                  |
| keywords 类型        | list                                |
| phrases 类型         | list                                |
| keyword 数量         | `5`                                 |
| phrase 数量          | `3`                                 |
| A5 详细测试首个 keyword  | `latte`                             |
| A5 详细测试 keywords   | `latte`、`get`、`milk`、`want`、`large` |
| A5 详细测试 phrases    | `Can I Get`、`to go`、`with milk`     |
| 阶段总览 keywords      | 包含 `latte` 和 `milk`                 |
| 阶段总览 phrases       | 包含 `Can I Get` 和 `to go`            |
| API 最新 analysis id | `5`                                 |

API 返回核心字段：

| 字段                       | 当前结果                                             |
| ------------------------ | ------------------------------------------------ |
| `cleaned_text`           | `get latte milk want large latte go`             |
| `keywords`               | `["latte", "get", "milk", "want", "large"]`      |
| `phrases`                | `["Can I Get", "to go", "with milk"]`            |
| `suggested_review_items` | `["latte", "get", "milk", "Can I Get", "to go"]` |

## 代码和数据影响

| 字段                  | 内容                                                          |
| ------------------- | ----------------------------------------------------------- |
| 业务代码                | 修改 `backend/nlp_engine.py`                                  |
| 修改位置                | `_title_phrase()`                                           |
| 修改原因                | 让 `to go`、`for here`、`with milk` 这类功能短语保持自然小写，避免显示成 `to Go` |
| 中文注释                | 已更新中文注释说明 phrase 展示规则                                       |
| 数据库                 | A5 验收过程中通过 `/analyze_text` 写入多条 `analysis_results`          |
| analysis_results 总数 | `5`                                                         |
| 最新 analysis id      | `5`                                                         |
| review_items        | 未新增，`review_today` 仍为 `4`                                   |

## 当前 Dashboard 记录

| 字段              | 当前结果                                |
| --------------- | ----------------------------------- |
| saved words     | `receipt`、`latte`                   |
| saved phrases   | `for here`、`to go`                  |
| top context     | `coffee_shop`                       |
| recent keywords | `latte`、`get`、`milk`、`want`、`large` |
| review_today    | `4`                                 |

## 服务状态记录

| 字段   | 内容                       |
| ---- | ------------------------ |
| 当前进程 | `42864`                  |
| 本机访问 | `http://127.0.0.1:8000/` |
| 停止命令 | `Stop-Process -Id 42864` |

## 结论

- A5 已通过。
- `keywords` 能按词频返回最多 5 个学习关键词，`latte` 在测试文本中排在最前面。
- `phrases` 能优先匹配 Coffee Shop 的 seed phrases，并返回最多 3 个 list 项。
- Phrase 展示格式已调整为更适合学习者阅读的形式，例如 `Can I Get` 和 `to go`。
