# Task B4 记录 - 结果展示整理

日期：2026-05-03

## 目标

让评委不看 raw JSON 也能一眼看懂分析结果。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |

## 结果展示布局

```text
┌─── Detected Context (wide) ─────────────────┐
│  Coffee Shop                                 │
│  coffee_shop · real-world · 92% confidence  │
└─────────────────────────────────────────────┘
┌─── Top Keywords ────┐  ┌─── Useful Phrases ──┐
│  [latte] [milk]     │  │  [can I get]        │
│  [size ] [order]    │  │  [to go    ]        │
└─────────────────────┘  └─────────────────────┘
┌─── Context Summary (wide) ──────────────────┐
│  This is a coffee shop ordering scenario...  │
└─────────────────────────────────────────────┘
┌─── Suggested Review Items (wide) ───────────┐
│  [latte] [milk] [to go]                      │
└─────────────────────────────────────────────┘
▶ Debug raw analysis JSON（折叠）
```

## 字段说明

| 字段 | 来源 | 展示方式 |
| --- | --- | --- |
| `detected_context.title` | `/analyze_text` 返回 | 大字标题 |
| `detected_context.id` / `type` / `confidence` | `/analyze_text` 返回 | 灰色小字 |
| `keywords` | `/analyze_text` 返回 | green chip |
| `phrases` | `/analyze_text` 返回 | blue chip |
| `summary` | `/analyze_text` 返回 | 段落文字 |
| `suggested_review_items` | `/analyze_text` 返回 | chip |

## 实现逻辑

```text
analyzeText() 成功
  -> renderAnalysisResult(latestResult)
     -> 读取 detected_context、keywords、phrases、summary、suggested_review_items
     -> innerHTML 写入 result-grid 面板
     -> keywords 用 renderChips("word") 渲染绿色 chip
     -> phrases 用 renderChips("phrase") 渲染蓝色 chip
     -> raw JSON 保留在 <details> 折叠区
```

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 实现 `renderAnalysisResult()` | 5 个面板：Context、Keywords、Phrases、Summary、Suggested Items |
| 2 | 实现 `renderChips()` | 支持 word（绿）、phrase（蓝）两种样式 |
| 3 | 实现 `renderAnalysisEmpty()` | 分析前 / 失败时的空状态 |
| 4 | raw JSON 移入 `<details>` | 默认折叠，不影响正常展示 |
| 5 | 实现 `escapeHtml()` | 防止 API 返回内容被当成 HTML 执行 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 输入 Coffee Shop 文本后，一眼看出场景是 Coffee Shop | 通过 |
| keywords 和 phrases 不挤在一起 | 通过，左右双列面板 |
| summary 不被按钮遮挡 | 通过，独立 wide 面板 |
| raw JSON 不是唯一展示 | 通过，折叠在 `<details>` 里 |
| 字段缺失时不崩溃 | 通过，`asArray()` 防御空值 |
