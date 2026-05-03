# Task B7 记录 - 四段测试输入

日期：2026-05-03

## 目标

用固定文本测试 Web 调用链路，一键填入，不用手动复制粘贴。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `web/index.html` |

## 四段测试文本

| 按钮 | Source | 文本 |
| --- | --- | --- |
| Coffee Shop | real-world | Hi, can I get a latte with milk to go? How much is the large size? |
| Doctor / Pharmacy | real-world | I have a headache and a cough. Do I need medicine from the pharmacy? |
| King's Cross | story | Which platform should I use to catch the train to the magic school at King's Cross? |
| Baker Street | story | The detective found a clue on Baker Street and tried to solve the case. |

## 实现逻辑

```text
点击 demo 按钮（data-demo="coffee" 等）
  -> useDemoInput(key)
  -> sourceType.value = demo.source（自动切换 Real-world / Story）
  -> rawText.value = demo.text
  -> renderContextOptions()（更新 context 下拉框）
  -> contextSelect.value = ""（重置为 Auto detect）
  -> 状态栏提示已加载
```

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 定义 `demoInputs` 对象（4 组 source + text） | 通过 |
| 2 | HTML 中添加 4 个 `data-demo` 属性按钮 | 通过，`.demo-buttons` grid 布局 |
| 3 | 实现 `useDemoInput()` | 自动切换 source、填入文本、重置 context |
| 4 | 事件绑定：`querySelectorAll("[data-demo]")` | 通过 |

## 验收结果

| 验收项 | 结果 |
| --- | --- |
| 四段文本都能从 Web 输入框提交 | 通过 |
| Real-world / Story source type 能正确切换 | 通过 |
| 自动识别不稳定时，可手动选择 optional context | 通过，context 下拉框保留 Auto detect + 具体选项 |
