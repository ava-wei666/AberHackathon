# LINE_A 答辩说明（后端 / NLP / 数据库）

这份文档用来在答辩或评审时给老师讲清楚 SceneLingo 项目里 **线 A** 的工作：做了什么、为什么这么选、怎么演示、未来怎么扩展。可以直接照着念，也可以挑表格回答提问。

## 一句话定位

> 线 A 是 SceneLingo 的后端，负责接收一段英文文本，做轻量 NLP 分析，把结果保存到本地 SQLite，再通过统一 HTTP API 给网页端（线 B）和 CYD 嵌入式屏幕（线 C）使用。

整个 demo 没有任何外部网络依赖：没网、没 LLM API key 也能完整跑通。

## 项目分工

```
线 A：Backend + NLP + SQLite          ← 本文档负责说清这一条
线 B：Web Input + Web Dashboard
线 C：CYD LVGL Display + Hardware Integration
```

线 A 的边界很明确：

- **做**：FastAPI 路由、文本分析规则、数据库读写、给线 B / 线 C 提供稳定接口。
- **不做**：网页页面、CYD LVGL UI、用户登录、云部署、LLM 强依赖。

## 端到端数据流

```
Web 输入 / CYD 触发
        │
        ▼
  POST /analyze_text  ── (FastAPI 路由层 main.py)
        │
        ▼
  nlp_engine.analyze_text()  ── 清洗 → 关键词 → 短语 → 分类 → 总结
        │
        ▼
  database.insert_analysis() ── SQLite 持久化
        │
        ▼
  返回 JSON 给前端
        │
        ▼
  用户点 Save → POST /save_item → SQLite review_items 表
        │
        ▼
  GET /dashboard ── 给 CYD / 网页 dashboard 渲染复习数据
```

## 技术栈与选型理由

线 A 的核心原则：**hackathon 现场不出意外**。所有选型都围绕"少装东西、稳、能离线演示"展开。

| 层        | 选用                                                                             | 为什么                                                        | 没用什么 / 为什么不用                                                                |
| -------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------- | --------------------------------------------------------------------------- |
| 语言       | **Python 3**                                                                   | 团队都熟、NLP 标准库够用、跨平台                                         | 不用 Node.js / Go：会让另两条线（Web、CYD）调试成本上升                                       |
| Web 框架   | **FastAPI**                                                                    | 自动生成 OpenAPI 文档、Pydantic 校验请求/响应、原生 `async`、性能足够 hackathon | 不用 Flask：缺少类型校验和文档生成；不用 Django：体量过大，引入 ORM、admin、模板等用不到的东西                  |
| ASGI 服务器 | **Uvicorn**                                                                    | FastAPI 官方推荐、`--reload` 方便开发、单条命令启动                        | 不用 Gunicorn：多进程模型对 SQLite 反而有锁竞争；hackathon 不需要负载均衡                          |
| 数据校验     | **Pydantic v2**                                                                | 请求模型自带 `field_validator`，例如自动裁剪空白、空字符串归一化为 `null`，比手写校验更安全 | 不用 marshmallow / dataclasses：FastAPI 已与 Pydantic 深度集成                       |
| 数据库      | **SQLite**（标准库 `sqlite3`）                                                      | 单文件 `scenelingo.db`，零配置、可跟代码一起分发、关闭后端就能复制带走、足够 demo 量级     | 不用 PostgreSQL / MySQL：要装服务、要配账号、断网会挂；不用 MongoDB：本项目数据完全是结构化的                |
| NLP      | **Python 标准库 + 规则**（`re`、`collections.Counter`）                                | 离线、可解释、可调；评委问"为什么这个词被选中"我们能直接指到代码                          | 不用 spaCy / NLTK：需要下载语言模型，hackathon 现场带宽不可控；不用 LLM API：网络依赖、有 token 成本、回答不稳定 |
| 跨域       | **FastAPI CORSMiddleware**，`allow_origins=["*"]`                               | hackathon 局域网联调阶段允许手机、CYD、电脑共用同一后端                         | 生产环境会改白名单，MVP 阶段不收紧                                                         |
| 数据格式     | **JSON**                                                                       | API、配置、seed 数据全用 JSON                                      | 不用 YAML / XML：减少依赖                                                          |
| 自测       | 自己写的 `backend/selftest.py` + `web_smoke.py` + `cyd_smoke.py` + `demo_check.py` | 一条命令完成离线 / Web / CYD / Demo 文本四种自测，失败时退出码非 0               | 不用 pytest：只为答辩多装一个框架不划算，标准库 `assert` 够用                                     |

