# SceneLingo 三线并行开发计划

这份文件只做分工和执行顺序，不再继续拆更多文档。三条线都直接做功能，最后合到同一个 MVP 闭环：

```
Web 输入文本 -> FastAPI 后端分析 -> SQLite 保存 -> CYD Dashboard 展示
```

## 总体分配

```
线 A：Backend + NLP + SQLite
线 B：Web Input + Web Dashboard
线 C：CYD LVGL Display + Hardware Integration
```

## 统一技术栈

为了避免 hackathon 现场技术栈混乱，三条线统一按下面做：

```
Backend：Python + FastAPI + Uvicorn + Pydantic
NLP：Python 标准库 rule-based pipeline
Storage：SQLite + JSON seed data
Web：原生 HTML + CSS + JavaScript + fetch
CYD：MicroPython + LVGL + HTTP requests
Network：同一个 Wi-Fi / hotspot，本地 laptop 当后端服务器
```

明确不要做：

- 不换 Flask / Django / Node.js 后端
- 不上 React / Vue / Next.js / Vite
- 不上 PostgreSQL / MongoDB / Redis
- 不让 CYD 做 NLP
- 不做登录注册
- 不做真实 GPS / 地图 / 路线规划
- 不强依赖 LLM 或实时语音识别

## 固定 API 合约

三条线最后靠这些接口集合，字段名尽量不要改。

```
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

## 线 A - Backend + NLP + SQLite

负责人目标：直接把后端跑通，给线 B 的 Web 和线 C 的 CYD 提供稳定 API。线 A 不再拆新文档，只改代码、跑接口、交付可访问地址。

主要文件：

- `backend/main.py`：FastAPI 路由和请求/返回模型
- `backend/nlp_engine.py`：文本清洗、关键词、短语、context 分类、summary
- `backend/database.py`：SQLite 建表、seed data、分析结果、复习项、dashboard 汇总
- `backend/seed_data.json`：4 个固定 context
- `requirements.txt`：后端依赖，不随便加大包

线 A 技术栈固定：

```
Python + FastAPI + Uvicorn + Pydantic + SQLite + Python 标准库 NLP
```

线 A 不做：

- 不换 Flask / Django / Node.js
- 不引入 spaCy / NLTK 作为必需依赖
- 不接 LLM 作为必需能力
- 不做登录注册
- 不让 CYD 直接碰数据库

### A0 - 本地环境确认

任务：

- 激活 `.venv`
- 确认依赖安装完成
- 确认 Python 文件没有语法错误

命令：

```powershell
cd C:\hackathon
.\.venv\Scripts\Activate.ps1
python -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

验收：

- 命令无报错
- 不新建第二个虚拟环境
- 不把依赖装到系统 Python

### A1 - 启动 FastAPI

任务：

- 启动本地后端
- 确认健康检查接口可用

命令：

```powershell
uvicorn backend.main:app --reload
```

验收：

- 浏览器打开 `http://localhost:8000`
- 返回 `{"status":"ok","service":"SceneLingo API"}`

### A2 - 固定 4 个 Context Seed Data

任务：

- 检查 `backend/seed_data.json`
- 确保只有 MVP 需要的 4 个 context
- 确保 keywords / phrases 能支持分类

必须保留：

```
coffee_shop
doctor_pharmacy
kings_cross
baker_street
```

验收：

- `GET /contexts` 返回 2 个 real-world、2 个 story
- `GET /context/coffee_shop` 返回 Coffee Shop 卡片
- JSON 不写注释，不加无关场景

### A3 - SQLite 存储跑通

任务：

- 启动时自动创建 `scenelingo.db`
- 创建 `contexts`
- 创建 `analysis_results`
- 创建 `review_items`
- 每次启动同步 `seed_data.json`

验收：

- 第一次启动自动生成 `scenelingo.db`
- 重启不会把 seed data 插乱
- `/save_item` 能写入 review item
- `/dashboard` 能读到 saved words / saved phrases

### A4 - NLP Cleaning

任务：

