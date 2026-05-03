# 三线合并与 CYD 部署记录

日期：2026-05-03

## 目标

`docs/TASK_PHASES.md` 把 MVP 拆成三条线并行：

```
线 A：Backend + NLP + SQLite
线 B：Web Input + Web Dashboard
线 C：CYD LVGL Display
```

三条线各自完成后需要：

1. 把三条线的产物合到同一个 `main` 分支
2. 把 CYD 业务文件烧到 ESP32 (CYD)，让屏幕跑出 Scene Words 的 Home / Insight / Dashboard 页面
3. 完成 `Web 输入 -> FastAPI 分析 -> SQLite 保存 -> CYD Dashboard 展示` 的闭环

本文件记录从「三条线 push 完」到「ESP32 屏幕亮 + 真实 API 联调」的全部操作。

## 关键发现：合并 `a5bceb2` 把线 C 的文件丢了

### 提交图

```
a5bceb2 (HEAD, origin/main)  Merge — Geist-L
├── 32d931d  "change files"      (Geist-L 这边的 Line A docs + web 改动)
└── d9ea00b  Merge (Ruotong)     (含线 C 全部成果，链路 cd45afe → ... → 7b8b5a2)
```

合并 `a5bceb2` 时本地解决冲突错了，把右侧 (`d9ea00b`) 带过来的线 C 文件全部删掉，左侧 (`32d931d`) 又没有这些文件，于是合并结果里 **没有任何 CYD 业务文件**。

### 验证命令

```powershell
git ls-tree 7b8b5a2 -- lvgl9_firmwares/    # 线 C 那一侧：有 scenelingo_dashboard.py
git ls-tree origin/main -- lvgl9_firmwares/ # 合并后的 main：没有 scenelingo_dashboard.py
```

### 丢失文件清单

| 文件                                                   | 状态                |
| ---------------------------------------------------- | ----------------- |
| `lvgl9_firmwares/scenelingo_dashboard.py`            | 931 行的 CYD 主程序，丢失 |
| `docs/TASK_C2_RECORD.md` ~ `docs/TASK_C14_RECORD.md` | 13 个任务记录全部丢失      |

未丢失：`docs/TASK_C0_RECORD.md`、`docs/TASK_C1_RECORD.md`（线 C 早期 Wi-Fi / 触摸验证）；`docs/LINE_A/`（线 A 步骤文档）；`backend/`（线 A 后端）；`web/index.html`（线 B 网页）。

## 恢复操作

不动任何已有提交，只把丢掉的 14 个文件从 `7b8b5a2`（线 C 顶端）checkout 出来，作为一个新的恢复 commit。

```powershell
git checkout 7b8b5a2 -- `
  lvgl9_firmwares/scenelingo_dashboard.py `
  docs/TASK_C2_RECORD.md docs/TASK_C3_RECORD.md docs/TASK_C4_RECORD.md `
  docs/TASK_C5_RECORD.md docs/TASK_C6_RECORD.md docs/TASK_C7_RECORD.md `
  docs/TASK_C8_RECORD.md docs/TASK_C9_RECORD.md docs/TASK_C10_RECORD.md `
  docs/TASK_C11_RECORD.md docs/TASK_C12_RECORD.md docs/TASK_C13_RECORD.md `
  docs/TASK_C14_RECORD.md

git add -A
git commit -m "Restore Line C files lost in merge a5bceb2"
```

恢复后的 commit：`34aadc6 Restore Line C files lost in merge a5bceb2`，14 个文件 / 2477 行。

为什么不用 `git revert a5bceb2`：merge commit 的 revert 会牵连太多无关变更，而且会把 `32d931d` 那一侧的 Line A 文档也回退掉。直接 checkout 丢失文件是最小破坏的恢复方式。

`docs/TASK_C0_RECORD.md` 在两侧都有但格式不同（线 A 改成对齐表格），diff 后内容一致，仅空白差异，因此跳过不恢复。

## 上传到 CYD（mock 模式验证）

### 与 `TASK_C1_RECORD.md` 不同的实测情况

| 项              | C1 记录        | 本次实测            |
| -------------- | ------------ | --------------- |
| CYD 串口         | `COM7`       | `COM3`（USB 口换了） |
| laptop WLAN IP | `10.83.6.63` | `10.88.0.183`   |
| Mobile Hotspot | `On`         | `Off`（需要重新打开）   |

### 选择「mock 模式优先上传」的原因

`scenelingo_dashboard.py` 顶部默认 `USE_MOCK_DATA = True`、`AUTO_CONNECT_WIFI = False`。先用 mock 上传可以：

- 验证 CYD 固件、LVGL 模块、文件本身没问题
- 屏幕上立刻看到 Home 页，不需要先解决 Wi-Fi 和后端
- 失败时可以确定是硬件 / 文件问题，而不是网络问题

### 上传命令

