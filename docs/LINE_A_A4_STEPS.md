# LINE_A Task A4 操作记录

## 记录字段

| 字段       | 内容                                                        |
| -------- | --------------------------------------------------------- |
| Line     | `LINE_A`                                                  |
| Task     | `A4 - NLP Text Cleaning`                                  |
| 状态       | 已通过                                                       |
| 执行日期     | `2026-05-03`                                              |
| 工作目录     | `C:\hackathon`                                            |
| 后端地址     | `http://127.0.0.1:8000/`                                  |
| 当前服务进程   | `19644`                                                   |
| 主要涉及文件   | `backend/nlp_engine.py`、`backend/main.py`、`scenelingo.db` |
| 本次业务代码改动 | 无                                                         |
| 文档记录     | `docs/LINE_A_A4_STEPS.md`                                 |
| 下一步      | A5 Keyword / Phrase Extraction                            |

## 任务目标

把用户输入的英文文本清洗成适合词频统计、关键词提取和 context 分类的 tokens。

## Cleaning 规则记录

| 规则           | 当前实现                                                        |
| ------------ | ----------------------------------------------------------- |
| 英文大小写        | `_tokenize()` 中统一转小写                                        |
| 无意义符号        | `TOKEN_RE` 只保留英文词 token                                     |
| filler words | `_clean_tokens()` 删除 `um`、`uh`、`erm`、`hmm`、`like` 等         |
| stopwords    | `_clean_tokens()` 删除 `a`、`an`、`the`、`to`、`of`、`please` 等    |
| 连续重复词        | `_clean_tokens()` 删除连续重复 token                              |
| 主流程位置        | cleaning 保持在 `backend/nlp_engine.py`，没有写到 `backend/main.py` |
| 外部依赖         | 没有引入 spaCy / NLTK 等复杂 NLP 依赖                                |

## 测试文本

```
Um, hi, hi, can I get a latte with milk to go please?
```

期望 cleaned text：

```
hi get latte milk go
```

## 验收命令

直接函数检查：

```powershell
.\.venv\Scripts\python.exe -c "from backend.nlp_engine import analyze_text; print(analyze_text('Um, hi, hi, can I get a latte with milk to go please?')['cleaned_text'])"
```

边界输入检查：

```powershell
.\.venv\Scripts\python.exe -c "from backend.nlp_engine import analyze_text; result=analyze_text('UM!!! Hi, hi... CAN I get a LATTE with milk to go please?? 123'); print(result['cleaned_text']); print('has_um=' + str('um' in result['cleaned_text'].split())); print('has_please=' + str('please' in result['cleaned_text'].split())); print('has_hi_hi=' + str('hi hi' in result['cleaned_text']));"
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\nlp_engine.py backend\main.py
```

API 端到端检查：

```powershell
$payload = @{ raw_text = "Um, hi, hi, can I get a latte with milk to go please?"; source_type = "real-world"; optional_context = "coffee_shop" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri http://127.0.0.1:8000/analyze_text -Method Post -ContentType "application/json" -Body $payload
$response.cleaned_text
```

## 验收结果

| 检查项              | 结果                                       |
| ---------------- | ---------------------------------------- |
| 直接函数输出           | `hi get latte milk go`                   |
| 大小写归一            | 通过，`UM` / `LATTE` 被转成小写                  |
| 标点清理             | 通过，`!!!`、`,`、`...`、`??` 不进入 cleaned text |
| 数字清理             | 通过，`123` 不进入 cleaned text                |
| filler word 清理   | 通过，`um` 不存在                              |
| stopword 清理      | 通过，`please` 不存在                          |
| 连续重复词清理          | 通过，`hi hi` 不重复出现                         |
| Python 编译检查      | 通过                                       |
| API cleaned_text | `hi get latte milk go`                   |

边界输入检查输出：

```
hi get latte milk go
has_um=False
has_please=False
has_hi_hi=False
```

API 返回核心字段：

| 字段                            | 当前结果                   |
| ----------------------------- | ---------------------- |
| `id`                          | `2`                    |
| `cleaned_text`                | `hi get latte milk go` |
| `keywords`                    | `get`、`latte`、`milk`   |
| `detected_context.id`         | `coffee_shop`          |
| `detected_context.confidence` | `1.0`                  |

## 代码和数据影响

| 字段              | 内容                                                    |
| --------------- | ----------------------------------------------------- |
| 业务代码            | 未修改，现有实现已满足 A4                                        |
| 中文注释            | `backend/nlp_engine.py` 的主流程和关键 helper 已有中文注释         |
| 数据库             | API 端到端验收通过 `/analyze_text` 写入 1 条 `analysis_results` |
| 最新 analysis id  | `2`                                                   |
| 最新 cleaned_text | `hi get latte milk go`                                |
| review_items    | 未新增，`review_today` 仍为 `4`                             |

## 当前 Dashboard 记录

| 字段              | 当前结果                 |
| --------------- | -------------------- |
| saved words     | `receipt`、`latte`    |
| saved phrases   | `for here`、`to go`   |
| top context     | `coffee_shop`        |
| recent keywords | `get`、`latte`、`milk` |
| review_today    | `4`                  |

## 服务状态记录

| 字段   | 内容                       |
| ---- | ------------------------ |
| 当前进程 | `19644`                  |
| 本机访问 | `http://127.0.0.1:8000/` |
| 停止命令 | `Stop-Process -Id 19644` |

## 结论

- A4 已通过。
- `backend/nlp_engine.py` 已能完成小写化、符号清理、filler words 清理、stopwords 清理和连续重复词压缩。
- cleaning 逻辑保留在 NLP 模块中，没有污染 FastAPI 路由层。
- 当前不需要引入额外 NLP 依赖。
