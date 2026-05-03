# Task B2 记录 - 加载 Contexts

日期：2026-05-03

## 目标

页面启动时从后端拿 context 列表，并根据 source type 渲染下拉框。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |

## API 接口

```
GET /contexts
```

返回格式示例：

```json
{
  "real_world": [
    { "id": "coffee_shop", "title": "Coffee Shop" },
    { "id": "doctor_pharmacy", "title": "Doctor / Pharmacy" }
  ],
  "story": [
    { "id": "kings_cross", "title": "King's Cross" },
    { "id": "baker_street", "title": "Baker Street" }
  ]
}
```

## 实现逻辑

```text
页面加载
  -> loadContexts()
  -> fetch GET /contexts
  -> 成功：保存 contextGroups，调用 renderContextOptions()
  -> 失败：contextGroups 置空，显示错误，页面不白屏

sourceType 切换
  -> renderContextOptions()
  -> 读取 contextGroups[real_world 或 story]
  -> 重新渲染 #contextSelect 下拉选项
```

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 实现 `loadContexts()` | try/catch，失败时显示错误状态 |
| 2 | 实现 `renderContextOptions()` | 根据 sourceType.value 切换 real_world / story |
| 3 | 页面初始化调用 `loadContexts()` | 通过 |
| 4 | `sourceType` 监听 `change` 事件 | 切换时重新渲染下拉框 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| Real-world 下显示 Coffee Shop、Doctor / Pharmacy | 通过 |
| Story 下显示 King's Cross、Baker Street | 通过 |
| 切换 source type 时下拉框内容同步变化 | 通过 |
| 后端没启动时页面显示错误，不白屏 | 通过，`setStatus(contextStatus, error.message, "error")` |
