# Task B9 记录 - CYD Fallback Demo

日期：2026-05-03

## 目标

CYD 临时失败时，Web 仍能在 60 秒内完整展示 MVP 闭环。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |
| 是否依赖 CYD | 否 |

## 60 秒演示流程

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开 `web/index.html` | 页面加载，Contexts loaded |
| 2 | 点击 Coffee Shop demo 按钮 | 自动填入文本，source 切换为 Real-world |
| 3 | 点击 Analyze Text | 显示 Analyzing... |
| 4 | 等待结果 | 展示 Detected Context: Coffee Shop、keywords、phrases、summary |
| 5 | 点击一个 Save Word 按钮 | 显示 Saved word: latte |
| 6 | 点击一个 Save Phrase 按钮 | 显示 Saved phrase: can I get |
| 7 | 点击 Refresh Dashboard | Dashboard 更新，saved_words 和 saved_phrases 可见 |

## 关键展示字段

- `detected_context.title`：显示 Coffee Shop
- `keywords`：显示至少 3 个词
- `phrases`：显示至少 2 个短语
- `summary`：显示场景描述
- `saved_words`：保存后 Dashboard 可见
- `saved_phrases`：保存后 Dashboard 可见
- `review_today`：数字递增

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 不依赖 CYD，Web 能完整演示 | 通过 |
| 60 秒内完成完整闭环 | 通过 |
| Dashboard 更新在页面上清楚可见 | 通过，saved_words / saved_phrases 面板实时更新 |
