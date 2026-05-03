# Scene Words 产品介绍

> 一份用来给别人讲清楚 **Scene Words** 这款产品的中文说明文档。 所有专有名词、字段名、接口路径、按钮文案、文件名都保留英文原文，方便你在演示时直接对照代码或屏幕。

---

## 1. 一句话定位

**Scene Words** 是一个 **context-based language learning**（基于场景的语言学习）的 MVP 产品。它会接收用户的一段英文输入（打字或语音转写），用本地 NLP 流水线识别出说话所处的「场景」（context），抽取这段话里值得学的 **keywords** 和 **phrases**，并把它们保存到一个可在 **Web Dashboard** 与 **CYD 嵌入式屏幕** 上查看的复习库里。

整个产品 **完全离线可用**：没有网络、没有 LLM API key、也没有云服务依赖，只靠本地 Python 标准库 + 一个 SQLite 文件就能完整跑通。

---

## 2. 产品由哪几条线组成

项目按 `docs/TASK_PHASES.md` 的拆分，由三条独立工作线组成，每条线都能独立 demo：

| 线                                      | 负责什么                                                | 主要技术                                                    |
| -------------------------------------- | --------------------------------------------------- | ------------------------------------------------------- |
| **Line A — Backend / NLP / SQLite**    | FastAPI 路由、规则化 NLP、SQLite 持久化                       | Python 3, FastAPI, Uvicorn, Pydantic v2, SQLite         |
| **Line B — Web Input / Web Dashboard** | 浏览器输入页 + 网页版 Dashboard fallback                     | 原生 HTML / CSS / JavaScript（无框架）                         |
| **Line C — CYD LVGL Display**          | 烧在 ESP32 「**CYD (Cheap Yellow Display)**」上的 LVGL UI | MicroPython, LVGL 9, ILI9341 (display), XPT2046 (touch) |

三条线之间只通过 **HTTP + JSON** 通信，互不依赖具体实现，单点改不影响整体。

---

## 3. 端到端数据流

```
Web Input  /  CYD touch
        │
        ▼
   POST /analyze_text  ─────►  FastAPI route (backend/main.py)
        │
        ▼
   nlp_engine.analyze_text()
   tokenize → clean → keyword extraction → context classification
            → phrase extraction → summary
        │
        ▼
   database.insert_analysis()  ─────►  SQLite (scenelingo.db)
        │
        ▼
   JSON response  ─────►  浏览器或 CYD 渲染 Detected Context / Keywords / Phrases
        │
        ▼
   用户点击 Save Word / Save Phrase
        │
        ▼
   POST /save_item  ─────►  review_items 表
        │
        ▼
   GET /dashboard  ─────►  Web Dashboard / CYD Dashboard 复习视图
```

闭环演示路径（30 秒讲完）：

1. 浏览器打开 `web/index.html`，在 **Text Input** 里粘一句英文。
2. 点 **Analyze Text** → 看到 **Detected Context**、**Keywords**、**Phrases**、**Summary**。
3. 点击 **Save Word / Save Phrase** chip → 写入 `review_items`。
4. 点 **Refresh Dashboard** → 看到 **saved_words / saved_phrases / top_context / recent_keywords / review_today** 五块汇总。
5. 同一时刻在 CYD 屏幕上点 **Refresh** → 看到刚才在 Web 端保存的同一条数据，证明双向同步。

---

## 4. 四个内置场景（seed contexts）

整个 MVP 内置 **4 个 context**，分两类，写在 `backend/seed_data.json` 里。每个 context 都有 `seed_keywords` 和 `seed_phrases`，既用于触发分类，也用于在 UI 里给用户做练习提示。

### 4.1 Real-world contexts（真实生活场景）

| id                | title                 | tag           | summary                                                                          | 部分 seed_keywords                                                                                                           | 部分 seed_phrases                                                           |
| ----------------- | --------------------- | ------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `coffee_shop`     | **Coffee Shop**       | `coffee shop` | Ordering drinks, asking about prices, and using polite service phrases.          | `coffee`, `latte`, `tea`, `milk`, `order`, `menu`, `cash`, `card`, `receipt`, `takeaway`, `size`, `drink`                  | `can i get`, `how much is`, `for here`, `to go`, `with milk`              |
| `doctor_pharmacy` | **Doctor / Pharmacy** | `doctor`      | Describing symptoms, asking for medicine, and understanding basic health advice. | `doctor`, `pharmacy`, `medicine`, `pain`, `cough`, `fever`, `symptom`, `tablet`, `prescription`, `appointment`, `headache` | `i have a`, `how long`, `take this`, `twice a day`, `make an appointment` |

