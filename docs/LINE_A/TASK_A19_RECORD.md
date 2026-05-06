# Task A19 记录 - /dashboard 返回 top_context_title

日期：2026-05-05

## 目标

按照 `LINE_A_BACKEND_TASKS.md` 的 Task A19 要求，在 `GET /dashboard` 响应里新增 `top_context_title` 字段，让 Web 和 CYD 直接显示"Coffee Shop"，而不是原始 id `"coffee_shop"`，避免双端各自做 id → title 映射且容易不一致的问题。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 主要改动文件 | `backend/database.py` |
| 新增记录文档 | `docs/TASK_A19_RECORD.md` |
| 是否改动数据库表结构 | 否 |
| 是否影响现有接口返回格式 | 是（`/dashboard` 新增 `top_context_title` 字段，向后兼容） |

---

## 改动详情

### `backend/database.py` — `get_dashboard()` 内新增 title 查询

在 `top_context` 查询之后，同一个 `with get_connection()` 块内追加：

```python
# A19: 用 top_context id 反查 contexts 表拿 display title。
top_context_title: str | None = None
if top_context:
    title_row = connection.execute(
        "SELECT title FROM contexts WHERE id = ?",
        (top_context["detected_context"],),
    ).fetchone()
    top_context_title = title_row["title"] if title_row else None
```

选择在同一个连接块内做第二次查询，而不是开新连接，避免两次连接之间出现 race condition（尽管 SQLite 单写者模型下概率极低）。

返回字典新增一行：

```python
return {
    ...
    "top_context": top_context["detected_context"] if top_context else None,
    "top_context_title": top_context_title,   # A19 新增
    ...
}
```

---

## API 变更说明

### `/dashboard` 返回格式变化（向后兼容）

新增 `top_context_title` 字段，原有 `top_context`（id 字符串）保留不动：

```json
{
  "top_context": "coffee_shop",
  "top_context_title": "Coffee Shop",
  "saved_words": [...],
  "saved_phrases": [...],
  "recent_keywords": [...],
  "review_today": 2
}
```

| 情况 | `top_context` | `top_context_title` |
| --- | --- | --- |
| 有分析记录，context 在 DB | `"coffee_shop"` | `"Coffee Shop"` |
| 有分析记录，context id 已删除（罕见） | `"coffee_shop"` | `null` |
| 没有任何分析记录 | `null` | `null` |

### 线 B 使用建议

```javascript
// 优先用 title，fallback 到 id，再 fallback 到"None yet"
panel.textContent = dashboard.top_context_title
    ?? dashboard.top_context
    ?? 'None yet';
```

### 线 C（CYD）使用建议

```python
# mock 和真实模式都可以加这一行判断
title = data.get("top_context_title") or data.get("top_context") or "None"
```

---

## 冒烟测试结果

测试时 `analysis_results` 表为空（未调用 `/analyze_text`），`top_context` 和 `top_context_title` 均为 `None`，符合预期。

完整链路验证需要：

1. 启动后端
2. 调用 `POST /analyze_text` 至少一次
3. 调用 `GET /dashboard`，确认 `top_context_title` 返回对应 context 的 `title`

---

## A19 验收结果

| 验收项 | 结果 |
| --- | --- |
| 有分析记录时 `top_context_title` 返回对应 `title` | 待后端启动后集成验证 |
| 无分析记录时两个字段均为 `null` | 通过（冒烟测试确认） |
| 原有 `top_context` 字段保留，不影响旧代码 | 通过 |
| 线 B / 线 C 旧代码不改动仍可运行 | 通过（新字段只是追加） |
| 不新增表、不改表结构 | 通过 |