- 把输入文本转成小写 token
- 去掉 filler words：`um`、`uh`、`erm`、`hmm`、`like`
- 去掉 stopwords：`a`、`an`、`the`、`to`、`of` 等
- 去掉连续重复词
- 去掉无意义符号

测试文本：

```
Um, hi, hi, can I get a latte with milk to go please?
```

验收：

- cleaned text 里没有 `um`
- cleaned text 里没有 `please`
- `hi hi` 不重复出现

### A5 - Keywords / Phrases

任务：

- Keywords：从 cleaned tokens 做词频统计，最多返回 5 个
- Phrases：优先匹配 seed phrases，再拼 2-3 词短语，最多返回 3 个

Coffee Shop 测试文本：

```
Hi, can I get a latte with milk to go? How much is the large size?
```

验收：

- keywords 包含 `latte` 或 `milk`
- phrases 包含 `Can I Get` 或 `to go`
- 返回字段是 list，不是字符串

### A6 - Context Classification

任务：

- 如果请求传了 `optional_context`，优先使用
- 如果没传，用 seed keywords 给 context 打分
- 返回完整 context object，不只返回字符串

验收文本：

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

验收：

- 四段文本分别识别到 `coffee_shop`、`doctor_pharmacy`、`kings_cross`、`baker_street`
- `detected_context` 包含 `id`、`title`、`type`、`tag`、`confidence`
- 没有外网也能分类

### A7 - Summary

任务：

- 用模板生成 1 句学习建议
- 包含 context title
- 包含 2-3 个关键词
- 不依赖 LLM

验收：

- summary 是普通字符串
- CYD 小屏幕能显示
- 不超过 1-2 句

### A8 - 完成 `/analyze_text`

任务：

- 接收 `raw_text`
- 接收 `source_type`
- 接收 `optional_context`
- 调用 NLP pipeline
- 保存 analysis result
- 返回完整分析结果

返回必须包含：

```
id
cleaned_text
keywords
phrases
detected_context
summary
suggested_review_items
```

验收：

- Coffee Shop 文本返回 `detected_context.id = coffee_shop`
- 返回 HTTP 200
- 结果写入 `analysis_results`

### A9 - 完成 Context API

任务：

- `GET /contexts`
- `GET /context/{id}`

验收：

- `/contexts` 能给线 B 渲染下拉框
- `/context/coffee_shop` 能给线 C 渲染 CYD 场景卡片
- 不存在的 id 返回 404

### A10 - 完成 Save / Dashboard API

任务：

- `POST /save_item`
- `GET /dashboard`

验收：

- 保存 word 后，dashboard 的 `saved_words` 出现它
- 保存 phrase 后，dashboard 的 `saved_phrases` 出现它
- dashboard 返回 `top_context`、`recent_keywords`、`review_today`

### A11 - 局域网联调准备

任务：

- 后端监听 `0.0.0.0`
- 给线 B 和线 C 一个 laptop 局域网 IP
- 确认 Windows 防火墙没有挡住请求

命令：

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

交付给线 B / 线 C：

```
本地 API：http://localhost:8000
局域网 API：http://你的电脑IP:8000
context ids：coffee_shop、doctor_pharmacy、kings_cross、baker_street
```

### A12 - 线 A 完成标准

线 A 完成时必须满足：

- `GET /` 可用
- `GET /contexts` 返回 4 个 context
- `POST /analyze_text` 能分析 4 段测试文本
- `POST /save_item` 能保存 word / phrase
- `GET /dashboard` 能返回 saved items
- Web 不需要知道数据库细节
- CYD 不需要做 NLP
- 无网络、无 LLM API key 也能完整演示

## 线 B - Web Input + Web Dashboard

负责人目标：直接把网页输入端做出来，作为用户输入入口和 CYD 失败时的 fallback demo。线 B 不写新文档，不写后端，不写 CYD，只改 Web 页面并接线 A 的 API。

主要文件：

- `web/index.html`

线 B 技术栈固定：

```
原生 HTML + CSS + JavaScript + fetch API
```

线 B 不做：