### 4.2 Story contexts（故事场景）

| id             | title                              | tag            | summary                                                                                   | 部分 seed_keywords                                                                                                    | 部分 seed_phrases                                                                           |
| -------------- | ---------------------------------- | -------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `kings_cross`  | **Harry Potter - King's Cross**    | `magic school` | A station scene about travel, tickets, platforms, luggage, and magical school vocabulary. | `train`, `station`, `platform`, `ticket`, `luggage`, `magic`, `school`, `journey`, `king`, `cross`, `wizard`        | `which platform`, `catch the train`, `lost my ticket`, `magic school`, `king's cross`     |
| `baker_street` | **Sherlock Holmes - Baker Street** | `detective`    | A detective scene about clues, cases, clients, observations, and careful questioning.     | `detective`, `clue`, `case`, `client`, `mystery`, `observe`, `evidence`, `london`, `baker`, `street`, `investigate` | `tell me everything`, `what happened`, `look for clues`, `solve the case`, `baker street` |

> **为什么选这 4 个**：两个 real-world 解决「真的能用上」，两个 story 让演示有趣（评委一眼能记住 Harry Potter / Sherlock）。结构上是开放的——只要在 `seed_data.json` 里加一条记录、重启后端就生效，**不需要改任何代码**。

---

## 5. NLP 流水线（5 步，全部规则化）

文件：`backend/nlp_engine.py`，入口函数 `analyze_text(raw_text, source_type, optional_context, contexts)`。

```
raw_text
   │
   ▼
