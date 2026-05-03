# LINE_A Task A2 操作记录

## 记录字段

| 字段 | 内容 |
| --- | --- |
| Line | `LINE_A` |
| Task | `A2 - Seed Data 管理` |
| 状态 | 已通过 |
| 执行日期 | `2026-05-03` |
| 工作目录 | `C:\hackathon` |
| 后端地址 | `http://127.0.0.1:8000/` |
| 当前服务进程 | A7 后已重启为 `48024` |
| 主要涉及文件 | `backend/seed_data.json`、`backend/database.py`、`backend/main.py` |
| 本次业务代码改动 | 无 |
| 文档记录 | `docs/LINE_A_A2_STEPS.md` |
| 下一步 | A3 SQLite 初始化 |

## 任务目标

维护 4 个 MVP context，保证后端分类和前端展示都有基础数据。

## 数据字段规范

| 字段 | 规范 |
| --- | --- |
| `id` | snake_case |
| `title` | 面向前端展示的人类可读标题 |
| `type` | 只能是 `real-world` 或 `story` |
| `tag` | 用于卡片展示和轻量分类提示 |
| `summary` | 场景说明，给前端卡片展示 |
| `seed_keywords` | 小写英文单词数组 |
| `seed_phrases` | 小写英文短语数组 |
| JSON 注释 | 不允许在 JSON 中写注释 |

## MVP Context 清单

| id | title | type | tag |
| --- | --- | --- | --- |
| `coffee_shop` | `Coffee Shop` | `real-world` | `coffee shop` |
| `doctor_pharmacy` | `Doctor / Pharmacy` | `real-world` | `doctor` |
| `kings_cross` | `Harry Potter - King's Cross` | `story` | `magic school` |
| `baker_street` | `Sherlock Holmes - Baker Street` | `story` | `detective` |

## 验收命令

字段和数量检查：

```powershell
$contexts = Get-Content .\backend\seed_data.json -Encoding UTF8 | ConvertFrom-Json
$contexts | Select-Object id,title,type,tag
"count=$($contexts.Count)"
"real_world=$(@($contexts | Where-Object { $_.type -eq 'real-world' }).Count)"
"story=$(@($contexts | Where-Object { $_.type -eq 'story' }).Count)"
```

API 检查：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/contexts
Invoke-RestMethod -Uri http://127.0.0.1:8000/context/coffee_shop
```

## 验收结果

| 检查项 | 结果 |
| --- | --- |
| context 总数 | `4` |
| real-world 数量 | `2` |
| story 数量 | `2` |
| 必须保留的 id | 全部存在 |
| id snake_case | 通过 |
| type 合法性 | 通过 |
| seed_keywords 小写英文 | 通过 |
| seed_phrases 小写英文 | 通过 |
| `/contexts` | 返回 2 个 real-world 和 2 个 story |
| `/context/coffee_shop` | 返回 Coffee Shop 卡片数据 |

字段规范检查输出：

```text
count_is_4=True
ids_match=True
ids_are_snake_case=True
types_valid=True
keywords_lowercase_english=True
phrases_lowercase_english=True
```

## 接口返回字段记录

`GET /contexts` 返回分组结构：

| 字段 | 内容 |
| --- | --- |
| `real_world` | real-world context 数组 |
| `story` | story context 数组 |

`GET /context/coffee_shop` 返回单个 context：

| 字段 | 内容 |
| --- | --- |
| `id` | `coffee_shop` |
| `title` | `Coffee Shop` |
| `type` | `real-world` |
| `tag` | `coffee shop` |
| `summary` | Coffee Shop 场景说明 |
| `seed_keywords` | Coffee Shop 分类关键词 |
| `seed_phrases` | Coffee Shop 场景短语 |

## 代码和数据影响

- 本次未修改 `backend/seed_data.json`，因为现有内容已经符合 A2。
- 本次未修改业务代码。
- `backend/database.py` 中读取并同步 seed data 的关键逻辑已有中文注释。

## 结论

- A2 已通过。
- Seed data 当前满足 MVP 范围，不包含无关场景。
- `/contexts` 和 `/context/coffee_shop` 两个验收接口均可用。
