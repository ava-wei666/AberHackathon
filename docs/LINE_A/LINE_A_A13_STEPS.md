# LINE_A Task A13 操作记录

## 记录字段

| 字段       | 内容                                                                                     |
| -------- | -------------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                               |
| Task     | `A13 - GET /dashboard`                                                                 |
| 状态       | 已通过                                                                                    |
| 执行日期     | `2026-05-03`                                                                           |
| 工作目录     | `C:\hackathon`                                                                         |
| 后端验收地址   | `http://127.0.0.1:8000/`                                                               |
| 验收服务方式   | PowerShell `Start-Job` 临时启动 Uvicorn，验收结束后清理                                            |
| 主要涉及文件   | `backend/main.py`、`backend/database.py`、`scenelingo.db`                                |
| 本次业务代码改动 | 有，`get_dashboard()` 增加按 item_text 去重、`review_today` 改为按本地日期统计、`recent_keywords` 增加空值过滤 |
| 中文注释     | 已在新增和修改的逻辑处补充中文注释                                                                      |
| 文档记录     | `docs/LINE_A_A13_STEPS.md`                                                             |
| 下一步      | A14 后端自测清单                                                                             |

## 编号说明

`docs/TASK_PHASES.md` 在 A12 收口为线 A 完成标准。`docs/LINE_A_BACKEND_TASKS.md` 中的 A13 是 `GET /dashboard` 的细节验收。本次按 `LINE_A_BACKEND_TASKS.md` 的编号继续推进，重点是把 dashboard 接口针对 CYD 小屏幕和真实演示场景再做一轮加固。

## 任务目标

让 `GET /dashboard` 给 CYD dashboard 提供稳定、能直接显示的字段：

- `saved_words` 和 `saved_phrases` 分开返回。
- `top_context` 根据 `analysis_results` 统计。
- `recent_keywords` 不重复。
- `review_today` 反映"今天保存了多少复习项"。
- CYD 不再需要在端上做去重、日期过滤等加工。

## 代码改动

文件：`backend/database.py`

`get_dashboard()` 内部改动如下：

- 取 word / phrase 的 SQL 把 `LIMIT 20` 调到 `LIMIT 60`：先多取，再在 Python 端按 `item_text` 去重，确保去重后仍能凑够 CYD 展示数量。
- 新增私有函数 `_deduplicate_review_rows(rows, limit)`：按 `item_text` 去重，保留最近一次保存（rows 已按 `created_at DESC` 排序），最多返回 `limit` 个。
- `recent_keywords` 在原有基础上多做一次空字符串过滤，保证 CYD 直接显示不会出现空白条目。
- `review_today` 改为单独 SQL 查询，使用 `DATE(created_at, 'localtime') = DATE('now', 'localtime')` 严格按本地日期统计今天保存的复习项数量。

API 字段名保持不变，线 B、线 C 已经接好的代码不需要改。

## 代码片段说明

去重 helper：

```python
def _deduplicate_review_rows(rows: list[sqlite3.Row], limit: int) -> list[dict[str, Any]]:
    # 按 item_text 去重，保留最近一次保存（rows 已按 created_at DESC 排序），最多返回 limit 个。
    seen_item_texts: set[str] = set()
    unique_items: list[dict[str, Any]] = []
    for row in rows:
        item_text = row["item_text"]
        if item_text in seen_item_texts:
            continue
        seen_item_texts.add(item_text)
        unique_items.append(_review_from_row(row))
        if len(unique_items) >= limit:
            break
    return unique_items
```

`review_today` 用 SQL 直接过滤，避免 Python 端再处理时区：

```python
review_today_row = connection.execute(
    """
    SELECT COUNT(*) AS count
    FROM review_items
    WHERE DATE(created_at, 'localtime') = DATE('now', 'localtime')
    """
).fetchone()
```

`recent_keywords` 多了一层空字符串保护：

```python
for row in recent_rows:
    for keyword in json.loads(row["keywords_json"]):
        cleaned_keyword = keyword.strip() if isinstance(keyword, str) else ""
        if cleaned_keyword and cleaned_keyword not in recent_keywords:
            recent_keywords.append(cleaned_keyword)
```

