# 线 C 详细任务书 - CYD LVGL Display / Hardware Integration

这份文件只给线 C 使用。新的三线分配下，线 C 不再负责内容文档、demo 脚本或 QA 文档，线 C 只负责 CYD 硬件展示端：把 SceneLingo 的学习结果显示在 Cheap Yellow Display 上，并完成刷新 dashboard 和保存复习项的交互。

## 三条线重新分配

```
线 A：Backend + NLP + SQLite
线 B：Web Input + Web Dashboard
线 C：CYD LVGL Display + Hardware Integration
```

线 C 只做 CYD，不写后端，不写 Web，不继续拆新文档。

## 统一技术栈

线 C 技术栈固定如下：

```
设备：CYD / ESP32 Cheap Yellow Display
语言：MicroPython
UI：LVGL
网络：Wi-Fi / hotspot
HTTP：urequests 或 MicroPython HTTP requests
数据格式：JSON
后端 API：FastAPI，由线 A 提供
```

## 明确不要使用

MVP 阶段不要引入这些东西，避免现场调试爆炸：

- 不写 FastAPI 后端
- 不写 Web 页面
- 不直接读 SQLite
- 不在 CYD 上做 NLP
- 不在 CYD 上做实时语音识别
- 不直接调用 LLM
- 不做 GPS / 地图 / 路线规划
- 不做复杂动画
- 不用大型图片资源
- 不删除 `touch_color_test.py`
- 不继续写新的任务文档

## 当前文件归属

线 C 主要负责：

```
embedded/
  touch_color_test.py          # 已有测试文件，尽量不破坏
  scenelingo_dashboard.py      # 建议新增，作为 CYD 业务主文件
```

线 C 不负责：

```
backend/                       # 线 A
web/index.html                 # 线 B
docs/                          # 不再继续拆文档
```

## 线 C 最终目标

CYD 端要完成这个闭环：

```
CYD Home
  -> Context Select
  -> Insight View
  -> Save Word / Save Phrase
  -> Dashboard View
  -> Refresh
```

核心原则：

- CYD 只展示 API 返回结果
- CYD 不做 NLP
- CYD 不读数据库
- CYD 网络失败时不能直接崩溃
- CYD 页面文案要短，按钮要大

## 固定 API 地址规则

CYD 访问 laptop 后端时，必须使用 laptop 的局域网 IP：

```
http://192.168.x.x:8000
```

CYD 业务文件顶部只保留一个 API 地址配置：

```python
API_BASE = "http://192.168.x.x:8000"
```

线 A 局域网联调时应这样启动：

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

验收：

- 换后端 IP 只改一处
- API 地址包含 `http://`
- CYD 和 laptop 在同一 Wi-Fi / hotspot

## Task C0 - CYD 基础能力确认

目标：先确认硬件、屏幕、触摸都正常。

任务：

- 运行已有 `touch_color_test.py`
- 确认屏幕显示正常
- 确认触摸能响应
- 确认屏幕方向正确
- 确认按钮能点中

验收：

- CYD 能显示测试画面
- 触摸有响应
- 不破坏已有测试文件

## Task C1 - Wi-Fi / Network 确认

目标：确认 CYD 能连到和 laptop 同一个网络。

任务：

- 配置 Wi-Fi SSID / password
- CYD 连上 Wi-Fi 或 hotspot
- 记录 CYD IP
- 确认 laptop 和 CYD 在同一网段

验收：

- CYD 成功连接 Wi-Fi
- 后端地址使用 laptop 局域网 IP
- 不再使用 `localhost` 作为 CYD API 地址

## Task C2 - 新建 CYD 业务主文件

目标：不要把 SceneLingo 业务 UI 写进测试文件。

建议新增：

```
embedded/scenelingo_dashboard.py
```

文件结构建议：

```
API config
Wi-Fi config / connect_wifi()
mock data
HTTP helper
LVGL style helper
screen navigation
Home screen
Context Select screen
Insight View
Dashboard View
Save interaction
```

验收：

- `scenelingo_dashboard.py` 可以单独上传运行
- `API_BASE` 在文件顶部
- 不删除 `touch_color_test.py`

## Task C3 - Mock 数据先行

目标：后端或网络还没好时，CYD UI 也能先开发。

建议 mock：

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
- 换真实 API 时不重写 UI 结构

## Task C4 - HTTP Helper

目标：所有 API 请求集中管理，避免散落在按钮回调里。

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