[1] _tokenize        正则 [a-zA-Z][a-zA-Z']* 切英文词，统一小写
   │
   ▼
[2] _clean_tokens    去 STOPWORDS（a, the, to, ...）
                     去 FILLER_WORDS（um, uh, like, actually, basically, okay, ...）
                     去连续重复词
   │
   ▼
[3] _extract_keywords    Counter 词频统计，长度 > 2 的词参与，最多 5 个
   │
   ▼
[4] _classify_context    与每个 context 的 seed_keywords + title + tag 做命中打分
                         得分最高 → detected_context
                         有 optional_context 时直接信任前端选择
                         confidence = min(0.95, 0.45 + best_score * 0.12)
   │
   ▼
[5] _extract_phrases    优先匹配 detected_context 的 seed_phrases（命中即按 _title_phrase 美化）
                        再从清洗 token 里拼 3 词短语，凑不够拼 2 词，最多 3 个
   │
   ▼
_build_summary       本地模板拼一句话："This looks like {title}: focus on {top3 keywords} and practice phrases like '{first phrase}'."
   │
   ▼
返回 JSON：{
  cleaned_text,
  keywords,
  phrases,
  detected_context: {id, title, type, tag, summary, seed_phrases, confidence},
  summary,
  suggested_review_items   ← keywords[:3] + phrases[:2]，给前端 Save 按钮直接用
}
```

**为什么走规则不走 LLM / spaCy / NLTK**：

- **可解释**：评委问「为什么这个词被选中」，能直接指到代码行。
- **离线**：不依赖网络，不需要下载语言模型。
- **可调**：调 `seed_keywords` / `seed_phrases` 即生效，不需要重训。
- **稳定**：没有 LLM 幻觉，输出在每次请求间保持一致。
- 留有扩展点：以后接 LLM 只需要在 `_build_summary()` 里加一个分支，主管线不动。

---

## 6. 后端 API 合约（6 个接口）

文件：`backend/main.py`，FastAPI app 名为 `Scene Words API`。Pydantic 请求模型：`AnalyzeTextRequest`、`SaveItemRequest`，都带字段裁剪与空字符串归一化校验。

| Method | Path            | 用途                                                                                      | 谁在调用                        |
| ------ | --------------- | --------------------------------------------------------------------------------------- | --------------------------- |
| `GET`  | `/`             | 健康检查，返回 `{"status":"ok","service":"Scene Words API"}`                                   | 任何客户端                       |
| `GET`  | `/contexts`     | 拉所有 context，按 `real_world` / `story` 分组返回                                               | Web、CYD                     |
| `GET`  | `/context/{id}` | 拿单个场景卡片（含 seed_phrases、summary 等）                                                       | CYD Insight View            |
| `POST` | `/analyze_text` | **核心入口**：文本进 → 完整分析 JSON 出                                                              | Web、CYD                     |
| `POST` | `/save_item`    | 保存复习项（`item_type` ∈ `"word"` / `"phrase"`）                                              | Web、CYD                     |
| `GET`  | `/dashboard`    | 汇总 `saved_words` / `saved_phrases` / `top_context` / `recent_keywords` / `review_today` | Web Dashboard、CYD Dashboard |

### 6.1 `POST /analyze_text` 请求 / 响应示例

请求：

```json
{
  "raw_text": "Hi, can I get a latte with milk to go? How much is the large size?",
  "source_type": "real-world",
  "optional_context": null
}
```

响应（实测 demo 数据，`docs/LINE_A/LINE_A_PRESENTATION.md` 已验收）：

```json
{
  "id": 1,
  "cleaned_text": "hi get latte milk go",
  "keywords": ["get", "latte", "milk", "how", "much"],
  "phrases": ["Can I Get", "How Much Is", "to go"],
  "detected_context": {
    "id": "coffee_shop",
    "title": "Coffee Shop",
    "type": "real-world",
    "tag": "coffee shop",
    "summary": "Ordering drinks, asking about prices, ...",
    "confidence": 0.81
  },
  "summary": "This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.",
  "suggested_review_items": ["get", "latte", "milk", "Can I Get", "How Much Is"]
}
```

### 6.2 `GET /dashboard` 响应字段

```json
{
  "saved_words":     [ { "item_text": "...", "source_context": "...", "created_at": "..." } ],
  "saved_phrases":   [ { "item_text": "...", "source_context": "...", "created_at": "..." } ],
  "top_context":     "coffee_shop",
  "recent_keywords": ["latte", "milk", "order", "..."],
  "review_today":    3
}
```

`saved_words` / `saved_phrases` 都按 `item_text` 去重并按时间倒序，最多 20 条；`recent_keywords` 取自最近 10 次分析的 `keywords_json`，按出现顺序去重，最多 10 条；`review_today` 用 SQL 的 `DATE(..., 'localtime')` 过滤当天保存数。

---

## 7. 数据库 Schema（3 张表）

文件：`backend/database.py`，单文件 SQLite，路径 `scenelingo.db`，启动时自动建表 + 同步 seed。

```sql
-- 4 个固定场景，从 seed_data.json 同步，ON CONFLICT(id) DO UPDATE 让重启即生效
CREATE TABLE contexts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,                 -- 'real-world' or 'story'
    tag TEXT NOT NULL,
    summary TEXT NOT NULL,
    seed_keywords_json TEXT NOT NULL,
    seed_phrases_json TEXT NOT NULL
);

-- 每次 POST /analyze_text 留底，用于 top_context / recent_keywords 统计
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_text TEXT NOT NULL,
    cleaned_text TEXT NOT NULL,
    detected_context TEXT NOT NULL,     -- 命中的 context id
    keywords_json TEXT NOT NULL,
    phrases_json TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 用户点 Save 保存的复习项
CREATE TABLE review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_text TEXT NOT NULL,
    item_type TEXT NOT NULL CHECK (item_type IN ('word', 'phrase')),
    source_context TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

每次连接都用 Python 的 `with get_connection()` 包住，显式 `commit` / `rollback` / `close`，避免 Windows 现场联调时残留文件占用。

---

## 8. Web 前端（Line B）

文件：`web/index.html`，一个 **零框架、零打包** 的单页 HTML。可以双击直接打开，也可以放在 LAN IP 的简易 HTTP server 下让手机访问。`API_BASE` 常量集中在脚本顶部，**改一处即可切换 backend 地址**。

页面分 5 个 section，按编号引导用户：

| #   | Section              | 关键控件                                                                                                                                        |
| --- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Source / Context** | `Source select` (Real-world / Story)、`Optional Context select`（默认 `Auto detect`）                                                            |
| 2   | **Text Input**       | `Typed Text / Transcript` textarea，附 4 个一键 demo 按钮：`Coffee Shop` / `Doctor / Pharmacy` / `King's Cross` / `Baker Street`，主按钮 `Analyze Text` |
| 3   | **Analysis Result**  | `Detected Context` 卡片 + Keywords / Phrases / Summary 面板 + `Debug raw analysis JSON` 折叠                                                      |
| 4   | **Save Buttons**     | 用 `suggested_review_items` 渲染成可点击的 chips，点击即 `POST /save_item`                                                                              |
| 5   | **Web Dashboard**    | `Refresh Dashboard` 按钮，渲染 `review_today` / `top_context` / `recent_keywords` / `saved_words` / `saved_phrases`                              |

