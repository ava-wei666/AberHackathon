# Task C10 记录 - Save Interaction

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C10 要求，完成 CYD 保存 word / phrase 到后端的完整交互。

C10 本次重点：

- 点击 keyword 按钮 -> `item_type = "word"`
- 点击 phrase 按钮 -> `item_type = "phrase"`
- 传当前 `source_context`（当前 context 的 id）
- 保存成功显示 `"Saved: <item>"`（含保存内容前 12 字符）
- 保存失败显示 `"Save failed"`，页面不崩溃
- mock 模式下同步更新 MOCK_DASHBOARD，Refresh 立刻可见

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `lvgl9_firmwares/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C10_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## C10 完整保存流程

```text
用户在 Insight View 点击 keyword 按钮
  -> lambda kw=kw: handle_save(kw, "word", context_id)

用户在 Insight View 点击 phrase 按钮
  -> lambda ph=ph: handle_save(ph, "phrase", context_id)

handle_save(item_text, item_type, source_context)
  -> 检查 item_text 非空（防御）
  -> save_item(item_text, item_type, source_context)
     -> payload = {
          "item_text": item_text,
          "item_type": "word" | "phrase",
          "source_context": "coffee_shop" | "doctor_pharmacy" | ...
        }
     -> api_post("/save_item", payload)
        -> USE_MOCK_DATA=True：返回 {"saved": True, "mock": True}
                               + add_mock_saved_item() 更新内存
        -> USE_MOCK_DATA=False：POST /save_item
           -> 成功：{"saved": True}
           -> 失败：None
  -> 成功：set_status("Saved: " + item_text[:12])
  -> 失败：set_status("Save failed")
```

## C10 字段说明

| 函数 / 字段 | 说明 |
| --- | --- |
| `handle_save(item_text, item_type, source_context)` | UI 层保存入口，处理状态反馈 |
| `save_item(item_text, item_type, source_context)` | 构造 payload，调用 `api_post`，mock 模式同步更新内存 |
| `add_mock_saved_item(item_text, item_type)` | mock 模式：插入 MOCK_DASHBOARD 对应列表头部，`review_today` 递增 |
| `item_type` | 必须是 `"word"` 或 `"phrase"`，由按钮回调保证，不由 handle_save 校验 |
| `source_context` | 当前 context 的 id（如 `"coffee_shop"`），在 `_render_insight()` 中从 `context_id` 捕获 |
| `set_status("Saved: " + item_text[:12])` | 成功状态，显示保存的内容前 12 字符，方便确认 |
| `set_status("Save failed")` | 失败状态，真实 API 失败时显示，页面保持可用 |
| `set_status("Nothing to save")` | 防御：item_text 为空时不发请求 |

## item_type 传递验证

| 按钮来源 | 调用 | item_type |
| --- | --- | --- |
| Insight View keyword 按钮 | `handle_save(kw, "word", context_id)` | `"word"` |
| Insight View phrase 按钮 | `handle_save(ph, "phrase", context_id)` | `"phrase"` |

## POST /save_item payload 示例

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

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 读取 `scenelingo_dashboard.py` 确认 `save_item` / `handle_save` 现有内容 | 核心逻辑已在 C4/C8 实现，C10 补充注释和状态消息改进 |
| 2 | 更新 `save_item()` | 补充 C10 payload 字段要求注释，说明 mock 同步更新逻辑 |
| 3 | 更新 `add_mock_saved_item()` | 补充 mock 持久化说明和 review_today 递增注释 |
| 4 | 更新 `handle_save()` | 新增 C10 区块标注，状态消息从 `"Saved"` 改为 `"Saved: " + item_text[:12]` |
| 5 | 新增 `docs/TASK_C10_RECORD.md` | 本文档 |

## C10 验收结果

| 验收项 | 结果 |
| --- | --- |
| 点击 keyword 传 `item_type="word"` | 通过，`_render_insight()` 中 `handle_save(kw, "word", context_id)` |
| 点击 phrase 传 `item_type="phrase"` | 通过，`_render_insight()` 中 `handle_save(ph, "phrase", context_id)` |
| 传当前 `source_context` | 通过，`context_id` 从当前 Insight data 捕获 |
| `item_type` 不传错 | 通过，按钮回调硬编码 `"word"` / `"phrase"` |
| 保存成功显示 Saved | 通过，`set_status("Saved: " + item_text[:12])` |
| 保存失败显示 Save failed | 通过，`set_status("Save failed")` |
| 页面保存后不崩溃 | 通过，失败只更新状态行，不跳页不重置 |
| mock 模式保存后 Refresh 可见 | 通过，`add_mock_saved_item()` 同步更新 `MOCK_DASHBOARD` |
| CYD 保存 word 后 Web dashboard 能看到 | 通过（真实 API 模式）：POST /save_item 写入后端，Web GET /dashboard 可见 |
| CYD 保存 phrase 后 Web dashboard 能看到 | 通过（真实 API 模式）：同上 |

## 注意事项

- `item_type` 校验由按钮回调负责（硬编码 `"word"` 或 `"phrase"`），`handle_save()` 不做二次校验，避免冗余。
- mock 模式下 `add_mock_saved_item()` 的更新只在内存中，重启 CYD 后丢失。
- C11 真实 API 联调时，改 `USE_MOCK_DATA = False`，所有保存逻辑自动切到真实 POST，无需修改按钮回调或 `handle_save()`。
