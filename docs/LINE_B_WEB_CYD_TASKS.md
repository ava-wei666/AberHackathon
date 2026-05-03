# 线 B 详细任务书 - Web Input / Web Dashboard

这份文件只给线 B 使用。新的三线分配下，线 B 不再负责 CYD，线 B 只负责把 Web 输入端和 Web Dashboard 做稳。它既是用户输入入口，也是 CYD 临时失败时的 fallback demo。

## 三条线重新分配

```
线 A：Backend + NLP + SQLite
线 B：Web Input + Web Dashboard
线 C：CYD LVGL Display + Hardware Integration
```

线 B 只改 Web 页面，只消费线 A 的 API，不写后端，不写 CYD，不继续拆新文档。

## 统一技术栈

线 B 技术栈固定如下：

```
Web 页面：原生 HTML + CSS + JavaScript
网络请求：浏览器 fetch API
部署方式：直接打开 HTML，或用 Python 内置 http.server 做静态服务
后端 API：FastAPI，由线 A 提供
数据格式：JSON
```

## 明确不要使用

MVP 阶段不要引入这些东西，避免技术栈混乱：

- 不用 React
- 不用 Vue
- 不用 Angular
- 不用 Next.js
- 不用 Vite
- 不用 Tailwind
- 不用 Bootstrap
- 不用 Node.js / npm / pnpm / yarn
- 不做新的前端构建系统
- 不写 FastAPI 后端逻辑
- 不直接读 SQLite
- 不写 CYD LVGL 页面
- 不改 `touch_color_test.py`
- 不新增 CYD 业务文件

## 当前文件归属

线 B 主要负责：

```
web/
  index.html
```

线 B 不负责：

```
backend/                       # 线 A
lvgl9_firmwares/               # 线 C
docs/LINE_C_CONTENT_DEMO_QA_TASKS.md
```

注意：这个文件虽然是任务说明，但线 B 的实际开发交付只落在 `web/index.html`。

## 线 B 最终目标

线 B 要完成这个 Web 闭环：

```
Typed Text / Transcript
  -> POST /analyze_text
  -> 展示 detected context / keywords / phrases / summary
  -> POST /save_item
  -> GET /dashboard
  -> 展示 saved words / saved phrases / top context
```

线 B 做出来后，即使 CYD 网络临时失败，也能用 Web 页面完整演示 MVP。

## 固定 API 地址规则

开发默认地址：

```
http://localhost:8000
```

手机访问 laptop 后端时，必须改成 laptop 的局域网 IP：

```
http://192.168.x.x:8000
```

`web/index.html` 里只保留一个 API 地址配置：

```javascript
const API_BASE = "http://localhost:8000";
```

验收：

- 换 API 地址只改一处
- 代码里没有散落多个后端地址
- 手机访问时知道 `localhost` 要换成 laptop IP

## Task B0 - Web 运行确认

目标：不用构建工具，直接跑 Web 页面。

电脑浏览器：

```
C:\hackathon\web\index.html
```

如果需要手机访问 Web 页面：

```powershell
cd C:\hackathon
python -m http.server 5500 --directory web
```

手机访问：

```
http://你的电脑IP:5500
```

验收：

- 电脑能打开页面
- 手机能打开页面
- 不需要安装 Node.js 依赖
- 不需要启动前端 dev server

## Task B1 - 页面基础结构

目标：页面一打开就能完成输入和查看结果。

文件：

```
web/index.html
```

页面必须保留这些区域：

```
1. Source / Context 选择区
2. Text 输入区
3. Analysis Result 结果区
4. Save buttons 区
5. Dashboard 预览区
```

必须有这些控件：

- Source select：Real-world / Story
- Optional Context select
- Textarea
- Analyze Text button
- Refresh Dashboard button

验收：

- 页面打开后能看到 SceneLingo 标题
- 能输入文本
- 能选择 source type
- 有 Analyze Text 按钮
- 有 Dashboard 区域

## Task B2 - 加载 Contexts

目标：页面启动时从后端拿 context 列表。

接口：

```
GET /contexts
```

Web 逻辑：

```
页面加载
  -> fetch GET /contexts
  -> 保存 real_world 和 story 两组数据
  -> 根据 source type 渲染 optional context 下拉框
```

验收：

- Real-world 显示 Coffee Shop、Doctor / Pharmacy
- Story 显示 King's Cross、Baker Street
- 切换 source type 时下拉框跟着变
- 后端没启动时页面显示错误，不白屏

## Task B3 - 提交文本分析

目标：用户点击 Analyze Text 后调用后端 NLP。

接口：

```
POST /analyze_text
```

请求格式：

```json
{
  "raw_text": "Hi, can I get a latte with milk to go?",
  "source_type": "real-world",
  "optional_context": null
}
```

Web 逻辑：

```
点击 Analyze Text
  -> result 区显示 Analyzing...
  -> fetch POST /analyze_text
  -> 保存 latestResult
  -> 展示结果
  -> 渲染 Save buttons
```

验收：

- Coffee Shop 文本返回 `coffee_shop`
- 页面能显示 keywords
- 页面能显示 phrases
- 页面能显示 detected context
- 页面能显示 summary
- 请求失败时显示错误信息

## Task B4 - 结果展示整理

目标：让评委不用看 raw JSON 也能看懂结果。

页面至少显示：

```
Detected Context
Top Keywords
Useful Phrases
Context Summary
Suggested Review Items
```

建议：

