# Task B1 记录 - 页面基础结构

日期：2026-05-03

## 目标

页面一打开就能看到完整的输入和查看结果区域。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |

## 页面区域布局

```text
┌─────────────────────────────────────┐
│  SceneLingo                         │  header
│  Web Input / Web Dashboard...       │
├─────────────────────────────────────┤
│  1. Source / Context                │  section 1
│  [ Source select ▼ ] [ Context ▼ ] │
├─────────────────────────────────────┤
│  2. Text Input                      │  section 2
│  [ textarea                       ] │
│  [ Coffee Shop ] [ Doctor ] ...     │  demo 快捷按钮
│  [ Analyze Text ]                   │
├─────────────────────────────────────┤
│  3. Analysis Result                 │  section 3
│  ┌ Detected Context ──────────────┐ │
│  │ Keywords │ Phrases             │ │
│  │ Summary ───────────────────────│ │
│  └────────────────────────────────┘ │
├─────────────────────────────────────┤
│  4. Save Buttons                    │  section 4
│  [ Save Word: latte ] ...           │
├─────────────────────────────────────┤
│  5. Web Dashboard                   │  section 5
│  [ Refresh Dashboard ]              │
│  ┌ Review Today │ Top Context ────┐ │
│  │ Saved Words  │ Saved Phrases   │ │
│  │ Recent Keywords ───────────────│ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 必需控件清单

| 控件 | id / 属性 |
| --- | --- |
| Source select | `#sourceType`，选项 Real-world / Story |
| Optional Context select | `#contextSelect`，默认 Auto detect |
| Textarea | `#rawText` |
| Analyze Text 按钮 | `#analyzeButton` |
| Refresh Dashboard 按钮 | `#dashboardButton` |

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 建立 5 个 `<section>` 区块 | Source/Context、Text Input、Analysis Result、Save Buttons、Dashboard |
| 2 | 添加所有必需控件 | 通过，id 与 JS 引用一致 |
| 3 | 响应式布局：`@media (max-width: 760px)` | 移动端单列，桌面端双列 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 页面打开能看到 SceneLingo 标题 | 通过 |
| 能输入文本 | 通过 |
| 能选择 source type | 通过 |
| 有 Analyze Text 按钮 | 通过 |
| 有 Dashboard 区域 | 通过 |