**一句话总结技术栈**：

> Python + FastAPI + Uvicorn + Pydantic + SQLite + 标准库规则 NLP + JSON。**全部依赖只有 `requirements.txt` 里 3 行**，零外部服务、零云、零 LLM key。

## 项目文件清单

```
backend/
  __init__.py          # 仅作为包标记
  main.py              # FastAPI 路由 + Pydantic 请求模型
  nlp_engine.py        # 文本清洗 / 关键词 / 短语 / 情境分类 / 总结
  database.py          # SQLite 建表 / seed 同步 / dashboard 汇总
  seed_data.json       # 4 个 MVP context 的固定数据
  selftest.py          # 一键离线自测脚本（A14）
  web_smoke.py         # 模拟网页闭环冒烟（A15）
  cyd_smoke.py         # 模拟 CYD 闭环冒烟（A16，含双向同步校验）
  demo_check.py        # 4 段 demo 文本验收（A17）
requirements.txt       # fastapi、uvicorn、pydantic 三个依赖
scenelingo.db          # 运行后自动生成，不进 git
docs/
  LINE_A_BACKEND_TASKS.md  # 线 A 任务书（A0–A17）
  LINE_A_A0_A1_STEPS.md    # 各阶段操作记录
  LINE_A_A2_STEPS.md
  ...
  LINE_A_A17_STEPS.md
  LINE_A_PRESENTATION.md   # 本文档
```

## API 合约（6 个接口）

| Method | Path            | 用途                                                                       | 谁在调                        |
| ------ | --------------- | ------------------------------------------------------------------------ | -------------------------- |
| `GET`  | `/`             | 健康检查                                                                     | 任何人                        |
| `GET`  | `/contexts`     | 拉 4 个 context，分 `real_world` / `story` 两组                                | 线 B、线 C                    |
| `GET`  | `/context/{id}` | 拿单个场景卡片（标题、关键词、短语、摘要）                                                    | 线 C 的 Insight View         |
| `POST` | `/analyze_text` | **核心**：文本进 → JSON 分析结果出                                                  | 线 B 网页                     |
| `POST` | `/save_item`    | 保存复习项（word / phrase）                                                     | 线 B、线 C                    |
| `GET`  | `/dashboard`    | 复习页数据：saved_words、saved_phrases、top_context、recent_keywords、review_today | 线 B 网页、线 C 的 CYD Dashboard |

`/analyze_text` 返回的稳定字段：

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
    "summary": "...",
    "confidence": 0.81
  },
  "summary": "This looks like Coffee Shop: focus on get, latte, milk and practice phrases like 'Can I Get'.",
  "suggested_review_items": ["get", "latte", "milk", "Can I Get", "How Much Is"]
}
```

## NLP 管线（5 步规则化）

整个 NLP 流程在 `backend/nlp_engine.py` 里，**一段文本走 5 步**：

1. **Tokenize**：`re` 切英文词，统一小写。
2. **Clean**：去掉 stopwords（`a`、`the`、`to`…）、filler words（`um`、`like`、`okay`…）、连续重复词。
3. **Keyword Extraction**：用 `Counter` 统计词频，长度 ≤ 2 的词不参与，最多返回 5 个。
4. **Context Classification**：把清洗后的 token 与 4 个 context 的 `seed_keywords` 做匹配打分，得分最高的胜出；如果用户在网页里手动选了 context，就跳过自动分类。
5. **Phrase Extraction**：先匹配当前 context 的 `seed_phrases`，再从 token 里拼 3 词短语，凑不够再拼 2 词，最多返回 3 个。

最后一步是 `_build_summary()`，用模板拼出 1 句话的学习建议（不依赖任何模型）。

**为什么走规则不走模型**：

- 评委可以追溯每一个 keyword / phrase 的出处（看代码就懂）。
- 没有"幻觉"，输出可预测。
- 完全离线。
- 调整规则只需改 `seed_data.json`（不需要重新训练）。

## 数据库 Schema

`scenelingo.db` 只有 3 张表：

```sql
contexts (
    id TEXT PRIMARY KEY,           -- coffee_shop / doctor_pharmacy / kings_cross / baker_street
    title TEXT,
    type TEXT,                     -- 'real-world' or 'story'
    tag TEXT,
    summary TEXT,
    seed_keywords_json TEXT,       -- JSON list 字符串
    seed_phrases_json TEXT
);

analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_text TEXT,
    cleaned_text TEXT,
    detected_context TEXT,         -- 命中的 context id
    keywords_json TEXT,
    phrases_json TEXT,
    summary TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_text TEXT,
    item_type TEXT CHECK (item_type IN ('word', 'phrase')),
    source_context TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

3 张表的职责：

- `contexts`：从 `seed_data.json` 同步过来的 4 个固定场景（`ON CONFLICT(id) DO UPDATE`，每次重启自动同步最新 seed）。
- `analysis_results`：每一次 `POST /analyze_text` 留底，用于 `top_context` 和 `recent_keywords` 统计。
- `review_items`：用户点 Save 保存的复习项，给 `dashboard` 提供数据。

## 演示文本（A17 已验收）

| #   | 标签                | 文本                                                                                    | 期望识别              | 实测置信度    |
| --- | ----------------- | ------------------------------------------------------------------------------------- | ----------------- | -------- |
| 1   | Coffee Shop       | `Hi, can I get a latte with milk to go? How much is the large size?`                  | `coffee_shop`     | **0.81** |
| 2   | Doctor / Pharmacy | `I have a headache and a cough. Do I need medicine from the pharmacy?`                | `doctor_pharmacy` | **0.93** |
| 3   | King's Cross      | `Which platform should I use to catch the train to the magic school at King's Cross?` | `kings_cross`     | **0.95** |
| 4   | Baker Street      | `The detective found a clue on Baker Street and tried to solve the case.`             | `baker_street`    | **0.95** |

四段文本都能在 100ms 内完成完整 NLP + 数据库写入。

## 离线 / 鲁棒性证明

线 A 在以下情况都能正常 demo：

| 场景              | 表现                              |
| --------------- | ------------------------------- |
| 没有外网            | ✅ 全部 NLP 走本地规则                  |
| 没有 LLM API key  | ✅ summary 走模板，不调 LLM            |
| 没装 spaCy / NLTK | ✅ 只用标准库                         |
| 数据库被删           | ✅ 重启时自动重建 + 同步 4 个 seed context |
| 端口 8000 被占      | ✅ 一行命令换 `--port 8001` 即可        |
| 第一次启动           | ✅ 自动建表 + 写 seed                 |

## 自测命令

```powershell
# 一键离线自测：编译 + seed + 数据库 + NLP + Dashboard 形状
.\.venv\Scripts\python.exe -m backend.selftest

# 4 段 demo 文本验收
.\.venv\Scripts\python.exe -m backend.demo_check

# 启动后端（局域网监听）
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 模拟网页闭环
.\.venv\Scripts\python.exe -m backend.web_smoke