- keywords 用 chip 或短列表展示
- phrases 用 chip 或短列表展示
- summary 单独一段展示
- raw JSON 可以保留在调试区，但不要成为唯一展示

验收：

- 输入 Coffee Shop 文本后，页面能一眼看出这是 Coffee Shop
- keywords 和 phrases 不挤在一起
- summary 不被按钮遮挡

## Task B5 - 保存复习项

目标：关键词和短语可以保存到 dashboard。

接口：

```
POST /save_item
```

请求格式：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

Web 逻辑：

```
分析成功
  -> keywords 生成 Save Word 按钮
  -> phrases 生成 Save Phrase 按钮
  -> 点击按钮调用 POST /save_item
  -> 保存成功后刷新 dashboard
```

验收：

- 保存 word 后 `/dashboard` 的 `saved_words` 能看到
- 保存 phrase 后 `/dashboard` 的 `saved_phrases` 能看到
- 保存失败时页面有提示
- Save 按钮数量不要多到撑爆页面

## Task B6 - Web Dashboard

目标：Web 端展示复习数据，作为 CYD 的字段验证来源。

接口：

```
GET /dashboard
```

重点字段：

```json
{
  "saved_words": [],
  "saved_phrases": [],
  "top_context": "coffee_shop",
  "recent_keywords": [],
  "review_today": 2
}
```

验收：

- 点击 Refresh Dashboard 能显示最新数据
- saved_words 和 saved_phrases 分开展示
- top_context 能显示
- recent_keywords 能显示
- review_today 能显示

## Task B7 - 四段测试输入

目标：用固定文本测试 Web 调用链路，不额外新建测试文档。

Coffee Shop：

```
Hi, can I get a latte with milk to go? How much is the large size?
```

Doctor / Pharmacy：

```
I have a headache and a cough. Do I need medicine from the pharmacy?
```

King's Cross：

```
Which platform should I use to catch the train to the magic school at King's Cross?
```

Baker Street：

```
The detective found a clue on Baker Street and tried to solve the case.
```

验收：

- 四段文本都能从 Web 输入框提交
- Real-world / Story source type 能正确切换
- 如果自动识别不稳定，可以选择 optional context 继续演示

## Task B8 - 手机浏览器联调

目标：让手机也可以作为输入端。

前置条件：

- 线 A 后端用 `--host 0.0.0.0` 启动
- laptop 和手机在同一 Wi-Fi / hotspot
- `API_BASE` 改成 laptop 局域网 IP

验收：

- 手机能加载 contexts
- 手机能提交 `/analyze_text`
- 手机能保存 item
- 手机能刷新 dashboard

## Task B9 - CYD Fallback Demo

目标：CYD 临时失败时，Web 仍能完整展示 MVP。

Web fallback 流程：

```
1. 输入 Coffee Shop transcript
2. 点击 Analyze Text
3. 展示 detected context、keywords、phrases、summary
4. 保存一个 word / phrase
5. Refresh Dashboard
6. 展示 saved review item
```

验收：

- 不依赖 CYD，Web 也能在 60 秒内演示完整闭环
- 页面上能明确看到 dashboard 更新

## Task B10 - 给线 A 的反馈

线 B 发现问题时，只反馈和 API 有关的具体信息：

- 哪个接口失败
- 请求 payload 是什么
- 返回 status 是什么
- 返回字段是否缺失
- 浏览器 console 里的错误

线 B 不要求线 A 改数据库结构，除非当前 API 无法完成 MVP。

## Task B11 - 给线 C 的交付

线 C 负责 CYD。线 B 只需要交付这些信息：

- Web 已验证可用的 dashboard 字段
- 保存 item 后 dashboard 的变化
- 哪些字段适合 CYD 显示：

```
detected_context.title
keywords
phrases
summary
saved_words
saved_phrases
top_context
review_today
```

线 B 不写 CYD 页面，也不调整 LVGL。

## 线 B 完成标准

线 B 完成时，必须满足：

- 只改 `web/index.html`
- 不引入 React、Node、Tailwind、构建工具
- Web 可以加载 `/contexts`
- Web 可以调用 `/analyze_text`
- Web 可以调用 `/save_item`
- Web 可以调用 `/dashboard`
- Web 可以在电脑浏览器完成完整闭环
- Web 可以在手机浏览器完成完整闭环
- CYD 失败时，Web 可以作为 fallback demo
- 线 B 没有额外承担后端、CYD、项目文档产出

## 常见问题处理

### Web 页面提示无法连接 API

检查：

- 后端是否启动
- `API_BASE` 是否正确
- 浏览器控制台是否有 CORS 或网络错误
- 如果手机访问，是否把 `localhost` 改成 laptop 局域网 IP

### 手机能打开 Web，但不能调用后端

原因通常是 `API_BASE` 仍然写着：

```
http://localhost:8000
```

手机里的 localhost 指手机自己，不是 laptop。应改成：

```
http://laptop局域网IP:8000
```

### Analyze Text 没有结果

检查：

- `raw_text` 是否为空
- `source_type` 是否是 `real-world` 或 `story`
- `optional_context` 空值是否传 `null`，不要传乱字符串
- 后端 `/analyze_text` 是否返回错误 JSON

### 保存后 Dashboard 没更新

检查：

- `/save_item` 是否返回 `saved: true`
- `item_type` 是否是 `word` 或 `phrase`
- 保存后是否调用了 `GET /dashboard`
- dashboard 区域是否重新渲染