- 不上 React / Vue / Angular / Next.js / Vite
- 不用 npm / pnpm / yarn
- 不做新的前端构建系统
- 不写 FastAPI 后端逻辑
- 不写 CYD LVGL 页面
- 不直接读 SQLite

### B0 - Web 运行方式确认

任务：

- 直接用浏览器打开 `web/index.html`
- 确认页面能显示
- 确认页面里只有一个 API 地址配置

如果需要手机访问 Web 页面，可以临时用：

```powershell
python -m http.server 5500 --directory web
```

验收：

- 电脑浏览器能打开页面
- 手机浏览器能访问 `http://你的电脑IP:5500`
- 不需要安装任何 Node.js 依赖

### B1 - API 地址集中配置

任务：

- 在 `web/index.html` 里保留一个 `API_BASE`
- 本机开发默认 `http://localhost:8000`
- 手机访问时改成 laptop 局域网 IP

示例：

```javascript
const API_BASE = "http://localhost:8000";
```

验收：

- 换后端 IP 只改一处
- 代码里没有散落的 `http://localhost:8000`
- 手机访问时知道要把 `localhost` 改成电脑 IP

### B2 - 页面基础结构

任务：

- 保留 SceneLingo 标题
- Source 选择：Real-world / Story
- Optional Context 下拉框
- Text 输入框
- Analyze Text 按钮
- Analysis Result 区
- Save buttons 区
- Dashboard 预览区
- Refresh Dashboard 按钮

验收：

- 页面一打开就能看到输入框和 Analyze Text
- 页面布局在电脑和手机浏览器都能用
- 不做登录页，不做多页面路由，不做 marketing landing page

### B3 - 接 `/contexts`

任务：

- 页面加载时调用 `GET /contexts`
- 保存 `real_world` 和 `story` 两组数据
- Real-world 显示 Coffee Shop、Doctor / Pharmacy
- Story 显示 King's Cross、Baker Street
- 切换 source type 时更新 optional context 下拉框

验收：

- 后端启动后，下拉框自动有 4 个 context
- Source 切换时，下拉选项跟着切换
- 后端没启动时，页面显示连接错误，不白屏

### B4 - 接 `/analyze_text`

任务：

- 点击 Analyze Text 后读取文本框内容
- 读取 `source_type`
- 读取 `optional_context`
- 调用 `POST /analyze_text`
- 保存 `latestResult`
- 展示分析结果

请求格式：

```json
{
  "raw_text": "Hi, can I get a latte with milk to go?",
  "source_type": "real-world",
  "optional_context": null
}
```

验收：

- 输入 Coffee Shop 文本后，页面显示 `coffee_shop`
- 页面能看到 cleaned text
- 页面能看到 Top Keywords
- 页面能看到 Top Phrases
- 页面能看到 summary
- Analyze 过程中有 `Analyzing...` 状态

### B5 - 结果展示整理

任务：

- Analysis Result 不只依赖一坨 JSON
- 至少把这些字段清楚显示出来：

```
Detected Context
Top Keywords
Top Phrases
Summary
Suggested Review Items
```

验收：

- 评委不看控制台也能看懂结果
- keywords 和 phrases 是列表或 chip
- summary 不被按钮挤在一起
- 如果 JSON 还保留，只作为调试区

### B6 - 接 `/save_item`

任务：

- keywords 生成 Save Word 按钮
- phrases 生成 Save Phrase 按钮
- 点击 word 时发送 `item_type = word`
- 点击 phrase 时发送 `item_type = phrase`
- 带上 `source_context`
- 保存成功后刷新 dashboard

请求格式：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

验收：

- 保存 `latte` 后 dashboard 出现 saved word
- 保存 `Can I Get` 后 dashboard 出现 saved phrase
- 保存失败时页面有提示，不静默失败

### B7 - 接 `/dashboard`

任务：

- 点击 Refresh Dashboard 调用 `GET /dashboard`
- 显示 saved words
- 显示 saved phrases
- 显示 top context
- 显示 recent keywords
- 显示 review today

验收：

- Web 端可以完成完整闭环：输入 -> 分析 -> 保存 -> dashboard
- Dashboard 数据刷新后不用手动重开页面
- saved words 和 saved phrases 分开显示

