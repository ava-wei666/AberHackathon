# Task B11 记录 - 给线 C 的交付

日期：2026-05-03

## 目标

线 B 向线 C 交付 Web 已验证的 dashboard 字段，供 CYD 接入使用。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | 无（沟通任务） |

## Web 已验证可用的 Dashboard 字段

以下字段经 Web 端实际调用 `/dashboard` 验证，线 C 可直接照此接入：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `detected_context.title` | string | 场景名称，例：Coffee Shop |
| `detected_context.id` | string | 场景 ID，例：coffee_shop |
| `keywords` | string[] | 关键词列表 |
| `phrases` | string[] | 短语列表 |
| `summary` | string | 场景描述，建议截取第一句 |
| `saved_words` | object[] | 已保存词，含 `item_text`、`source_context` |
| `saved_phrases` | object[] | 已保存短语，含 `item_text`、`source_context` |
| `top_context` | string | 最常出现的 context ID |
| `review_today` | number | 今日复习数量 |

## 适合 CYD 显示的字段建议

CYD 屏幕较小，建议只展示：

| 字段 | CYD 展示建议 |
| --- | --- |
| `detected_context.title` | 主标题，大字 |
| `keywords[:5]` | 最多 5 个，每个独立按钮 |
| `phrases[:3]` | 最多 3 个，每个独立按钮 |
| `summary` | 截取第一句，小字 |
| `top_context` | Context Select 页显示 |
| `review_today` | Dashboard 页显示数字 |

## 注意事项

- 线 B 不写 CYD 页面，也不调整 LVGL。
- 线 B 不要求线 C 改 API，字段已在 Web 端验证完毕。
- `saved_words` / `saved_phrases` 的每个元素是 object，取 `item.item_text` 显示文本。
