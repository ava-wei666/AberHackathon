# Task B6 记录 - Web Dashboard

日期：2026-05-03

## 目标

Web 端展示复习数据，作为 CYD 的字段验证来源。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |

## API 接口

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

## Dashboard 展示布局

```text
┌─── Review Today ─────┐  ┌─── Top Context ──────┐
│              2        │  │  Coffee Shop          │
└──────────────────────┘  └──────────────────────┘
┌─── Saved Words ──────┐  ┌─── Saved Phrases ─────┐
│  latte  coffee_shop  │  │  can I get coffee_shop │
│  milk   coffee_shop  │  │  to go    coffee_shop  │
└──────────────────────┘  └──────────────────────┘
┌─── Recent Keywords (wide) ──────────────────────┐
│  [latte] [milk] [size]                           │
└─────────────────────────────────────────────────┘
▶ Debug raw dashboard JSON（折叠）
```

## 实现逻辑

```text
点击 Refresh Dashboard / 保存 item 后
  -> loadDashboard()
  -> dashboardButton.disabled = true
  -> fetch GET /dashboard
  -> 成功：renderDashboard(dashboard)，raw JSON 写入 <details>
  -> 失败：显示错误面板
  -> finally：dashboardButton.disabled = false
```

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 实现 `loadDashboard()` | try/catch，按钮 disabled 管理 |
| 2 | 实现 `renderDashboard()` | 5 个面板：review_today、top_context、saved_words、saved_phrases、recent_keywords |
| 3 | 实现 `renderReviewList()` | 展示 item_text + source_context |
| 4 | raw JSON 移入 `<details>` | 默认折叠 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 点击 Refresh Dashboard 能显示最新数据 | 通过 |
| saved_words 和 saved_phrases 分开展示 | 通过，左右双列面板 |
| top_context 能显示 | 通过 |
| recent_keywords 能显示 | 通过，chip 形式 |
| review_today 能显示 | 通过，大数字展示 |
| 字段缺失时不崩溃 | 通过，`asArray()` 防御空值 |