- 换 IP 只改 `API_BASE`
- 请求失败时返回 `None` 或 mock fallback
- 请求结束后尽量关闭 response
- 网络失败时 CYD 不崩溃

## Task C5 - Screen Navigation

目标：先把页面切换跑通。

需要的页面：

```
Home
Context Select
Insight View
Dashboard View
```

需要的基础能力：

- `show_home()`
- `show_context_select(source_type)`
- `show_insight(data)`
- `show_dashboard()`
- `go_back()` 或每页 Back 按钮

验收：

- 页面之间可以来回切换
- 切换不会卡死
- 每页都有明确返回路径

## Task C6 - Home Screen

目标：做 CYD 第一屏。

屏幕内容：

```
SceneLingo

[Real-world]
[Story]
[Dashboard]
```

按钮行为：

- Real-world -> Context Select，只显示 real-world contexts
- Story -> Context Select，只显示 story contexts
- Dashboard -> Dashboard View

验收：

- 三个按钮都能点击
- 按钮够大
- 文案不挤出屏幕

## Task C7 - Context Select Screen

目标：显示 4 个 context 入口。

Real-world：

```
Coffee Shop
Doctor / Pharmacy
```

Story：

```
King's Cross
Baker Street
```

点击行为：

```
点击 context
  -> 优先 GET /context/{id}
  -> 成功则进入 Insight View
  -> 失败则用 mock context 进入 Insight View
```

验收：

- 4 个 context 都能进入
- Back 能回 Home
- 请求失败时不黑屏

## Task C8 - Insight View

目标：显示某个 context 或某次分析结果。

必须显示：

```
Context title
Top Keywords
Useful Phrases
Summary
Back
```

交互：

- 点击 keyword -> 保存为 word
- 点击 phrase -> 保存为 phrase

验收：

- Coffee Shop 数据能看清楚
- 至少显示 5 个 keywords
- 至少显示 3 个 phrases
- summary 最多显示 1-2 句
- 长 phrase 不撑破布局

## Task C9 - Dashboard View

目标：显示复习列表和统计。

接口：

```
GET /dashboard
```

必须显示：

```
Saved Words
Saved Phrases
Top Context
Review Today
Refresh
Back
```

验收：

- Web 保存 item 后，CYD Refresh 能看到
- saved words 和 saved phrases 分开显示
- Refresh 不会卡死
- 网络失败时显示 mock dashboard 或错误提示

## Task C10 - Save Interaction

目标：CYD 可以保存 word / phrase 到后端。

接口：

```
POST /save_item
```

请求：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

任务：

- 点击 keyword 时传 `item_type = word`
- 点击 phrase 时传 `item_type = phrase`
- 传当前 `source_context`
- 保存成功显示 `Saved`
- 保存失败显示 `Save failed` 或 fallback

验收：

- CYD 保存 word 后，Web dashboard 能看到
- CYD 保存 phrase 后，Web dashboard 能看到
- `item_type` 不传错

## Task C11 - 真实 API 联调

目标：把 mock 数据切到线 A 的真实后端。

前置条件：

- 线 A 后端已启动
- 后端使用 `--host 0.0.0.0`
- CYD 和 laptop 在同一网络
- `API_BASE` 是 laptop 局域网 IP

联调顺序：

```
1. CYD 请求 GET /dashboard
2. Web 保存一个 word
3. CYD Refresh Dashboard
4. CYD 显示 Web 刚保存的 item
5. CYD 保存一个 phrase
6. Web Refresh Dashboard 验证更新
```

验收：

- CYD 能请求真实后端
- CYD 能显示真实 dashboard
- CYD 能保存 item
- Web 和 CYD 看到同一份 dashboard 数据

## Task C12 - 小屏幕显示规则

目标：保证 CYD 画面可读、可点、不卡。

规则：

- 每屏最多 3-5 个主要元素
- keywords 最多显示 5 个
- phrases 最多显示 3 个
- summary 最多 1-2 句
- 按钮要大，不要太贴边
- 长文本优先截断或换行

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

- 字体不用缩到看不清
- 按钮不会互相重叠
- 手指能点中主要按钮

## Task C13 - 给线 A 的反馈

线 C 只反馈 API 和 CYD 显示需要：

- 哪个接口 CYD 请求失败
- CYD 使用的 `API_BASE`
- 返回字段是否太长
- dashboard 字段是否能直接显示
- 保存 item 后是否能看到更新

线 C 不要求线 A 改数据库结构，除非当前 API 无法完成 CYD 展示。

