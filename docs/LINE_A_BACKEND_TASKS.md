# 线 A 详细任务书 - Backend / NLP / Database

这份文档只给线 A 使用，目标是让负责后端的人不用再讨论技术选型，直接按任务推进。线 A 的最终交付物是一个稳定的 FastAPI 后端，负责接收文本、完成 NLP 分析、保存结果，并给 Web 和 CYD 提供统一 API。

## 统一技术栈

线 A 只使用下面这套技术栈，MVP 阶段不要混用其他后端框架。

```
语言：Python
虚拟环境：.venv
Web 框架：FastAPI
API Server：Uvicorn
数据校验：Pydantic
数据库：SQLite
NLP：Python 标准库 rule-based pipeline
数据格式：JSON
```

## 明确不要使用

MVP 阶段先不要引入这些东西，避免技术栈混乱和现场调试成本上升。

- 不用 Flask
- 不用 Django
- 不用 Node.js / Express 做后端
- 不用 MongoDB / PostgreSQL / MySQL
- 不用 Redis
- 不用 Docker
- 不强依赖 spaCy / NLTK
- 不强依赖 LLM API
- 不做用户登录注册
- 不做复杂服务拆分

如果后面要接 LLM，只能作为 `nlp_engine.py` 里的可选增强层，不改变主 API，不影响无网络演示。

## 当前文件归属

线 A 主要负责这些文件：

```
backend/
  __init__.py
  main.py
  nlp_engine.py
  database.py
  seed_data.json
requirements.txt
scenelingo.db
```

说明：

- `backend/main.py`：FastAPI 路由层
- `backend/nlp_engine.py`：文本清洗、关键词、短语、context 分类、summary
- `backend/database.py`：SQLite 建表、读写、dashboard 汇总
- `backend/seed_data.json`：4 个 MVP context 的种子数据
- `requirements.txt`：Python 依赖版本
- `scenelingo.db`：运行后自动生成，不提交到 Git

## 本地启动步骤

在 PowerShell 里执行：

```powershell
cd C:\hackathon
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

如果 PowerShell 不允许激活虚拟环境：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

启动成功后访问：

```
http://localhost:8000
```

预期返回：

```json
{
  "status": "ok",
  "service": "SceneLingo API"
}
```

## 线 A 最终目标

后端必须稳定提供这 5 个接口：

```
POST /analyze_text
GET  /contexts
GET  /context/{id}
POST /save_item
GET  /dashboard
```

整体数据流：

```
Web / CYD
  -> POST /analyze_text
  -> nlp_engine.py
  -> database.py
  -> SQLite
  -> API response
  -> Web / CYD dashboard
```

## Task A0 - 环境确认

目标：确认后端开发环境可用。

操作：

```powershell
cd C:\hackathon
.\.venv\Scripts\Activate.ps1
python --version
pip list
python -m py_compile backend\main.py backend\nlp_engine.py backend\database.py
```

验收：

- 能激活 `.venv`
- `fastapi`、`uvicorn`、`pydantic` 已安装
- Python 编译检查无报错

不要做：

- 不要重新创建另一个 venv
- 不要把依赖装到系统 Python
- 不要新增另一个 requirements 文件

## Task A1 - API 健康检查

目标：保证后端服务能被 Web、CYD 和队友访问。

文件：

```
backend/main.py
```

接口：

```
GET /
```

返回：

```json
{
  "status": "ok",
  "service": "SceneLingo API"
}
```

测试：

```powershell
curl http://localhost:8000/
```

验收：

- 浏览器打开 `http://localhost:8000` 能看到 JSON
- 命令行 curl 能返回同样内容

## Task A2 - Seed Data 管理

目标：维护 4 个 MVP context，保证分类和展示都有基础数据。

文件：

```
backend/seed_data.json
```

必须包含：

```
coffee_shop
doctor_pharmacy
kings_cross
baker_street
```

每个 context 必须有：

```json
{
  "id": "coffee_shop",
  "title": "Coffee Shop",
  "type": "real-world",
  "tag": "coffee shop",
  "summary": "...",
  "seed_keywords": ["coffee", "latte"],
  "seed_phrases": ["can i get", "to go"]
}
```

字段规范：

- `id` 用 snake_case
- `type` 只能是 `real-world` 或 `story`
- `seed_keywords` 全部小写英文
- `seed_phrases` 全部小写英文
- 不要在 JSON 里写注释

验收：

- 后端启动时能读取 `seed_data.json`
- `GET /contexts` 能返回 4 个 context
- `GET /context/coffee_shop` 能返回 Coffee Shop 数据

## Task A3 - SQLite 初始化

目标：启动后端时自动创建数据库和三张表。

文件：

```
backend/database.py
```

数据库文件：

```
C:\hackathon\scenelingo.db
```

三张表：

```
contexts
analysis_results
review_items
```

表职责：

- `contexts`：保存 4 个场景定义
- `analysis_results`：保存每次文本分析结果
- `review_items`：保存用户点击复习的 word / phrase