UI 风格：浅色背景（`#f5f7fa`）+ 主色 `#0f6f68`，字体 Inter / system-ui，强调可读性而非视觉冲击力，目的是 **2 秒看懂、3 秒能用**。

---

## 9. CYD 嵌入式屏幕（Line C）

文件：`lvgl9_firmwares/scenelingo_dashboard.py`（约 900+ 行），运行在 **ESP32-2432S028R** 也就是俗称 **CYD (Cheap Yellow Display)** 的开发板上。

### 9.1 硬件 / 固件栈

| 角色      | 选用                                 |
| ------- | ---------------------------------- |
| MCU     | ESP32                              |
| Display | ILI9341，240×320，通过 `lcd_bus` + SPI |
| Touch   | XPT2046 电阻触摸（带触摸校准）                |
| 运行时     | MicroPython（带 LVGL 9 绑定）           |
| UI 框架   | LVGL 9（Python class API）           |

主要常量在文件顶部：

```python
API_BASE          = "http://192.168.137.1:8000"
WIFI_SSID         = "CHANGE_ME"     # 真实联调时本地替换，不入 git
WIFI_PASSWORD     = "CHANGE_ME"
AUTO_CONNECT_WIFI = False           # 默认走 mock，避免 Wi-Fi/LVGL 内存冲突
USE_MOCK_DATA     = True
```

### 9.2 三个页面（routes）

| 页面               | 内容                                                                                                       | 数据源                                            |
| ---------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Home**         | 选择 Real-world / Story 和具体 context（4 个入口）                                                                 | `MOCK_CONTEXTS` 或 `GET /contexts`              |
| **Insight View** | 显示当前 context 的 Detected Context、Keywords（最多 5 个，按钮文本截断 14 字符）、Phrases（最多 3 个，截断 30 字符）、Summary（截断 48 字符） | `MOCK_ANALYSES[ctx_id]` 或 `POST /analyze_text` |
| **Dashboard**    | 显示 `saved_words` / `saved_phrases` / `top_context` / `recent_keywords` / `review_today`                  | `MOCK_DASHBOARD` 或 `GET /dashboard`            |

为了适配 240×320 的小屏，所有截断与上限统一在文件顶部 `_C12_*` 常量里：`_C12_MAX_KW=5` / `_C12_MAX_PH=3` / `_C12_MAX_WORDS=5` / `_C12_KW_CHARS=14` / `_C12_PH_CHARS=30` / `_C12_SUM_CHARS=48` / `_C12_LABEL_CHARS=40`。改一行即可统一调整布局密度。

### 9.3 Mock 模式 vs 真实联调

CYD 默认走 mock，原因写在 `docs/INTEGRATION_RECORD.md` 的 **「CYD Wi-Fi/LVGL 内存冲突」** 章节：CYD 内部 SRAM 不足以同时驻留 Wi-Fi 驱动栈和 LVGL DMA 帧缓冲，启用 Wi-Fi 后会导致显示初始化失败。所以现场演示策略是：

- **CYD 端**：用 `MOCK_CONTEXTS` / `MOCK_ANALYSES` / `MOCK_DASHBOARD` 让屏幕跑出完整 UI（Home / Insight / Dashboard）。
- **真实闭环**：由 Web 端承载（`web/index.html` ↔ FastAPI ↔ SQLite），评委可以同时看到屏幕和浏览器两侧。
- **想在 CYD 上跑真实 API**：改 4 行配置（`API_BASE` 设为 laptop 局域网 IP、填 `WIFI_SSID` / `WIFI_PASSWORD`、`AUTO_CONNECT_WIFI=True`、`USE_MOCK_DATA=False`），后端用 `--host 0.0.0.0` 启动即可。

### 9.4 HTTP helper

为兼容不同 MicroPython 固件，CYD 端的 HTTP 调用集中封装：

