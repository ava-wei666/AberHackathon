# 线 B 详细任务书 - Web Input / CYD Display

这份文档只给线 B 使用，目标是让负责 Web 输入端和 CYD 展示端的人可以直接上手做。线 B 不负责 NLP、不负责数据库、不负责后端业务逻辑，只负责把用户输入送到 API，并把 API 返回结果展示成可学习的 dashboard。

## 统一技术栈

线 B 必须使用下面这套技术栈，MVP 阶段不要混用其他前端框架或后端技术。

```
Web 输入端：原生 HTML + CSS + JavaScript
Web 网络请求：浏览器 fetch API
Web 部署方式：直接打开 HTML，或用 Python 内置 http.server 做本地静态服务

CYD 端：MicroPython
CYD UI：LVGL
CYD 网络请求：MicroPython HTTP requests / urequests
CYD 数据格式：JSON

后端 API：FastAPI，由线 A 提供
```

## 明确不要使用

MVP 阶段先不要引入这些东西，避免技术栈混乱和比赛现场难调试。

- 不用 React
- 不用 Vue
- 不用 Angular
- 不用 Next.js
- 不用 Vite
- 不用 Tailwind
- 不用 Bootstrap
- 不用 Node.js / npm / pnpm / yarn
- 不做新的前端构建系统
- 不在 CYD 上做 NLP
- 不在 CYD 上做 SQLite
- 不在 CYD 上做实时语音识别
- 不让 CYD 直接调用 LLM
- 不做复杂动画和重图片资源

如果要改 UI，直接改 `web/index.html` 或 CYD 的 MicroPython/LVGL 文件，不新增复杂项目结构。

## 当前文件归属

线 B 主要负责这些文件：

```
web/
  index.html

lvgl9_firmwares/
  touch_color_test.py
  scenelingo_dashboard.py    # 建议后续新增，专门写 SceneLingo CYD UI
```

说明：

- `web/index.html`：手机/电脑输入文本、调用后端、预览分析结果、保存复习项
- `touch_color_test.py`：当前已有 CYD 测试文件，不建议直接改成业务主文件
- `scenelingo_dashboard.py`：建议新增为 CYD 业务展示文件，避免污染测试文件

## 线 B 最终目标

线 B 最终要完成两个展示入口：

```
Web 输入端：
Typed Text / Transcript -> POST /analyze_text -> 展示结果 -> POST /save_item

CYD 展示端：
Home -> Context Select -> Insight View -> Save Item -> Dashboard
```

线 B 只消费线 A 的 API，不直接读 SQLite，不直接改后端数据库。

## 固定 API 地址规则

开发时默认：

```
http://localhost:8000
```

手机或 CYD 访问 laptop 后端时，必须改成 laptop 的局域网 IP：

```
http://192.168.x.x:8000
```

线 A 如果用局域网联调，应这样启动后端：

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

线 B 不要在代码里写多个散落的 API 地址。Web 端只保留一个：

```javascript
const API_BASE = "http://localhost:8000";
```

CYD 端也只保留一个：

```python
API_BASE = "http://192.168.x.x:8000"
```

## Task B0 - 环境确认

目标：确认 Web 和 CYD 的最小运行方式。

Web 操作：

```powershell
cd C:\hackathon
```

然后直接用浏览器打开：

```
C:\hackathon\web\index.html
```

如果需要手机访问 Web 页面，可以用 Python 内置静态服务器：

```powershell
python -m http.server 5500 --directory web
```

然后手机访问：

```
http://你的局域网IP:5500
```

CYD 操作：

- 确认 CYD 能运行已有 `touch_color_test.py`
- 确认屏幕、触摸、LVGL 基础 UI 正常
- 确认 CYD 可以连接和 laptop 相同的 Wi-Fi / hotspot

验收：

- Web 页面可以打开
- CYD 可以显示 LVGL 测试画面
- CYD 和 laptop 在同一网络下

