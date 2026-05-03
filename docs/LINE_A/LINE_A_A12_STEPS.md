# LINE_A Task A12 操作记录

## 记录字段

| 字段       | 内容                                                                              |
| -------- | ------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                        |
| Task     | `A12 - 线 A 完成标准`                                                                |
| 状态       | 已通过                                                                             |
| 执行日期     | `2026-05-03`                                                                    |
| 工作目录     | `C:\hackathon`                                                                  |
| 后端验收地址   | `http://127.0.0.1:8000/`                                                        |
| 验收服务方式   | PowerShell `Start-Job` 临时启动 Uvicorn，验收结束后清理                                     |
| 主要涉及文件   | `backend/main.py`、`backend/database.py`、`backend/nlp_engine.py`、`scenelingo.db` |
| 本次业务代码改动 | 有，补强请求模型的空白裁剪和空内容校验                                                             |
| 中文注释     | 已在新增校验逻辑处补充中文注释                                                                 |
| 文档记录     | `docs/LINE_A_A12_STEPS.md`                                                      |
| 下一步      | 线 B / 线 C 可以进入完整集成彩排                                                            |

## 编号说明

`docs/TASK_PHASES.md` 中 A12 是线 A 的完成标准，本次按这个阶段编号收口。

`docs/LINE_A_BACKEND_TASKS.md` 中的 A12 `POST /save_item` 和 A13 `GET /dashboard` 已经在前面的 Save / Dashboard 验收中覆盖；本次 A12 重点检查线 A 整体 API 是否满足最终演示闭环。

## 任务目标

确认线 A 后端满足最终 MVP 完成标准：

- `GET /` 可用。
- `GET /contexts` 返回 4 个 context。
- `POST /analyze_text` 能分析 4 段 demo 文本。
- `POST /save_item` 能保存 word / phrase。
- `GET /dashboard` 能返回 saved items。
- Web 不需要知道数据库细节。
- CYD 不需要做 NLP。
- 无网络、无 LLM API key 也能完整演示。

## 代码改动

文件：`backend/main.py`

本次只补强请求模型校验，不改变 API 字段名：

- `AnalyzeTextRequest.raw_text`：先裁剪首尾空白，纯空白返回 HTTP 422。
- `AnalyzeTextRequest.optional_context`：空字符串或纯空白统一转成 `None`。
- `SaveItemRequest.item_text`：先裁剪首尾空白，纯空白返回 HTTP 422。
- `SaveItemRequest.source_context`：空字符串或纯空白统一转成 `None`。

新增逻辑旁边均已写中文注释，保持线 A 后端文件的注释风格。

## 代码片段说明

请求模型现在会在进入路由前完成基础清洗：

```python
@field_validator("item_text")
@classmethod
def normalize_item_text(cls, value: str) -> str:
    # 保存复习项前统一裁剪空白，确保 review_items 里不会出现空内容。
    stripped_value = value.strip()
    if not stripped_value:
        raise ValueError("item_text cannot be empty")
    return stripped_value
```

## 验收命令

语法检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

请求模型校验：

```powershell
@'
from pydantic import ValidationError
from backend.main import AnalyzeTextRequest, SaveItemRequest

checks = []
checks.append(("trim_raw_text", AnalyzeTextRequest(raw_text="  Hi there  ").raw_text == "Hi there"))
checks.append(("blank_optional_context_to_none", AnalyzeTextRequest(raw_text="Hi", optional_context="   ").optional_context is None))
checks.append(("trim_item_text", SaveItemRequest(item_text="  latte  ", item_type="word").item_text == "latte"))
checks.append(("blank_source_context_to_none", SaveItemRequest(item_text="latte", item_type="word", source_context="   ").source_context is None))

try:
    AnalyzeTextRequest(raw_text="   ")
    checks.append(("blank_raw_text_rejected", False))
except ValidationError:
    checks.append(("blank_raw_text_rejected", True))

try:
    SaveItemRequest(item_text="   ", item_type="word")
    checks.append(("blank_item_text_rejected", False))
except ValidationError:
    checks.append(("blank_item_text_rejected", True))

try:
    SaveItemRequest(item_text="latte", item_type="sentence")
    checks.append(("bad_item_type_rejected", False))
except ValidationError:
    checks.append(("bad_item_type_rejected", True))

for name, passed in checks:
    print(f"{name}={passed}")
print(f"all_model_checks={all(passed for _, passed in checks)}")
'@ | .\.venv\Scripts\python.exe -
```

真实 HTTP 验收使用临时 Uvicorn Job：