必须实现的函数：

```python
init_db()
list_contexts()
get_context_by_id(context_id)
insert_analysis(raw_text, result)
save_review_item(item_text, item_type, source_context)
get_dashboard()
```

测试：

```powershell
python -c "from backend.database import init_db, list_contexts; init_db(); print(len(list_contexts()))"
```

验收：

- 第一次启动后自动生成 `scenelingo.db`
- 重复启动不会重复插入脏数据
- 修改 `seed_data.json` 后重启，contexts 能同步更新

## Task A4 - Text Cleaning

目标：把输入文本清洗成适合统计的 tokens。

文件：

```
backend/nlp_engine.py
```

输入例子：

```
Um, hi, hi, can I get a latte with milk to go please?
```

期望 cleaned tokens 类似：

```
hi get latte milk go
```

必须处理：

- 英文大小写统一为小写
- 去掉无意义符号
- 去掉 filler words：`um`、`uh`、`erm`、`hmm`、`like`
- 去掉 stopwords：`a`、`an`、`the`、`to`、`of` 等
- 去掉连续重复词

不要做：

- 不要接复杂 NLP 依赖
- 不要为了中文、日文等多语言扩展改主流程
- 不要把 cleaning 写到 `main.py`

测试：

```powershell
python -c "from backend.nlp_engine import analyze_text; print(analyze_text('Um, hi, hi, can I get a latte with milk to go please?')['cleaned_text'])"
```

验收：

- 输出里没有 `um`
- 输出里没有 `please`
- 连续重复的 `hi hi` 被压缩

## Task A5 - Keyword Extraction

目标：提取 Top 5 有学习价值的关键词。

文件：

```
backend/nlp_engine.py
```

规则：

- 基于 cleaned tokens 统计词频
- 长度小于等于 2 的词不作为 keyword
- 默认最多返回 5 个

输出格式：

```json
["latte", "milk", "large", "size", "receipt"]
```

测试文本：

```
Can I get a latte with milk? I want a large latte to go.
```

验收：

- `latte` 应该排在前面
- 返回必须是 list
- 不要返回完整句子

## Task A6 - Phrase Extraction

目标：提取 Top 3 有学习价值的短语。

文件：

```
backend/nlp_engine.py
```

规则优先级：

1. 先匹配当前 context 的 `seed_phrases`
2. 再从 cleaned tokens 里拼 3 词短语
3. 不够时再拼 2 词短语
4. 最多返回 3 个

输出格式：

```json
["Can I Get", "to go", "latte milk"]
```

注意：

- phrase 是给学习者看的，不是给机器看的
- 可以保留轻量格式化，但不要过度美化
- MVP 不做复杂语法分析

验收：

- Coffee Shop 文本里出现 `can i get` 时，phrases 应该优先包含它
- 返回必须是 list
- 最多 3 个

## Task A7 - Context Classification

目标：把输入文本分类到 MVP context。

文件：

```
backend/nlp_engine.py
```

分类范围：

```
coffee_shop
doctor_pharmacy
kings_cross
baker_street
```

分类规则：

- 如果请求里有 `optional_context`，优先使用它
- 如果没有，就用 cleaned tokens 和 seed keywords 做打分
- 分数最高的 context 作为 detected context
- 如果完全没有命中，按 `source_type` 给一个默认 context

返回结构：

```json
{
  "id": "coffee_shop",
  "title": "Coffee Shop",
  "type": "real-world",
  "tag": "coffee shop",
  "summary": "...",
  "confidence": 0.69
}
```

验收测试文本：

```
Coffee Shop:
Hi, can I get a latte with milk to go?

Doctor / Pharmacy:
I have a headache and need medicine from the pharmacy.

King's Cross:
Which platform should I use to catch the train to the magic school?

Baker Street:
The detective found a clue and started to solve the case.
```

验收：

- 四段文本能分类到对应 context
- `confidence` 是数字
- 不要返回只有字符串的 context，要返回对象

## Task A8 - Summary 生成

目标：给每次分析生成一句简短学习建议。

文件：

```
backend/nlp_engine.py
```

MVP 规则：

- 先用模板生成
- 不依赖 LLM
- summary 里包含 context title
- summary 里包含 2-3 个重点关键词

例子：

```
This looks like Coffee Shop. Focus on latte, milk, size. Practice phrases like 'Can I Get'.
```

验收：

- 没有外网时也能生成
- 返回是普通字符串
- 不要超过 1-2 句话

## Task A9 - POST /analyze_text

目标：打通核心分析接口。

文件：

```
backend/main.py
backend/nlp_engine.py
backend/database.py
```

请求：

```json
{
  "raw_text": "Hi, can I get a latte with milk to go?",
  "source_type": "real-world",
  "optional_context": null
}
```

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

测试：

```powershell
curl -X POST http://localhost:8000/analyze_text `
  -H "Content-Type: application/json" `
  -d "{\"raw_text\":\"Hi, can I get a latte with milk to go?\",\"source_type\":\"real-world\",\"optional_context\":null}"
```