## 验收命令

语法检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

数据库层 dashboard 形状检查：

```powershell
.\.venv\Scripts\python.exe -c "from backend.database import init_db, get_dashboard; import json; init_db(); d = get_dashboard(); print(json.dumps(d, indent=2, ensure_ascii=False, default=str))"
```

`review_today` 日期过滤验证（临时插入一条昨天的复习项，验证 `review_today` 不会把它算进去，再清理）：

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; from backend.database import DB_PATH, get_dashboard; conn = sqlite3.connect(DB_PATH); conn.execute(\"INSERT INTO review_items (item_text, item_type, source_context, created_at) VALUES ('yesterday_test', 'word', 'coffee_shop', '2026-05-02 09:00:00')\"); conn.commit(); inserted_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]; conn.close(); print('after_insert_yesterday_review_today=', get_dashboard()['review_today']); conn = sqlite3.connect(DB_PATH); conn.execute('DELETE FROM review_items WHERE id = ?', (inserted_id,)); conn.commit(); conn.close()"
```

真实 HTTP 验收使用临时 Uvicorn Job：

```powershell
$job = Start-Job -ScriptBlock {
  Set-Location "C:\hackathon"
  .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
}

# 等待健康检查通过后，依次请求：
# GET /            -> 健康检查
# GET /dashboard   -> 记录初始 dashboard 状态
# POST /save_item  -> 保存一个 word（espresso）
# POST /save_item  -> 保存一个 phrase（to go）
# GET /dashboard   -> 验证刚保存的 item 是否出现，review_today 是否 +2

Stop-Job -Job $job
Remove-Job -Job $job -Force
```

## 验收结果

| 检查项                                  | 结果                                                                                |
| ------------------------------------ | --------------------------------------------------------------------------------- |
| Python 编译检查                          | 通过                                                                                |
| `GET /` 健康检查                         | HTTP `200`，返回 `SceneLingo API`                                                    |
| `GET /dashboard` 返回字段                | `saved_words`、`saved_phrases`、`top_context`、`recent_keywords`、`review_today` 全部存在 |
| `saved_words` 与 `saved_phrases` 分开返回 | 通过                                                                                |
| `saved_words` `item_text` 去重         | 通过，4 个条目无重复                                                                       |
| `saved_phrases` `item_text` 去重       | 通过，2 个条目无重复                                                                       |
| `top_context` 来自分析历史统计               | `baker_street`，`analysis_results` 中 detected_context 出现次数最多                       |
| `recent_keywords` 不重复                | 通过，10 个条目去重后仍为 10                                                                 |
| `recent_keywords` 无空字符串              | 通过                                                                                |
| `review_today` 按本地日期统计               | 通过，今日新建的 12 条复习项全部计入                                                              |
| 保存 word（`espresso`）                  | `id=13`，`saved=True`                                                              |
| 保存 phrase（`to go`）                   | `id=14`，`saved=True`                                                              |
| 保存后 `saved_words` 数量                 | 由 `4` 增加到 `5`，`espresso` 出现在列表                                                    |
| 保存后 `saved_phrases` 数量               | 由 `2` 增加到 `3`，`to go` 出现在列表                                                       |
| 保存后 `review_today`                   | 由 `12` 增加到 `14`，正好等于 +2                                                           |
| 昨天日期复习项                              | 临时插入后 `review_today` 仍为 `14`，未被错误计入；测试数据已清理                                       |

核心 PowerShell 输出：

```
health_status=ok
health_service=SceneLingo API
dash1_saved_words_count=4
dash1_saved_phrases_count=2
dash1_top_context=baker_street
dash1_recent_keywords_count=10
dash1_review_today=12
dash1_saved_words_unique=True
dash1_saved_phrases_unique=True
dash1_recent_keywords_unique=True
save_word_id=13
save_word_saved=True
save_phrase_id=14
save_phrase_saved=True
dash2_saved_words_count=5
dash2_saved_phrases_count=3
dash2_review_today=14
dash2_espresso_visible=True
dash2_togo_visible=True
uvicorn_cleaned_up=True
```

`review_today` 日期过滤检查：

```
after_insert_yesterday_review_today= 14
saved_words_contains_yesterday_test= True
test_row_cleaned= True
after_cleanup_review_today= 14
```

说明：`saved_words` 列表本身不按日期过滤，所以临时插入的 `yesterday_test` 会出现在列表里；但 `review_today` 计数器使用 SQL 端的 `DATE(... , 'localtime')` 过滤，结果保持 `14` 不变。

## Dashboard 输出示例

`GET /dashboard` 返回当前内容（验收结束后状态）：

```json
{
  "saved_words": [
    {"item_text": "espresso", "source_context": "coffee_shop", "created_at": "2026-05-03 ..."},
    {"item_text": "detective", "source_context": "baker_street", "created_at": "2026-05-03 10:14:48"},
    {"item_text": "pharmacy", "source_context": "doctor_pharmacy", "created_at": "2026-05-03 10:14:48"},
    {"item_text": "headache", "source_context": "doctor_pharmacy", "created_at": "2026-05-03 10:14:48"},
    {"item_text": "latte", "source_context": "coffee_shop", "created_at": "2026-05-03 10:14:48"}
  ],
  "saved_phrases": [
    {"item_text": "to go", "source_context": "coffee_shop", "created_at": "2026-05-03 ..."},
    {"item_text": "King's Cross", "source_context": "kings_cross", "created_at": "2026-05-03 10:14:48"},
    {"item_text": "Can I Get", "source_context": "coffee_shop", "created_at": "2026-05-03 10:14:48"}
  ],
  "top_context": "baker_street",
  "recent_keywords": [
    "detective", "solved", "case", "left", "file",
    "found", "clue", "baker", "street", "headache"
  ],
  "review_today": 14
}
```

CYD 端使用建议：

- `saved_words[].item_text` 直接显示。
- `saved_phrases[].item_text` 直接显示。
- `recent_keywords` 直接渲染成 chip 或列表。
- `top_context` 当作字符串显示，需要 title 时调 `GET /context/{id}`。
- `review_today` 直接渲染成数字。

## 数据库影响

| 表名                 | 写入变化                                   |
| ------------------ | -------------------------------------- |
| `contexts`         | 无新增，仍为 4 个 MVP context                 |
| `analysis_results` | 无新增，仍为 8 条                             |
| `review_items`     | 新增 2 条（`espresso` word、`to go` phrase） |

新增复习项：

| item_text  | item_type | source_context |
| ---------- | --------- | -------------- |
| `espresso` | `word`    | `coffee_shop`  |
| `to go`    | `phrase`  | `coffee_shop`  |

最终 DB 计数：

```
contexts=4
analysis_results=8
review_items=14
today_reviews=14
```

## 当前 API 合约

线 B / 线 C 继续按下面接口集成，A13 不改字段名：

```
GET  /
GET  /contexts
GET  /context/{id}
POST /analyze_text
POST /save_item
GET  /dashboard
```

`GET /dashboard` 稳定字段：

```
saved_words           (list[{item_text, source_context, created_at}], item_text 已去重)
saved_phrases         (list[{item_text, source_context, created_at}], item_text 已去重)
top_context           (string | null)
recent_keywords       (list[string], 不重复，最多 10 个)
review_today          (int，今天本地日期保存的复习项数量)
```

## 服务状态记录

本次 A13 验收使用临时 Uvicorn Job，验收结束后已执行清理：

```powershell
Stop-Job -Job $job
Remove-Job -Job $job -Force
```

如需恢复局域网联调，参考 A11 步骤启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

本机访问：

```
http://127.0.0.1:8000/dashboard
```

局域网访问时使用：

```
http://你的电脑局域网IP:8000/dashboard
```

## 结论

- A13 已通过。
- `GET /dashboard` 满足 `LINE_A_BACKEND_TASKS.md` 的全部验收点。
- `saved_words` 和 `saved_phrases` 已按 `item_text` 去重，CYD 屏幕不会出现重复条目。
- `recent_keywords` 已去重并过滤空字符串，CYD 可不加工直接渲染。
- `review_today` 改为按本地日期严格统计，符合"今天复习了多少"的语义。
- API 字段名未变，线 B / 线 C 已经接好的逻辑无需调整。