## Task C14 - 给线 B 的联调点

线 B 是 Web 输入和 Web Dashboard。线 C 需要线 B 帮忙验证：

- Web 保存 word 后，CYD dashboard 是否能看到
- CYD 保存 phrase 后，Web dashboard 是否能看到
- Web 页面中哪些字段适合 CYD 展示

线 C 不修改 `web/index.html`。

## Task C15 - LVGL 配色对齐英格兰绿主题

**产品动机**：CYD 和 Web 现在看起来像两个不同产品。统一配色系统是"这是一套完整产品"的视觉证明，对作品集展示非常重要。

目标：把 `scenelingo_dashboard.py` 里散落的硬编码颜色提取成命名颜色常量，并对齐 Web 端的英格兰绿色系。

在文件顶部"显示配置区"新增颜色常量块（放在 `_C12_*` 常量旁边）：

```python
# ==================== C15 配色常量（英格兰绿·乡村色系）====================
# 与 web/index.html 的 CSS 变量系统对齐，保证 Web 和 CYD 属于同一产品视觉。
_COL_PRIMARY    = lv.color_hex(0x2d4a1e)   # 英格兰深绿（按钮、标题）
_COL_PRIMARY_LT = lv.color_hex(0x3d6428)   # 稍浅绿（按钮悬停 / 次要按钮）
_COL_ACCENT     = lv.color_hex(0x8b6914)   # 铜金（点缀、保存成功提示）
_COL_BG         = lv.color_hex(0xf5f1e8)   # 象牙白（页面背景）
_COL_SURFACE    = lv.color_hex(0xffffff)   # 卡片白（列表项底色）
_COL_TEXT       = lv.color_hex(0x1c1c1c)   # 正文墨黑
_COL_MUTED      = lv.color_hex(0x5a5a4a)   # 次要文字暖灰（副标题、label）
_COL_DANGER     = lv.color_hex(0x8b0000)   # 深红（保存失败提示）
```

替换规则（逐页检查，不要批量替换，先确认颜色含义再改）：

| 旧用法 | 替换为 | 说明 |
|--------|--------|------|
| `lv.color_hex(0x8899AA)` 等灰色副标题 | `_COL_MUTED` | 副标题、小标签 |
| 主按钮背景色（目前是 LVGL 默认蓝） | `_COL_PRIMARY` | Real-world / Story / Dashboard 按钮 |
| keyword 按钮背景 | `_COL_PRIMARY_LT` | Insight View 里的 keyword 按钮 |
| 保存成功状态文字颜色 | `_COL_ACCENT` | `Saved: xxx` 提示 |
| 保存失败状态文字颜色 | `_COL_DANGER` | `Save failed` 提示 |
| 屏幕背景（如果有手动设置） | `_COL_BG` | 整体背景 |

**不需要做的事**：

- 不需要改字体（LVGL 自带字体，不支持自定义 Web 字体）
- 不需要做动画
- 不需要改布局结构

验收：

- Home 页按钮背景是深绿 `#2d4a1e`，不是 LVGL 默认蓝
- Insight View 里 keyword 按钮背景是稍浅绿 `#3d6428`
- 保存成功的状态文字是铜金色
- 保存失败的状态文字是深红
- 屏幕整体背景接近象牙白（如果硬件支持设置）
- 颜色常量集中在文件顶部一个区块，不散落在各 render 函数里

---

## 线 C 完成标准

线 C 完成时，必须满足：

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

## 常见问题处理

### CYD 连不上后端

检查：

- 后端是否用 `--host 0.0.0.0` 启动
- CYD 和 laptop 是否同一 Wi-Fi / hotspot
- `API_BASE` 是否是 laptop IP，不是 `localhost`
- Windows 防火墙是否拦截
- URL 是否包含 `http://`

### Dashboard 为空

检查：

- Web 是否已经保存过 item
- CYD 是否请求了最新 `/dashboard`
- 返回 JSON 字段是否是 `saved_words` / `saved_phrases`
- 是否点击了 Refresh

### 屏幕显示不下

优先处理：

1. 减少显示数量
2. 缩短 label
3. summary 只显示 1 句
4. phrases 太长就截断
5. 必要时拆成下一屏

### 保存失败

检查：

- `POST /save_item` payload 是否包含 `item_text`
- `item_type` 是否是 `word` 或 `phrase`
- `source_context` 是否是当前 context id
- 后端是否返回 `saved: true`
