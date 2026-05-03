# Task B10 记录 - 给线 A 的反馈

日期：2026-05-03

## 目标

线 B 发现 API 问题时，只反馈和接口有关的具体信息，不要求线 A 改数据库结构。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | 无（沟通任务） |

## 反馈格式

线 B 向线 A 反馈时，提供以下信息：

| 字段 | 内容 |
| --- | --- |
| 哪个接口失败 | 例：`POST /analyze_text` |
| 请求 payload | 例：`{"raw_text": "...", "source_type": "real-world", "optional_context": null}` |
| 返回 status | 例：`HTTP 422` |
| 返回字段是否缺失 | 例：`response.keywords 为 undefined` |
| 浏览器 console 错误 | 例：`TypeError: Cannot read properties of undefined` |

## Web 已验证可用的接口

| 接口 | 状态 |
| --- | --- |
| `GET /contexts` | 可用，返回 real_world / story 两组 |
| `POST /analyze_text` | 可用，返回 detected_context / keywords / phrases / summary |
| `POST /save_item` | 可用，返回 `{ "saved": true }` |
| `GET /dashboard` | 可用，返回 saved_words / saved_phrases / top_context / recent_keywords / review_today |

## 注意事项

- 线 B 不要求线 A 改数据库结构，除非当前 API 无法完成 MVP。
- CORS 问题由线 A 在 FastAPI 中配置 `CORSMiddleware` 解决。
- 手机访问时如果有 CORS 报错，检查线 A 是否允许所有 origin 或指定 laptop IP。
