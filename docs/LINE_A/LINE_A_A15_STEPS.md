# LINE_A Task A15 操作记录

## 记录字段

| 字段       | 内容                                                                                         |
| -------- | ------------------------------------------------------------------------------------------ |
| Line     | `LINE_A`                                                                                   |
| Task     | `A15 - 给线 B 的联调信息`                                                                         |
| 状态       | 已通过                                                                                        |
| 执行日期     | `2026-05-03`                                                                               |
| 工作目录     | `C:\hackathon`                                                                             |
| 本地 API   | `http://localhost:8000`                                                                    |
| 局域网 API  | `http://10.88.0.183:8000`                                                                  |
| 验收方式     | Uvicorn 监听 `0.0.0.0:8000`，Python urllib 端到端跑 Web 闭环冒烟脚本                                    |
| 主要涉及文件   | `backend/web_smoke.py`（新增）、`backend/main.py`、`backend/database.py`、`backend/nlp_engine.py` |
| 本次业务代码改动 | 无业务逻辑改动；新增 `backend/web_smoke.py` 给线 B 的闭环参考脚本                                             |
| 中文注释     | `backend/web_smoke.py` 全文中文注释                                                              |
| 文档记录     | `docs/LINE_A_A15_STEPS.md`                                                                 |
| 下一步      | A16 给线 C 的 CYD 联调信息                                                                        |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` A15 的目标是：每次准备和线 B 联调前，把后端地址、可用接口、Web 闭环顺序整理给线 B，避免他们临时翻文档。本次额外封装一个 `backend/web_smoke.py`，让线 B 在接 API 前先有一份"Python 版的参考调用流程"，也方便线 A 在每次联调前自检。

## 任务目标

- 给线 B 一份能直接抄进 `web/index.html` 的联调清单。
- 给线 B 一段端到端可执行的参考调用流程，覆盖 `输入 -> /analyze_text -> /save_item -> /dashboard`。
- 保证 `localhost` 和局域网两个入口都能跑通完整闭环。
- 不改变现有 API 字段名，避免线 B 已经接好的代码要回头改。

## 给线 B 的联调清单

```
后端地址：
http://localhost:8000

手机 / CYD 地址：
http://10.88.0.183:8000

可用接口：
GET  /
GET  /contexts
GET  /context/{id}
POST /analyze_text
POST /save_item
GET  /dashboard
```

线 B Web 闭环（按顺序验证）：

```
1. 页面加载 -> GET /contexts
2. 用户输入文本 + 选 source_type / optional_context
3. 点击 Analyze -> POST /analyze_text
4. 显示 cleaned_text、keywords、phrases、detected_context、summary
5. 点击 Save Word / Save Phrase -> POST /save_item
6. 点击 Refresh Dashboard -> GET /dashboard
```

JavaScript 端推荐配置（线 B 直接抄）：

```javascript
// API 基础地址：本机开发用 localhost；手机访问改成 laptop 局域网 IP。
const API_BASE = "http://localhost:8000";
// 手机 / CYD 联调时改为：
// const API_BASE = "http://10.88.0.183:8000";

