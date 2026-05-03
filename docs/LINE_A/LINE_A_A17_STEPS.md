# LINE_A Task A17 操作记录

## 记录字段

| 字段       | 内容                                                                                                 |
| -------- | -------------------------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                                           |
| Task     | `A17 - Demo 测试文本自测`                                                                                |
| 状态       | 已通过                                                                                                |
| 执行日期     | `2026-05-03`                                                                                       |
| 工作目录     | `C:\hackathon`                                                                                     |
| 验收方式     | 离线脚本直接调 `analyze_text()`，不依赖 HTTP / Uvicorn / 网络                                                   |
| 主要涉及文件   | `backend/demo_check.py`（新增）、`backend/nlp_engine.py`、`backend/database.py`、`backend/seed_data.json` |
| 本次业务代码改动 | 无业务逻辑改动；新增 `backend/demo_check.py` 4 段 demo 文本验收脚本                                                 |
| 中文注释     | `backend/demo_check.py` 全文中文注释                                                                     |
| 文档记录     | `docs/LINE_A_A17_STEPS.md`                                                                         |
| 下一步      | 线 A 主任务收口；按需进入 demo 彩排                                                                             |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` A17 要求线 A 用 4 段固定 demo 文本自测后端：4 段都要分类正确、`keywords` 和 `phrases` 数量足够展示、`summary` 不能太长。本次把这 4 段文本封装到 `backend/demo_check.py`，跑完一次得到对应 4 行 `key=value` 输出，可直接贴回文档。脚本与 `backend/selftest.py` 的 `check_demo_texts` 互补：`selftest.py` 只关心"通不通过"，`demo_check.py` 还把分析输出全文打出来。

## 任务目标

- 4 段 demo 文本必须分别识别到 `coffee_shop`、`doctor_pharmacy`、`kings_cross`、`baker_street`。
- `keywords` 数量 ≥ 3，`phrases` 数量 ≥ 1，确保线 B / 线 C 有足够素材展示。
- `summary` 字符数 ≤ 300，CYD 小屏幕能装下，且非空。
- 自测脚本无副作用，不污染 `analysis_results` / `review_items`。
- 失败时退出码非 0，可串入 PowerShell / CI 流水线。

## 4 段 Demo 文本

| 编号  | 标签                | 预期 context        | source_type  | 文本                                                                                    |
| --- | ----------------- | ----------------- | ------------ | ------------------------------------------------------------------------------------- |
| 1   | Coffee Shop       | `coffee_shop`     | `real-world` | `Hi, can I get a latte with milk to go? How much is the large size?`                  |
| 2   | Doctor / Pharmacy | `doctor_pharmacy` | `real-world` | `I have a headache and a cough. Do I need medicine from the pharmacy?`                |
| 3   | King's Cross      | `kings_cross`     | `story`      | `Which platform should I use to catch the train to the magic school at King's Cross?` |
| 4   | Baker Street      | `baker_street`    | `story`      | `The detective found a clue on Baker Street and tried to solve the case.`             |

## 代码改动

新增文件：`backend/demo_check.py`

脚本特点：

- 直接调 `backend.nlp_engine.analyze_text()`，不走 HTTP，不写库（`/analyze_text` 路由才会触发 `insert_analysis`）。
- 每段 demo 单独评分：分类正确、keywords/phrases 数量够、summary 长度合理且非空。
- 失败原因列在 `demoN_problems`，方便一次定位多个问题。
- 输出统一为 `key=value`，可整段粘贴回 docs。

阈值常量：

- `SUMMARY_MAX_CHARS = 300`：CYD 经验上限，超过就回头裁 `nlp_engine.py` 模板。
- `MIN_KEYWORDS = 3`：低于 3 说明 seed_data 调得太严或 stopwords 过多。
- `MIN_PHRASES = 1`：phrase 是给学习者看的最小展示单位。

## 代码片段说明

单段 demo 的核心校验：

