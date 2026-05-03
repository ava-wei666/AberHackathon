# LINE_A Task A16 操作记录

## 记录字段

| 字段       | 内容                                                                                          |
| -------- | ------------------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                                    |
| Task     | `A16 - 给线 C 的 CYD 联调信息`                                                                     |
| 状态       | 已通过                                                                                         |
| 执行日期     | `2026-05-03`                                                                                |
| 工作目录     | `C:\hackathon`                                                                              |
| 本地 API   | `http://localhost:8000`                                                                     |
| 局域网 API  | `http://10.88.0.183:8000`                                                                   |
| 验收方式     | Uvicorn 监听 `0.0.0.0:8000`，Python urllib 端到端跑 CYD 闭环冒烟脚本，覆盖双向同步                              |
| 主要涉及文件   | `backend/cyd_smoke.py`（新增）、`backend/main.py`、`backend/database.py`、`backend/seed_data.json` |
| 本次业务代码改动 | 无业务逻辑改动；新增 `backend/cyd_smoke.py` 给线 C 的 CYD 闭环参考脚本                                         |
| 中文注释     | `backend/cyd_smoke.py` 全文中文注释                                                               |
| 文档记录     | `docs/LINE_A_A16_STEPS.md`                                                                  |
| 下一步      | A17 Demo 测试文本自测                                                                             |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` A16 的目标是：每次准备和线 C 联调前，把局域网 API、CYD 关心的 4 个接口、双向闭环顺序整理给线 C，避免他们盯着 LVGL 调一半还要回头查接口。本次额外封装一个 `backend/cyd_smoke.py`，让线 C 在写 MicroPython 之前，先用 PC 视角跑一遍 CYD 关心的调用链。

## 任务目标

- 给线 C 一份能直接抄进 CYD MicroPython 文件的联调清单。
- 给线 C 一段端到端可执行的参考调用流程，覆盖 `GET /contexts -> GET /context/{id} -> GET /dashboard -> POST /save_item -> GET /dashboard`。
- 验证 "CYD 保存 -> Web Refresh dashboard 能看到" 与 "Web 保存 -> CYD Refresh dashboard 能看到" 双向同步。
- API 字段保持稳定，CYD 不需要再做复杂数据加工。

## 给线 C 的联调清单

```
局域网 API：
http://10.88.0.183:8000

本机 fallback：
http://127.0.0.1:8000  （线 A 自测用）

CYD 主要调用：
GET  /contexts           // 加载 Real-world / Story 两组场景
GET  /context/{id}       // 进入某个场景卡片
POST /save_item          // 保存当前 keyword 或 phrase
GET  /dashboard          // 复习 dashboard

CYD 不需要调：
POST /analyze_text       // 由 Web 端触发；CYD 只读取分析后的 dashboard
```

CYD 闭环（按顺序验证）：

```
1. CYD 启动 -> GET /contexts -> 渲染 Real-world / Story 列表
2. 进入某个 context -> GET /context/{id} -> Insight View 渲染
3. 进入 Dashboard -> GET /dashboard -> 渲染 saved_words / saved_phrases
4. CYD 点击保存 -> POST /save_item -> {"saved": true}
5. 再点 Refresh -> GET /dashboard -> 看到刚保存的 item
6. Web 那边保存一条 -> CYD 点 Refresh -> 也能看到（双向同步）
```

## API 字段约定（CYD 视角）

`GET /contexts` 响应：

```json
{
  "real_world": [{ "id": "coffee_shop", "title": "Coffee Shop", ... }],
  "story":      [{ "id": "kings_cross",  "title": "King's Cross", ... }]
}
```

`GET /context/{id}` 响应（CYD 直接拿来渲染场景卡片）：

```
id              (string)
title           (string)
type            ("real-world" | "story")
tag             (string, 短)
summary         (string, 1-2 句)
seed_keywords   (list[string])
seed_phrases    (list[string])
```

`POST /save_item` 请求：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

`POST /save_item` 响应：

```json
{ "id": 7, "saved": true }
```

`GET /dashboard` 响应（CYD 直接渲染）：

```
saved_words      (list[{item_text, source_context, created_at}], item_text 已去重)
saved_phrases    (list[{item_text, source_context, created_at}], item_text 已去重)
top_context      (string | null, 直接显示 id)
recent_keywords  (list[string], 不重复，最多 10 个)
review_today    (int, 今天本地日期保存的复习项数量)
```

不存在的 `context_id` 一律返回 HTTP 404；CYD 收到 404 应回退到 mock context。

## CYD MicroPython 抄写片段

```python
# CYD 端的 API 配置（urequests 用法）。
import urequests
import ujson