### B8 - 准备 4 段测试输入

任务：

- 在页面里保留一个默认 Coffee Shop 文本
- 开发时用下面 4 段文本测试 Web 调用，不新建文档

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

验收：

- 四段文本都可以从 Web 输入框提交
- Real-world / Story source type 能正确切换
- 如果自动识别不稳定，可以用 optional context 演示 fallback

### B9 - 手机浏览器联调

任务：

- 让后端线 A 用 `--host 0.0.0.0` 启动
- 把 Web 的 `API_BASE` 改成 laptop 局域网 IP
- 手机和 laptop 连同一个 Wi-Fi / hotspot
- 手机打开 Web 页面并提交文本

验收：

- 手机能加载 context 下拉框
- 手机能提交 `/analyze_text`
- 手机能保存 item
- 手机能刷新 dashboard

### B10 - 作为 CYD Fallback Demo

任务：

- 保证不依赖 CYD 也能演示完整 MVP
- Web 页面能展示输入、分析、保存、复习列表
- 页面上保留清楚的 dashboard 区

验收：

- 如果 CYD 临时网络失败，Web 可以 60 秒内演示：

```
输入 Coffee Shop 文本 -> Analyze -> Save Word -> Refresh Dashboard
```

### B11 - 给线 A / 线 C 的交付

给线 A：

- Web 调用失败时的具体接口和错误信息
- 是否字段名不匹配
- 是否 CORS 或网络失败

给线 C：

- Web dashboard 中已经验证可用的字段
- CYD 应该显示哪些短字段
- Web 保存 item 后，CYD 可以刷新 dashboard 验证

### B12 - 线 B 完成标准

线 B 完成时必须满足：

- 只改 `web/index.html`
- 没有引入 React / Node / 构建工具
- 能加载 `/contexts`
- 能调用 `/analyze_text`
- 能调用 `/save_item`
- 能调用 `/dashboard`
- 能在电脑浏览器演示完整闭环
- 能在手机浏览器演示完整闭环
- CYD 失败时，Web 可以作为 fallback

## 线 C - CYD LVGL Display + Hardware Integration

负责人目标：直接把 CYD 展示端做出来。CYD 是学习 dashboard 终端，只负责显示、刷新、点击保存，不做 NLP、不读数据库、不写 Web、不写新文档。

主要文件：

- `lvgl9_firmwares/touch_color_test.py`
- 建议新增：`lvgl9_firmwares/scenelingo_dashboard.py`

线 C 技术栈固定：

```
MicroPython + LVGL + HTTP requests / urequests + JSON
```

线 C 不做：

- 不写 FastAPI 后端
- 不写 Web 页面
- 不直接读 SQLite
- 不在 CYD 上做 NLP
- 不在 CYD 上做实时语音识别
- 不直接调用 LLM
- 不继续拆新文档
- 不删除已有测试文件

### C0 - CYD 基础能力确认

任务：

- 确认 CYD 能运行 MicroPython
- 确认 LVGL 屏幕显示正常
- 确认触摸可用
- 确认已有 `touch_color_test.py` 可以跑
- 确认 CYD 可以连接 laptop 所在 Wi-Fi / hotspot

验收：

- `touch_color_test.py` 或已有测试画面能跑
- 触摸屏有响应
- 屏幕方向正确，按钮能点中
- 不改坏现有测试文件

### C1 - 新建 CYD 业务主文件

任务：

- 新建 `lvgl9_firmwares/scenelingo_dashboard.py`
- 文件顶部集中配置 `API_BASE`
- 文件顶部集中配置 Wi-Fi 信息或连接函数
- 集中写 HTTP helper
- 不把业务 UI 全塞进测试文件

建议结构：

```
API config
mock data
HTTP helper
LVGL style helper
Home screen
Context Select screen
Insight View
Dashboard View
Save interaction
```

验收：

- 换后端 IP 只需要改一处
- 上传这个文件后可以独立运行
- 网络失败时 CYD 不崩溃

