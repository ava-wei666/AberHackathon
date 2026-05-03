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

## CYD 切换真实 API 的尝试与最终决定

mock UI 跑通后尝试把 CYD 切到真实 API 模式，遇到一连串 Wi-Fi 与内存问题，最终决定**让 CYD 留在 mock 模式演 UI、Web 端承担真实 NLP/存储闭环**。本节记录全部排错过程，避免后人重走老路。

### 1. Wi-Fi 路径切换

| 阶段                                                                 | 结果                                                                                                                   |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| 一开始按 `TASK_C1_RECORD.md` 走 Windows Mobile Hotspot `SceneLingo-CYD` | C1 写的 SSID 已不再有效；Windows 11 现在默认 WPA2/WPA3 mixed (`authmode=7`)，ESP32 SAE 握手不稳，status 在 `201/1001/202` 之间反复，最终拿不到 IP |
| 改 Windows hotspot 为纯 ASCII SSID 与密码 (`scenewords-ap`)              | 同上失败，问题是混合模式不是密码字符                                                                                                   |
| 切到手机热点 `siwen`（纯 WPA2-PSK，2.4 GHz channel 6）                       | Wi-Fi 终于稳定握手，CYD 拿到 IP `192.168.245.107`，REPL 里 `urequests.get('/dashboard')` 返回 200                                 |

附带踩到的 Windows 行为：Mobile Hotspot 默认"无设备连接一段时间自动关"，过 1–2 分钟就 Off；CYD 第一次连尝试期间热点已经关了。我们临时跑了一个 PowerShell `keepalive.ps1` 每 2 秒检查、Off 就重启，作为 hotspot 排错期间的兜底。

### 2. CYD 端启动顺序与内存碰撞

完成 Wi-Fi 后用埋点把 `main()` 走过的步骤写到 flash `boot.log`，发现两组互斥的 OOM：

**组 A：原始顺序 `init_display() -> connect_wifi()`**

```
ets Jul 29 2019 12:21:46
rst:0xc (SW_CPU_RESET) ...
E (1871) wifi:wifi nvs cfg alloc out of memory
E (1871) wifi:init nvs: failed, ret=101
OSError: WiFi Out of Memory
```

LVGL 启动后吃光了大块 SRAM，wifi 驱动 init 时 NVS config 申请失败。

**组 B：交换后 `connect_wifi() -> init_display()`**

```
B:gc-done       mem=137936
B2:reserved-fb  mem=121152   (预占 16KB)
C:pre-wifi      mem=120768
D:wifi-done     mem=94400    (Wi-Fi 消耗 ~26KB)
E:pre-init_display mem=112256
Z:CRASH MemoryError('Unable to allocate memory for frame buffer (15360)')
```

Wi-Fi 装好后总余量还有 112KB，但 LVGL 想要的 15KB **DMA-capable + 连续** 的 frame buffer 拿不到。

试过的缓解都没救：

- `gc.collect()` 在 `connect_wifi()` 后立刻跑：mem 从 94KB 涨到 112KB，但仍分不出 15KB 连续块
- 在 wifi 之前 `bytearray(16384)` 预占 16KB，wifi 后 `del + gc.collect()` 释放：依然 fragmented
- `wlan.config(rxbuf=4096)` 想压小 wifi 接收缓冲：调用没报错，但实际 wifi 仍消耗 ~26KB

**根因**（用 `esp32.idf_heap_info(esp32.HEAP_DATA)` 看堆区域）：

```
total / free / largest_free
(84928,  4, 0)            <- 85KB DMA 区已被 Wi-Fi 占满
(113840, 74008, 59392)    <- 113KB 区有 59KB 连续，但不是 DMA-capable
...小区域全部 ~4 字节
```

LVGL 帧缓冲必须从 **DMA-capable internal SRAM** 取，那 85KB 区被 Wi-Fi 完全占用，剩下的 113KB 区给不出 DMA 内存。这台 CYD **没有 PSRAM**，所以也没法把帧缓冲挪到 SPIRAM。

要彻底修需要重编 LVGL MicroPython 固件，调小 `static_rx_buf_num` / 关 AMPDU / 缩小 wifi 静态分配。Hackathon 时间窗内不一定来得及。

### 3. 决定：CYD mock + Web 真实

和需求方确认后选择：

- **CYD**：`AUTO_CONNECT_WIFI = False`、`USE_MOCK_DATA = True`。屏幕显示 Home / Insight / Dashboard 三页 LVGL UI，数据来自脚本里硬编码的 `MOCK_ANALYSIS` / `MOCK_DASHBOARD`。这正是 C2/C3 任务里设计的"mock 数据先行"，本来就是 fallback。
- **Web**：承担真实 `Web → FastAPI → SQLite → Dashboard` 闭环。`web/index.html` 已修复合并冲突（见下一节），可以现场演示输入 → 分析 → 保存 → dashboard 刷新。
- **演示话术**：CYD 是受限设备，演 UI 故事；真实 NLP / 存储 / 复习闭环由 Web 端展示。两边架构相同，CYD 后续把 Wi-Fi 内存问题修了就能直接打开开关切真实数据。

### 4. 顺手发现：`web/index.html` 还留着未解决的合并冲突标记

合并 `a5bceb2` 时不只是 Line C 文件被删，`web/index.html` 里还有 5 处 `<<<<<<< HEAD ... ======= ... >>>>>>> d9ea00b` 标记没被解决就提交了。浏览器把这些标记当 JavaScript 解析直接 syntax error，整个 `<script>` 块不执行，Analyze / Save / Refresh 按钮都不响应。

解决：`git checkout d9ea00b -- web/index.html` 取 d9ea00b 那一侧（Line B 的完整 dashboard UI），重新打 Scene Words 改名补丁。提交在 `eb7ff2f`。

## 当前演示流程

1. laptop 跑后端：`uvicorn backend.main:app --host 0.0.0.0 --port 8000`
2. 浏览器双击打开 `web/index.html`
3. 输入 Coffee Shop 文本 → Analyze Text → Save Word/Phrase → Refresh Dashboard，全过程 30 秒可演完整闭环
4. CYD 上电，自动跑 `:main.py` (mock 模式)，屏幕显示 Scene Words Home，三按钮可点进 Insight / Dashboard，展示 LVGL UI 与产品形态

## 一句话给老师 / 队友

> 三条线（后端、网页、CYD）已合到 `main`。合并时一次错误冲突解决把 CYD 主程序和 14 个 task 记录删了，从线 C 顶端 `7b8b5a2` checkout 回来 (`34aadc6`)；同次合并还把 `web/index.html` 的合并冲突标记原样提交，导致 Web 按钮失灵，取 `d9ea00b` 完整版重做 (`eb7ff2f`)。CYD 烧上后做了 Scene Words 改名 + Wi-Fi/LVGL 顺序修复 (`95aefdb`)，但深入排查发现 ESP32 内部 SRAM 不够同时跑 Wi-Fi 驱动和 LVGL DMA 帧缓冲，hackathon 时间内无法重编固件，所以决定 CYD 走 mock 模式演 UI，Web 端展示真实闭环。整体演示是端到端跑通的，只是 CYD ↔ 后端的实时联动留作后续优化。
