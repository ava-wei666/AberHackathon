# LINE_A Task A6 操作记录

## 记录字段

| 字段       | 内容                                                                              |
| -------- | ------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                        |
| Task     | `A6 - Context Classification`                                                   |
| 状态       | 已通过                                                                             |
| 执行日期     | `2026-05-03`                                                                    |
| 工作目录     | `C:\hackathon`                                                                  |
| 后端地址     | `http://127.0.0.1:8000/`                                                        |
| 当前服务进程   | `42864`                                                                         |
| 主要涉及文件   | `backend/nlp_engine.py`、`backend/database.py`、`backend/main.py`、`scenelingo.db` |
| 本次业务代码改动 | 无                                                                               |
| 文档记录     | `docs/LINE_A_A6_STEPS.md`                                                       |
| 下一步      | A7 Summary                                                                      |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` 中详细拆分为 A5 Keyword Extraction、A6 Phrase Extraction、A7 Context Classification。

当前执行记录按 `docs/TASK_PHASES.md` 的阶段顺序推进：A5 已同时完成 keywords / phrases，因此本文件记录 A6 Context Classification。

## 任务目标

把输入文本分类到 4 个 MVP context，并返回完整 context object，而不是只返回字符串。

## 分类规则记录

| 规则                  | 当前实现                                                                       |
| ------------------- | -------------------------------------------------------------------------- |
| optional_context 优先 | 如果请求传了 `optional_context` 且 id 存在，直接返回该 context                            |
| 自动分类                | 未传 `optional_context` 时，用 cleaned tokens 与 seed keywords / title / tag 做打分 |
| 分类范围                | `coffee_shop`、`doctor_pharmacy`、`kings_cross`、`baker_street`               |
| source_type 过滤      | 优先在同类型 context 中分类，例如 `real-world` 或 `story`                               |
| 默认 context          | 完全没有命中时，按 `source_type` 使用默认 context                                       |
| confidence          | 返回数字，命中越多分数越高，最高限制为 `0.95`                                                 |
| 返回结构                | 返回包含 `id`、`title`、`type`、`tag`、`summary`、`seed_phrases`、`confidence` 的对象   |
| 外部依赖                | 不依赖外网，不依赖 LLM                                                              |

## 验收文本

```
Coffee Shop:
Hi, can I get a latte with milk to go? How much is the large size?

Doctor / Pharmacy:
I have a headache and a cough. Do I need medicine from the pharmacy?

King's Cross:
Which platform should I use to catch the train to the magic school at King's Cross?

Baker Street:
The detective found a clue on Baker Street and tried to solve the case.
```

## 验收命令

直接函数检查：

```powershell
@'
from backend.database import init_db, list_contexts
from backend.nlp_engine import analyze_text

init_db()
contexts = list_contexts()
cases = [
    ("coffee_shop", "real-world", "Hi, can I get a latte with milk to go? How much is the large size?"),
    ("doctor_pharmacy", "real-world", "I have a headache and a cough. Do I need medicine from the pharmacy?"),
    ("kings_cross", "story", "Which platform should I use to catch the train to the magic school at King's Cross?"),
    ("baker_street", "story", "The detective found a clue on Baker Street and tried to solve the case."),
]
for expected, source_type, text in cases:
    result = analyze_text(text, source_type=source_type, contexts=contexts)
    detected = result["detected_context"]
    required = ["id", "title", "type", "tag", "confidence"]
    print(f"expected={expected}; detected={detected['id']}; confidence={detected['confidence']}; confidence_type={type(detected['confidence']).__name__}; has_required={all(key in detected for key in required)}")
'@ | .\.venv\Scripts\python.exe -
```

optional_context 和默认 context 检查：

```powershell
@'
from backend.database import init_db, list_contexts
from backend.nlp_engine import analyze_text