### C2 - Mock 数据先行

任务：

- 先准备 mock analysis
- 先准备 mock dashboard
- 先用 mock 数据把 UI 跑通
- 后端未联调时，CYD 也能展示页面

建议 mock 字段：

```python
MOCK_ANALYSIS = {
    "detected_context": {"id": "coffee_shop", "title": "Coffee Shop"},
    "keywords": ["latte", "milk", "size", "order", "receipt"],
    "phrases": ["Can I Get", "to go", "with milk"],
    "summary": "This looks like Coffee Shop. Focus on latte, milk, size.",
}

MOCK_DASHBOARD = {
    "saved_words": [{"item_text": "latte"}, {"item_text": "milk"}],
    "saved_phrases": [{"item_text": "Can I Get"}],
    "top_context": "coffee_shop",
    "recent_keywords": ["latte", "milk", "order"],
    "review_today": 3,
}
```

验收：

- 不连后端也能显示 Insight View
- 不连后端也能显示 Dashboard View
- 后面换真实 API 时，不需要重写 UI

### C3 - HTTP Helper

任务：

- 集中封装 `api_get(path)`
- 集中封装 `api_post(path, payload)`
- 请求失败时返回 `None` 或 fallback mock
- 请求结束后关闭 response，减少内存占用

建议函数：

