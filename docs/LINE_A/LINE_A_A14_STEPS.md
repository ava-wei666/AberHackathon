# LINE_A Task A14 操作记录

## 记录字段

| 字段       | 内容                                                                                                                                       |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                                                                                 |
| Task     | `A14 - 后端自测清单`                                                                                                                           |
| 状态       | 已通过                                                                                                                                      |
| 执行日期     | `2026-05-03`                                                                                                                             |
| 工作目录     | `C:\hackathon`                                                                                                                           |
| 验收方式     | 直接调用后端模块的离线脚本，不依赖 HTTP / Uvicorn / 外网                                                                                                    |
| 主要涉及文件   | `backend/selftest.py`（新增）、`backend/__init__.py`、`backend/main.py`、`backend/nlp_engine.py`、`backend/database.py`、`backend/seed_data.json` |
| 本次业务代码改动 | 无业务逻辑改动；新增 `backend/selftest.py` 自测脚本                                                                                                    |
| 中文注释     | `backend/selftest.py` 全文中文注释                                                                                                             |
| 文档记录     | `docs/LINE_A_A14_STEPS.md`                                                                                                               |
| 下一步      | A15 给线 B 的联调信息                                                                                                                           |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` 中 A14 的目标是：每次改完线 A 都能跑同一套自测清单，确认基础功能没坏。本次把清单里的 3 条命令，加上 demo 文本分类、字段形状校验等扩展项，统一封装到 `backend/selftest.py`。命令式的最小清单仍可单独使用，便于现场临时排查。

## 任务目标

- 一条命令完成线 A 后端的离线快速验收。
- 既覆盖 `LINE_A_BACKEND_TASKS.md` A14 列出的 3 条核心命令，也覆盖 `LINE_A_BACKEND_TASKS.md` A17 的 4 段 demo 文本分类。
- 不依赖 HTTP / Uvicorn / 网络，避免端口占用、防火墙抖动干扰自测。
- 任何一项失败时退出码非 0，方便嵌入 PowerShell 链式调用或 CI。

## 代码改动

新增文件：`backend/selftest.py`

脚本结构：

- 顶部注释：执行方式、设计目标、依赖范围。
- 常量：`SOURCE_FILES`、`DEMO_TEXTS`、`REQUIRED_DASHBOARD_FIELDS`、`REQUIRED_ANALYSIS_FIELDS`。
- 工具函数 `run_check(name, fn)`：统一以 `key=value` 输出每个检查项的结果，失败时不会中断后续检查。
- 7 个检查项，对应不同维度：
  - `check_py_compile`：`backend/*.py` 全部 `py_compile.compile(..., doraise=True)`。
  - `check_seed_data_loadable`：直接读 `seed_data.json`，确认字段齐全、`type` 合法。
  - `check_contexts_count`：`init_db()` 后 `list_contexts()` 必须返回 4 个 MVP context，且 id 集合精确匹配。
  - `check_coffee_shop_detection`：A14 清单里的核心快速检查，验证 Coffee Shop 文本识别为 `coffee_shop`。
  - `check_demo_texts`：把 A17 的 4 段 demo 文本一次性跑一遍，确保分类规则没退化。
  - `check_analyze_fields`：`analyze_text` 返回值必须包含 `cleaned_text`、`keywords`、`phrases`、`detected_context`、`summary`、`suggested_review_items`，且 `keywords`、`phrases` 是 list。
  - `check_dashboard_shape`：`get_dashboard()` 返回字段齐全；`saved_words` / `saved_phrases` 的 `item_text` 已去重；`recent_keywords` 不重复；`review_today` 是 `int`。
- `main()`：依次执行检查项，输出 `selftest_passed`、`selftest_total`、`selftest_all_passed`，并返回 0 或 1。

整个文件按要求用中文注释覆盖每一段关键逻辑。

## 代码片段说明

统一的检查执行器：

```python
def run_check(name: str, fn: Callable[[], Any]) -> tuple[bool, Any]:
    """执行单个检查项并以统一格式输出。

    返回 (通过与否, 函数返回值)。函数返回值会作为 details 行输出，方便对比。
    """
    # 任何异常都视为失败；保留异常信息方便复现。
    try:
        result = fn()
        print(f"check_{name}=pass")
        if result is not None:
            print(f"detail_{name}={result}")
        return True, result
    except AssertionError as exc:
        print(f"check_{name}=fail")
        print(f"detail_{name}=AssertionError: {exc}")
        return False, exc
    except Exception as exc:  # noqa: BLE001
        print(f"check_{name}=fail")
        print(f"detail_{name}={type(exc).__name__}: {exc}")
        return False, exc
```

A14 清单里的核心快速检查：

```python
def check_coffee_shop_detection() -> str:
    # A14 清单里的核心快速检查：Coffee Shop 文本应被识别为 coffee_shop。
    from backend.database import init_db, list_contexts
    from backend.nlp_engine import analyze_text

    init_db()
    result = analyze_text(
        "Hi, can I get a latte with milk to go?",
        "real-world",
        None,
        list_contexts(),
    )
    detected_id = result["detected_context"]["id"]
    assert detected_id == "coffee_shop", f"expected coffee_shop, got {detected_id}"
    return f"detected_context_id={detected_id}"
```

Dashboard 形状校验：

```python
def check_dashboard_shape() -> str:
    # 校验 dashboard 返回结构，CYD 直接消费这些字段，不能少。
    from backend.database import get_dashboard, init_db

    init_db()
    dashboard = get_dashboard()
    missing = [field for field in REQUIRED_DASHBOARD_FIELDS if field not in dashboard]
    assert not missing, f"missing dashboard fields: {missing}"

    saved_words_unique = len({item["item_text"] for item in dashboard["saved_words"]}) == len(
        dashboard["saved_words"],
    )
    saved_phrases_unique = len(
        {item["item_text"] for item in dashboard["saved_phrases"]},
    ) == len(dashboard["saved_phrases"])
    recent_unique = len(set(dashboard["recent_keywords"])) == len(dashboard["recent_keywords"])
    assert saved_words_unique, "saved_words item_text not unique"
    assert saved_phrases_unique, "saved_phrases item_text not unique"
    assert recent_unique, "recent_keywords not unique"
    assert isinstance(dashboard["review_today"], int), "review_today must be int"
    return (
        f"saved_words={len(dashboard['saved_words'])},"
        f"saved_phrases={len(dashboard['saved_phrases'])},"
        f"recent_keywords={len(dashboard['recent_keywords'])},"
        f"review_today={dashboard['review_today']}"
    )
```

## 验收命令

A14 清单里的 3 条最小命令（保持原样，必要时可单独跑）：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
.\.venv\Scripts\python.exe -c "from backend.database import init_db, list_contexts; init_db(); print(len(list_contexts()))"
.\.venv\Scripts\python.exe -c "from backend.database import init_db, list_contexts; from backend.nlp_engine import analyze_text; init_db(); print(analyze_text('Hi, can I get a latte with milk to go?', 'real-world', None, list_contexts())['detected_context']['id'])"
```

预期输出：

```
4
coffee_shop
```

一键自测脚本（推荐每次改动后执行）：

```powershell
.\.venv\Scripts\python.exe -m backend.selftest
```

PowerShell 链式调用示例（自测失败时不会继续启动 Uvicorn）：

```powershell
.\.venv\Scripts\python.exe -m backend.selftest; if ($LASTEXITCODE -eq 0) { .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 }
```

## 验收结果

A14 清单 3 条最小命令：

| 命令                                | 输出            |
| --------------------------------- | ------------- |
| `py_compile`                      | 静默成功，无报错      |
| `len(list_contexts())`            | `4`           |
| Coffee Shop `detected_context.id` | `coffee_shop` |

`backend.selftest` 一键脚本：

| 检查项                     | 结果   | 详情                                                                 |
| ----------------------- | ---- | ------------------------------------------------------------------ |
| `py_compile`            | pass | `compiled=5`                                                       |
| `seed_data_loadable`    | pass | `seed_contexts=4`                                                  |
| `contexts_count`        | pass | `contexts_count=4`                                                 |
| `coffee_shop_detection` | pass | `detected_context_id=coffee_shop`                                  |
| `demo_texts`            | pass | `demo_texts_passed=4`                                              |
| `analyze_fields`        | pass | `analyze_fields_ok=True`                                           |
| `dashboard_shape`       | pass | `saved_words=5,saved_phrases=3,recent_keywords=10,review_today=14` |

汇总：

```
selftest_passed=7
selftest_total=7
selftest_all_passed=True
exit_code=0
```

完整 stdout：

```
check_py_compile=pass
detail_py_compile=compiled=5
check_seed_data_loadable=pass
detail_seed_data_loadable=seed_contexts=4
check_contexts_count=pass
detail_contexts_count=contexts_count=4
check_coffee_shop_detection=pass
detail_coffee_shop_detection=detected_context_id=coffee_shop
check_demo_texts=pass
detail_demo_texts=demo_texts_passed=4
check_analyze_fields=pass
detail_analyze_fields=analyze_fields_ok=True
check_dashboard_shape=pass
detail_dashboard_shape=saved_words=5,saved_phrases=3,recent_keywords=10,review_today=14
selftest_passed=7
selftest_total=7
selftest_all_passed=True
exit_code=0
```

## 数据库影响

| 表名                 | 写入变化                                                           |
| ------------------ | -------------------------------------------------------------- |
| `contexts`         | 无新增；`init_db` 同步 seed data，4 条不变                               |
| `analysis_results` | 无新增；A14 自测的 `analyze_text` 直接调用 NLP，未走 `/analyze_text` 路由，不会写入 |
| `review_items`     | 无新增；自测脚本只读取 dashboard，不调用 `save_review_item`                   |

A14 自测有意做成"无副作用"：调用 `analyze_text` 函数本身不会写库，只有走 `POST /analyze_text` 路由才会触发 `insert_analysis`。这样反复跑自测不会在数据库里留垃圾。

## 失败时的排查建议

| 失败检查项                   | 优先排查                                                                |
| ----------------------- | ------------------------------------------------------------------- |
| `py_compile`            | 查看具体报错文件路径；重点看最近改过的文件                                               |
| `seed_data_loadable`    | `backend/seed_data.json` 是否被改成不合法 JSON 或缺字段                         |
| `contexts_count`        | `seed_data.json` 是否被加 / 删了 context；或 `scenelingo.db` 损坏，可临时删除后重启    |
| `coffee_shop_detection` | `nlp_engine.py` 的 stopwords / filler / classification 是否被误改         |
| `demo_texts`            | 4 段 demo 是否都失败；如果只挂 1 个，定位单个 context 的 seed_keywords / seed_phrases |
| `analyze_fields`        | `analyze_text` 返回结构是否被改字段名；线 B / 线 C 也要同步告知                         |
| `dashboard_shape`       | `get_dashboard()` 是否被改字段；`saved_words` 去重是否被回退                      |

## 给线 B / 线 C 的提示

线 A 每次回归后会在群里贴这段：

```
selftest_all_passed=True
selftest_passed=7
selftest_total=7
```

如果出现 `selftest_all_passed=False`，线 B / 线 C 暂停联调，等线 A 修复并贴出新的全通过 stdout。

## 结论

- A14 已通过。
- `backend/selftest.py` 一条命令完成线 A 后端离线快速验收。
- 同时保留 `LINE_A_BACKEND_TASKS.md` A14 列出的 3 条最小命令，便于现场临时排查。
- 自测无副作用，不会污染 `analysis_results` 或 `review_items`。
- 失败时退出码非 0，可直接嵌入 PowerShell 链式启动流程。