- `_import_requests()`：自动兼容 `requests` 与 `urequests`。
- `_post_json()`：兼容 `json=` 与 `data=` 两种调用约定，回退用 `ujson.dumps()` + 手动设 `Content-Type`。
- `_request_json()`：统一处理 `status_code`，`USE_MOCK_DATA` 为 True 时直接走 mock，请求结束后强制 `response.close()` 避免内存泄漏。
- 对外只暴露 `api_get()` / `api_post()`，UI 按钮回调不直接发 HTTP。

---

## 10. 技术栈总览（为什么是这套）

| 层           | 选用                                                                | 为什么                                | 没用什么                                    |
| ----------- | ----------------------------------------------------------------- | ---------------------------------- | --------------------------------------- |
| 语言          | **Python 3**                                                      | 团队熟、NLP 标准库够用、跨平台                  | 不用 Node.js / Go：会让 Web、CYD 调试成本上升       |
| Web 框架      | **FastAPI**                                                       | 自动 OpenAPI、Pydantic 校验、原生 async    | 不用 Flask（缺校验和文档）、不用 Django（体量过大）        |
| ASGI server | **Uvicorn**                                                       | FastAPI 官方推荐、`--reload` 友好         | 不用 Gunicorn：多进程对 SQLite 反而锁竞争           |
| 校验          | **Pydantic v2**                                                   | `field_validator` 自动裁剪空白、空字符串归一化   | 不用 marshmallow：FastAPI 已与 Pydantic 深度集成 |
| 数据库         | **SQLite (`sqlite3`)**                                            | 单文件、零配置、可随代码分发、断网仍能跑               | 不用 PostgreSQL / MySQL：要装服务、断网会挂         |
| NLP         | **标准库 + 规则** (`re`, `collections.Counter`)                        | 离线、可解释、可调                          | 不用 spaCy / NLTK / LLM：网络、模型、token 都不可控  |
| 跨域          | **CORSMiddleware**, `allow_origins=["*"]`                         | 局域网联调阶段 Web / CYD / 手机共用同一后端       | 生产再收紧白名单                                |
| 数据格式        | **JSON**                                                          | API、配置、seed 全用 JSON                | 不用 YAML / XML，减少依赖                      |
| 嵌入式 UI      | **MicroPython + LVGL 9**                                          | 可在 ESP32 跑出现代 GUI，开发周期短            | 不用 Arduino C++：迭代速度太慢                   |
| 自测          | `selftest.py` + `web_smoke.py` + `cyd_smoke.py` + `demo_check.py` | 一键覆盖 离线 / Web / CYD / Demo 文本 四种场景 | 不用 pytest：标准库 `assert` 足够               |

`requirements.txt` 总共只有 `fastapi`、`uvicorn`、`pydantic` 三条核心依赖（加上它们的传递依赖）。**全部装机时间不超过 30 秒。**

---

## 11. 鲁棒性与离线证明

| 场景              | 表现                            |
| --------------- | ----------------------------- |
| 没有外网            | 全部 NLP 走本地规则                  |
| 没有 LLM API key  | summary 走本地模板                 |
| 没装 spaCy / NLTK | 只用标准库                         |
| 数据库被删           | 重启时自动重建 + 同步 4 个 seed context |
| 端口 8000 被占      | `--port 8001` 一行换             |
| 第一次启动           | 自动建表 + 写 seed                 |
| Wi-Fi 不通        | CYD 自动回退 mock，Web 仍可跑完整闭环     |

---

## 12. 自测脚本（一键验收）

| 命令                             | 作用                                                    |
| ------------------------------ | ----------------------------------------------------- |
| `python -m backend.selftest`   | 编译 + seed + 数据库 + NLP 形状 + Dashboard 形状 一键自测，**无副作用** |
| `python -m backend.demo_check` | 跑 4 段 demo 文本，断言每段都能命中预期 context                      |
| `python -m backend.web_smoke`  | 模拟 Web 端完整闭环                                          |
| `python -m backend.cyd_smoke`  | 模拟 CYD 闭环，含 **Web ↔ CYD 双向同步校验**                      |

任何一个脚本失败都会以非 0 退出码结束，方便挂在 CI 或 hackathon 现场快速 sanity check。

---

## 13. Demo 文本（已验收）

