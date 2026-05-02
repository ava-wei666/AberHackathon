# 线 C 详细任务书 - Content / Demo / QA

这份文档只给线 C 使用，目标是让负责内容、演示和测试的人可以直接上手做。线 C 不负责写后端主逻辑，不负责写 CYD UI 主逻辑，而是负责把 demo 内容准备好、把测试用例跑清楚、把最终展示讲顺。

## 统一技术栈

线 C 的产物统一使用下面这套工具和格式，MVP 阶段不要引入新的复杂技术栈。

```
文档：Markdown
文档目录：docs/
测试文本：Markdown 表格或代码块
Seed data 建议：JSON 字段建议，最终由线 A 写入 backend/seed_data.json
API 测试：PowerShell curl / 浏览器 / FastAPI docs
演示脚本：Markdown
Bug 记录：Markdown checklist
数据格式：JSON
```

## 明确不要使用

MVP 阶段先不要使用这些东西，避免资料分散和现场同步困难。

- 不用 Notion 作为唯一任务源
- 不用 Google Docs 作为唯一任务源
- 不用 Word 文档作为项目主文档
- 不用 Excel 管测试用例
- 不用 Jupyter Notebook
- 不用 Pandas 做数据处理
- 不爬取影视或小说数据库
- 不做真实地图数据
- 不做复杂用户研究报告
- 不强依赖 LLM 生成最终内容
- 不直接修改后端逻辑
- 不直接修改 CYD 主 UI 逻辑

如果需要临时用外部工具写草稿，可以用，但最终交付必须落到 `docs/` 的 Markdown 文档里。

## 当前文件归属

线 C 主要负责这些文件：

```
docs/
  TASK_PHASES.md
  LINE_A_BACKEND_TASKS.md
  LINE_B_WEB_CYD_TASKS.md
  LINE_C_CONTENT_DEMO_QA_TASKS.md
  DEMO_SCRIPT.md             # 建议新增
  API_TEST_CASES.md          # 建议新增
  DEMO_TEXTS.md              # 建议新增
  BUG_LOG.md                 # 建议新增
```

线 C 可以给这些文件提修改建议，但不要随意直接改主逻辑：

```
backend/seed_data.json
web/index.html
lvgl9_firmwares/scenelingo_dashboard.py
```

## 线 C 最终目标

线 C 最终要交付：

```
1. 4 段可直接复制的 demo 文本
2. 每段文本的期望 context / keywords / phrases
3. 一套 API 手动测试用例
4. 一份 60-90 秒 demo 讲稿
5. 一份 fallback 方案
6. 一份最终彩排 checklist
```

线 C 的价值不是“写更多功能”，而是让已有 MVP 在评委面前稳定、清楚、有说服力。

## Task C0 - 明确线 C 边界

目标：防止线 C 做着做着变成第四套技术栈。

线 C 负责：

- demo 内容
- 测试文本
- API 验收
- 文案长度控制
- 演示脚本
- fallback 方案
- bug 记录
- seed data 内容建议

线 C 不负责：

- FastAPI 路由实现
- SQLite 表结构实现
- NLP 代码实现
- CYD LVGL 页面实现
- Web 页面主交互实现
- 引入新框架

验收：

- 所有线 C 产物都在 `docs/` 中能找到
- 线 A 和线 B 可以直接拿线 C 的内容测试和演示

## Task C1 - 新建 Demo 文本库

目标：准备 4 段能稳定触发 MVP context 的文本。

建议新增：

```
docs/DEMO_TEXTS.md
```

必须覆盖：

```
Coffee Shop
Doctor / Pharmacy
Harry Potter - King's Cross
Sherlock Holmes - Baker Street
```

每段文本都要包含：

```
场景名
source_type
optional_context
可复制输入文本
期望 detected_context
期望 keywords
期望 phrases
展示讲解点
```

推荐模板：

````markdown
## Demo Text 1 - Coffee Shop

source_type: real-world
optional_context: null
expected_context: coffee_shop

Input:

```
Hi, can I get a latte with milk to go? How much is the large size?
````

Expected keywords:

- latte
- milk
- large
- size

Expected phrases:

- Can I Get
- to go
- with milk

Demo point:

This shows the system extracting useful ordering language from a real-world cafe conversation.

````

验收：

- 4 段文本都能直接复制进 Web 输入框
- 每段文本长度控制在 1-3 句
- 每段文本都包含明显场景关键词
- 不使用太长、太文学化、太难分类的句子

## Task C2 - Coffee Shop 内容准备

目标：准备最稳的 Coffee Shop demo。

输入文本建议：

```text
Hi, can I get a latte with milk to go? How much is the large size?
````