# 联调时直接改这一行；本机 demo 走 127.0.0.1，手机 / CYD 走 laptop 局域网 IP。
API_BASE = "http://10.88.0.183:8000"


def api_get(path):
    """统一 GET helper；请求结束后必须 close，否则 MicroPython 上会内存泄漏。"""
    response = urequests.get(API_BASE + path, timeout=5)
    try:
        if response.status_code != 200:
            return None
        return response.json()
    finally:
        response.close()


def api_post(path, payload):
    """统一 POST helper；headers 必须显式传 application/json，否则 FastAPI 报 422。"""
    headers = {"Content-Type": "application/json"}
    body = ujson.dumps(payload)
    response = urequests.post(API_BASE + path, data=body, headers=headers, timeout=5)
    try:
        if response.status_code != 200:
            return None
        return response.json()
    finally:
        response.close()


def fetch_contexts():
    return api_get("/contexts")


def fetch_context(context_id):
    return api_get("/context/" + context_id)


def fetch_dashboard():
    return api_get("/dashboard")


def save_item(item_text, item_type, source_context):
    return api_post("/save_item", {
        "item_text": item_text,
        "item_type": item_type,
        "source_context": source_context,
    })
```

## 网络与防火墙提示（沿用 A11 结论）

```
laptop 必须用 0.0.0.0 启动：
  uvicorn backend.main:app --host 0.0.0.0 --port 8000

CYD 和 laptop 在同一个 Wi-Fi / hotspot

如果跨设备访问失败，在管理员 PowerShell 执行：
  netsh advfirewall firewall add rule name="SceneLingo FastAPI 8000" dir=in action=allow protocol=TCP localport=8000

校园网客户端隔离会让设备互相不可达，此时改用同一热点或同一路由器 WiFi
```

## 代码改动

新增文件：`backend/cyd_smoke.py`

脚本特点：

- 用标准库 `urllib.request` 调用 HTTP，不引入新依赖。
- 闭环顺序与 CYD MicroPython 调用一致（不调用 `/analyze_text`）。
- 同步在脚本里跑双向校验：CYD 保存 -> dashboard 可见；Web 保存 -> dashboard 可见。
- 命令行第一个参数可切到局域网地址，模拟真实 CYD 视角。
- 任何字段缺失或值不符立刻 `AssertionError`，避免在 LVGL UI 层反查后端问题。

## 代码片段说明

CYD 闭环主流程（节选）：

```python
def run_cyd_loop(base_url: str) -> bool:
    """模拟 CYD 的完整调用顺序，并校验双向同步。"""
    # Step 1: GET /contexts，模拟 CYD Context Select 页加载。
    contexts = http_get(base_url, "/contexts")
    real_world_ids = [item["id"] for item in contexts.get("real_world", [])]
    story_ids = [item["id"] for item in contexts.get("story", [])]
    assert set(real_world_ids) == {"coffee_shop", "doctor_pharmacy"}
    assert set(story_ids) == {"kings_cross", "baker_street"}

    # Step 2: 逐个 GET /context/{id}，模拟 CYD 进入每个场景卡片。
    for context_id in CONTEXT_IDS:
        card = http_get(base_url, f"/context/{context_id}")
        assert_keys(f"/context/{context_id}", card, REQUIRED_CONTEXT_FIELDS)
        assert isinstance(card["seed_keywords"], list)
        assert isinstance(card["seed_phrases"], list)
    ...
```

JSON POST 助手（与 CYD 上 `urequests.post(json=...)` 行为等价）：

```python
def http_post(base_url: str, path: str, payload: dict[str, Any]) -> Any:
    """用 urllib 发 JSON POST 请求；与 CYD urequests.post(json=...) 等价。"""
    # 显式 Content-Type，否则 FastAPI 会按 form 解析直接 422。
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