```python
def check_one_demo(
    label: str,
    expected_id: str,
    source_type: str,
    raw_text: str,
    contexts: list[dict[str, Any]],
) -> tuple[bool, dict[str, Any]]:
    """跑单段 demo 文本，返回 (是否通过, 详细输出 dict)。"""
    from backend.nlp_engine import analyze_text

    # 调用 NLP 主入口，不传 optional_context，验证自动分类逻辑。
    result = analyze_text(
        raw_text=raw_text,
        source_type=source_type,
        optional_context=None,
        contexts=contexts,
    )

    detected = result.get("detected_context", {})
    detected_id = detected.get("id", "unknown")
    keywords = result.get("keywords", []) or []
    phrases = result.get("phrases", []) or []
    summary = result.get("summary", "") or ""

    # 拆开校验，每个失败原因都列出来，方便一次定位多个问题。
    problems: list[str] = []
    if detected_id != expected_id:
        problems.append(f"context_mismatch: expected {expected_id}, got {detected_id}")
    if len(keywords) < MIN_KEYWORDS:
        problems.append(f"too_few_keywords: {len(keywords)} < {MIN_KEYWORDS}")
    if len(phrases) < MIN_PHRASES:
        problems.append(f"too_few_phrases: {len(phrases)} < {MIN_PHRASES}")
    if len(summary) > SUMMARY_MAX_CHARS:
        problems.append(f"summary_too_long: {len(summary)} > {SUMMARY_MAX_CHARS}")
    if not summary.strip():
        problems.append("summary_empty")
    ...
```

短列表格式化（防止 docs 表格被超长 keywords 撑变形）：

```python
def format_list(items: list[Any], max_items: int = 5) -> str:
    """把 list 拼成短字符串方便贴回文档；超过 max_items 时省略号。"""
    # 截断后再 join，避免 docs 里出现一长串 keywords 把表格挤变形。
    short = items[:max_items]
    text = ", ".join(str(item) for item in short)
    if len(items) > max_items:
        text += f", ... ({len(items)} total)"
    return text
```

## 验收命令

一键 demo 自测：

```powershell
.\.venv\Scripts\python.exe -m backend.demo_check
```

PowerShell 链式调用（demo 自测失败就别启动 Uvicorn）：

```powershell
.\.venv\Scripts\python.exe -m backend.demo_check; if ($LASTEXITCODE -eq 0) { .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 }
```

也可以走 HTTP 验证（前提是 Uvicorn 已经起来），与 `web_smoke.py` / `cyd_smoke.py` 行为一致：

```powershell
.\.venv\Scripts\python.exe -m backend.web_smoke
```

## 验收结果

汇总：

```
contexts_loaded=4
demo_passed=4
demo_total=4
demo_all_passed=True
exit_code=0
```

逐段细节：

| #   | 标签                | detected_id       | confidence | cleaned_text                                                      | keywords | phrases | summary_len |
| --- | ----------------- | ----------------- | ---------- | ----------------------------------------------------------------- | -------- | ------- | ----------- |
| 1   | Coffee Shop       | `coffee_shop`     | `0.81`     | `hi get latte milk go how much large size`                        | 5        | 3       | 93          |
| 2   | Doctor / Pharmacy | `doctor_pharmacy` | `0.93`     | `headache cough do need medicine pharmacy`                        | 5        | 3       | 103         |
| 3   | King's Cross      | `kings_cross`     | `0.95`     | `which platform should use catch train magic school king's cross` | 5        | 3       | 121         |
| 4   | Baker Street      | `baker_street`    | `0.95`     | `detective found clue baker street tried solve case`              | 5        | 3       | 123         |

Keywords / Phrases 预览：

| #   | keywords_preview                            | phrases_preview                                      |
| --- | ------------------------------------------- | ---------------------------------------------------- |
| 1   | `get, latte, milk, how, much`               | `Can I Get, How Much Is, to go`                      |
| 2   | `headache, cough, need, medicine, pharmacy` | `I Have a, need medicine pharmacy, headache cough`   |
| 3   | `which, platform, should, use, catch`       | `Which Platform, Catch the Train, Magic School`      |
| 4   | `detective, found, clue, baker, street`     | `Solve the Case, Baker Street, detective found clue` |

Summary 全文：

| #   | summary                                                                                                                       |
| --- | ----------------------------------------------------------------------------------------------------------------------------- |
| 1   | `This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.`                               |
| 2   | `This looks like Doctor / Pharmacy: focus on headache, cough, need and practice phrases like 'I Have a'.`                     |
| 3   | `This looks like Harry Potter - King's Cross: focus on which, platform, should and practice phrases like 'Which Platform'.`   |
| 4   | `This looks like Sherlock Holmes - Baker Street: focus on detective, found, clue and practice phrases like 'Solve the Case'.` |

