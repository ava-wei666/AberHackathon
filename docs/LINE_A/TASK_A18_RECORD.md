# Task A18 记录 - DELETE /saved_item/{id}

日期：2026-05-05

## 目标

按照 `LINE_A_BACKEND_TASKS.md` 的 Task A18 要求，新增删除复习项接口，让 Web Dashboard 可以移除单条已保存的单词或短语，关闭"只进不出"的数据死循环。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 主要改动文件 | `backend/database.py`、`backend/main.py` |
| 新增记录文档 | `docs/TASK_A18_RECORD.md` |
| 是否改动数据库表结构 | 否（`review_items` 表结构不变，只新增 DELETE 操作） |
| 是否影响现有接口返回格式 | 是（`/dashboard` 的每条 item 新增 `id` 字段，向后兼容） |

---

## 改动详情

### 1. `backend/database.py` — 新增 `delete_review_item()`

```python
def delete_review_item(item_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM review_items WHERE id = ?",
            (item_id,),
        )
        return cursor.rowcount > 0
```

`rowcount > 0` 用来区分"删到了"和"id 不存在"两种情况，路由层根据返回值决定是 200 还是 404。

### 2. `backend/database.py` — `get_dashboard()` SELECT 加 `id`

word_rows 和 phrase_rows 的 SELECT 语句从

```sql
SELECT item_text, source_context, created_at
```

改为

```sql
SELECT id, item_text, source_context, created_at
```

### 3. `backend/database.py` — `_review_from_row()` 加 `id` 字段

```python
def _review_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],           # A18 新增，供 Web 删除按钮使用
        "item_text": row["item_text"],
        "source_context": row["source_context"],
        "created_at": row["created_at"],
    }
```

### 4. `backend/main.py` — 新增路由

```python
@app.delete("/saved_item/{item_id}")
def delete_saved_item_endpoint(item_id: int) -> dict:
    deleted = delete_review_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "deleted": True}
```

放在 `save_item_endpoint` 之后，`dashboard_endpoint` 之前。

---

## API 变更说明

### 新增接口

```
DELETE /saved_item/{item_id}
```

| 情况 | HTTP 状态 | 返回体 |
| --- | --- | --- |
| 删除成功 | 200 | `{"id": 3, "deleted": true}` |
| id 不存在 | 404 | `{"detail": "Item not found"}` |

### `/dashboard` 返回格式变化（向后兼容）

`saved_words` 和 `saved_phrases` 每条记录新增 `id` 字段：

```json
{
  "saved_words": [
    {
      "id": 3,
      "item_text": "latte",
      "source_context": "coffee_shop",
      "created_at": "2026-05-05 10:00:00"
    }
  ]
}
```

线 B 的 B15 任务需要这个 `id` 来构造删除请求。CYD 端（线 C）忽略 `id` 字段即可，不需要改动。

---

## 冒烟测试结果

```
saved id: 1
deleted: True
not found: False
saved_words[0] keys: ['id', 'item_text', 'source_context', 'created_at']
id present: True
ALL PASS
```

---

## A18 验收结果

| 验收项 | 结果 |
| --- | --- |
| `DELETE /saved_item/{id}` 成功返回 `{"deleted": true}` | 通过 |
| 对不存在 id 返回 HTTP 404 | 通过（`rowcount == 0` → `False` → 404） |
| `/dashboard` 每条 item 包含 `id` 字段 | 通过 |
| 不改动数据库表结构 | 通过 |
| 现有 `save_item` / `dashboard` 接口不受影响 | 通过 |
| 线 C（CYD）不需要改动 | 通过（`id` 是新增字段，旧代码忽略即可） |
