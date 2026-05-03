# LINE_A Task A2 操作记录

本文档记录 Task A2 的执行方式、字段校验和 API 验收结果。

## Task A2 - Seed Data 管理

目标：维护 4 个 MVP context，保证分类和展示都有基础数据。

涉及文件：

```
backend/seed_data.json
```

必须保留的 4 个 context：

```
coffee_shop
doctor_pharmacy
kings_cross
baker_street
```

字段规范：

- `id` 使用 snake_case。
- `type` 只能是 `real-world` 或 `story`。
- `seed_keywords` 全部使用小写英文单词。
- `seed_phrases` 全部使用小写英文短语。
- JSON 文件中不写注释。

## 本次检查结果

当前 `backend/seed_data.json` 已包含且仅包含 4 个 MVP context：

| id                | title                            | type         | tag            |
| ----------------- | -------------------------------- | ------------ | -------------- |
| `coffee_shop`     | `Coffee Shop`                    | `real-world` | `coffee shop`  |
| `doctor_pharmacy` | `Doctor / Pharmacy`              | `real-world` | `doctor`       |
| `kings_cross`     | `Harry Potter - King's Cross`    | `story`      | `magic school` |
| `baker_street`    | `Sherlock Holmes - Baker Street` | `story`      | `detective`    |

数量检查：

```
count=4
real_world=2
story=2
```

字段规范检查：

```
count_is_4=True
ids_match=True
ids_are_snake_case=True
types_valid=True
keywords_lowercase_english=True
phrases_lowercase_english=True
```

## API 验收

当前 FastAPI 服务已启动，本机地址：

```
http://127.0.0.1:8000/
```

已验证：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/contexts
```

结果：接口返回 2 个 `real-world` context 和 2 个 `story` context。

已验证：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/context/coffee_shop
```

结果：接口返回 `Coffee Shop` 卡片数据，包含 `id`、`title`、`type`、`tag`、`summary`、`seed_keywords`、`seed_phrases`。

## 代码注释约定

- 本次 A2 没有修改业务代码。
- 当前 `backend/database.py` 中读取并同步 seed data 的关键逻辑已经有中文注释。
- 后续如果 A3 或更后续任务需要修改数据库初始化、seed 同步或 API 返回逻辑，新增代码继续使用中文注释说明关键数据流和边界行为。

## 2026-05-03 执行结论

- A2 已执行并通过。
- `backend/seed_data.json` 当前无需修改。
- `/contexts` 和 `/context/coffee_shop` 两个验收接口均可用。