init_db()
contexts = list_contexts()
optional_result = analyze_text(
    "I am ordering a latte with milk.",
    source_type="real-world",
    optional_context="doctor_pharmacy",
    contexts=contexts,
)["detected_context"]
real_world_default = analyze_text(
    "zzzz qqqq nothing useful",
    source_type="real-world",
    contexts=contexts,
)["detected_context"]
story_default = analyze_text(
    "zzzz qqqq nothing useful",
    source_type="story",
    contexts=contexts,
)["detected_context"]
print(f"optional_priority={optional_result['id']}; confidence={optional_result['confidence']}")
print(f"real_world_default={real_world_default['id']}; type={real_world_default['type']}; confidence={real_world_default['confidence']}")
print(f"story_default={story_default['id']}; type={story_default['type']}; confidence={story_default['confidence']}")
'@ | .\.venv\Scripts\python.exe -
```

API 端到端检查：

```powershell
$cases = @(
  @{ expected = "coffee_shop"; source_type = "real-world"; raw_text = "Hi, can I get a latte with milk to go? How much is the large size?" },
  @{ expected = "doctor_pharmacy"; source_type = "real-world"; raw_text = "I have a headache and a cough. Do I need medicine from the pharmacy?" },
  @{ expected = "kings_cross"; source_type = "story"; raw_text = "Which platform should I use to catch the train to the magic school at King's Cross?" },
  @{ expected = "baker_street"; source_type = "story"; raw_text = "The detective found a clue on Baker Street and tried to solve the case." }
)
foreach ($case in $cases) {
  $payload = @{ raw_text = $case.raw_text; source_type = $case.source_type; optional_context = $null } | ConvertTo-Json
  $response = Invoke-RestMethod -Uri http://127.0.0.1:8000/analyze_text -Method Post -ContentType "application/json" -Body $payload
  $context = $response.detected_context
  $hasRequired = ($null -ne $context.id) -and ($null -ne $context.title) -and ($null -ne $context.type) -and ($null -ne $context.tag) -and ($null -ne $context.confidence)
  "expected=$($case.expected); detected=$($context.id); confidence=$($context.confidence); has_required=$hasRequired; analysis_id=$($response.id)"
}
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

## 验收结果

| 检查项                   | 结果                                         |
| --------------------- | ------------------------------------------ |
| Python 编译检查           | 通过                                         |
| Coffee Shop 分类        | `coffee_shop`，confidence `0.81`            |
| Doctor / Pharmacy 分类  | `doctor_pharmacy`，confidence `0.93`        |
| King's Cross 分类       | `kings_cross`，confidence `0.95`            |
| Baker Street 分类       | `baker_street`，confidence `0.95`           |
| confidence 类型         | `float`                                    |
| detected_context 必要字段 | `id`、`title`、`type`、`tag`、`confidence` 均存在 |
| optional_context 优先   | 通过，强制返回 `doctor_pharmacy`，confidence `1.0` |
| real-world 无命中默认      | `coffee_shop`                              |
| story 无命中默认           | `kings_cross`                              |
| API 端到端               | 4 段文本全部分类正确                                |

函数级分类输出：

```
expected=coffee_shop; detected=coffee_shop; confidence=0.81; confidence_type=float; has_required=True
expected=doctor_pharmacy; detected=doctor_pharmacy; confidence=0.93; confidence_type=float; has_required=True
expected=kings_cross; detected=kings_cross; confidence=0.95; confidence_type=float; has_required=True
expected=baker_street; detected=baker_street; confidence=0.95; confidence_type=float; has_required=True
```

optional_context 和默认 context 输出：

```
optional_priority=doctor_pharmacy; confidence=1.0
real_world_default=coffee_shop; type=real-world; confidence=0.35
story_default=kings_cross; type=story; confidence=0.35
```

API 端到端输出：

```
expected=coffee_shop; detected=coffee_shop; confidence=0.81; has_required=True; analysis_id=6
expected=doctor_pharmacy; detected=doctor_pharmacy; confidence=0.93; has_required=True; analysis_id=7
expected=kings_cross; detected=kings_cross; confidence=0.95; has_required=True; analysis_id=8
expected=baker_street; detected=baker_street; confidence=0.95; has_required=True; analysis_id=9
```

## 代码和数据影响

| 字段                  | 内容                                                           |
| ------------------- | ------------------------------------------------------------ |
| 业务代码                | 未修改，现有实现已满足 A6                                               |
| 中文注释                | `backend/nlp_engine.py` 的分类逻辑已有中文注释                          |
| 数据库                 | API 端到端验收通过 `/analyze_text` 写入 4 条 `analysis_results`        |
| analysis_results 总数 | `9`                                                          |
| 最新 analysis id      | `9`                                                          |
| 最新写入 contexts       | `coffee_shop`、`doctor_pharmacy`、`kings_cross`、`baker_street` |
| review_items        | 未新增，`review_today` 仍为 `4`                                    |

## 当前 Dashboard 记录

| 字段              | 当前结果                                                                                  |
| --------------- | ------------------------------------------------------------------------------------- |
| saved words     | `receipt`、`latte`                                                                     |
| saved phrases   | `for here`、`to go`                                                                    |
| top context     | `coffee_shop`                                                                         |
| recent keywords | `detective`、`found`、`clue`、`baker`、`street`、`which`、`platform`、`should`、`use`、`catch` |
| review_today    | `4`                                                                                   |

## 服务状态记录

| 字段   | 内容                       |
| ---- | ------------------------ |
| 当前进程 | `42864`                  |
| 本机访问 | `http://127.0.0.1:8000/` |
| 停止命令 | `Stop-Process -Id 42864` |

## 结论

- A6 已通过。
- 四个 MVP context 都可以在无外网、无 LLM 的情况下被正确分类。
- `optional_context` 优先级有效，适合 Web / CYD 已经选定场景时使用。
- `detected_context` 返回完整对象，包含前端展示和置信度所需字段。