四段 summary 字符数最大 123，远低于 300 上限；CYD 屏幕单行折两到三行就能装下。

## 数据库影响

| 表名                 | 写入变化                             |
| ------------------ | -------------------------------- |
| `contexts`         | 无新增；脚本只读取 `list_contexts()`      |
| `analysis_results` | **无新增**；`analyze_text()` 函数本身不写库 |
| `review_items`     | 无新增                              |

DB 计数验证：

```
contexts=4
analysis_results=16   # 与 A16 结束时一致
review_items=24       # 与 A16 结束时一致
```

A17 自测脚本设计为零副作用：反复跑不会让 dashboard 数据漂移，也不会污染 demo 现场。

## 给线 B / 线 C 的提示

Demo 阶段建议 4 段文本固定使用上面这套；任何 keywords / phrases / summary 文案出现意外，先比对下表：

| 文本                | 预期文案锚点                                                                                 |
| ----------------- | -------------------------------------------------------------------------------------- |
| Coffee Shop       | summary 含 `Coffee Shop`，phrases 含 `Can I Get` / `to go`                                |
| Doctor / Pharmacy | summary 含 `Doctor / Pharmacy`，phrases 含 `I Have a`                                     |
| King's Cross      | summary 含 `Harry Potter - King's Cross`，phrases 含 `Which Platform` 或 `Magic School`    |
| Baker Street      | summary 含 `Sherlock Holmes - Baker Street`，phrases 含 `Solve the Case` 或 `Baker Street` |

如果效果不好，按 `LINE_A_BACKEND_TASKS.md` A17 的优先级处理：

1. 调 `backend/seed_data.json` 的 `seed_keywords`。
2. 调 `backend/seed_data.json` 的 `seed_phrases`。
3. 改 `backend/nlp_engine.py` 的规则。

不要为了一个小问题引入新依赖。

## 失败时的排查建议

| 失败项                | 优先排查                                                                 |
| ------------------ | -------------------------------------------------------------------- |
| `context_mismatch` | `seed_data.json` 对应 context 的 `seed_keywords` / `seed_phrases` 是否被改弱 |
| `too_few_keywords` | `nlp_engine.py` 的 stopwords / filler 是否扩得太狠；或文本过短                    |
| `too_few_phrases`  | `seed_phrases` 是否为空，或 phrase 拼接规则被改                                  |
| `summary_too_long` | `nlp_engine.py` summary 模板是否新增了多余的句子                                 |
| `summary_empty`    | summary 模板是否被改坏；或 detected_context 缺 title                           |

## 服务状态记录

A17 全程不需要 Uvicorn，无需起进程也无需清理。如果要顺势继续 Web / CYD 联调：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 结论

- A17 已通过。
- 4 段 demo 文本全部分类到正确 context，置信度 0.81 ~ 0.95。
- 每段 keywords 都返回 5 个，phrases 都返回 3 个，足够线 B / 线 C 展示。
- summary 长度 93 ~ 123 字符，CYD 小屏可显示。
- 自测脚本零副作用，反复运行不影响 dashboard 数据。
- 至此 `LINE_A_BACKEND_TASKS.md` A0 ~ A17 全部完成，线 A 后端进入稳定演示状态。