双向同步校验（节选）：

```python
# Step 6: 再次 GET /dashboard，模拟 CYD 点 Refresh，验证刚保存的 item 出现。
dashboard_after = http_get(base_url, "/dashboard")
saved_words_after = {item["item_text"] for item in dashboard_after["saved_words"]}
saved_phrases_after = {item["item_text"] for item in dashboard_after["saved_phrases"]}
assert cyd_word_text in saved_words_after, "CYD-saved word not visible in dashboard"
assert cyd_phrase_text in saved_phrases_after, "CYD-saved phrase not visible in dashboard"
assert review_today_after - review_today_before == 2, "review_today did not increase by 2"

# Step 7: 模拟 "Web 保存 word -> CYD Refresh 看到"，验证反方向同步。
web_word_text = "web_smoke_to_cyd"
http_post(base_url, "/save_item", {
    "item_text": web_word_text, "item_type": "word", "source_context": "coffee_shop",
})
dashboard_after_web = http_get(base_url, "/dashboard")
saved_words_after_web = {item["item_text"] for item in dashboard_after_web["saved_words"]}
assert web_word_text in saved_words_after_web, "Web-saved word not visible from CYD view"
```

## 验收命令

启动局域网监听后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

本机闭环冒烟：

```powershell
.\.venv\Scripts\python.exe -m backend.cyd_smoke
```

局域网闭环冒烟（CYD 视角）：

```powershell
.\.venv\Scripts\python.exe -m backend.cyd_smoke http://10.88.0.183:8000
```

PowerShell `Invoke-RestMethod` 备用快查（CYD 不可用时排错）：

```powershell
$base = "http://10.88.0.183:8000"
Invoke-RestMethod -Uri "$base/contexts"
Invoke-RestMethod -Uri "$base/context/coffee_shop"
Invoke-RestMethod -Uri "$base/dashboard"
```

## 验收结果

`localhost` 闭环：

| 检查项                             | 结果                            |
| ------------------------------- | ----------------------------- |
| `step1_real_world_ids`          | `coffee_shop,doctor_pharmacy` |
| `step1_story_ids`               | `kings_cross,baker_street`    |
| `step2_coffee_shop_card_ok`     | `True,keywords=12,phrases=5`  |
| `step2_doctor_pharmacy_card_ok` | `True,keywords=11,phrases=5`  |
| `step2_kings_cross_card_ok`     | `True,keywords=11,phrases=5`  |
| `step2_baker_street_card_ok`    | `True,keywords=11,phrases=5`  |
| `step3_review_today_before`     | `18`                          |
| `step4_cyd_save_word_id`        | `20`，`saved=True`             |
| `step5_cyd_save_phrase_id`      | `21`，`saved=True`             |
| `step6_review_today_after`      | `20`                          |
| `step6_word_visible`            | `True`                        |
| `step6_phrase_visible`          | `True`                        |
| `step6_review_today_delta`      | `2`                           |
| `step7_web_save_word_id`        | `22`                          |
| `step7_web_word_visible_on_cyd` | `True`                        |
| `smoke_status`                  | `pass`，exit code `0`          |

局域网 `http://10.88.0.183:8000` 闭环：

| 检查项                             | 结果                                            |
| ------------------------------- | --------------------------------------------- |
| `step1_real_world_ids`          | `coffee_shop,doctor_pharmacy`                 |
| `step1_story_ids`               | `kings_cross,baker_street`                    |
| `step2_*_card_ok`               | 4 个 context 全部通过，`keywords/phrases` 数量与本机一致   |
| `step3_review_today_before`     | `21`（=本机闭环结束后的 19 + Web 保存的 1 + 本机 step7 的 1） |
| `step4_cyd_save_word_id`        | `23`，`saved=True`                             |
| `step5_cyd_save_phrase_id`      | `24`，`saved=True`                             |
| `step6_review_today_after`      | `23`                                          |
| `step6_word_visible`            | `True`                                        |
| `step6_phrase_visible`          | `True`                                        |
| `step6_review_today_delta`      | `2`                                           |
| `step7_web_save_word_id`        | `25`                                          |
| `step7_web_word_visible_on_cyd` | `True`                                        |
| `smoke_status`                  | `pass`，exit code `0`                          |

