# Task C14 记录 - 给线 B 的联调点

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C14 要求，整理 CYD 与 Web Dashboard 的联调验证点，反馈给线 B，确保 Web 保存的数据能在 CYD 上可见，CYD 保存的数据也能在 Web 上可见。

线 C 不修改 `web/index.html`，只列出联调点和字段依赖。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `embedded/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C14_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否修改 `web/index.html` | 否 |

---

## Web-CYD 共享数据模型

```text
┌──────────────┐     POST /save_item      ┌─────────────┐
│   Web 输入   │ ───────────────────────► │   后端 API  │
│ (web/index)  │                          │  (线 A)     │
└──────────────┘                          │             │
                                          │  SQLite DB  │
┌──────────────┐     POST /save_item      │             │
│   CYD 按钮   │ ───────────────────────► │             │
│ (Insight View│                          └─────────────┘
│  keyword/    │                                 │
│  phrase 按钮)│          GET /dashboard         │
└──────────────┘ ◄───────────────────────────────┘
                                          ▲
┌──────────────┐     GET /dashboard       │
│  Web Dashboard│◄────────────────────────┘
└──────────────┘
```

CYD 和 Web 共用同一个后端，通过 GET /dashboard 读取、POST /save_item 写入实现数据同步。

---

## 线 B 需要帮忙验证的 3 个联调点

### 联调点 1：Web 保存 word → CYD 可见

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | Web 页面输入文字，保存一个 word | Web Dashboard 显示新 word |
| 2 | CYD Dashboard View 点击 Refresh | CYD 显示 Web 刚保存的 word |

**CYD 依赖字段：** `saved_words[].item_text`

### 联调点 2：CYD 保存 word → Web 可见

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | CYD Insight View 点击 keyword 按钮 | CYD 状态行显示 `"Saved: <keyword>"` |
| 2 | Web 页面刷新 Dashboard | Web 显示 CYD 刚保存的 keyword |

**Web 需要展示字段：** `saved_words[].item_text`

### 联调点 3：CYD 保存 phrase → Web 可见

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | CYD Insight View 点击 phrase 按钮 | CYD 状态行显示 `"Saved: <phrase>"` |
| 2 | Web 页面刷新 Dashboard | Web 显示 CYD 刚保存的 phrase |

**Web 需要展示字段：** `saved_phrases[].item_text`

---

## CYD Dashboard 显示字段与 Web 字段对照

| GET /dashboard 字段 | CYD 显示方式 | Web 是否也显示 | 字段名须一致 |
| --- | --- | --- | --- |
| `saved_words[].item_text` | "Words: latte, milk, ..." | ✅ 需要 | ✅ 必须 |
| `saved_phrases[].item_text` | "Phrases: Can I Get, ..." | ✅ 需要 | ✅ 必须 |
| `top_context` | "Top: coffee_shop" | 可选 | 字符串类型 |
| `review_today` | "Review Today: 3" | 可选 | 整数类型 |
| `recent_keywords` | CYD 不显示 | Web 可自由使用 | 无约束 |
| `source_context`（per item） | CYD 不显示 | Web 可显示 | 无约束 |
| `created_at`（per item） | CYD 不显示 | Web 可显示 | 无约束 |

---

## 给线 B 的注意事项

| 项目 | 说明 |
| --- | --- |
| Web POST /save_item 需含 `source_context` | CYD 会传，Web 也应该传，否则 `top_context` 统计可能不准 |
| `item_text` 字段名必须一致 | CYD 硬依赖 `item_text`，Web 和后端须保持一致 |
| `item_type` 取值 | CYD 只传 `"word"` 或 `"phrase"`，Web 应使用相同取值 |
| Web 无需等 CYD | CYD 和 Web 独立运行，各自通过 API 同步，不需要 WebSocket 或轮询 |
| CYD 不读 Web HTML 状态 | CYD 只通过 REST API 与后端交互，不依赖 Web 页面 |
| 线 C 不修改 web/index.html | 如果 Web 页面字段名和 CYD 期望不符，由线 B 调整 Web 或由线 A 调整 API 返回 |

---

## Web POST /save_item 请求示例（供线 B 参考）

CYD 发送格式（线 B 的 Web 请求应保持一致）：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

```json
{
  "item_text": "Can I Get",
  "item_type": "phrase",
  "source_context": "coffee_shop"
}
```

期望后端返回：

```json
{"saved": true}
```

---

## 代码侧改动

| 修改 | 位置 | 说明 |
| --- | --- | --- |
| 新增 C14 Web-CYD 联调点注释块 | C13 契约块下方，`init_display()` 前 | 共享数据模型、3 个联调点、字段适配说明 |

---

## C14 验收结果

| 验收项 | 结果 |
| --- | --- |
| Web 保存 word 后 CYD Refresh 能看到 | 待联调验证（真实 API 模式） |
| CYD 保存 word 后 Web Refresh 能看到 | 待联调验证（真实 API 模式） |
| CYD 保存 phrase 后 Web Refresh 能看到 | 待联调验证（真实 API 模式） |
| Web 页面哪些字段适合 CYD 展示 | 记录：`saved_words[].item_text` / `saved_phrases[].item_text` / `top_context` / `review_today` |
| C14 联调点注释写入代码 | 通过，`init_display()` 前 C14 注释块 |
| 线 C 未修改 web/index.html | 通过 |
