# Task B3 记录 - 提交文本分析

日期：2026-05-03

## 目标

用户点击 Analyze Text 后调用后端 NLP 接口，展示分析结果。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |

## API 接口

```
POST /analyze_text
```

请求体：

```json
{
  "raw_text": "Hi, can I get a latte with milk to go?",
  "source_type": "real-world",
  "optional_context": null
}
```

注意：未选择 optional context 时传 `null`，不传空字符串。

## 实现逻辑

```text
点击 Analyze Text
  -> 校验文本不为空，为空则提示错误
  -> analyzeButton.disabled = true（防止重复提交）
  -> 显示 Analyzing...
  -> fetch POST /analyze_text
  -> 成功：保存 latestResult，渲染结果，渲染保存按钮
  -> 失败：显示错误信息
  -> finally：analyzeButton.disabled = false
```

## 错误处理

- 空文本：`setStatus(analysisStatus, "Please enter some text first.", "error")`
- 网络失败：catch 捕获，`setStatus` 显示错误
- HTTP 非 2xx：`parseJsonResponse()` 统一抛出 `HTTP 状态码: 错误详情`

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 实现 `analyzeText()` | 含空输入校验、loading 状态、try/catch |
| 2 | 实现 `parseJsonResponse()` | 统一处理非 2xx HTTP 响应 |
| 3 | 按钮 disabled 状态管理 | 分析中禁用，完成后恢复 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| Coffee Shop 文本能提交 | 通过 |
| 分析中显示 Analyzing... | 通过 |
| 页面能显示 keywords | 通过 |
| 页面能显示 phrases | 通过 |
| 页面能显示 detected context | 通过 |
| 页面能显示 summary | 通过 |
| 空文本点击时显示提示 | 通过 |
| 请求失败时显示错误信息 | 通过 |