完整 stdout（节选 localhost）：

```
base_url=http://localhost:8000
step1_real_world_ids=coffee_shop,doctor_pharmacy
step1_story_ids=kings_cross,baker_street
step2_coffee_shop_card_ok=True,keywords=12,phrases=5
step2_doctor_pharmacy_card_ok=True,keywords=11,phrases=5
step2_kings_cross_card_ok=True,keywords=11,phrases=5
step2_baker_street_card_ok=True,keywords=11,phrases=5
step3_review_today_before=18
step3_saved_words_count_before=6
step3_saved_phrases_count_before=3
step4_cyd_save_word_id=20
step4_cyd_save_word_saved=True
step5_cyd_save_phrase_id=21
step5_cyd_save_phrase_saved=True
step6_review_today_after=20
step6_word_visible=True
step6_phrase_visible=True
step6_review_today_delta=2
step7_web_save_word_id=22
step7_web_word_visible_on_cyd=True
smoke_status=pass
```

## 数据库影响

| 表名                 | 写入变化                                                          |
| ------------------ | ------------------------------------------------------------- |
| `contexts`         | 无新增                                                           |
| `analysis_results` | 无新增（CYD 闭环不调用 `/analyze_text`）                                |
| `review_items`     | 新增 6 条（每次闭环写 3 条：CYD word + CYD phrase + Web word；本机和局域网各跑一次） |

最终 DB 计数：

```
contexts=4
analysis_results=16
review_items=24
today_reviews=24
```

最近 6 条 review_items：

```
{'id': 25, 'item_text': 'web_smoke_to_cyd',  'item_type': 'word',   'source_context': 'coffee_shop'}
{'id': 24, 'item_text': 'cyd smoke phrase',  'item_type': 'phrase', 'source_context': 'kings_cross'}
{'id': 23, 'item_text': 'cyd_smoke_word',    'item_type': 'word',   'source_context': 'doctor_pharmacy'}
{'id': 22, 'item_text': 'web_smoke_to_cyd',  'item_type': 'word',   'source_context': 'coffee_shop'}
{'id': 21, 'item_text': 'cyd smoke phrase',  'item_type': 'phrase', 'source_context': 'kings_cross'}
{'id': 20, 'item_text': 'cyd_smoke_word',    'item_type': 'word',   'source_context': 'doctor_pharmacy'}
```

`saved_words` / `saved_phrases` 已经按 `item_text` 去重，所以即使同名条目被插入多次，CYD dashboard 上仍然只显示一份。

## 给线 C 的下一步

1. 先按 "CYD MicroPython 抄写片段" 把 `API_BASE` 与 `api_get / api_post / fetch_dashboard / save_item` 接好。
2. 联调前先在 laptop 跑 `python -m backend.cyd_smoke http://10.88.0.183:8000`，确认 `smoke_status=pass`，再开始动 LVGL。
3. CYD 上拿不到响应时优先排查：
   - laptop Uvicorn 是否用 `--host 0.0.0.0` 启动。
   - CYD 是否连了同一个 Wi-Fi / hotspot（校园网常见的客户端隔离会拦截设备互访）。
   - Windows 防火墙是否放行 TCP 8000（管理员 PowerShell 加规则，命令见上文）。
1. CYD 显示不下的字段直接告诉线 A，看是否压缩 `summary` 或拆分 dashboard，**不要**在 CYD 端做加工。
2. CYD 不要直接读 SQLite，所有数据走 `GET /dashboard` 与 `GET /context/{id}`。

## 服务状态记录

本次 A16 验收使用临时 Uvicorn Job，验收结束后已执行清理：

```powershell
Stop-Job -Job $job
Remove-Job -Job $job -Force
```

需要重新启动局域网监听：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 结论

- A16 已通过。
- 给线 C 的联调清单、CYD MicroPython 抄写片段、双向同步验证全部就位。
- `backend/cyd_smoke.py` 一条命令完成 CYD 闭环冒烟，本机和局域网两个入口都通过验收。
- CYD 保存 -> dashboard 可见、Web 保存 -> dashboard 可见的双向同步均通过断言。
- API 字段保持稳定，CYD 不需要在端上做去重、日期过滤等额外加工。
