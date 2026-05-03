# LINE_A Task A9 操作记录

## 记录字段

| 字段       | 内容                                                                               |
| -------- | -------------------------------------------------------------------------------- |
| Line     | `LINE_A`                                                                         |
| Task     | `A9 - Context API`                                                               |
| 状态       | 已通过                                                                              |
| 执行日期     | `2026-05-03`                                                                     |
| 工作目录     | `C:\hackathon`                                                                   |
| 后端地址     | `http://127.0.0.1:8000/`                                                         |
| 当前服务进程   | `48024`                                                                          |
| 主要涉及文件   | `backend/main.py`、`backend/database.py`、`backend/seed_data.json`、`scenelingo.db` |
| 本次业务代码改动 | 无                                                                                |
| 文档记录     | `docs/LINE_A_A9_STEPS.md`                                                        |
| 下一步      | A10 Save / Dashboard API                                                         |

## 编号说明

`docs/LINE_A_BACKEND_TASKS.md` 中详细拆分为 A10 `GET /contexts` 和 A11 `GET /context/{id}`。

当前执行记录按 `docs/TASK_PHASES.md` 的阶段顺序推进：A9 记录 Context API。

## 任务目标

完成 Web 和 CYD 共用的 context 读取接口：

- `GET /contexts`：给线 B 渲染 context 下拉框 / 选择页。
- `GET /context/{id}`：给线 C 渲染 CYD 场景卡片 / Insight View。
- 不存在的 context id 返回 HTTP 404。

## 接口定义

`GET /contexts`

| 字段     | 内容                               |
| ------ | -------------------------------- |
| Method | `GET`                            |
| Path   | `/contexts`                      |
| 用途     | 返回 real-world / story 两组 context |
| 数据来源   | SQLite `contexts` 表              |
| 写数据库   | 否                                |

`GET /context/{id}`

| 字段     | 内容                                        |
| ------ | ----------------------------------------- |
| Method | `GET`                                     |
| Path   | `/context/{context_id}`                   |
| 用途     | 返回单个 context 卡片数据                         |
| 数据来源   | SQLite `contexts` 表                       |
| 不存在 id | HTTP 404，`{"detail":"Context not found"}` |
| 写数据库   | 否                                         |

## 返回字段记录

`GET /contexts` 顶层结构：

| 字段           | 内容                    |
| ------------ | --------------------- |
| `real_world` | real-world context 数组 |
| `story`      | story context 数组      |

每个 context 至少包含：

```
id
title
type
summary
seed_keywords
seed_phrases
```

当前实现还包含：

```
tag
```

## 验收命令

`GET /contexts` 分组和字段检查：

```powershell
$contexts = Invoke-RestMethod -Uri http://127.0.0.1:8000/contexts
$required = @('id', 'title', 'type', 'summary', 'seed_keywords', 'seed_phrases')
$allContexts = @($contexts.real_world) + @($contexts.story)
$missing = @()
foreach ($context in $allContexts) {
  foreach ($field in $required) {
    if ($field -notin @($context.PSObject.Properties.Name)) {
      $missing += "$($context.id).$field"
    }
  }
}
"real_world_count=$(@($contexts.real_world).Count)"
"story_count=$(@($contexts.story).Count)"
"total_count=$($allContexts.Count)"
"real_world_ids=$((@($contexts.real_world) | ForEach-Object { $_.id }) -join ',')"
"story_ids=$((@($contexts.story) | ForEach-Object { $_.id }) -join ',')"
"missing_fields=$($missing -join ',')"
$contexts | ConvertTo-Json -Depth 8
```

`GET /context/coffee_shop` 检查：

```powershell
$context = Invoke-RestMethod -Uri http://127.0.0.1:8000/context/coffee_shop
$required = @('id', 'title', 'type', 'tag', 'summary', 'seed_keywords', 'seed_phrases')
$fields = @($context.PSObject.Properties.Name)
$missing = @($required | Where-Object { $_ -notin $fields })
"status=HTTP_200"
"id=$($context.id)"
"title=$($context.title)"
"type=$($context.type)"
"keyword_count=$(@($context.seed_keywords).Count)"
"phrase_count=$(@($context.seed_phrases).Count)"
"missing_fields=$($missing -join ',')"
$context | ConvertTo-Json -Depth 8
```