// 闭环示例（线 B 自行替换 textarea / button 绑定）：
async function analyzeAndSave(rawText, sourceType, optionalContext) {
  const analyzeResp = await fetch(API_BASE + "/analyze_text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      raw_text: rawText,
      source_type: sourceType,
      optional_context: optionalContext,
    }),
  });
  const analysis = await analyzeResp.json();

  await fetch(API_BASE + "/save_item", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      item_text: analysis.keywords[0],
      item_type: "word",
      source_context: analysis.detected_context.id,
    }),
  });

  const dashboardResp = await fetch(API_BASE + "/dashboard");
  return dashboardResp.json();
}
```

## API 字段稳定性承诺

线 A 不会临时改下面字段名，直到 MVP 演示结束：

`POST /analyze_text` 请求：

```
raw_text          (string, 必填，前后空白会被裁剪)
source_type       (string, "real-world" | "story", 默认 "real-world")
optional_context  (string | null, 空字符串等同 null)
```

`POST /analyze_text` 响应：

```
id                       (int)
cleaned_text             (string)
keywords                 (list[string])
phrases                  (list[string])
detected_context         ({id, title, type, tag, summary, confidence})
summary                  (string)
suggested_review_items   (list[string])
```

`POST /save_item` 请求：

```
item_text       (string, 必填，前后空白会被裁剪)
item_type       ("word" | "phrase")
source_context  (string | null)
```

`POST /save_item` 响应：

```
id     (int)
saved  (bool)
```

`GET /contexts` 响应：

```
real_world  (list of context object)
story       (list of context object)
```

`GET /dashboard` 响应：

```
saved_words      (list[{item_text, source_context, created_at}], item_text 已去重)
saved_phrases    (list[{item_text, source_context, created_at}], item_text 已去重)
top_context      (string | null)
recent_keywords  (list[string], 不重复，最多 10 个)
review_today    (int, 今天本地日期保存的复习项数量)
```

非法输入约定（线 B 调试时遇到要按这个解读）：

- 纯空白 `raw_text` -> HTTP 422
- 纯空白 `item_text` -> HTTP 422
- 非 `word|phrase` 的 `item_type` -> HTTP 422
- 不存在的 `context_id` -> HTTP 404

## 代码改动

新增文件：`backend/web_smoke.py`

脚本特点：

- 用标准库 `urllib.request` 调用 HTTP，不引入新依赖。
- 默认调 `http://localhost:8000`，命令行第一个参数可改为局域网地址，方便切到手机视角。
- 闭环顺序与线 B 网页 `fetch` 调用顺序一致。
- 字段缺失或值不符合预期时立刻 `AssertionError`，避免线 B 在网页上反查后端问题。
- 任何步骤失败都返回非 0，可嵌入 PowerShell 链式调用。

## 代码片段说明

闭环主流程（节选）：

```python
def run_smoke(base_url: str) -> bool:
    """跑完整 Web 闭环；任何一步失败直接抛异常，main() 会兜住并返回非 0。"""
    # Step 1: 健康检查，确认后端已经起来。
    health = http_get(base_url, "/")
    assert health.get("status") == "ok", "health check failed"

    # Step 2: GET /contexts，模拟网页加载下拉框。
    contexts = http_get(base_url, "/contexts")
    real_world_ids = [item["id"] for item in contexts.get("real_world", [])]
    story_ids = [item["id"] for item in contexts.get("story", [])]
    assert set(real_world_ids) == {"coffee_shop", "doctor_pharmacy"}
    assert set(story_ids) == {"kings_cross", "baker_street"}

    # Step 3: 用 4 段 demo 文本依次跑 /analyze_text，模拟用户输入并点击 Analyze。
    analyze_results: dict[str, dict[str, Any]] = {}
    for expected_id, source_type, text in DEMO_TEXTS:
        result = http_post(
            base_url,
            "/analyze_text",
            {"raw_text": text, "source_type": source_type, "optional_context": None},
        )
        actual_id = result["detected_context"]["id"]
        assert actual_id == expected_id
        analyze_results[expected_id] = result
    ...
```

JSON POST 助手：

```python
def http_post(base_url: str, path: str, payload: dict[str, Any]) -> Any:
    """发送 JSON POST 请求并解析 JSON 返回；与线 B 网页 fetch 行为保持一致。"""
    # 显式声明 `Content-Type: application/json`，否则 FastAPI 会按 form 解析报 422。
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))
```

## 验收命令

启动局域网监听后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

本机闭环冒烟：

```powershell
.\.venv\Scripts\python.exe -m backend.web_smoke
```

局域网闭环冒烟（手机 / CYD 视角）：

```powershell
.\.venv\Scripts\python.exe -m backend.web_smoke http://10.88.0.183:8000
```

PowerShell `Invoke-RestMethod` 备用快查：

```powershell
$base = "http://10.88.0.183:8000"
Invoke-RestMethod -Uri "$base/"
Invoke-RestMethod -Uri "$base/contexts"
Invoke-RestMethod -Uri "$base/dashboard"
```

## 验收结果

`localhost` 闭环：

| 检查项                     | 结果                               |
| ----------------------- | -------------------------------- |
| `step1_health_status`   | `ok`                             |
| `step1_health_service`  | `SceneLingo API`                 |
| `step2_real_world_ids`  | `coffee_shop,doctor_pharmacy`    |
| `step2_story_ids`       | `kings_cross,baker_street`       |
| `step3_coffee_shop`     | `coffee_shop`                    |
| `step3_doctor_pharmacy` | `doctor_pharmacy`                |
| `step3_kings_cross`     | `kings_cross`                    |
| `step3_baker_street`    | `baker_street`                   |
| `step4_save_word`       | `get`，`id=16`，`saved=True`       |
| `step4_save_phrase`     | `Can I Get`，`id=17`，`saved=True` |
| `step5_word_visible`    | `True`                           |
| `step5_phrase_visible`  | `True`                           |
| `step5_review_today`    | `16`                             |
| `smoke_status`          | `pass`，exit code `0`             |