## Task B1 - Web 页面结构整理

目标：Web 输入页先完成完整后端闭环，作为 CYD 联调前的稳定 fallback。

文件：

```
web/index.html
```

页面必须保留 4 块：

```
1. Source / Context 选择区
2. Text 输入区
3. Analysis Result 结果区
4. Dashboard 预览区
```

不要做：

- 不做登录页
- 不做营销 landing page
- 不做多页面路由
- 不做构建工具

验收：

- 页面打开后能看到 SceneLingo 标题
- 能选择 `real-world` 或 `story`
- 能输入一段文本
- 有 Analyze Text 按钮
- 有 Refresh Dashboard 按钮

## Task B2 - Web 加载 Contexts

目标：页面启动时调用后端 `/contexts`，渲染 context 下拉框。

接口：

```
GET /contexts
```

Web 逻辑：

```
页面加载
  -> fetch GET /contexts
  -> 保存 real_world 和 story 两组数据
  -> 根据 Source 类型渲染 Optional Context 下拉框
```

验收：

- Source 选择 `Real-world` 时，下拉框显示 Coffee Shop、Doctor / Pharmacy
- Source 选择 `Story` 时，下拉框显示 King's Cross、Baker Street
- 如果后端没启动，页面给出明显错误提示

## Task B3 - Web 文本分析

目标：用户点击 Analyze Text 后，把文本提交到后端。

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
  -> 展示 JSON 或格式化结果
  -> 渲染 Save buttons
```

验收：

- Coffee Shop 测试文本能返回 `coffee_shop`
- 页面能显示 keywords
- 页面能显示 phrases
- 页面能显示 detected context
- 页面能显示 summary

## Task B4 - Web 保存复习项

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

- 保存 word 后 `/dashboard` 能看到 saved_words
- 保存 phrase 后 `/dashboard` 能看到 saved_phrases
- 按钮不要重复挤爆页面，最多展示当前结果里的关键词和短语

## Task B5 - Web Dashboard 预览

目标：Web 端先完成 dashboard 数据预览，作为 CYD 的字段参考。

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

## Task B6 - CYD 新建业务文件

目标：新建一个 SceneLingo 专用 CYD 文件，不把业务 UI 全写进测试文件。

建议新增：

```
lvgl9_firmwares/scenelingo_dashboard.py
```

文件职责：

```
Wi-Fi / API config
HTTP helper
LVGL screen helpers
Home screen
Context select screen
Insight view
Dashboard view
Save item interaction
```

不要做：

- 不要删除 `touch_color_test.py`
- 不要把网络请求散落在每个按钮回调里
- 不要让每个 screen 重复写大量样式

验收：

- 新文件可以单独上传到 CYD 测试
- 文件开头能清楚看到 `API_BASE`
- 所有 API 请求集中在 helper 函数里

## Task B7 - CYD Mock 数据先行

目标：在后端或 Wi-Fi 不稳定时，CYD 也能先把 UI 做出来。

建议 mock 数据：

```python
MOCK_ANALYSIS = {
    "detected_context": {"id": "coffee_shop", "title": "Coffee Shop"},
    "keywords": ["latte", "milk", "size", "receipt", "order"],
    "phrases": ["Can I Get", "to go", "with milk"],
    "summary": "This looks like Coffee Shop. Focus on latte, milk, size.",
}

MOCK_DASHBOARD = {
    "saved_words": [{"item_text": "latte"}, {"item_text": "receipt"}],
    "saved_phrases": [{"item_text": "Can I Get"}],
    "top_context": "coffee_shop",
    "recent_keywords": ["latte", "milk", "order"],
    "review_today": 3,
}
```

验收：

- 不连后端时，CYD 也能显示 Insight View
- 不连后端时，CYD 也能显示 Dashboard
- UI 做完后只需要替换数据来源，不需要重写页面

## Task B8 - CYD Screen 1 Home

目标：做第一个入口页。

屏幕内容：

```
SceneLingo

