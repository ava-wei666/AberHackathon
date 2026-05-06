# Line A 答辩稿（最简版）

> 背稿用，全程约 90 秒。所有英文标识符都是代码里的真实命名。

---

## 开场（一句话定位）

> 「Line A 是 Scene Words 的后端。它负责接收一段英文文本，做轻量 NLP 分析，把结果存到本地 SQLite，再用统一的 HTTP API 给 Web 端和 CYD 屏幕用。**全程离线、不依赖 LLM、不依赖云。**」

---

## 主体（按顺序讲，每点 10–15 秒）

1. **技术栈**：Python 3 + FastAPI + Uvicorn + Pydantic v2 + SQLite。`requirements.txt` 只有三行核心依赖。
2. **NLP 流水线 5 步**：
   `tokenize` → `clean` (去 STOPWORDS / FILLER_WORDS) → `keyword extraction` (Counter 词频) → `context classification` (跟 seed_keywords 打分) → `phrase extraction` (优先匹配 seed_phrases)，最后模板拼一句 summary。
   **走规则不走 LLM，是为了可解释、可追溯、可离线。**
3. **6 个 API**：
   - `GET /`
   - `GET /contexts`
   - `GET /context/{id}`
   - `POST /analyze_text`（核心）
   - `POST /save_item`
   - `GET /dashboard`
4. **3 张表**：
   - `contexts`（4 个 seed 场景）
   - `analysis_results`（每次分析留底）
   - `review_items`（用户保存的 word / phrase）
5. **4 个内置场景**：Coffee Shop、Doctor / Pharmacy、Harry Potter - King's Cross、Sherlock Holmes - Baker Street，两个 real-world、两个 story。
6. **验收成绩**：4 段 demo 文本分类 confidence **0.81–0.95**，全部 100ms 内完成。

---

## 现场演示流程（30 秒）

```powershell
# 1. 一键自测，证明功能完整
python -m backend.selftest

# 2. 启动后端
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 3. 浏览器开 web/index.html → 点 Analyze Text → 点 Save Word/Phrase → 点 Refresh Dashboard
```

---

## 收尾（一句话）

> 「Line A 已经完成 MVP 全部接口承诺。**零外部服务、零云、零 LLM key**。Line B 的网页和 Line C 的 CYD 都已经接入并跑通双向同步校验。」

---

## 评委高频提问（一句话回答）

| Q | A |
| --- | --- |
| 为什么不用 LLM？ | MVP 阶段优先稳定演示。`_build_summary()` 留了接入点，加一行分支即可。 |
| 4 个 context 太少？ | `seed_data.json` 加一条记录、重启即生效，schema 已通用。 |
| SQLite 并发怎么办？ | hackathon 量级单进程足够，每次连接 `with` 包住、显式 commit/close。 |
| 怎么保证 Web 和 CYD 同步？ | 都流过 `GET /dashboard`，`cyd_smoke.py` 跑过双向同步断言。 |
| 测试覆盖怎么样？ | 4 个独立脚本：`selftest` / `demo_check` / `web_smoke` / `cyd_smoke`，任何一个失败退出码非 0。 |
