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
embedded/               # 线 C
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

## Task B12 - 视觉基础：CDN 引入 + CSS 变量系统

**产品动机**：当前页面是开发者原型观感，作为作品集展示需要第一眼建立"这是一个有设计感的产品"的印象。所有后续视觉任务都依赖本任务建立的变量系统。

目标：在 `web/index.html` 的 `<head>` 里引入三个外部资源，并定义项目级 CSS 变量。

引入资源（全部 CDN，不需要 npm）：

```html
<!-- Pico CSS 基础 reset -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css">

<!-- 英伦字体：标题装饰 / section 标题 / 正文 -->
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English&family=Playfair+Display:wght@400;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">

<!-- 图标（按需加载，不拉全量包） -->
<script src="https://code.iconify.design/iconify-icon/1.0.8/iconify-icon.min.js" defer></script>
```

在现有 `<style>` 的 `:root` 里替换或追加以下变量：

```css
:root {
  /* 英格兰绿·乡村色系 */
  --sw-bg:           #f5f1e8;   /* 象牙白页面背景 */
  --sw-surface:      #ffffff;   /* 卡片白 */
  --sw-primary:      #2d4a1e;   /* 英格兰深绿（主按钮、标题） */
  --sw-primary-hover:#3d6428;   /* 悬停稍浅 */
  --sw-accent:       #8b6914;   /* 铜金点缀 */
  --sw-text:         #1c1c1c;   /* 正文墨黑 */
  --sw-text-muted:   #5a5a4a;   /* 次要文字暖灰 */
  --sw-border:       #c8bda0;   /* 边框暖褐 */
  --sw-chip-word:    #e8f0e0;   /* keyword chip 浅绿底 */
  --sw-chip-phrase:  #f5e8d0;   /* phrase chip 浅金底 */
  --sw-danger:       #8b0000;   /* 删除 / 错误深红 */
}
```

验收：

- 浏览器打开页面，字体已切换为衬线体（不再是系统默认 sans-serif）
- 页面背景色为象牙白 `#f5f1e8`，不是纯白
- 控制台无 CDN 加载错误
- 不引入 React / Vue / Node / npm，不新增构建步骤

---

## Task B13 - 品牌 Header 重构

**产品动机**：页面首屏是产品的名片。当前 `<h1>Scene Words</h1>` 没有任何品牌感。一个有辨识度的 header 能让评委或招聘者在 3 秒内判断"这是认真做的项目"。

目标：重构页面 `<header>` 区域，建立英伦乡村风品牌形象。

视觉规格：

| 元素 | 字体 | 大小 | 颜色 |
|------|------|------|------|
| `<h1>Scene Words</h1>` | IM Fell English | `clamp(36px, 5vw, 56px)` | `--sw-primary` |
| 副标题 `Learn English in Context` | Playfair Display italic | 18px | `--sw-text-muted` |
| 分割线装饰 | 纯 CSS | — | `--sw-accent` |

分割线 CSS（header 底部）：

```css
.sw-divider {
  border: none;
  border-top: 2px solid var(--sw-primary);
  border-bottom: 1px solid var(--sw-accent);
  margin: 1rem 0 2rem;
  position: relative;
}
.sw-divider::after {
  content: '✦';
  position: absolute;
  left: 50%;
  top: -11px;
  transform: translateX(-50%);
  background: var(--sw-bg);
  color: var(--sw-accent);
  padding: 0 12px;
  font-size: 16px;
}
```

验收：

- "Scene Words" 用 IM Fell English 大字显示，视觉上像英伦报纸标题
- 副标题用 Playfair Display 斜体，位于主标题正下方
- 标题区和正文区之间有带菱形的双线分割
- 移动端不错位（使用 `clamp` 字号）

---

## Task B14 - 组件美化：chip、按钮、卡片

**产品动机**：五个 section 当前视觉权重相同，用户无法快速判断重要信息在哪里。通过卡片层次和 chip 颜色区分，引导视线流向"detected context → keywords → phrases → save"。

目标：统一五类视觉组件的样式。

**Section 卡片**（每个 section 包裹 `<section class="sw-card">`）：

```css
.sw-card {
  background: var(--sw-surface);
  border: 1px solid var(--sw-border);
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 3px rgba(45, 74, 30, 0.08);
}
.sw-card h2 {
  font-family: 'Playfair Display', serif;
  color: var(--sw-primary);
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}
```

**Keyword chip**（`.chip.word`）：

```css
.chip { display: inline-block; border-radius: 4px; padding: 3px 10px; font-size: 13px; margin: 3px; font-family: 'Crimson Text', serif; }
.chip.word   { background: var(--sw-chip-word);   color: var(--sw-primary); border: 1px solid #b8d4a0; }
.chip.phrase { background: var(--sw-chip-phrase);  color: var(--sw-accent);  border: 1px solid #d4b87a; }
```

**主按钮**（Analyze / Save / Refresh）：

```css
.sw-btn-primary {
  background: var(--sw-primary);
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 20px;
  font-family: 'Playfair Display', serif;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.sw-btn-primary:hover { background: var(--sw-primary-hover); }
.sw-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
```

**状态 badge**（section 右上角 `status`）：小字 + 圆角底色，success 用 `#e8f0e0` 配深绿字，error 用淡红底深红字。

验收：

- keyword chip 是绿色系，phrase chip 是金色系，两类可以一眼区分
- 五个 section 都是白色卡片，整体页面背景象牙白，层次分明
- 主按钮深绿，非破坏性操作（Demo 按钮）用轮廓样式
- 任何按钮 disabled 状态下不可误点

---

## Task B15 - Dashboard 升级：删除功能 + 场景名称显示

**产品动机**：没有删除功能的复习列表是"只进不出"的数据垃圾桶，用户无法维护自己的词库。同时 `top_context` 显示原始 id（`coffee_shop`）不是产品该有的体验。

前置条件：线 A 完成 A18（DELETE 接口）和 A19（top_context_title 字段）。

目标：

1. saved_words / saved_phrases 每条右侧加删除按钮
2. top_context 显示 `top_context_title` 而不是 id

**删除按钮逻辑**：

```javascript
async function deleteItem(id, type) {
  await fetch(`${API_BASE}/saved_item/${id}`, { method: 'DELETE' });
  loadDashboard(); // 删除成功后刷新
}
```

注意：`/dashboard` 接口目前不返回每条 item 的 `id`，需要线 A 在 `saved_words` / `saved_phrases` 条目里附带 `id` 字段（和 A18/A19 一起确认）。

**删除按钮样式**：

```css
.sw-btn-delete {
  background: none;
  border: none;
  color: var(--sw-danger);
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  opacity: 0.6;
}
.sw-btn-delete:hover { opacity: 1; }
```

**top_context 显示**：

```javascript
// 旧
panel.textContent = dashboard.top_context ?? 'None yet';
// 新
panel.textContent = dashboard.top_context_title ?? dashboard.top_context ?? 'None yet';
```

验收：

- saved_words / saved_phrases 每条右侧有小删除按钮
- 点击删除后列表立即更新，不需要手动 Refresh
- Dashboard 显示"Coffee Shop"而不是"coffee_shop"
- 删除请求失败时按钮恢复，status 行显示错误提示

---

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
