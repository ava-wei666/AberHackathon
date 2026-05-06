# Task C8 记录 - Insight View

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C8 要求，完成 Insight View 页面的实现。

C8 本次重点：

- 显示 context 标题
- 至少 5 个 keyword，每个独立可点击 → 保存为 word
- 至少 3 个 phrase，每个独立可点击 → 保存为 phrase
- summary 最多显示 1 句
- 长 phrase 截断，不撑破布局
- 保存成功 / 失败在状态行提示
- Back 按钮返回 Context Select

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `lvgl9_firmwares/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C8_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## C8 Insight View 布局

```text
┌─────────────────────────┐  y=0
│       Coffee Shop       │  y=8   主标题（context 名称）
│    Top Keywords         │  y=36  区块标签（灰色小字）
│  [latte  ] [milk   ]    │  y=55  KW row 1（2 列，每列 108×26）
│  [size   ] [order  ]    │  y=85  KW row 2
│  [receipt]              │  y=115 KW row 3（最后 1 个，左列）
│    Useful Phrases       │  y=145 区块标签（灰色小字）
│  [Can I Get           ] │  y=163 Phrase 0（210×26）
│  [to go               ] │  y=191 Phrase 1
│  [with milk           ] │  y=219 Phrase 2
│  This looks like...     │  y=251 Summary（1 句，灰色小字）
│                         │  y=269 状态行（Saved / Save failed）
│         [Back]          │  y=285 Back 按钮（90×28）
└─────────────────────────┘  y=320
```

## C8 字段说明

| 元素 / 参数 | 说明 |
| --- | --- |
| `keywords[:5]` | 截取前 5 个，防止超出屏幕高度 |
| `phrases[:3]` | 截取前 3 个 |
| `kw[:14]` | keyword 按钮文本截断到 14 字符，防止超出 108px 宽度 |
| `ph[:30]` | phrase 按钮文本截断到 30 字符，防止撑破 210px 宽度 |
| `y_kw` | 动态 y 坐标，每 2 个 keyword 增加 30px |
| `x_ofs = -59 / +59` | 关键词左列 / 右列的水平偏移，相对屏幕中心对称 |
| `y_ph_hdr` | Phrases 标签 y = 最后一个 keyword y + 30 |
| `y_ph` | phrase 按钮起始 y，步进 28px |
| `summary_short` | `summary.split(".")[0][:48]`，只取第一句最多 48 字符 |
| `status_label` | 全局变量，`handle_save()` 通过 `set_status()` 回写文本 |
| `add_button(..., x_ofs)` | `add_button` 新增 `x_ofs=0` 参数支持水平偏移，向后兼容 |

## add_button 变更说明

原签名：`add_button(parent, text, y, cb, width=190, height=44)`

新签名：`add_button(parent, text, y, cb, width=190, height=44, x_ofs=0)`

- 新增 `x_ofs=0` 默认参数，现有调用无需修改（向后兼容）。
- C8 keyword 按钮传入 `x_ofs=-59` 或 `x_ofs=+59` 实现 2 列布局。

## 点击 keyword / phrase 的保存流程

```text
用户点击 keyword 按钮
  -> handle_save(kw, "word", context_id)
  -> save_item(kw, "word", context_id)
     -> api_post("/save_item", {...})
        -> USE_MOCK_DATA=True：返回 {"saved": True, "mock": True}
        -> USE_MOCK_DATA=False：POST /save_item
           -> 成功：{"saved": True}
           -> 失败：None
  -> set_status("Saved") 或 set_status("Save failed")

用户点击 phrase 按钮
  -> handle_save(ph, "phrase", context_id)  [同上流程，item_type="phrase"]
```

## 执行命令记录

| 步骤 | 操作 | 结果 |
| --- | --- | --- |
| 1 | 读取 `scenelingo_dashboard.py` 确认现有 `_render_insight()` 内容 | 原实现只有 1 个 keyword 按钮 + 1 个 phrase 按钮，不满足 C8 逐个可点击要求 |
| 2 | 修改 `add_button` 新增 `x_ofs=0` 参数 | 向后兼容，C8 keyword 2 列布局使用 |
| 3 | 重写 `_render_insight()` | 5 个独立 keyword 按钮（2 列）+ 3 个独立 phrase 按钮 + summary + 状态行 + Back |
| 4 | 更新 `handle_save()` | 统一 mock 和真实 API 的 Saved 提示，移除 "Saved mock" 分支 |
| 5 | 新增 `docs/TASK_C8_RECORD.md` | 本文档 |

## C8 验收结果

| 验收项 | 结果 |
| --- | --- |
| 显示 context 标题 | 通过，`add_title(scr, title)` |
| 至少显示 5 个 keywords | 通过，`keywords[:5]` 最多取 5 个，每个独立按钮 |
| 每个 keyword 可点击保存为 word | 通过，`handle_save(kw, "word", context_id)` |
| 至少显示 3 个 phrases | 通过，`phrases[:3]` 最多取 3 个，每个独立按钮 |
| 每个 phrase 可点击保存为 phrase | 通过，`handle_save(ph, "phrase", context_id)` |
| summary 最多 1 句 | 通过，`summary.split(".")[0][:48]` |
| 长 phrase 不撑破布局 | 通过，`ph[:30]` 截断 + 按钮宽 210px |
| 保存成功显示 Saved | 通过，`set_status("Saved")` |
| 保存失败显示 Save failed | 通过，`set_status("Save failed")` |
| Back 按钮返回 Context Select | 通过，`go_back()` 弹出历史栈 |
| Coffee Shop 数据能看清楚 | 通过，mock 含 5 个 keywords + 3 个 phrases |
| lambda 闭包无陷阱 | 通过，`lambda kw=kw` / `lambda ph=ph` 默认参数捕获 |

## 注意事项

- `handle_save()` 中移除了原来的 `elif USE_MOCK_DATA: set_status("Saved mock")` 分支。mock 模式下 `api_post` 返回 `{"saved": True}`，与真实 API 成功路径一致，统一显示 "Saved"。
- keyword 文本截断到 14 字符（`kw[:14]`）适配 108px 宽度；如果 keyword 较长可适当调整。
- C11 真实 API 联调时改 `USE_MOCK_DATA = False`，所有按钮逻辑和布局无需改动。
