# SceneLingo 三线并行开发计划

这份文档的目标是让 3 个人可以同时开工：每个人负责一条线，先用固定接口和 mock 数据独立推进，最后再接到同一个 FastAPI 后端上完成 demo 闭环。

## 总体原则

- 先固定 API 合约，再各自开发。
- 每条线都要能单独运行、单独验收。
- 集成前不要互相等待：前端和 CYD 可以先用 mock JSON，后端可以先用 Postman / 浏览器 / Python 命令测试。
- 最终闭环只追求 MVP：Input -> NLP -> Context Tagging -> Dashboard。

## 固定接口合约

这 5 个接口是三条线汇合的边界，尽量不要频繁改字段名。

```text
GET  /
POST /analyze_text
GET  /contexts
GET  /context/{id}
POST /save_item
GET  /dashboard
```

### POST /analyze_text

请求：

```json
{
  "raw_text": "Hi, can I get a latte with milk to go?",
  "source_type": "real-world",
  "optional_context": null
}
```

返回重点字段：

```json
{
  "id": 1,
  "cleaned_text": "hi get latte milk go",
  "keywords": ["get", "latte", "milk"],
  "phrases": ["Can I Get", "get latte milk"],
  "detected_context": {
    "id": "coffee_shop",
    "title": "Coffee Shop",
    "type": "real-world",
    "tag": "coffee shop",
    "confidence": 0.69
  },
  "summary": "This looks like Coffee Shop. Focus on get, latte, milk.",
  "suggested_review_items": ["get", "latte", "milk", "Can I Get"]
}
```

### POST /save_item

请求：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

返回：

```json
{
  "id": 1,
  "saved": true
}
```

## 三条并行线

## 线 A - Backend / NLP / Database

负责人目标：把后端做成稳定中控，保证所有 API 能被 Web 和 CYD 调用。

主要文件：

- `backend/main.py`
- `backend/nlp_engine.py`
- `backend/database.py`
- `backend/seed_data.json`
- `requirements.txt`

独立任务：

- 启动 FastAPI：`uvicorn backend.main:app --reload`
- 完成 `/analyze_text` 的输入校验和返回结构
- 完成 rule-based NLP：cleaning、keywords、phrases、context classification、summary
- 完成 SQLite 表：contexts、analysis_results、review_items
- 完成 `/contexts`、`/context/{id}`、`/save_item`、`/dashboard`
- 准备 4 类 context 的 seed data

单独验收：

- `GET /` 返回 `status: ok`
- coffee shop 文本能识别为 `coffee_shop`
- doctor/pharmacy 文本能识别为 `doctor_pharmacy`
- 保存一个 word 后，`GET /dashboard` 能看到它
- 没有 LLM、没有外网时，核心分析仍然能跑

交付给其他线：

- 后端本地地址，例如 `http://localhost:8000`
- 如果手机或 CYD 访问，需要提供 laptop 局域网 IP，例如 `http://192.168.x.x:8000`
- API 字段名不要临时大改；必须改时同步给线 B 和线 C

## 线 B - Web Input / CYD Display

负责人目标：把用户输入和 CYD dashboard 做出来，先 mock，后接真实 API。

主要文件：

- `web/index.html`
- `lvgl9_firmwares/touch_color_test.py`
- 后续可新增 `lvgl9_firmwares/scenelingo_dashboard.py`

独立任务：

- Web 输入页支持输入 transcript / typed text
- Web 输入页支持 source type：Real-world / Story
- Web 输入页支持 optional context 下拉框
- Web 输入页调用 `/analyze_text` 并展示结果
- Web 输入页调用 `/save_item` 保存 word / phrase
- CYD 做 4 个基础 screen：Home、Context Select、Insight View、Dashboard
- CYD 能用 mock JSON 先显示 Top Keywords、Useful Phrases、Detected Context、Saved Items
- 后端稳定后，把 CYD mock JSON 换成 HTTP 请求

单独验收：

- 不依赖 CYD 时，网页端能完成输入、分析、保存、dashboard 刷新
- 不依赖后端时，CYD 可以用 mock 数据展示页面
- 接入后端后，CYD 能显示 `/dashboard` 的 saved words / saved phrases
- CYD 不做 NLP，只展示 API 返回结果