期望结果：

```
detected_context: coffee_shop
keywords: latte, milk, large, size, get
phrases: Can I Get, to go, with milk
```

讲解重点：

- 这是现实场景
- 学习目标是点单、询价、外带
- CYD dashboard 可以保存 `latte` 或 `Can I Get`

验收：

- `/analyze_text` 返回 `coffee_shop`
- keywords 里至少有 `latte` 或 `milk`
- phrases 里最好出现 `Can I Get` 或 `to go`

## Task C3 - Doctor / Pharmacy 内容准备

目标：准备最稳的 Doctor / Pharmacy demo。

输入文本建议：

```
I have a headache and a cough. Do I need medicine from the pharmacy?
```

期望结果：

```
detected_context: doctor_pharmacy
keywords: headache, cough, medicine, pharmacy
phrases: I Have a, need medicine, medicine pharmacy
```

讲解重点：

- 这是现实健康场景
- 学习目标是描述症状和询问药物
- 可以保存 `headache`、`medicine`、`I Have a`

验收：

- `/analyze_text` 返回 `doctor_pharmacy`
- keywords 里至少有 `headache`、`medicine`、`pharmacy` 中的两个
- summary 不要太长，CYD 能显示

## Task C4 - King's Cross 内容准备

目标：准备最稳的 Story Context demo。

输入文本建议：

```
Which platform should I use to catch the train to the magic school at King's Cross?
```

期望结果：

```
detected_context: kings_cross
keywords: platform, train, magic, school, cross
phrases: which platform, catch the train, magic school
```

讲解重点：

- 这是故事场景，不是真地图导航
- 学习目标是 station / train / school 相关表达
- 可以展示故事地点卡片，不需要真实路线规划

验收：

- source_type 用 `story`
- `/analyze_text` 返回 `kings_cross`
- phrases 里最好出现 `catch the train` 或 `magic school`

## Task C5 - Baker Street 内容准备

目标：准备最稳的 Detective Story demo。

输入文本建议：

```
The detective found a clue on Baker Street and tried to solve the case.
```

期望结果：

```
detected_context: baker_street
keywords: detective, clue, baker, street, case
phrases: solve the case, baker street, found clue
```

讲解重点：

- 这是故事场景
- 学习目标是 detective / clue / case 相关表达
- 适合展示关键词和短语提取

验收：

- source_type 用 `story`
- `/analyze_text` 返回 `baker_street`
- keywords 里至少有 `detective`、`clue`、`case` 中的两个

## Task C6 - 新建 API 测试文档

目标：让任何队友都能按文档手动测试后端。

建议新增：

```
docs/API_TEST_CASES.md
```

必须包含这些测试：

```
GET /
GET /contexts
GET /context/coffee_shop
POST /analyze_text - Coffee Shop
POST /analyze_text - Doctor / Pharmacy
POST /analyze_text - King's Cross
POST /analyze_text - Baker Street
POST /save_item - word
POST /save_item - phrase
GET /dashboard
```

推荐测试命令格式：

```powershell
curl http://localhost:8000/
```

```powershell
curl -X POST http://localhost:8000/analyze_text `
  -H "Content-Type: application/json" `
  -d "{\"raw_text\":\"Hi, can I get a latte with milk to go?\",\"source_type\":\"real-world\",\"optional_context\":null}"
```

每个测试都要写：

```
目的
命令
预期结果
失败时检查什么
```

验收：

- 线 A 可以照着测试后端
- 线 B 可以照着确认 Web/CYD 字段
- 不需要额外安装测试框架

## Task C7 - 新建 Bug Log

目标：用最简单的方式记录问题，不让问题散在聊天里。

建议新增：

```
docs/BUG_LOG.md
```

推荐格式：

```markdown
## Bug 001 - CYD cannot fetch dashboard

Status: open
Owner: Line B
Found by: Line C
Date: 2026-05-02

Steps:

1. Start backend with localhost only
2. CYD requests http://192.168.x.x:8000/dashboard
3. Request fails

Expected:

CYD should receive dashboard JSON.

Actual:

Request timeout.

Possible cause:

Backend did not start with --host 0.0.0.0.
```

状态统一用：

```
open
in-progress
fixed
won't-fix-for-mvp
```

验收：

- 每个 blocker 都有 owner
- 每个 bug 都有复现步骤
- 每次彩排后更新 bug 状态

## Task C8 - Seed Data 内容检查

