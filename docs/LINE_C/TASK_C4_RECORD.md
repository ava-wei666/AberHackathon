# Task C4 记录 - HTTP Helper

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C4 要求，把所有 API 请求集中管理，避免 HTTP 请求散落在按钮回调里。

C4 本次重点：

- `API_BASE` 仍然只保留在文件顶部
- 所有 GET / POST 请求集中到 HTTP helper
- 请求失败返回 `None`
- 上层业务函数提供 mock fallback
- 请求结束后尽量关闭 `response`
- 网络失败时 CYD 不黑屏、不崩溃

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 业务主文件 | `embedded/scenelingo_dashboard.py` |
| 板端上传文件 | `:scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C4_RECORD.md` |
| 是否修改 `touch_color_test.py` | 否 |
| 是否提交真实 Wi-Fi 密码 | 否 |

## C4 HTTP helper 字段

| 字段 / 函数 | 作用 |
| --- | --- |
| `API_BASE` | 后端基础地址，当前为 `http://192.168.137.1:8000` |
| `USE_MOCK_DATA` | mock-first 开关，当前为 `True` |
| `_build_url(path)` | 统一拼接 URL，避免斜杠处理散落 |
| `_import_requests()` | 兼容 `requests` / `urequests` |
| `_post_json(requests, url, payload)` | 统一 POST JSON，兼容 `json=` 和 `data=` |
| `_json_from_response(response)` | 统一解析 JSON |
| `_request_json(method, path, payload)` | 真正执行 HTTP 请求的集中函数 |
| `api_get(path)` | C4 对外 GET helper |
| `api_post(path, payload)` | C4 对外 POST helper |
| `fetch_contexts()` | `GET /contexts`，失败回退 mock |
| `fetch_context(context_id)` | `GET /context/{id}`，失败回退 mock |
| `fetch_dashboard()` | `GET /dashboard`，失败回退 mock |
| `save_item(item_text, item_type, source_context)` | `POST /save_item` |

## 执行命令记录

| 步骤 | 命令 | 做了什么 | 结果字段 |
| --- | --- | --- | --- |
| 1 | `git status --short --branch` | 检查工作区状态 | C2 / C3 文件仍未提交 |
| 2 | `rg -n "requests|urequests|api_get|api_post|fetch_contexts|fetch_context\\(|fetch_dashboard|save_item|handle_save|API_BASE|USE_MOCK_DATA" embedded\scenelingo_dashboard.py` | 查找 HTTP 和业务 helper 位置 | 找到现有 `api_get`, `api_post`, `fetch_*`, `save_item` |
| 3 | `Get-Content -Raw -Encoding UTF8 embedded\scenelingo_dashboard.py` | 读取 C3 业务主文件 | 确认已有 C3 mock-first 结构 |
| 4 | `python -m py_compile embedded\scenelingo_dashboard.py` | 本地语法检查 | 通过，无语法错误 |
| 5 | `rg -n "requests\\.|urequests|\\.get\\(|\\.post\\(|api_get|api_post|_request_json|_build_url|fetch_contexts|fetch_context\\(|fetch_dashboard|save_item" embedded\scenelingo_dashboard.py` | 检查 HTTP 请求是否集中 | `requests.get/post` 只在 `_request_json()` / `_post_json()` 内出现 |
| 6 | `mpremote connect COM7 fs cp embedded\scenelingo_dashboard.py :scenelingo_dashboard.py` | 上传更新后的业务文件到 CYD | 上传成功 |
| 7 | `Select-String -Path embedded\scenelingo_dashboard.py -Pattern ...` | 检查关键函数和 `response.close()` | 找到 `_request_json`, `api_get`, `api_post`, `fetch_*`, `save_item`, `response.close` |

## 本次实现说明

`scenelingo_dashboard.py` 增加 / 调整了：

```text
_build_url()
_import_requests()
_post_json()
_request_json()
api_get()
api_post()
```

请求流程变成：

```text
UI button
  -> fetch_contexts() / fetch_context() / fetch_dashboard() / save_item()
  -> api_get() / api_post()
  -> _request_json()
  -> requests / urequests
```

这样按钮回调不直接发 HTTP，请求失败只影响返回值，不会让页面崩溃。

## C4 验收结果

| 验收项 | 结果 |
| --- | --- |
| 换 IP 只改 `API_BASE` | 通过 |
| 所有 GET 集中到 `api_get()` | 通过 |
| 所有 POST 集中到 `api_post()` | 通过 |
| 按钮回调不直接调用 requests | 通过 |
| 请求失败返回 `None` | 通过，`_request_json()` 异常时返回 `None` |
| 请求结束尽量关闭 response | 通过，`finally` 中调用 `response.close()` |
| `/contexts` 失败有 mock fallback | 通过 |
| `/context/{id}` 失败有 mock fallback | 通过 |
| `/dashboard` 失败有 mock fallback | 通过 |
| `/save_item` payload 包含必要字段 | 通过，包含 `item_text`, `item_type`, `source_context` |

## 注意事项

- 当前 `USE_MOCK_DATA = True`，所以默认不会真的发 HTTP 请求。
- C11 真实 API 联调时，把 `USE_MOCK_DATA` 改为 `False`，并确认 C1 网络仍然可用。
- 真实 Wi-Fi 密码仍然不能写入 Git。
- 本次没有覆盖板端 `main.py`，只更新了 `:scenelingo_dashboard.py`。