交付给其他线：

- Web 页面截图或现场可操作页面
- CYD 页面截图或实机演示
- 如果 CYD 字体、屏幕尺寸、触摸区域有限，及时告诉线 C 调整文案长度

## 线 C - Content / Demo / QA

负责人目标：准备内容、测试文本、演示脚本和最终集成检查，让项目看起来完整可信。

主要文件：

- `docs/TASK_PHASES.md`
- 可新增 `docs/DEMO_SCRIPT.md`
- 可新增 `docs/API_TEST_CASES.md`
- 可协助维护 `backend/seed_data.json`

独立任务：

- 准备 4 段 demo 输入文本：Coffee Shop、Doctor / Pharmacy、King's Cross、Baker Street
- 每段文本标注期望 context、期望 keywords、期望 phrases
- 准备 60-90 秒演示流程
- 准备 fallback 方案：如果 CYD 网络不稳，就用 Web 输入页演示完整闭环
- 准备最终 pitch：产品一句话、MVP 价值、系统架构、demo 流程
- 记录 bug 和集成风险
- 帮线 A 做 API 测试，帮线 B 控制屏幕文案长度

单独验收：

- 4 段测试文本都能直接复制进 Web 输入页
- 每段文本都有清晰的讲解点
- 演示流程 1 分钟内能讲完闭环
- 有一份“出问题时怎么演”的 fallback 话术

交付给其他线：

- demo 文本
- seed data 修改建议
- API 测试结果
- 最终展示讲稿

## 集成阶段

## Integration 1 - API 对齐

目标：线 A 提供真实 API，线 B 和线 C 用同一套字段联调。

检查项：

- 后端启动：`uvicorn backend.main:app --reload`
- `GET /contexts` 能返回 4 个 context
- Web 下拉框能显示这 4 个 context
- `POST /analyze_text` 返回字段和固定接口合约一致
- `GET /dashboard` 能返回 saved words 和 saved phrases

## Integration 2 - Web 闭环

目标：先用网页完成完整 MVP，保证后端和数据流没有问题。

检查项：

- 输入 Coffee Shop 文本
- 点击 Analyze Text
- 页面展示 Detected Context、Keywords、Phrases、Summary
- 点击保存一个 word 和一个 phrase
- 刷新 Dashboard 后能看到保存项

## Integration 3 - CYD 闭环

目标：让 CYD 接入真实后端，完成展示端 demo。

检查项：

- CYD 和 laptop 在同一 Wi-Fi / hotspot
- CYD 能请求 laptop IP 的 API
- CYD 能显示 context 列表
- CYD 能显示分析结果或预设 context 卡片
- CYD 能显示 dashboard saved items

## Integration 4 - 最终演示

目标：把技术闭环变成顺畅 demo。

推荐演示顺序：

1. 打开 Web 输入页，输入 Coffee Shop transcript
2. 点击 Analyze Text，展示关键词、短语和 detected context
3. 保存一个 word / phrase
4. 切到 CYD，刷新 Dashboard
5. CYD 展示 saved review items
6. 讲一句架构：Web 负责输入，FastAPI 负责 NLP 和存储，CYD 负责学习 dashboard

## 文件归属建议

- 线 A 主要修改 `backend/`
- 线 B 主要修改 `web/` 和 `lvgl9_firmwares/`
- 线 C 主要修改 `docs/` 和测试文本，必要时提交 `backend/seed_data.json` 的内容建议

如果多人同时改同一个文件，优先提前说清楚谁负责最终合并。

## 最短冲刺顺序

1. 线 A：跑通 `/analyze_text` 和 `/dashboard`
2. 线 B：Web 输入页接上 `/analyze_text`
3. 线 C：准备 4 段测试文本和 demo 讲稿
4. 线 B：CYD 先用 mock JSON 完成页面
5. 三线集成：CYD 改成请求真实 API
6. 全员彩排：按 60-90 秒流程演示一遍

## 最终验收标准

- 用户可以输入一段真实对话或故事文本
- 系统可以自动提取 keywords 和 phrases
- 系统可以检测 context
- 用户可以保存 review item
- CYD 可以展示 dashboard
- 断网或 CYD 临时失败时，Web 仍能完整演示核心闭环