不存在 id 的 404 检查：

```powershell
@'
from urllib.error import HTTPError
from urllib.request import urlopen

try:
    urlopen('http://127.0.0.1:8000/context/not_a_real_context')
    print('unexpected_success=True')
except HTTPError as error:
    print(f'status={error.code}')
    print('body=' + error.read().decode('utf-8'))
'@ | .\.venv\Scripts\python.exe -
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\__init__.py backend\main.py backend\nlp_engine.py backend\database.py
```

## 验收结果

| 检查项                               | 结果                               |
| --------------------------------- | -------------------------------- |
| Python 编译检查                       | 通过                               |
| `/contexts` HTTP 状态               | `200`                            |
| `/contexts` real-world 数量         | `2`                              |
| `/contexts` story 数量              | `2`                              |
| `/contexts` context 总数            | `4`                              |
| real-world ids                    | `coffee_shop`、`doctor_pharmacy`  |
| story ids                         | `kings_cross`、`baker_street`     |
| `/contexts` 必要字段                  | 无缺失                              |
| `/context/coffee_shop` HTTP 状态    | `200`                            |
| `/context/coffee_shop` id         | `coffee_shop`                    |
| `/context/coffee_shop` title      | `Coffee Shop`                    |
| `/context/coffee_shop` keyword 数量 | `12`                             |
| `/context/coffee_shop` phrase 数量  | `5`                              |
| 不存在 id                            | HTTP `404`                       |
| 404 响应体                           | `{"detail":"Context not found"}` |

`GET /contexts` 检查输出：

```
real_world_count=2
story_count=2
total_count=4
real_world_ids=coffee_shop,doctor_pharmacy
story_ids=kings_cross,baker_street
missing_fields=
```

`GET /context/coffee_shop` 检查输出：

```
status=HTTP_200
id=coffee_shop
title=Coffee Shop
type=real-world
keyword_count=12
phrase_count=5
missing_fields=
```

404 检查输出：

```
status=404
body={"detail":"Context not found"}
```

## 代码和数据影响

| 字段                  | 内容                                   |
| ------------------- | ------------------------------------ |
| 业务代码                | 未修改，现有实现已满足 A9                       |
| 中文注释                | `backend/main.py` 的 context 路由已有中文注释 |
| 数据库写入               | 无，Context API 只读                     |
| contexts 总数         | `4`                                  |
| analysis_results 总数 | `12`                                 |
| review_items 总数     | `4`                                  |

## 给线 B / 线 C 的联调信息

| 使用方     | 接口                         | 用途                              |
| ------- | -------------------------- | ------------------------------- |
| 线 B Web | `GET /contexts`            | 渲染 context 选择控件                 |
| 线 C CYD | `GET /context/coffee_shop` | 渲染 Coffee Shop 场景卡片             |
| 线 C CYD | `GET /context/{id}`        | 渲染任意 MVP context 的 Insight View |

可用 context ids：

```
coffee_shop
doctor_pharmacy
kings_cross
baker_street
```

## 当前 Dashboard 记录

| 字段              | 当前结果                                                                          |
| --------------- | ----------------------------------------------------------------------------- |
| saved words     | `receipt`、`latte`                                                             |
| saved phrases   | `for here`、`to go`                                                            |
| top context     | `coffee_shop`                                                                 |
| recent keywords | `get`、`latte`、`milk`、`how`、`much`、`detective`、`found`、`clue`、`baker`、`street` |
| review_today    | `4`                                                                           |

## 服务状态记录

| 字段   | 内容                       |
| ---- | ------------------------ |
| 当前进程 | `48024`                  |
| 本机访问 | `http://127.0.0.1:8000/` |
| 停止命令 | `Stop-Process -Id 48024` |

## 结论

- A9 已通过。
- `/contexts` 可以给线 B 返回 2 个 real-world 和 2 个 story context。
- `/context/coffee_shop` 可以给线 C 返回可直接展示的 Coffee Shop 卡片数据。
- 不存在的 context id 会返回 HTTP 404。
- Context API 是只读接口，本次验收没有写入数据库。