验收：

- 返回 HTTP 200
- 返回 `detected_context.id = coffee_shop`
- 数据写入 `analysis_results`
- Dashboard 的 `top_context` 会随分析结果更新

## Task A10 - GET /contexts

目标：给 Web 和 CYD 提供 context 选择页数据。

文件：

```
backend/main.py
backend/database.py
```

返回结构：

```json
{
  "real_world": [],
  "story": []
}
```

验收：

- `real_world` 有 Coffee Shop 和 Doctor / Pharmacy
- `story` 有 King's Cross 和 Baker Street
- 每个 context 包含 `id`、`title`、`type`、`summary`、`seed_keywords`、`seed_phrases`

## Task A11 - GET /context/{id}

目标：给 CYD 的场景卡片提供预设内容。

文件：

```
backend/main.py
backend/database.py
```

测试：

```powershell
curl http://localhost:8000/context/coffee_shop
```

验收：

- 存在的 id 返回 HTTP 200
- 不存在的 id 返回 HTTP 404
- 返回内容可以直接显示在 CYD 的 Insight View

## Task A12 - POST /save_item

目标：保存用户选择复习的单词或短语。

文件：

```
backend/main.py
backend/database.py
```

请求：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

规则：

- `item_type` 只能是 `word` 或 `phrase`
- `item_text` 不能为空
- `source_context` 可以为空，但建议传

验收：

- 保存成功返回 `{ "saved": true }`
- 非法 `item_type` 返回校验错误
- 保存后 `/dashboard` 能看到这个 item

## Task A13 - GET /dashboard

目标：给 CYD dashboard 提供复习数据。

文件：

```
backend/main.py
backend/database.py
```

返回重点字段：

```json
{
  "saved_words": [],
  "saved_phrases": [],
  "top_context": "coffee_shop",
  "recent_keywords": ["latte", "milk"],
  "review_today": 2
}
```

验收：

- saved words 和 saved phrases 分开
- top context 能根据分析历史统计
- recent keywords 不重复
- CYD 可以不加工直接显示这些字段

## Task A14 - 后端自测清单

每次改完线 A，至少跑这些检查：

```powershell
python -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
python -c "from backend.database import init_db, list_contexts; init_db(); print(len(list_contexts()))"
python -c "from backend.database import init_db, list_contexts; from backend.nlp_engine import analyze_text; init_db(); print(analyze_text('Hi, can I get a latte with milk to go?', 'real-world', None, list_contexts())['detected_context']['id'])"
```

预期：

```
4
coffee_shop
```

## Task A15 - 给线 B 的联调信息

线 A 每次准备联调时，必须给线 B 这几项：

```
后端地址：
http://localhost:8000

手机 / CYD 地址：
http://你的局域网IP:8000

可用接口：
GET /contexts
POST /analyze_text
POST /save_item
GET /dashboard
```

如果 CYD 访问 laptop，要确认：

- laptop 和 CYD 在同一个 Wi-Fi / hotspot
- Windows 防火墙允许 Python / Uvicorn 访问
- Uvicorn 需要监听局域网时使用：

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Task A16 - 给线 C 的测试支持

线 C 会准备 4 段 demo 文本。线 A 要帮忙检查：

- 文本能否分类到正确 context
- keywords 是否适合展示
- phrases 是否适合学习
- summary 是否太长
- CYD 屏幕上是否能显示得下

如果效果不好，优先调整：

1. `backend/seed_data.json` 的 `seed_keywords`
2. `backend/seed_data.json` 的 `seed_phrases`
3. `backend/nlp_engine.py` 的规则

不要优先引入新库解决小问题。

## 线 A 完成标准

线 A 完成时，必须满足：

- 后端可以一条命令启动
- 5 个 MVP API 全部可用
- SQLite 自动初始化
- 4 个 context seed data 正常返回
- 文本输入能得到 cleaned text、keywords、phrases、detected context、summary
- save item 能写入 dashboard
- Web 和 CYD 不需要知道数据库细节
- 没有网络、没有 LLM API key 时仍可完整演示

## 常见问题处理

### 端口 8000 被占用

换端口：

```powershell
uvicorn backend.main:app --reload --port 8001
```

同时通知线 B 修改 API 地址。

### 修改 seed_data 后没有变化

重启后端：

```powershell
Ctrl+C
uvicorn backend.main:app --reload
```

如果还是不对，临时删除本地 `scenelingo.db` 后再启动。注意这会清空本地测试数据。

### 手机或 CYD 访问不了后端

检查：

- 后端是不是用 `--host 0.0.0.0` 启动
- 地址是不是 laptop 的局域网 IP
- 防火墙是否拦截
- 是否在同一个 Wi-Fi / hotspot

### NLP 结果不够聪明

MVP 优先保证稳定，不追求完美。先通过 seed keywords 和 seed phrases 调整结果。等完整 demo 稳定后，再考虑 LLM summary 或更复杂 phrase ranking。