目标：保证 `backend/seed_data.json` 的内容适合分类和展示。

线 C 检查内容：

- context title 是否短
- summary 是否能在 CYD 上显示
- seed_keywords 是否包含 demo 文本里的关键词
- seed_phrases 是否包含 demo 文本里的短语
- real-world 和 story 的 `type` 是否正确

检查清单：

```
coffee_shop:
- 是否有 latte / milk / order / menu / size
- 是否有 can i get / to go / with milk

doctor_pharmacy:
- 是否有 headache / cough / medicine / pharmacy
- 是否有 i have a / take this / make an appointment

kings_cross:
- 是否有 train / station / platform / magic / school
- 是否有 catch the train / magic school / which platform

baker_street:
- 是否有 detective / clue / case / evidence / street
- 是否有 solve the case / look for clues / baker street
```

验收：

- 线 C 给出的 demo 文本能被 seed data 支持
- 如果分类不准，先建议改 seed keywords，不建议马上改算法

## Task C9 - CYD 文案长度控制

目标：让线 B 的 CYD 页面不被长文案撑爆。

规则：

- 标题尽量不超过 20 个英文字符
- keyword 尽量是单词
- phrase 尽量 2-4 个词
- summary 最多 1-2 句
- dashboard label 使用短词

推荐 CYD 文案：

```
Home
Real-world
Story
Dashboard
Keywords
Phrases
Context
Saved
Review
Refresh
Back
```

不推荐：

```
Automatically Detected Learning Context
Useful Phrases Recommended For Memorization
Saved Review Items For Today's Learning Session
```

验收：

- 线 B 不需要大幅缩小字体也能显示文案
- demo 时观众能一眼看懂屏幕内容

## Task C10 - 新建 Demo Script

目标：准备 60-90 秒最终演示讲稿。

建议新增：

```
docs/DEMO_SCRIPT.md
```

讲稿结构：

```
1. 产品一句话
2. 痛点
3. MVP 方案
4. 实际 demo
5. 技术架构
6. 总结价值
```

推荐讲稿骨架：

```markdown
# SceneLingo Demo Script

## 0-10s - Product

SceneLingo is a context-based language learning dashboard. It turns real conversations and story scenes into keywords, useful phrases, and review items.

## 10-25s - Input

Here we paste a real coffee shop transcript into the web input page.

## 25-45s - NLP Result

The backend cleans the text, extracts keywords and phrases, and detects that this is a Coffee Shop context.

## 45-65s - Save Review Item

We save a useful word or phrase for later review.

## 65-85s - CYD Dashboard

The CYD refreshes the dashboard and shows the saved review item.

## 85-90s - Architecture

Web handles input, FastAPI handles NLP and storage, and CYD acts as the learning dashboard.
```

验收：

- 讲稿能在 90 秒内讲完
- 每句话都服务 demo，不讲太多理论
- 技术架构一句话能讲清楚

## Task C11 - 准备 Fallback 方案

目标：比赛现场出问题时仍然能演示核心价值。

必须准备 3 个 fallback：

```
Fallback 1: CYD 网络失败
用 Web 页面完整演示输入、分析、保存、dashboard。

Fallback 2: 后端临时启动失败
展示提前保存的截图或 JSON 输出，讲清楚已经完成的接口和数据流。

Fallback 3: 文本分类结果不理想
使用 optional_context 手动指定 context，保证演示继续。
```

每个 fallback 都要写：

```
触发条件
现场操作
讲解话术
不影响的核心价值
```

验收：

- 任意一条线临时失败时，demo 还能继续
- fallback 不撒谎，只说 MVP 现场网络或设备限制

## Task C12 - 彩排 Checklist

目标：最终展示前按清单检查，减少现场意外。

建议新增到 `docs/DEMO_SCRIPT.md` 或单独文档：

```markdown
## Rehearsal Checklist

- [ ] Backend starts successfully
- [ ] Web page can call /contexts
- [ ] Coffee Shop text returns coffee_shop
- [ ] Save Word works
- [ ] Dashboard shows saved item
- [ ] CYD is on the same Wi-Fi
- [ ] CYD can refresh dashboard
- [ ] Demo text is copied somewhere easy to access
- [ ] Fallback screenshots are ready
- [ ] Speaker can finish in 90 seconds
```

验收：

- 每次彩排都能记录通过 / 未通过
- 未通过项写入 `BUG_LOG.md`

## Task C13 - 评委问答准备

目标：准备最可能被问到的问题，避免现场卡住。

常见问题：

