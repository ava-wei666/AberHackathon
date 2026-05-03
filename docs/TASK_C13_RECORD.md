# Task C13 记录 - 给线 A 的反馈

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C13 要求，整理 CYD 侧对各 API 接口的字段依赖和显示需求，反馈给线 A 后端，避免联调时出现字段不匹配或显示异常。

线 C 不要求线 A 修改数据库结构，只反馈显示层的最低字段要求。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `lvgl9_firmwares/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C13_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |

## CYD 使用的 API_BASE

```
http://192.168.137.1:8000
```

联调时改为 laptop 实际局域网 IP，其余路径不变。

---

## 接口 1：GET /contexts

### CYD 期望格式

```json
{
  "real_world": [
    {"id": "coffee_shop",      "title": "Coffee Shop"},
    {"id": "doctor_pharmacy",  "title": "Doctor / Pharmacy"}
  ],
  "story": [
    {"id": "kings_cross",  "title": "King's Cross"},
    {"id": "baker_street", "title": "Baker Street"}
  ]
}
```

### 注意事项

| 项目 | 说明 |
| --- | --- |
| 字段名 `real_world` | CYD 内部映射为 `real-world`（连字符），`fetch_contexts()` 处理，线 A 无需改动 |
| 每项必须包含 `id` | CYD 用 `id` 调用 `/context/{id}` |
| 每项必须包含 `title` | CYD 用 `title` 显示按钮文案 |
| 失败处理 | 请求失败自动回退 mock，CYD 不黑屏 |

---

## 接口 2：GET /context/{id}

### CYD 期望格式（任意一种均可）

**方案 A（推荐）：**
```json
{
  "id": "coffee_shop",
  "title": "Coffee Shop",
  "keywords": ["latte", "milk", "size"],
  "phrases": ["Can I Get", "to go"],
  "summary": "This looks like Coffee Shop."
}
```

**方案 B（也兼容）：**
```json
{
  "id": "coffee_shop",
  "title": "Coffee Shop",
  "seed_keywords": ["latte", "milk", "size"],
  "seed_phrases": ["Can I Get", "to go"],
  "summary": "This looks like Coffee Shop."
}
```

### 字段长度建议

| 字段 | CYD 截断规则 | 建议长度 |
| --- | --- | --- |
| 每个 keyword | 按钮文本截断到 14 字符（`_C12_KW_CHARS`） | ≤ 14 字符 |
| 每个 phrase | 按钮文本截断到 30 字符（`_C12_PH_CHARS`） | ≤ 30 字符 |
| summary | 只取第一句前 48 字符（`_C12_SUM_CHARS`） | 1 句为佳 |

### 注意事项

| 项目 | 说明 |
| --- | --- |
| `keywords` / `seed_keywords` 均可 | `normalize_context()` 做 fallback 兼容 |
| `phrases` / `seed_phrases` 均可 | 同上 |
| keyword 个数 | CYD 最多显示 5 个（`_C12_MAX_KW`），超出静默忽略 |
| phrase 个数 | CYD 最多显示 3 个（`_C12_MAX_PH`），超出静默忽略 |
| 失败处理 | 请求失败自动回退对应 context 的 mock，CYD 不黑屏 |

---

## 接口 3：GET /dashboard

### CYD 期望格式

```json
{
  "saved_words": [
    {"item_text": "latte"},
    {"item_text": "milk"}
  ],
  "saved_phrases": [
    {"item_text": "Can I Get"}
  ],
  "top_context": "coffee_shop",
  "review_today": 3
}
```

### 注意事项

| 项目 | 说明 |
| --- | --- |
| `item_text` 字段名 | CYD 硬依赖 `item_text`，不支持别名（如 `text`、`word`），必须完全匹配 |
| `saved_words` / `saved_phrases` | CYD 分区显示，字段名必须完全匹配 |
| `top_context` | 字符串类型，CYD 直接显示，建议不超过 24 字符 |
| `review_today` | 整数类型，CYD 转 str 显示 |
| `recent_keywords` | CYD 当前不显示此字段，无需强求格式 |
| saved words 条数 | CYD 最多显示 5 条（`_C12_MAX_WORDS`），超出静默忽略 |
| saved phrases 条数 | CYD 最多显示 3 条（`_C12_MAX_PH`），超出静默忽略 |
| 失败处理 | 请求失败自动回退 mock dashboard，CYD 不黑屏 |

---

## 接口 4：POST /save_item

### CYD 发送格式

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

### CYD 期望返回

```json
{"saved": true}
```

### 注意事项

| 项目 | 说明 |
| --- | --- |
| `item_type` 取值 | 只会是 `"word"` 或 `"phrase"`，不会传其他值 |
| `source_context` | 当前 context 的 id（如 `"coffee_shop"`） |
| `saved` 字段类型 | 必须是布尔 `true`，不能是字符串 `"true"`，否则 CYD 判定为失败 |
| 失败处理 | 返回非 `{"saved": true}` 时，CYD 显示 `"Save failed"`，但不跳页不崩溃 |

---

## 代码侧改动

| 修改 | 位置 | 说明 |
| --- | --- | --- |
| 新增 C13 API 契约注释块 | `normalize_context()` 下方 | 四个接口的字段要求汇总，代码即文档 |
| `normalize_context()` 加注释 | `scenelingo_dashboard.py:385` | 说明兼容两种字段命名的原因 |

---

## 联调验证清单（给线 A 确认）

| 验证项 | 方法 |
| --- | --- |
| `/contexts` 返回 `real_world` 和 `story` 两个键 | CYD Context Select 能显示 4 个 context 按钮 |
| `/context/{id}` 返回 `keywords` 或 `seed_keywords` | CYD Insight View 能显示 5 个关键词按钮 |
| `/dashboard` 每个 item 有 `item_text` 字段 | CYD Dashboard 显示 saved words / phrases 非空 |
| `POST /save_item` 返回 `{"saved": true}` | CYD 状态行显示 `"Saved: <item>"` |
| Web 保存后 `/dashboard` 立刻更新 | CYD Refresh 能看到 Web 新保存的 item |
| CYD 保存后 `/dashboard` 立刻更新 | Web Refresh 能看到 CYD 新保存的 item |

---

## C13 验收结果

| 验收项 | 结果 |
| --- | --- |
| 哪个接口 CYD 请求失败 | 记录：全部接口失败时有 mock fallback，不黑屏 |
| CYD 使用的 `API_BASE` | 记录：`http://192.168.137.1:8000`（占位符） |
| 返回字段是否太长 | 记录：keyword ≤14 字符，phrase ≤30 字符，超出截断显示 |
| dashboard 字段能直接显示 | 通过：依赖 `item_text`、`top_context`、`review_today` |
| 保存 item 后能看到更新 | 通过（真实 API 模式）：POST 后 GET /dashboard 返回新数据 |
| API 契约注释写入代码 | 通过：`normalize_context()` 下方 C13 注释块 |
