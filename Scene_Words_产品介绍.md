# Scene Words 产品介绍

> 一份用来给别人讲清楚 **Scene Words** 这款产品的中文说明文档。
> 所有专有名词、字段名、接口路径、按钮文案、文件名都保留英文原文，方便你在演示时直接对照代码或屏幕。
>
> **重点章节**：
> - [§9 Web 前端 — 每个 section 的每个功能](#9-web-前端--每个-section-的每个功能)
> - [§10 CYD 嵌入式屏幕 — 每个页面的每个功能](#10-cyd-嵌入式屏幕--每个页面的每个功能)

---

## 1. 一句话定位

**Scene Words** 是一个 **context-based language learning**（基于场景的语言学习）的 MVP 产品。它会接收用户的一段英文输入（打字或语音转写），用本地 NLP 流水线识别出说话所处的「场景」（context），抽取这段话里值得学的 **keywords** 和 **phrases**，并把它们保存到一个可在 **Web Dashboard** 与 **CYD 嵌入式屏幕** 上查看的复习库里。

整个产品 **完全离线可用**：没有网络、没有 LLM API key、也没有云服务依赖，只靠本地 Python 标准库 + 一个 SQLite 文件就能完整跑通。

---

## 2. 产品由哪几条线组成

| 线 | 负责什么 | 主要技术 |
| --- | --- | --- |
| **Line A — Backend / NLP / SQLite** | FastAPI 路由、规则化 NLP、SQLite 持久化 | Python 3, FastAPI, Uvicorn, Pydantic v2, SQLite |
| **Line B — Web Input / Web Dashboard** | 浏览器输入页 + 网页版 Dashboard fallback | 原生 HTML / CSS / JavaScript（无框架） |
| **Line C — CYD LVGL Display** | 烧在 ESP32 「**CYD (Cheap Yellow Display)**」上的 LVGL UI | MicroPython, LVGL 9, ILI9341, XPT2046 |

三条线之间只通过 **HTTP + JSON** 通信，互不依赖具体实现。

---

## 3. 端到端数据流

```
Web Input  /  CYD touch
        │
        ▼
   POST /analyze_text  ─────►  FastAPI (backend/main.py)
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
   JSON response  ─────►  浏览器 / CYD 渲染
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

---

## 4. 四个内置场景（seed contexts）

`backend/seed_data.json` 里写死的 4 个 context，分两类。

### 4.1 Real-world 场景

| id | title | seed_keywords（节选） | seed_phrases |
| --- | --- | --- | --- |
| `coffee_shop` | **Coffee Shop** | `coffee`, `latte`, `tea`, `milk`, `order`, `menu`, `cash`, `card`, `receipt`, `takeaway`, `size`, `drink` | `can i get`, `how much is`, `for here`, `to go`, `with milk` |
| `doctor_pharmacy` | **Doctor / Pharmacy** | `doctor`, `pharmacy`, `medicine`, `pain`, `cough`, `fever`, `symptom`, `tablet`, `prescription`, `appointment`, `headache` | `i have a`, `how long`, `take this`, `twice a day`, `make an appointment` |

### 4.2 Story 场景

| id | title | seed_keywords（节选） | seed_phrases |
| --- | --- | --- | --- |
| `kings_cross` | **Harry Potter - King's Cross** | `train`, `station`, `platform`, `ticket`, `luggage`, `magic`, `school`, `journey`, `king`, `cross`, `wizard` | `which platform`, `catch the train`, `lost my ticket`, `magic school`, `king's cross` |
| `baker_street` | **Sherlock Holmes - Baker Street** | `detective`, `clue`, `case`, `client`, `mystery`, `observe`, `evidence`, `london`, `baker`, `street`, `investigate` | `tell me everything`, `what happened`, `look for clues`, `solve the case`, `baker street` |

---

## 5. NLP 流水线（5 步规则化）

文件：`backend/nlp_engine.py`，入口 `analyze_text(raw_text, source_type, optional_context, contexts)`。

```
raw_text
   │
   ▼
[1] _tokenize             正则 [a-zA-Z][a-zA-Z']* 切词，统一小写
   │
   ▼
[2] _clean_tokens         去 STOPWORDS / FILLER_WORDS / 连续重复词
   │
   ▼
[3] _extract_keywords     Counter 词频，长度 > 2 的词参与，最多 5 个
   │
   ▼
[4] _classify_context     与每个 context 的 seed_keywords + title + tag 打分
                          得分最高 → detected_context
                          confidence = min(0.95, 0.45 + best_score * 0.12)
   │
   ▼
[5] _extract_phrases      优先匹配 detected_context.seed_phrases
                          再从 token 拼 3 词短语，凑不够拼 2 词，最多 3 个
   │
   ▼
_build_summary            模板拼一句："This looks like {title}: focus on {top3} and practice phrases like '{first}'."
```

---

## 6. 后端 6 个 API

文件：`backend/main.py`，FastAPI app 名为 **Scene Words API**。

### 6.1 `GET /` — 健康检查

返回：`{"status": "ok", "service": "Scene Words API"}`。任何客户端用来 ping 后端是否起来。

### 6.2 `GET /contexts` — 拉所有场景

返回按 `real_world` / `story` 分两组的数组。Web 端 `loadContexts()` 启动时调一次，渲染 Optional Context select；CYD 端 `fetch_contexts()` 在 Context Select 页用。

### 6.3 `GET /context/{context_id}` — 拉单个场景

返回单个场景卡片（含 `title`, `tag`, `summary`, `seed_keywords`, `seed_phrases`）。CYD 的 Insight View 在真实 API 模式下用，找不到时返回 404。

### 6.4 `POST /analyze_text` — 核心分析入口

请求体：

```json
{
  "raw_text": "...",                    // 必填，自动 strip
  "source_type": "real-world" | "story",
  "optional_context": null | "coffee_shop" | ... // 可选，指定后跳过自动分类
}
```

返回完整分析结果，包含 `cleaned_text` / `keywords` / `phrases` / `detected_context` / `summary` / `suggested_review_items`，并在 SQLite `analysis_results` 表落盘。

### 6.5 `POST /save_item` — 保存复习项

请求体：

```json
{
  "item_text": "latte",
  "item_type": "word" | "phrase",
  "source_context": "coffee_shop"        // 可选
}
```

写入 `review_items` 表，返回 `{"id": <int>, "saved": true}`。

### 6.6 `GET /dashboard` — 复习汇总

返回 `saved_words` / `saved_phrases`（按 item_text 去重，最多 20 条）/ `top_context` / `recent_keywords`（去重，最多 10 个）/ `review_today`（当天保存数）。Web Dashboard 与 CYD Dashboard 共用同一接口，**这是 Web ↔ CYD 双向同步的唯一同步点**。

---

## 7. 数据库（3 张表）

```sql
contexts            -- 4 个固定场景，从 seed_data.json 同步
analysis_results    -- 每次 POST /analyze_text 留底
review_items        -- 用户点 Save 保存的复习项（item_type ∈ word / phrase）
```

---

## 8. 现场启动方式

```powershell
# 1. 启动后端
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 2. 双击打开 web/index.html（或 start web/index.html）

# 3. CYD 上电 → 自动跑 :main.py（mock 模式），屏幕显示 Scene Words Home
```

---

## 9. Web 前端 — 每个 section 的每个功能

文件：[web/index.html](web/index.html)，单文件零框架页面。脚本顶部 `const API_BASE = "http://localhost:8000"` 是唯一的后端地址配置点。

页面整体分 **5 个编号 section**，每个 section 的右上角都有一个 `status` 小字，会随交互变成 `success`（绿）或 `error`（红）。

---

### 9.1 Section 1 — Source / Context（场景选择）

**目的**：让用户告诉后端「我说的话发生在什么场合」，可以全自动也可以手动指定。

| 控件 | 真实文案 / 默认值 | 行为 |
| --- | --- | --- |
| `Source select` 下拉 | 选项：`Real-world` / `Story`，默认 `Real-world` | 切换时触发 `renderContextOptions()`，重新填充下方的 Optional Context select |
| `Optional Context select` 下拉 | 默认第一项 `Auto detect`，下方是当前 source 对应的 context titles | 选 `Auto detect` → 后端自动分类；选具体 context（例如 `Coffee Shop`）→ `optional_context` 字段直接传 id，后端跳过自动分类 |
| 右上角状态 `contextStatus` | 启动时显示 `Loading contexts...` | 加载成功 → `Contexts loaded.`（绿）；失败 → `Could not load contexts: <error>`（红） |

**幕后调用**：页面加载时立即调 `loadContexts()` → `GET /contexts`，把返回结果分成 `real_world` / `story` 两组缓存到 `contextGroups`，再渲染下拉。**网络失败时**两个数组都置空，下拉里只剩 `Auto detect`，但页面其余功能仍可用（分析时 `optional_context` 传 `null`）。

---

### 9.2 Section 2 — Text Input（文本输入）

**目的**：让用户把要分析的英文粘进来，并提供一键 demo 按钮免去打字。

| 控件 | 真实文案 / 默认值 | 行为 |
| --- | --- | --- |
| `Typed Text / Transcript` textarea | 默认值：`Hi, can I get a latte with milk to go? How much is the large size?` | 用户可自由编辑，`Analyze Text` 时取 `value.trim()` |
| Demo 按钮 ① | `Coffee Shop` | 一键填入 source=`real-world` + 上面的咖啡店 demo 文本 |
| Demo 按钮 ② | `Doctor / Pharmacy` | 一键填入 source=`real-world` + `I have a headache and a cough. Do I need medicine from the pharmacy?` |
| Demo 按钮 ③ | `King's Cross` | 一键填入 source=`story` + `Which platform should I use to catch the train to the magic school at King's Cross?` |
| Demo 按钮 ④ | `Baker Street` | 一键填入 source=`story` + `The detective found a clue on Baker Street and tried to solve the case.` |
| 主按钮 | `Analyze Text` | 触发 `analyzeText()`，按钮 disable 防重复点击，结束后恢复 |
| 右上角状态 `analysisStatus` | 默认 `Waiting for input.` | 分析中 `Analyzing...` → 完成 `Analysis complete.`（绿）/ 失败 `Could not analyze text: <error>`（红） |

**Demo 按钮的细节**：每个按钮通过 HTML `data-demo="coffee|pharmacy|kings|baker"` 属性绑定。点击后 `useDemoInput()` 会同步把 source dropdown 切到对应类型，并把 Optional Context 重置为 `Auto detect`，让评委一键切换 demo。

**校验**：textarea 为空时直接弹红色 status，**不发请求**。

---

### 9.3 Section 3 — Analysis Result（分析结果）

**目的**：把后端 `/analyze_text` 返回的 JSON 翻译成 5 个面板，一眼看完。

分析未完成时只显示一个 `Detected Context` 占位面板，文字 `Analyze text to see the detected context, keywords, phrases, and summary.`

完成后展开 5 个面板：

| 面板 | 真实标题 | 内容 |
| --- | --- | --- |
| ① | `Detected Context`（宽面板） | 大字 `detectedContext.title`（例如 `Coffee Shop`），下方一行小灰字：`<id> · <type> · <confidence>% confidence`（例如 `coffee_shop · real-world · 81% confidence`） |
| ② | `Top Keywords` | `result.keywords` 渲染成绿色 chip；空时显示 `No items returned.` |
| ③ | `Useful Phrases` | `result.phrases` 渲染成另一种 chip（`chip phrase`，颜色与 word 区分） |
| ④ | `Context Summary`（宽面板） | `result.summary`（模板生成的一句话学习建议）；缺失时回退 `detectedContext.summary` |
| ⑤ | `Suggested Review Items`（宽面板） | `result.suggested_review_items`（前 3 个 keyword + 前 2 个 phrase）chip 列表 |

**额外功能**：底部有一个 `<details>` 折叠 `Debug raw analysis JSON`，展开后显示原始返回 JSON（缩进 2 空格），方便联调和答辩时给评委看「后端到底返回了啥」。

**置信度计算位**：`Math.round(detected_context.confidence * 100)`，把 `0.81` 显示成 `81% confidence`，更直观。

---

### 9.4 Section 4 — Save Buttons（保存按钮）

**目的**：让用户把刚才识别出的词和短语一键加入复习库。

| 控件 | 文案模板 | 行为 |
| --- | --- | --- |
| 保存按钮（自动生成） | `Save Word: <keyword>` 或 `Save Phrase: <phrase>` | 点击后按钮立即 disable，发 `POST /save_item`，传 `item_text` / `item_type` / `source_context`（取自 detectedContext.id） |
| 右上角状态 `saveStatus` | 分析前 `Analyze text before saving review items.` | 分析后 `Choose a word or phrase to save.`；保存中 `Saving <type>: <item>...`；成功 `Saved <type>: <item>`（绿）；失败 `Could not save item: <error>`（红） |

**自动渲染规则**：`renderSaveButtons()` 取 `keywords` 前 6 个生成 word 按钮、`phrases` 前 6 个生成 phrase 按钮，**用 `Set` 去重避免同一文案出现两次**。

**保存成功后**：自动调 `loadDashboard()` 刷新 Section 5 的 Web Dashboard，让用户立刻看到自己刚保存的内容出现在 dashboard 上 —— 这是给评委看「闭环」的最佳时机。

**没有可保存项时**：状态行变成 `No keywords or phrases available to save.`，按钮区显示 `No save buttons available.`，按钮不渲染，避免误点。

---

### 9.5 Section 5 — Web Dashboard（复习页 / fallback Dashboard）

**目的**：作为 CYD 屏幕的网页镜像，让评委即使不看 CYD 也能看到完整复习状态。

| 控件 | 真实文案 | 行为 |
| --- | --- | --- |
| 主按钮 | `Refresh Dashboard` | 触发 `loadDashboard()`，发 `GET /dashboard`，按钮 disable 防重复点击 |
| 右上角状态 `dashboardStatus` | 默认 `Dashboard not loaded yet.` | 加载中 `Loading dashboard...` → 成功 `Dashboard loaded.`（绿）/ 失败 `Could not load dashboard: <error>`（红） |

加载完成后渲染 5 个面板：

| 面板 | 真实标题 | 内容 |
| --- | --- | --- |
| ① | `Review Today` | 大数字 `dashboard.review_today`（当天保存了多少条复习项） |
| ② | `Top Context` | 大字显示出现频次最高的 context id（例如 `coffee_shop`）；空时 `None yet` |
| ③ | `Saved Words` | `<ul>` 列表：`item_text` 加粗 + `source_context` 小灰字；空时 `No saved items yet.` |
| ④ | `Saved Phrases` | 同上结构 |
| ⑤ | `Recent Keywords`（宽面板） | 最近 10 次分析的 keyword 去重后 chip 化 |

**额外功能**：底部 `<details>` 折叠 `Debug raw dashboard JSON`，展开看原始 dashboard JSON。

**网络失败时**：整个面板区被替换成红色错误提示，**不会清掉之前的数据缓存**，再次点击 Refresh 即可恢复。

---

### 9.6 全局行为补充

- **跨域**：后端开了 `CORSMiddleware allow_origins=["*"]`，所以页面用 `file://` 协议直接打开也能正常发请求，**不需要本地 HTTP server**。
- **错误显示**：所有 `parseJsonResponse()` 失败统一抛 `HTTP <status>: <detail>`，前端 status 行直接显示，便于现场快速排错。
- **HTML 转义**：所有动态文本都过 `escapeHtml()`，避免 demo 文本里的 `'` `<` 等字符破坏布局。

---

## 10. CYD 嵌入式屏幕 — 每个页面的每个功能

文件：[lvgl9_firmwares/scenelingo_dashboard.py](lvgl9_firmwares/scenelingo_dashboard.py)，约 950 行，运行在 ESP32 + ILI9341（240×320）+ XPT2046 触摸 上。

### 10.0 全局元素与运行模式

| 项 | 说明 |
| --- | --- |
| 屏幕尺寸 | 240×320 (`_DISPLAY_WIDTH × _DISPLAY_HEIGHT`)，竖屏 |
| 通用按钮 | `add_button(parent, text, y, cb, width, height, x_ofs)`，最小高度 26–48px，保证手指可点中 |
| 路由栈 | `screen_history`（list），`go_to(route, arg)` 入栈，`go_back()` 弹栈，栈空时回 Home |
| 模式开关 | `USE_MOCK_DATA` 控制走 mock 还是发 HTTP；`AUTO_CONNECT_WIFI` 控制是否启动时连 Wi-Fi |
| 显示规则常量 | `_C12_MAX_KW=5` / `_C12_MAX_PH=3` / `_C12_MAX_WORDS=5` / `_C12_KW_CHARS=14` / `_C12_PH_CHARS=30` / `_C12_SUM_CHARS=48` / `_C12_LABEL_CHARS=40`，统一截断防止小屏挤爆 |

CYD 总共 **4 个屏幕**：Home → Context Select → Insight View → Dashboard（其中 Context Select 是 Home 的子页，外部介绍时常和 Home 合并讲）。

---

### 10.1 Home 页（`_render_home()`）

**入口**：上电后 `main()` 直接调 `show_home()`。

**屏幕从上到下的元素**：

| y 坐标 | 元素 | 真实文案 | 行为 |
| --- | --- | --- | --- |
| 顶部 | 主标题 `add_title` | **Scene Words** | 静态显示，居中大字 |
| 46 | 副标题 `add_label` | `Learn English in Context` | 灰色小字 `#8899AA`，纯展示 |
| 86 | 按钮 ① | `Real-world` | 点击 → `go_to("context_select", "real-world")`，进入 Real-world 场景列表 |
| 146 | 按钮 ② | `Story` | 点击 → `go_to("context_select", "story")`，进入 Story 场景列表 |
| 206 | 按钮 ③ | `Dashboard` | 点击 → `go_to("dashboard")`，跳过 Context Select 直达复习页 |
| 268 | 模式标签 | `Mock` 或 `API <ip>:<port>`（例如 `API 192.168.137.1:8000`） | 静态显示，**让人一眼看出当前 CYD 是 mock 还是连了真后端** |

按钮间距 56px，确保电阻屏触摸不会误点相邻按钮。

---

### 10.2 Context Select 页（`_render_context_select(source_type)`）

**入口**：从 Home 点 `Real-world` 或 `Story` 进来。`source_type` 由调用方传入并写入全局 `current_source_type`。

**屏幕从上到下的元素**：

| y 坐标 | 元素 | 真实文案 | 行为 |
| --- | --- | --- | --- |
| 顶部 | 主标题 | `Real-world` 或 `Story`（由 `_SOURCE_TYPE_LABELS` 映射） | 让用户清楚自己在哪一层 |
| 46 | 副标题 | `Select a context` | 灰色小字提示操作 |
| 84 起 | context 按钮（最多 4 个，间距 64px，宽 210px、高 48px） | 来自 `fetch_contexts()`，例如 `Coffee Shop` / `Doctor / Pharmacy`（real-world）或 `King's Cross` / `Baker Street`（story） | 点击 → `open_context(context_id)` → 调 `fetch_context(id)` 拿场景详情 → `go_to("insight", data)` |
| 270 | 按钮 | `Back` | 点击 → `go_back()`，弹栈回到 Home |

**数据来源 fallback**：`fetch_contexts()` 在真实 API 失败时会自动用 `MOCK_CONTEXTS`，每类各 2 个固定 context，所以**网络断了页面也照样能用**。

**lambda 闭包陷阱防御**：每个按钮的回调都用 `lambda context_id=context_id:` 默认参数捕获 id，避免 4 个按钮全都跳到同一个 context（这是 Python 闭包常见坑）。

---

### 10.3 Insight View 页（`_render_insight(data)`）

**入口**：从 Context Select 点任一 context 后进来，`data` 是该场景对应的分析结果（mock 模式来自 `MOCK_ANALYSES[ctx_id]`，真实模式来自 `POST /analyze_text` 返回）。

**屏幕从上到下的元素**：

| 元素 | 真实文案 | 行为 |
| --- | --- | --- |
| 主标题 | context 名称（例如 `Coffee Shop`） | 取自 `data.detected_context.title` |
| 区块标题 | `Top Keywords`（灰色小字） | 静态展示 |
| Keyword 按钮组 | 最多 5 个（`_C12_MAX_KW`），每个文本截断到 14 字符，2 列布局：偶数索引左列 `x=-59`、奇数索引右列 `x=+59`，按钮 108×26 px | 点击 → `handle_save(kw, "word", context_id)` → `save_item()` 发 `POST /save_item` |
| 区块标题 | `Useful Phrases`（灰色小字） | 静态展示 |
| Phrase 按钮组 | 最多 3 个（`_C12_MAX_PH`），全宽 210×26 px，文本截断到 30 字符 | 点击 → `handle_save(ph, "phrase", context_id)` |
| Summary 标签 | 取 `summary` 第一句、截断 48 字符（例如 `This looks like Coffee Shop. Focus on latte, milk, size`） | 静态展示，节省纵向空间 |
| 状态标签 `status_label` | 默认空 | 保存后变成 `Saved: <item 前12字符>` 或 `Save failed` 或 `Nothing to save` |
| 按钮 | `Back` | 点击 → `go_back()` 回到 Context Select |

**保存逻辑（`handle_save()`）**：

- 空文本直接显示 `Nothing to save`，**不发请求**
- 真实模式发 `POST /save_item`；mock 模式直接返回 `{"saved": True, "mock": True}` 并把数据塞进 `MOCK_DASHBOARD` 的 `saved_words` / `saved_phrases`，**让 mock 模式下点保存也能立刻在 Dashboard 看见**
- 整个流程任何异常都不会让页面崩溃，只在 status 行显示 `Save failed`

**没有 PSRAM 的小屏适配**：所有截断长度都从文件顶部 `_C12_*` 常量读取，调一行就能整体收紧/放宽布局。

---

### 10.4 Dashboard 页（`_render_dashboard()`）

**入口**：从 Home 点 `Dashboard` 直达，或从其他页 `go_back()` 间接跳回。

**数据获取**：调 `fetch_dashboard()`，真实模式发 `GET /dashboard`，失败时**自动 fallback 到 `MOCK_DASHBOARD`**，保证页面不黑屏。

**屏幕从上到下的元素**：

| y 坐标 | 元素 | 真实文案 | 行为 |
| --- | --- | --- | --- |
| 顶部 | 主标题 | `Dashboard` | 静态 |
| 36 | 区块标题 | `Saved Words`（灰色小字） | 静态 |
| 55 | 内容标签 | 把 `saved_words[:5]` 的 `item_text` 用 `, ` 拼接，截断到 40 字符（例如 `latte, milk, platform`），空时 `None yet` | 静态展示 |
| 92 | 区块标题 | `Saved Phrases`（灰色小字） | 静态 |
| 111 | 内容标签 | 同上结构，取 `saved_phrases[:3]` | 静态 |
| 148 | 标签 | `Top: <context_id>`（例如 `Top: coffee_shop`，截断到 24 字符） | 显示出现频次最高的场景 |
| 174 | 标签 | `Review Today: <n>`（例如 `Review Today: 3`） | 显示当天保存条数 |
| 200 | 数据源标签 | `mock` 或 `live`（灰色小字） | **现场答辩的关键提示**：`live` 表示 CYD 真的连到了后端 |
| 222 左 | 按钮 | `Refresh` | 点击 → 重新调 `_render_dashboard()`，再次拉 `/dashboard` |
| 222 右 | 按钮 | `Back` | 点击 → `go_back()`，回到上一页 |

**Refresh 的妙处**：复用整个 render 函数，不做局部更新，**实现简单且不会出现部分失败的中间态**。Web 端保存一个新词后，CYD 点 Refresh 立刻能看到 —— 这就是「Web ↔ CYD 双向同步」的演示路径。

---

### 10.5 CYD 启动顺序（`main()`）

```python
gc.collect()
init_display()           # LVGL 显示初始化
if AUTO_CONNECT_WIFI:    # 默认 False，跳过
    connect_wifi()
    if not USE_MOCK_DATA:
        probe_api()      # 发 GET /dashboard 验证后端可达
show_home()              # 进 Home 页等待用户操作
```

**默认走 mock**：`USE_MOCK_DATA = True` + `AUTO_CONNECT_WIFI = False`，所以上电几秒内就能看到 Home 页。要切真实 API 只需改 4 行配置（`API_BASE` / `WIFI_SSID` / `WIFI_PASSWORD` / 两个开关翻转），不动任何 UI 代码。

---

## 11. 技术栈总览

| 层 | 选用 | 为什么 |
| --- | --- | --- |
| 语言 | Python 3 | 团队熟、NLP 标准库够用 |
| Web 框架 | **FastAPI** | 自动 OpenAPI、Pydantic 校验 |
| ASGI server | **Uvicorn** | FastAPI 官方推荐 |
| 校验 | **Pydantic v2** | `field_validator` 自动裁剪空白 |
| 数据库 | **SQLite** | 单文件、零配置、随代码分发 |
| NLP | 标准库 + 规则 (`re`, `Counter`) | 离线、可解释、可调 |
| 跨域 | `CORSMiddleware` `allow_origins=["*"]` | 局域网联调阶段 Web / CYD / 手机共用 |
| 嵌入式 UI | **MicroPython + LVGL 9** | ESP32 上跑出现代 GUI |

`requirements.txt` 只有 `fastapi`、`uvicorn`、`pydantic` 三条核心依赖。

---

## 12. 自测脚本

| 命令 | 作用 |
| --- | --- |
| `python -m backend.selftest` | 编译 + seed + DB + NLP + Dashboard 形状自测，**无副作用** |
| `python -m backend.demo_check` | 跑 4 段 demo 文本，断言命中预期 context |
| `python -m backend.web_smoke` | 模拟 Web 闭环 |
| `python -m backend.cyd_smoke` | 模拟 CYD 闭环（含 Web ↔ CYD 双向同步校验） |

---

## 13. Demo 文本（已验收）

| # | 标签 | 文本 | 期望 detected_context | 实测 confidence |
| --- | --- | --- | --- | --- |
| 1 | Coffee Shop | `Hi, can I get a latte with milk to go? How much is the large size?` | `coffee_shop` | **0.81** |
| 2 | Doctor / Pharmacy | `I have a headache and a cough. Do I need medicine from the pharmacy?` | `doctor_pharmacy` | **0.93** |
| 3 | King's Cross | `Which platform should I use to catch the train to the magic school at King's Cross?` | `kings_cross` | **0.95** |
| 4 | Baker Street | `The detective found a clue on Baker Street and tried to solve the case.` | `baker_street` | **0.95** |

---

## 14. 项目目录速查

```
hackathon/
├─ backend/
│  ├─ main.py              FastAPI 路由 + Pydantic 模型 (AnalyzeTextRequest, SaveItemRequest)
│  ├─ nlp_engine.py        analyze_text 主管线
│  ├─ database.py          init_db / list_contexts / insert_analysis / save_review_item / get_dashboard
│  ├─ seed_data.json       4 个 MVP context
│  ├─ selftest.py / web_smoke.py / cyd_smoke.py / demo_check.py   自测脚本
├─ web/
│  └─ index.html           Web Input + Web Dashboard 单文件页
├─ lvgl9_firmwares/
│  ├─ scenelingo_dashboard.py     CYD 主程序（Home / Context Select / Insight / Dashboard）
│  └─ lvgl9_3_micropython_cyd.bin LVGL 9 + MicroPython 固件
├─ docs/
│  ├─ LINE_A/LINE_A_PRESENTATION.md   Line A 答辩稿
│  └─ INTEGRATION_RECORD.md           三线合并 + CYD 部署记录
├─ requirements.txt
└─ scenelingo.db           启动时自动生成
```

---

## 15. 一句话总结

> **Scene Words** 用 **FastAPI + SQLite + 规则化 NLP** 的本地后端识别用户当下处于的语言场景，提取 keywords / phrases / summary 三类学习材料；**零框架的 Web 页面** 提供完整输入与 Dashboard 闭环；**MicroPython + LVGL 9 的 CYD 屏幕** 用 4 个页面（Home / Context Select / Insight View / Dashboard）展示同一份产品形态。三端通过 6 个 HTTP 接口 (`/`, `/contexts`, `/context/{id}`, `/analyze_text`, `/save_item`, `/dashboard`) 对话，**全程离线可演示**，4 段固定 demo 文本的分类置信度在 0.81–0.95 之间。