```powershell
mpremote connect COM3 fs cp lvgl9_firmwares/scenelingo_dashboard.py :main.py
mpremote connect COM3 reset
```

文件复制为板端 `main.py`，复位后 CYD 自动运行。CYD 屏幕显示 Home 页，三个按钮（Real-world / Story / Dashboard）。

板端依赖：`lcd_bus`、`ili9341`、`xpt2046`、`task_handler`、`touch_cal_data` 由 LVGL MicroPython 固件冻结提供；`:lib/` 下另有 `lv_config.py`、`lv_helper.py`、`lv_utils.py`。无需额外上传依赖。

## 产品名修正：SceneLingo → Scene Words

CYD 屏幕显示的 Home 标题写的是 `SceneLingo`，与产品正式名 `Scene Words` 不一致。修改 6 处用户可见字面值：

| 文件                                        | 行   | 修改前                                                    | 修改后                                                     |
| ----------------------------------------- | --- | ------------------------------------------------------ | ------------------------------------------------------- |
| `lvgl9_firmwares/scenelingo_dashboard.py` | 665 | `add_title(scr, "SceneLingo")`                         | `add_title(scr, "Scene Words")`                         |
| `lvgl9_firmwares/scenelingo_dashboard.py` | 923 | `print("--> SceneLingo CYD dashboard ready.")`         | `print("--> Scene Words CYD dashboard ready.")`         |
| `web/index.html`                          | 6   | `<title>SceneLingo Web Input</title>`                  | `<title>Scene Words Web Input</title>`                  |
| `web/index.html`                          | 376 | `<h1>SceneLingo</h1>`                                  | `<h1>Scene Words</h1>`                                  |
| `backend/main.py`                         | 76  | `app = FastAPI(title="SceneLingo API", ...)`           | `app = FastAPI(title="Scene Words API", ...)`           |
| `backend/main.py`                         | 91  | `return {"status": "ok", "service": "SceneLingo API"}` | `return {"status": "ok", "service": "Scene Words API"}` |

### 暂未修改的位置（避免破坏现有联调或属于历史记录）

- 文件名：`lvgl9_firmwares/scenelingo_dashboard.py`、`scenelingo.db`
- 热点 SSID：`SceneLingo-CYD`（改名要重配热点 + CYD 重连）
- 历史任务记录：`docs/TASK_C*_RECORD.md`、`docs/LINE_*` 系列
- 内部脚本与说明：`README.md`、`backend/{selftest,demo_check,cyd_smoke,web_smoke}.py`
- Python 模块标识符：`scenelingo_dashboard`、`scenelingo` 等 `import` 路径

### 重新上传 CYD

```powershell
mpremote connect COM3 fs cp lvgl9_firmwares/scenelingo_dashboard.py :main.py
mpremote connect COM3 reset
```

CYD 屏幕 Home 页标题更新为 `Scene Words`。

## 后续步骤（待执行）

mock 模式只是 UI 验证，闭环还需要切到真实 API。以下步骤将在用户提供 Wi-Fi 密码后继续：

1. **打开 Mobile Hotspot**：让 CYD 通过 SSID `SceneLingo-CYD` 接入 laptop 局域网（laptop 自己仍走 eduroam）
2. **启动后端**（必须 `--host 0.0.0.0`，否则 CYD 连不到）：
   ```powershell
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

1. **修改 `lvgl9_firmwares/scenelingo_dashboard.py` 顶部 4 项**（密码不写入 Git）：
   ```python
   API_BASE          = "http://192.168.137.1:8000"   # 已正确，不动
   WIFI_SSID         = "SceneLingo-CYD"
   WIFI_PASSWORD     = "<本地填，禁止 commit>"
   AUTO_CONNECT_WIFI = True
   USE_MOCK_DATA     = False
   ```

1. **重新上传并复位**：
   ```powershell
   mpremote connect COM3 fs cp lvgl9_firmwares/scenelingo_dashboard.py :main.py
   mpremote connect COM3 reset
   ```

1. **`git restore` 把密码改回 `CHANGE_ME`**，避免误 commit
2. **闭环验证**（参见 `TASK_PHASES.md` Step 5）：
   - CYD 进入 Dashboard → Refresh，看到真实数据
   - Web 提交一段 Coffee Shop 文本 → Save Word
   - CYD 再 Refresh → 看到刚保存的词

## 一句话给老师 / 队友

> 三条线（后端、网页、CYD 业务文件）都已经合到 `main`。合并时一次解决冲突错误把 CYD 主程序删掉了，从线 C 那一支的最后一个 commit (`7b8b5a2`) 把丢失的 14 个文件捡回来，新加 commit `34aadc6` 完成恢复。然后把 CYD 业务文件以 mock 模式烧到 ESP32 验证 UI（屏幕亮、按钮可点），再把产品名从 `SceneLingo` 改成 `Scene Words`。下一步打开热点 + 启动后端，把 CYD 切到真实 API，完成 Web → 后端 → SQLite → CYD 的闭环。