```powershell
$base = "http://127.0.0.1:8000"
$job = Start-Job -ScriptBlock {
  Set-Location "C:\hackathon"
  .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
}

# 等待健康检查通过后，依次请求：
# GET /
# GET /contexts
# POST /analyze_text，覆盖 4 段 demo 文本
# POST /save_item，分别保存 word 和 phrase
# POST /save_item，检查非法 item_type 返回 422
# POST /save_item，检查纯空白 item_text 返回 422
# POST /analyze_text，检查纯空白 raw_text 返回 422
# GET /dashboard

Stop-Job -Job $job
Remove-Job -Job $job -Force
```

说明：`fastapi.testclient` 需要额外的 `httpx` 包，当前项目未安装。为避免临时增加依赖，本次改用真实 Uvicorn HTTP 请求验收。

## 验收结果

| 检查项                       | 结果                              |
| ------------------------- | ------------------------------- |
| Python 编译检查               | 通过                              |
| 请求模型校验                    | 通过                              |
| `GET /`                   | HTTP `200`，返回 `SceneLingo API`  |
| `GET /contexts`           | HTTP `200`，返回 4 个 context       |
| real-world ids            | `coffee_shop`、`doctor_pharmacy` |
| story ids                 | `kings_cross`、`baker_street`    |
| Coffee Shop demo          | 识别为 `coffee_shop`               |
| Doctor / Pharmacy demo    | 识别为 `doctor_pharmacy`           |
| King's Cross demo         | 识别为 `kings_cross`               |
| Baker Street demo         | 识别为 `baker_street`              |
| `/analyze_text` 返回字段      | 无缺失                             |
| 保存 word                   | `cappuccino` 保存成功，`id=7`        |
| 保存 phrase                 | `magic school` 保存成功，`id=8`      |
| 非法 `item_type`            | HTTP `422`                      |
| 纯空白 `item_text`           | HTTP `422`                      |
| 纯空白 `raw_text`            | HTTP `422`                      |
| Dashboard word 可见         | 通过                              |
| Dashboard phrase 可见       | 通过                              |
| Dashboard `top_context`   | `coffee_shop`                   |
| Dashboard recent keywords | 10 个，且不重复                       |
| Dashboard `review_today`  | `8`                             |

核心输出：

```
uvicorn_job_id=1
uvicorn_job_state=Running
health_status=200
health_service=SceneLingo API
contexts_total=4
real_world_ids=coffee_shop,doctor_pharmacy
story_ids=kings_cross,baker_street
analyze_coffee_shop_detected=coffee_shop
analyze_doctor_pharmacy_detected=doctor_pharmacy
analyze_kings_cross_detected=kings_cross
analyze_baker_street_detected=baker_street
save_word_saved=True
save_word_id=7
save_phrase_saved=True
save_phrase_id=8
bad_type_status=422
blank_item_status=422
blank_raw_text_status=422
dashboard_word_visible=True
dashboard_phrase_visible=True
dashboard_top_context=coffee_shop
dashboard_recent_keywords_count=10
dashboard_recent_keywords_unique=True
dashboard_review_today=8
analysis_before=12
analysis_after=16
analysis_inserted=4
review_before=6
review_after=8
review_inserted=2
```

## 数据库影响

| 表名                 | 写入变化                   |
| ------------------ | ---------------------- |
| `contexts`         | 无新增，仍为 4 个 MVP context |
| `analysis_results` | 新增 4 条 demo 文本分析结果     |
| `review_items`     | 新增 2 条复习项              |

新增复习项：

| item_text      | item_type | source_context |
| -------------- | --------- | -------------- |
| `cappuccino`   | `word`    | `coffee_shop`  |
| `magic school` | `phrase`  | `kings_cross`  |

## 当前 API 合约

线 B / 线 C 可以继续按下面接口集成：

```
GET  /
GET  /contexts
GET  /context/{id}
POST /analyze_text
POST /save_item
GET  /dashboard
```

稳定字段：

```
id
cleaned_text
keywords
phrases
detected_context
summary
suggested_review_items
saved_words
saved_phrases
top_context
recent_keywords
review_today
```

## 服务状态记录

本次 A12 验收使用临时 Uvicorn Job，验收结束后已执行清理：

```powershell
Stop-Job -Job $job
Remove-Job -Job $job -Force
```

如果继续本地联调，请重新启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

本机访问：

```
http://127.0.0.1:8000
```

局域网访问时使用：

```
http://你的电脑局域网IP:8000
```

## 结论

- A12 已通过。
- 线 A 的核心 API 已满足最终完成标准。
- 后端能离线完成 NLP 分析、SQLite 保存和 Dashboard 汇总。
- Web 可以通过 API 完成输入、分析、保存和 dashboard 展示。
- CYD 可以只请求 API，不需要做 NLP，也不需要直接访问 SQLite。
- 本次额外加固了空白输入校验，避免空内容进入分析结果或复习列表。