# 模拟 CYD 闭环（含 Web↔CYD 双向同步校验）
.\.venv\Scripts\python.exe -m backend.cyd_smoke
```

四个脚本都设计成"无副作用"，`selftest` 与 `demo_check` 不写库，可以反复跑。

## 已交付的阶段成果

按 `docs/LINE_A_BACKEND_TASKS.md` 顺序：

| 阶段    | 主题                          | 状态  |
| ----- | --------------------------- | --- |
| A0–A1 | 环境确认 + API 健康检查             | ✅   |
| A2    | 4 个 seed context            | ✅   |
| A3    | SQLite 自动建表 + seed 同步       | ✅   |
| A4    | 文本清洗                        | ✅   |
| A5    | 关键词提取                       | ✅   |
| A6    | 短语提取                        | ✅   |
| A7    | Context 分类                  | ✅   |
| A8    | Summary 生成                  | ✅   |
| A9    | `POST /analyze_text`        | ✅   |
| A10   | `GET /contexts`             | ✅   |
| A11   | `GET /context/{id}` + 局域网联调 | ✅   |
| A12   | `POST /save_item` + 输入校验加固  | ✅   |
| A13   | `GET /dashboard`（去重 / 日期过滤） | ✅   |
| A14   | 离线一键自测脚本                    | ✅   |
| A15   | 给线 B 的联调信息 + Web 闭环冒烟       | ✅   |
| A16   | 给线 C 的 CYD 联调信息 + 双向同步校验    | ✅   |
| A17   | 4 段 Demo 文本最终验收             | ✅   |

每个阶段都有对应的 `docs/LINE_A_A*_STEPS.md` 操作记录，可以现场翻给评委看。

## 未来可扩展点（不影响 MVP）

如果评委问"以后能怎么扩"，回答可以从这里挑：

| 扩展方向           | 怎么接                                                                     | 是否影响现有 API    |
| -------------- | ----------------------------------------------------------------------- | ------------- |
| 用户自建 context   | 加 `POST /context` 路由 + 网页表单                                             | ❌ 现有接口字段不变    |
| LLM 增强 summary | 在 `nlp_engine._build_summary()` 加可选分支，读 `os.environ` 里的 key；没 key 则回退模板 | ❌             |
| 中文 / 日文支持      | tokenizer 换 jieba 或 fugashi，stopwords / filler 表替换                      | ❌（输入语言切换在前端选） |
| 词频排序换 TF-IDF   | 替换 `_extract_keywords()` 内部实现                                           | ❌             |
| 多用户            | 加 `users` 表 + `review_items.user_id`                                    | 接口要加 token，会变 |
| 云部署            | 把 SQLite 换成 PostgreSQL，加 Docker                                         | 中等改动          |

## 评委可能的提问 & 回答方向

**Q：为什么不用 LLM？**\
A：MVP 阶段优先稳定演示。LLM 有网络、token、延迟、可解释性四个不确定性。我们留了接入点，下一步想接的话，只需要在 `_build_summary()` 加一个分支，主管线不变。

**Q：4 个固定 context 是不是太少？**\
A：是 MVP 限定。结构上只是 `seed_data.json` 多写几条的事，数据库 schema 已经是通用的。再加一个 context 只是加 1 个 JSON 对象 + 重启服务。

**Q：分类准确度怎么保证？**\
A：基于 seed_keywords 打分，可解释、可调；当前 4 段 demo 文本置信度 0.81–0.95。如果某个文本被分错，先调 `seed_keywords` / `seed_phrases`，不动主管线代码。

**Q：用 SQLite 不会有并发问题吗？**\
A：单 Uvicorn 进程 + 单文件 SQLite，hackathon demo 量级完全够用。每次连接都用 `with` 包住、显式 commit / rollback / close。要扩到多人并发再换 PostgreSQL。

**Q：怎么保证 Web 和 CYD 数据同步？**\
A：所有数据流过 `GET /dashboard`。Web 保存 → 数据库 → CYD Refresh 拿到；CYD 保存 → 数据库 → Web Refresh 拿到。我们写了 `cyd_smoke.py` 专门跑双向同步断言，已通过。

**Q：测试覆盖怎么样？**\
A：4 个独立脚本：编译 + seed + NLP 形状 + Dashboard 形状（`selftest`）、4 段 demo 文本（`demo_check`）、Web 闭环（`web_smoke`）、CYD 闭环含双向同步（`cyd_smoke`）。任何一项失败退出码非 0。

## 一行命令演示路径

如果只想给评委 30 秒演示线 A，按这个顺序：

```powershell
# 1. 一键自测，证明现有功能正常
.\.venv\Scripts\python.exe -m backend.selftest

# 2. 启动后端
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 3. 在浏览器或 PowerShell 里打 4 段 demo 文本看分类
Invoke-RestMethod -Uri "http://127.0.0.1:8000/dashboard" | ConvertTo-Json -Depth 5
```

或者更简单：网页打开 `web/index.html`，点 Analyze、点 Save、点 Refresh Dashboard，整套闭环 30 秒讲完。

## 结论

线 A 后端已经完成 MVP 的全部功能与接口承诺，技术栈选型围绕"hackathon 现场不出意外"展开：**Python 标准化生态、零外部服务、纯规则 NLP、单文件 SQLite、自带 4 套自测脚本**。线 B 的网页和线 C 的 CYD 都已经按线 A 提供的 API 合约接入并通过双向同步验证。