[Real-world]
[Story]
[Dashboard]
```

按钮行为：

- Real-world：进入 Context Select，并只显示 real-world contexts
- Story：进入 Context Select，并只显示 story contexts
- Dashboard：进入 Dashboard View

验收：

- 三个按钮都能点击
- 点击后能切换到对应 screen
- 字体大小适合 CYD 小屏幕，不要挤在一起

## Task B9 - CYD Screen 2 Context Select

目标：显示 4 个 context 的选择入口。

Real-world 模式显示：

```
Coffee Shop
Doctor / Pharmacy
```

Story 模式显示：

```
King's Cross
Baker Street
```

按钮行为：

```
点击 context
  -> 优先 GET /context/{id}
  -> 展示该 context 的 seed keywords、seed phrases、summary
```

验收：

- Context 标题能显示完整
- 返回按钮能回到 Home
- 没联网时可以用 mock context 数据

## Task B10 - CYD Screen 3 Insight View

目标：展示一次分析结果或一个预设 context 卡片。

必须显示：

```
Detected Context
Top Keywords
Useful Phrases
Context Summary
```

建议布局：

```
顶部：Context title
中部：Keywords 列表
中部：Phrases 列表
底部：Summary + Save / Back 按钮
```

CYD 小屏幕注意：

- 每个 keyword 最多一行
- phrases 太长时截断或换行
- summary 最多显示 2-3 行
- 不要一次显示太多文字

验收：

- Coffee Shop mock analysis 可以完整显示
- keywords 至少显示 5 个
- phrases 至少显示 3 个
- 有 Back 按钮

## Task B11 - CYD Save Interaction

目标：CYD 可以保存 word / phrase 到后端。

接口：

```
POST /save_item
```

交互建议：

```
点击 keyword
  -> 保存为 word

点击 phrase
  -> 保存为 phrase

保存成功
  -> 简短提示 Saved
```

注意：

- 不要做复杂弹窗
- 不要做长时间阻塞 UI
- 网络失败时显示 Save failed 或保持静默 fallback

验收：

- 点击一个 keyword 后，Web dashboard 能看到 saved_words 更新
- 点击一个 phrase 后，Web dashboard 能看到 saved_phrases 更新

## Task B12 - CYD Screen 4 Dashboard View

目标：CYD 展示学习复盘 dashboard。

接口：

```
GET /dashboard
```

必须显示：

```
Saved Words
Saved Phrases
Most Frequent Context
Review Today
```

建议布局：

```
顶部：Dashboard
左/上：Saved Words
右/中：Saved Phrases
底部：Top Context + Review Today + Refresh
```

验收：

- 能显示至少 3 个 saved words
- 能显示至少 3 个 saved phrases
- 能显示 top_context
- Refresh 按钮能重新请求 `/dashboard`
- Back 按钮能回到 Home

## Task B13 - CYD HTTP Helper

目标：集中管理 CYD 端所有 HTTP 请求，避免代码散乱。

建议函数：

```python
def api_get(path):
    # GET API_BASE + path，返回 JSON dict
    pass

def api_post(path, payload):
    # POST JSON，返回 JSON dict
    pass

def fetch_contexts():
    return api_get("/contexts")

def fetch_context(context_id):
    return api_get("/context/" + context_id)

def save_item(item_text, item_type, source_context):
    return api_post("/save_item", {...})

def fetch_dashboard():
    return api_get("/dashboard")