```python
def api_get(path):
    pass

def api_post(path, payload):
    pass

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

验收：

- 所有 HTTP 请求都集中在 helper
- 换 IP 只改 `API_BASE`
- 网络失败时页面不崩溃

### C4 - CYD Home Screen

任务：

- 显示 `SceneLingo`
- 三个按钮：Real-world、Story、Dashboard

按钮行为：

- Real-world -> Context Select
- Story -> Context Select
- Dashboard -> Dashboard View

验收：

- 三个按钮能点击
- 页面切换不卡死
- 按钮够大，手指能点中
- 文案不挤出屏幕

### C5 - CYD Context Select

任务：

- Real-world 显示 Coffee Shop、Doctor / Pharmacy
- Story 显示 King's Cross、Baker Street
- 点击 context 后优先请求 `GET /context/{id}`
- 请求失败时使用 mock context
- 点击 context 后进入 Insight View
- 有 Back 按钮回 Home

验收：

- 4 个 context 都能进入
- 文案不挤出屏幕
- Back 能回 Home
- 请求失败时不黑屏

### C6 - CYD Insight View

任务：

- 展示 Context title
- 展示 Top Keywords
- 展示 Useful Phrases
- 展示 Summary
- 支持保存 word / phrase
- 有 Back 按钮

验收：

- Coffee Shop 结果能看清楚
- 至少显示 5 个 keywords
- 至少显示 3 个 phrases
- 有 Back 按钮
- summary 最多显示 1-2 句
- 长 phrase 不撑破布局

### C7 - CYD Dashboard View

任务：

- 请求 `GET /dashboard`
- 显示 Saved Words
- 显示 Saved Phrases
- 显示 Top Context
- 显示 Review Today
- 有 Refresh 按钮
- 有 Back 按钮

验收：

- Web 保存 item 后，CYD 刷新能看到
- CYD 不需要知道 SQLite 细节
- 网络失败时显示 mock dashboard 或错误提示
- Refresh 不会卡死 UI

### C8 - CYD 保存交互

任务：

- 点击 keyword 保存为 word
- 点击 phrase 保存为 phrase
- 调用 `POST /save_item`
- 保存成功显示 `Saved`
- 保存失败显示 `Save failed` 或保持 fallback

验收：

- CYD 保存后，Web dashboard 能看到更新
- `item_type` 正确传 `word` 或 `phrase`
- `source_context` 正确传当前 context id

### C9 - 真实 API 联调

任务：

- 让线 A 用 `--host 0.0.0.0` 启动后端
- CYD 和 laptop 连同一个 Wi-Fi / hotspot
- 把 `API_BASE` 改成 laptop 局域网 IP
- 测试 `GET /dashboard`
- 测试 `POST /save_item`

联调顺序：

```
1. CYD 请求 /dashboard
2. Web 保存一个 word
3. CYD Refresh Dashboard
4. CYD 显示 Web 刚保存的 item
5. CYD 保存一个 phrase
6. Web Refresh Dashboard 验证更新
```

验收：

- CYD 能请求真实后端
- CYD 能显示真实 dashboard
- CYD 保存后 Web 能看到更新

### C10 - CYD 小屏幕显示规则

任务：

- 每屏只显示最关键字段
- 文案短，按钮大
- keywords 最多显示 5 个
- phrases 最多显示 3 个
- summary 最多 1-2 句

推荐文案：

```
Home
Real-world
Story
Dashboard
Keywords
Phrases
Saved
Refresh
Back
```

验收：

- 不需要把字体缩到看不清
- 按钮不会互相重叠
- 触摸区域足够大

### C11 - 给其他线的交付

必须交付：

- CYD 可运行文件
- 当前 `API_BASE` 配置方式
- CYD 屏幕展示截图或实机展示
- CYD 能显示哪些字段
- CYD 显示不下哪些字段
- 需要线 A 缩短哪些 API 文案
- 需要线 B 用 Web 验证哪些保存结果

### C12 - 线 C 完成标准

线 C 完成时必须满足：

- CYD 能运行 SceneLingo 业务文件
- CYD Home / Context Select / Insight / Dashboard 四个页面可切换
- CYD 不做 NLP
- CYD 不读 SQLite
- CYD 能用 mock 数据展示
- CYD 能请求真实 `/dashboard`
- CYD 能调用真实 `/save_item`
- Web 保存 item 后，CYD refresh 能看到
- CYD 保存 item 后，Web refresh 能看到
- 线 C 没有额外承担后端、Web、项目文档产出

## 三线集成顺序

### Step 1 - 后端先稳定

负责人：线 A

检查：

- `GET /` 可用
- `/contexts` 返回 4 个 context
- `/analyze_text` 可分析 Coffee Shop 文本
- `/dashboard` 可返回 JSON

### Step 2 - Web 接真实 API

负责人：线 B

检查：

- Web 下拉框能加载 contexts
- Web 能分析 Coffee Shop 文本
- Web 能保存 word / phrase
- Web dashboard 能显示 saved items

### Step 3 - CYD 先用 mock UI

负责人：线 C

检查：

- Home 可点击
- Context Select 可点击
- Insight View 可显示 mock keywords / phrases
- Dashboard 可显示 mock saved items

### Step 4 - CYD 接真实 API

负责人：线 C + 线 A

检查：

- 后端用 `--host 0.0.0.0` 启动
- CYD 和 laptop 在同一网络
- CYD 的 `API_BASE` 是 laptop 局域网 IP
- CYD 能请求 `/dashboard`
- CYD 能保存 item

### Step 5 - 全员彩排

负责人：三条线一起

最终演示流程：

1. Web 输入 Coffee Shop transcript
2. 点击 Analyze Text
3. Web 显示 keywords、phrases、detected context
4. 保存一个 word / phrase
5. CYD 打开 Dashboard
6. CYD 刷新并显示刚保存的 review item
7. 讲一句架构：Web 负责输入，FastAPI 负责 NLP 和存储，CYD 负责学习 dashboard

## 今日最短冲刺顺序

1. 线 A：确保 `/analyze_text` 和 `/dashboard` 稳定
2. 线 B：Web 接上 `/contexts`、`/analyze_text`、`/save_item`
3. 线 C：CYD 先做 mock Home / Dashboard
4. 线 A：用 `--host 0.0.0.0` 开局域网后端
5. 线 C：CYD 改真实 API 地址
6. 三线：完成 Web 保存 -> CYD dashboard 刷新的闭环

## 最终验收标准

- 用户可以在 Web 输入一段真实对话或故事文本
- 后端可以自动提取 keywords 和 phrases
- 后端可以检测 context
- 用户可以保存 review item
- CYD 可以展示 dashboard
- Web 可以作为 CYD 失败时的 fallback
- 整个 demo 可以在 60-90 秒内讲完