```
Q: 为什么不用 CYD 直接做 NLP？
A: ESP32/CYD 更适合展示和轻交互，重 NLP 放在 laptop FastAPI 后端更稳定，也更容易扩展。

Q: 为什么没有实时语音识别？
A: MVP 聚焦文本分析闭环。语音可以先转成 transcript，再进入同一个 /analyze_text pipeline。

Q: 为什么没有 GPS 或地图？
A: Story context 在 MVP 中是学习场景卡片，不是真路线规划。我们先证明 context-based learning dashboard 的核心价值。

Q: 没有 LLM 时还能用吗？
A: 可以。当前 rule-based pipeline 可以完成 cleaning、keywords、phrases 和 context tagging。LLM 是后续增强层。

Q: 这个项目怎么扩展？
A: 增加更多 contexts、接入 ASR、接入 LLM summary、增加 spaced repetition review。
```

验收：

- 每个队友都能回答项目为什么这样设计
- 回答不引入未完成功能当作已完成能力

## Task C14 - 最终展示材料

目标：把最终展示需要的东西集中到一处。

建议在 `docs/DEMO_SCRIPT.md` 末尾整理：

```
Demo URL:
http://localhost:8000
web/index.html

Laptop LAN API:
http://192.168.x.x:8000

Main demo text:
Hi, can I get a latte with milk to go? How much is the large size?

Backup demo text:
I have a headache and a cough. Do I need medicine from the pharmacy?

CYD screen order:
Home -> Dashboard -> Saved Items

Speaker order:
Person 1: Product + input
Person 2: NLP + backend
Person 3: CYD + summary
```

验收：

- 演示前 5 分钟可以快速打开这份材料
- 不需要在聊天记录里翻找关键信息

## Task C15 - 线 C 每日 / 每轮同步格式

目标：让三条线同步时信息密度高，不浪费时间。

推荐同步格式：

```
Line C update:

Done:
- Prepared 4 demo texts
- Tested Coffee Shop and Doctor APIs

Blocked:
- King's Cross classification returns coffee_shop

Need from Line A:
- Add platform / train / magic to kings_cross seed_keywords

Need from Line B:
- CYD summary area can show 2 lines max

Next:
- Finish 90-second demo script
```

验收：

- 每次同步都能明确谁要做什么
- blocker 有 owner
- 不把问题只停留在口头讨论

## 线 C 完成标准

线 C 完成时，必须满足：

- `docs/DEMO_TEXTS.md` 有 4 段可复制测试文本
- `docs/API_TEST_CASES.md` 有完整手动 API 测试
- `docs/DEMO_SCRIPT.md` 有 60-90 秒讲稿
- `docs/BUG_LOG.md` 记录过至少一次彩排问题
- 每段 demo 文本都有期望 context、keywords、phrases
- fallback 方案明确
- 最终讲稿不承诺 MVP 没做的功能
- 所有文档都在 `docs/`，不散落在外部工具里

## 最短执行顺序

1. 新建 `docs/DEMO_TEXTS.md`
2. 写 Coffee Shop 和 Doctor 两段测试文本
3. 用 Web 或 curl 测 `/analyze_text`
4. 补 King's Cross 和 Baker Street 文本
5. 新建 `docs/API_TEST_CASES.md`
6. 新建 `docs/DEMO_SCRIPT.md`
7. 新建 `docs/BUG_LOG.md`
8. 和线 A 调 seed keywords / seed phrases
9. 和线 B 控制 CYD 文案长度
10. 全员彩排 60-90 秒 demo

## 常见问题处理

### 分类结果不对

优先检查：

- demo 文本是否包含目标 context 的明显关键词
- `source_type` 是否选对
- `backend/seed_data.json` 是否包含这些关键词
- 是否可以用 `optional_context` 做演示 fallback

不要第一时间要求线 A 重写算法。

### Keywords 不适合展示

优先处理：

- 修改 demo 文本，让学习词更明显
- 建议线 A 调整 stopwords
- 建议线 A 调整 seed keywords

### Phrases 太奇怪

优先处理：

- 在 seed phrases 里加入更好的短语
- demo 文本中明确包含该短语
- 不要让句子太长

### CYD 显示不下

优先处理：

- 缩短 summary
- 缩短 phrases
- 每屏只显示 Top 3
- 把长标题换成短标题

### Demo 超时

删掉：

- 技术细节解释
- 不必要的背景故事
- P2 扩展功能

保留：

- 输入
- 分析
- 保存
- CYD dashboard
- 架构一句话