```

注意：

- 请求失败时返回 `None` 或 mock fallback
- 请求结束后尽量关闭 response，避免内存占用
- API 地址只从 `API_BASE` 拼接

验收：

- 所有网络请求都能在文件里快速找到
- 换 IP 时只改一处
- 网络失败时 CYD 不崩溃

## Task B14 - CYD 联调真实 API

目标：把 CYD mock 数据换成线 A 的真实 API。

前置条件：

- 线 A 后端已启动
- 后端使用 `--host 0.0.0.0`
- CYD 和 laptop 在同一网络
- `API_BASE` 改成 laptop 局域网 IP

测试顺序：

1. CYD 请求 `/contexts`
2. CYD 请求 `/context/coffee_shop`
3. CYD 请求 `/dashboard`
4. CYD 调用 `/save_item`
5. 用 Web dashboard 验证保存结果

验收：

- CYD 能获取 context
- CYD 能获取 dashboard
- CYD 保存 item 后，Web 能看到更新

## Task B15 - Web 和 CYD 一起演示

目标：完成最终 MVP 展示闭环。

演示流程：

```
1. Web 输入 Coffee Shop transcript
2. Web 点击 Analyze Text
3. Web 展示 keywords / phrases / detected context
4. Web 保存一个 word 或 phrase
5. CYD 打开 Dashboard
6. CYD 刷新并显示刚保存的 review item
```

验收：

- 全流程 1 分钟内完成
- 即使 CYD 临时连不上，Web 端也能完整展示闭环
- 讲解时能明确说出：Web 输入，FastAPI 分析，SQLite 保存，CYD 复习展示

## 推荐 UI 文案

CYD 小屏幕文案要短，不要用长句。

推荐：

```
Home
Real-world
Story
Dashboard
Keywords
Phrases
Context
Saved
Refresh
Back
```

避免：

```
Detected Context Classification Result
Automatically Generated Useful Learning Phrases
Saved Review Items For Today's Practice
```

## 推荐颜色和布局

MVP 重点是清楚，不追求复杂视觉。

建议：

- 背景用深色或浅色固定一种
- 按钮颜色保持一致
- 关键词和短语用列表，不用复杂卡片嵌套
- 每屏最多 3-5 个主要元素
- 字体优先可读，别太小

不要：

- 不要堆太多渐变
- 不要做过多动画
- 不要把所有内容塞在一屏
- 不要让按钮太小导致触摸困难

## 给线 A 的依赖

线 B 需要线 A 提供：

- 后端 API 地址
- `/contexts` 返回字段
- `/analyze_text` 返回字段
- `/dashboard` 返回字段
- 测试用 context ids

线 B 不要求线 A 改数据库结构。需要新字段时，先确认是否真的影响 MVP。

## 给线 C 的依赖

线 B 需要线 C 提供：

- 4 段 demo 文本
- 每段文本对应的讲解重点
- CYD 上适合显示的短 phrases
- 最终演示顺序

如果线 C 的文案太长，线 B 可以直接要求缩短到 CYD 可显示范围。

## 线 B 完成标准

线 B 完成时，必须满足：

- Web 输入页能独立完成输入、分析、保存、dashboard 刷新
- CYD 能显示 Home、Context Select、Insight View、Dashboard
- CYD 能用 mock 数据演示 UI
- CYD 能请求真实 `/dashboard`
- CYD 能保存至少一个 word 或 phrase
- API 地址集中配置，不散落在代码里
- 不引入 React、Node、Tailwind 等额外技术栈

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

### CYD 能连 Wi-Fi，但请求 API 失败

检查：

- laptop 后端是否用 `--host 0.0.0.0`
- Windows 防火墙是否拦截
- CYD 和 laptop 是否同一网络
- `API_BASE` 是否少写了 `http://`
- 后端端口是否还是 8000

### CYD 屏幕显示不下

优先处理：

1. 缩短 UI 文案
2. 限制 keywords 显示数量
3. 限制 phrases 显示数量
4. summary 只显示前 1-2 句
5. 必要时拆成下一屏

### 保存后 CYD 没看到 dashboard 更新

检查：

- `/save_item` 是否返回 `saved: true`
- 是否点击了 Refresh
- Web dashboard 是否能看到保存项
- CYD 是否请求到了最新 `/dashboard`
