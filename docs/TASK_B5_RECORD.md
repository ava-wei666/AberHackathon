# Task B5 记录 - 保存复习项

日期：2026-05-03

## 目标

关键词和短语可以一键保存到 dashboard。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |

## API 接口

```
POST /save_item
```

请求体：

```json
{
  "item_text": "latte",
  "item_type": "word",
  "source_context": "coffee_shop"
}
```

成功返回：`{ "saved": true }`

## 实现逻辑

```text
分析成功
  -> renderSaveButtons(latestResult)
  -> keywords（最多 6 个，去重）生成 "Save Word: xxx" 按钮
  -> phrases（最多 6 个，去重）生成 "Save Phrase: xxx" 按钮

点击 Save 按钮
  -> button.disabled = true（防止重复保存）
  -> saveItem(itemText, itemType, contextId, button)
  -> fetch POST /save_item
  -> 成功：result.saved === true，刷新 dashboard
  -> 失败：button.disabled = false，显示错误
```

## 数量限制

- keywords 最多展示 6 个（`uniqueLimitedItems(result.keywords, 6)`）
- phrases 最多展示 6 个
- 去重处理，避免重复按钮

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 实现 `renderSaveButtons()` | 分析成功后生成 save-chip 按钮 |
| 2 | 实现 `saveItem()` | try/catch，失败时恢复按钮状态 |
| 3 | 实现 `uniqueLimitedItems()` | 去重 + 限制数量，防止按钮过多 |
| 4 | 保存成功后调用 `loadDashboard()` | 自动刷新，立刻可见结果 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 保存 word 后 `/dashboard` 的 saved_words 能看到 | 通过 |
| 保存 phrase 后 `/dashboard` 的 saved_phrases 能看到 | 通过 |
| 保存失败时页面有提示 | 通过，`setStatus(saveStatus, error.message, "error")` |
| Save 按钮不超过 12 个（word 6 + phrase 6） | 通过 |
| 保存中按钮禁用，防止重复提交 | 通过 |