局域网 `http://10.88.0.183:8000` 闭环：

| 检查项                     | 结果                               |
| ----------------------- | -------------------------------- |
| `step1_health_status`   | `ok`                             |
| `step1_health_service`  | `SceneLingo API`                 |
| `step2_real_world_ids`  | `coffee_shop,doctor_pharmacy`    |
| `step2_story_ids`       | `kings_cross,baker_street`       |
| `step3_coffee_shop`     | `coffee_shop`                    |
| `step3_doctor_pharmacy` | `doctor_pharmacy`                |
| `step3_kings_cross`     | `kings_cross`                    |
| `step3_baker_street`    | `baker_street`                   |
| `step4_save_word`       | `get`，`id=18`，`saved=True`       |
| `step4_save_phrase`     | `Can I Get`，`id=19`，`saved=True` |
| `step5_word_visible`    | `True`                           |
| `step5_phrase_visible`  | `True`                           |
| `step5_review_today`    | `18`                             |
| `smoke_status`          | `pass`，exit code `0`             |

完整 stdout（节选）：

```
base_url=http://localhost:8000
step1_health_status=ok
step1_health_service=SceneLingo API
step2_real_world_ids=coffee_shop,doctor_pharmacy
step2_story_ids=kings_cross,baker_street
step3_coffee_shop_detected=coffee_shop
step3_doctor_pharmacy_detected=doctor_pharmacy
step3_kings_cross_detected=kings_cross
step3_baker_street_detected=baker_street
step4_save_word_text=get
step4_save_word_id=16
step4_save_word_saved=True
step4_save_phrase_text=Can I Get
step4_save_phrase_id=17
step4_save_phrase_saved=True
step5_dashboard_saved_words_count=6
step5_dashboard_saved_phrases_count=3
step5_dashboard_top_context=baker_street
step5_dashboard_review_today=16
step5_word_visible=True
step5_phrase_visible=True
smoke_status=pass
```

## 数据库影响

| 表名                 | 写入变化                                        |
| ------------------ | ------------------------------------------- |
| `contexts`         | 无新增                                         |
| `analysis_results` | 新增 8 条（`localhost` 4 段 + 局域网 4 段 demo）      |
| `review_items`     | 新增 4 条（`get` ×2 word，`Can I Get` ×2 phrase） |

最终 DB 计数：

```
contexts=4
analysis_results=16
review_items=18
today_reviews=18
```

`saved_words` / `saved_phrases` 已经按 `item_text` 去重，所以即使重复保存了同一个 `get` / `Can I Get`，dashboard 里仍然只显示一份。

## 给线 B 的下一步

线 B 直接做这几件事：

1. 把 `web/index.html` 里 `API_BASE` 改成 `http://localhost:8000`（本机调试）或 `http://10.88.0.183:8000`（手机访问）。
2. 按上文 JS 片段串好 `analyzeAndSave` 闭环。
3. 联调前先跑 `python -m backend.web_smoke`，确认 `smoke_status=pass`，再开始接网页。
4. 如果网页上 fetch 失败：
   - 看 DevTools Network：是 4xx 还是网络错误。
   - 4xx 直接看 response body，会有 FastAPI 的 `detail`。
   - 网络错误优先确认 `API_BASE` 写对、Uvicorn 用 `--host 0.0.0.0` 启动、Wi-Fi 一致。

## 服务状态记录

本次 A15 验收使用临时 Uvicorn Job，验收结束后已执行清理：

```powershell
Stop-Job -Job $job
Remove-Job -Job $job -Force
```

需要重新启动局域网监听：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 结论

- A15 已通过。
- 给线 B 的联调清单、API 字段稳定性承诺、JS 抄写片段全部就位。
- `backend/web_smoke.py` 提供端到端的 Web 闭环冒烟，本机和局域网两个入口都通过验收。
- 数据库写入符合预期，`saved_words` / `saved_phrases` 去重逻辑工作正常。
- 线 B 现在可以直接接 API，遇到失败时按"下一步"流程排查。
