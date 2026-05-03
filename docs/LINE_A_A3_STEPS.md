# LINE_A Task A3 操作记录

## 记录字段

| 字段 | 内容 |
| --- | --- |
| Line | `LINE_A` |
| Task | `A3 - SQLite 初始化` |
| 状态 | 已通过 |
| 执行日期 | `2026-05-03` |
| 工作目录 | `C:\hackathon` |
| 数据库文件 | `C:\hackathon\scenelingo.db` |
| 后端地址 | `http://127.0.0.1:8000/` |
| 当前服务进程 | `19644` |
| 主要涉及文件 | `backend/database.py`、`backend/main.py`、`.gitignore` |
| 本次业务代码改动 | `backend/database.py` 显式关闭 SQLite 连接 |
| 文档记录 | `docs/LINE_A_A3_STEPS.md` |
| 下一步 | A4 NLP Text Cleaning |

## 任务目标

启动后端时自动创建 SQLite 数据库和三张 MVP 核心表，并且每次启动同步 `backend/seed_data.json`。

## 数据库字段记录

必须存在的业务表：

| 表名 | 职责 |
| --- | --- |
| `contexts` | 保存 4 个场景定义 |
| `analysis_results` | 保存每次文本分析结果 |
| `review_items` | 保存用户点击复习的 word / phrase |

必须实现的函数：

| 函数 | 职责 |
| --- | --- |
| `init_db()` | 建表并同步 seed data |
| `list_contexts()` | 返回 context 列表 |
| `get_context_by_id(context_id)` | 根据 id 返回单个 context |
| `insert_analysis(raw_text, result)` | 保存文本分析结果 |
| `save_review_item(item_text, item_type, source_context)` | 保存复习项 |
| `get_dashboard()` | 汇总 dashboard 数据 |

## 验收命令

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\database.py backend\main.py
```

重复初始化检查：

```powershell
.\.venv\Scripts\python.exe -c "from backend.database import init_db, list_contexts; init_db(); init_db(); print(len(list_contexts()))"
```

表结构检查：

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; con=sqlite3.connect('scenelingo.db'); rows=con.execute('SELECT name,type FROM sqlite_master ORDER BY name').fetchall(); print([row[0] for row in rows if row[1] == 'table']); con.close()"
```

API 检查：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/
Invoke-RestMethod -Uri http://127.0.0.1:8000/contexts
Invoke-RestMethod -Uri http://127.0.0.1:8000/dashboard
```

写入检查：

```powershell
$wordPayload = @{ item_text = "receipt"; item_type = "word"; source_context = "coffee_shop" } | ConvertTo-Json
$phrasePayload = @{ item_text = "for here"; item_type = "phrase"; source_context = "coffee_shop" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/save_item -Method Post -ContentType "application/json" -Body $wordPayload
Invoke-RestMethod -Uri http://127.0.0.1:8000/save_item -Method Post -ContentType "application/json" -Body $phrasePayload
```

## 验收结果

| 检查项 | 结果 |
| --- | --- |
| Python 编译检查 | 通过 |
| `scenelingo.db` | 存在 |
| 重复 `init_db()` | context 数量仍为 `4` |
| 业务表 | `contexts`、`analysis_results`、`review_items` 均存在 |
| seed 同步 | 通过临时数据库验证 |
| `/save_item` 写入 word | `receipt` 写入成功，`word_id=3` |
| `/save_item` 写入 phrase | `for here` 写入成功，`phrase_id=4` |
| `/dashboard` 读取 | 能读到 saved words / saved phrases |
| 服务重启 | 已重启，当前进程 `19644` |

表结构检查输出：

```text
['analysis_results', 'contexts', 'review_items', 'sqlite_sequence']
```

`sqlite_sequence` 是 SQLite 为自增主键自动维护的系统表，不属于业务表。

核心字段检查输出：

```text
contexts=4
analysis_results_columns=['id', 'raw_text', 'cleaned_text', 'detected_context', 'keywords_json', 'phrases_json', 'summary', 'created_at']
review_items_columns=['id', 'item_text', 'item_type', 'source_context', 'created_at']
```

seed data 同步检查输出：

```text
temp_db_created=True
first_count=4
second_count=4
seed_sync_summary=A3 sync check summary
```

## 代码和数据影响

`backend/database.py` 已具备 A3 要求的建表、seed data 同步、分析结果写入、复习项保存和 dashboard 汇总能力。

本次额外修复 SQLite 连接管理：

| 修改点 | 说明 |
| --- | --- |
| 新增 `@contextmanager` | 统一管理 SQLite 连接生命周期 |
| 成功时 `commit()` | 保证写入落库 |
| 异常时 `rollback()` | 避免半写入状态 |
| 最终 `close()` | 避免 Windows 下数据库文件占用 |
| 中文注释 | 已在关键逻辑处说明原因 |

## 当前 Dashboard 记录

| 字段 | 当前结果 |
| --- | --- |
| saved words | `receipt`、`latte` |
| saved phrases | `for here`、`to go` |
| top context | `coffee_shop` |
| recent keywords | `get`、`latte`、`milk` |
| review_today | `4` |

## 服务状态记录

| 字段 | 内容 |
| --- | --- |
| 当前进程 | `19644` |
| 本机访问 | `http://127.0.0.1:8000/` |
| 局域网监听 | `0.0.0.0:8000` |
| 停止命令 | `Stop-Process -Id 19644` |

## 临时目录记录

验证过程中有一个沙盒异常权限目录 `tmprfy6_l4u` 无法由当前进程删除。它是临时测试目录，不参与项目运行。

已在 `.gitignore` 中加入：

```text
/tmp*/
```

这样 Git 不再扫描根目录下的临时测试目录，也不会影响提交内容。

## 结论

- A3 已通过。
- 后端启动时可以自动创建并初始化 SQLite 数据库。
- 三张 MVP 业务表均已存在。
- 重复启动不会重复插入 context。
- 修改 seed data 后重新初始化可以同步更新 context。
- `/save_item` 可以写入 review item。
- `/dashboard` 可以读取 saved words 和 saved phrases。