| #   | 标签                | 文本                                                                                    | 期望 detected_context | 实测 confidence |
| --- | ----------------- | ------------------------------------------------------------------------------------- | ------------------- | ------------- |
| 1   | Coffee Shop       | `Hi, can I get a latte with milk to go? How much is the large size?`                  | `coffee_shop`       | **0.81**      |
| 2   | Doctor / Pharmacy | `I have a headache and a cough. Do I need medicine from the pharmacy?`                | `doctor_pharmacy`   | **0.93**      |
| 3   | King's Cross      | `Which platform should I use to catch the train to the magic school at King's Cross?` | `kings_cross`       | **0.95**      |
| 4   | Baker Street      | `The detective found a clue on Baker Street and tried to solve the case.`             | `baker_street`      | **0.95**      |

四段文本都能在 **100ms 内** 完成「NLP + SQLite 写入 + JSON 序列化」全流程。

---

## 14. 项目目录速查

```
hackathon/
├─ backend/
│  ├─ main.py              FastAPI 路由 + Pydantic 请求模型 (AnalyzeTextRequest, SaveItemRequest)
│  ├─ nlp_engine.py        analyze_text 主管线 + STOPWORDS / FILLER_WORDS / TOKEN_RE
│  ├─ database.py          init_db / list_contexts / insert_analysis / save_review_item / get_dashboard
│  ├─ seed_data.json       4 个 MVP context 的固定数据
│  ├─ selftest.py          一键离线自测
│  ├─ web_smoke.py         Web 闭环冒烟
│  ├─ cyd_smoke.py         CYD 闭环冒烟（双向同步）
│  └─ demo_check.py        4 段 demo 文本验收
├─ web/
│  └─ index.html           Web Input + Web Dashboard 单文件页
├─ lvgl9_firmwares/
│  ├─ scenelingo_dashboard.py     CYD 主程序（Home / Insight / Dashboard）
│  └─ lvgl9_3_micropython_cyd.bin LVGL 9 + MicroPython 固件
├─ docs/
│  ├─ TASK_PHASES.md
│  ├─ LINE_A_BACKEND_TASKS.md
│  ├─ LINE_B_WEB_CYD_TASKS.md
│  ├─ LINE_C_CONTENT_DEMO_QA_TASKS.md
│  ├─ LINE_A/LINE_A_PRESENTATION.md   Line A 答辩稿
│  ├─ TASK_C0_RECORD.md ~ TASK_C14_RECORD.md  CYD 各阶段记录
│  └─ INTEGRATION_RECORD.md           三线合并 + CYD 部署记录
├─ requirements.txt        fastapi / uvicorn / pydantic 三个核心依赖
└─ scenelingo.db           启动时自动生成的 SQLite，默认不入 git
```

---

## 15. 未来扩展方向（不影响现有 MVP）

| 想加什么           | 怎么加                                                           | 是否影响现有 API              |
| -------------- | ------------------------------------------------------------- | ----------------------- |
| 用户自建 context   | 加 `POST /context` 路由 + Web 表单                                 | ❌ 现有字段不变                |
| LLM 增强 summary | 在 `_build_summary()` 里加可选分支，读 `os.environ` 里的 key；缺 key 时回退模板 | ❌                       |
| 中文 / 日文支持      | tokenizer 换 jieba 或 fugashi，stopwords / filler 表替换            | ❌（语言切换在前端）              |
| 词频排序换 TF-IDF   | 替换 `_extract_keywords()` 内部实现                                 | ❌                       |
| 多用户            | 加 `users` 表 + `review_items.user_id`                          | 接口要加 token，会变           |
| 云部署            | SQLite 换 PostgreSQL，加 Docker                                  | 中等改动                    |
| 真实语音输入         | 在 Web 接 Web Speech API；CYD 接 INMP441 mic + 云 ASR              | 不改后端，只多一个 transcript 来源 |

---

## 16. 给别人讲产品时的一句话总结

> **Scene Words** 是一个把「用户当下处于的语言场景」识别出来、再围绕这个场景给出 keywords / phrases / summary 三类学习材料的轻量产品。它由 **FastAPI + SQLite + 规则化 NLP** 的本地后端、**零框架的 Web Input / Dashboard**、以及一块跑着 **MicroPython + LVGL 9** 的 **CYD** 嵌入式屏幕组成；三端通过 6 个 HTTP 接口 (`/`, `/contexts`, `/context/{id}`, `/analyze_text`, `/save_item`, `/dashboard`) 对话，全程离线可演示，4 段固定 demo 文本的分类置信度在 0.81–0.95 之间。
