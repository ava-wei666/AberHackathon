# INTEGRATION_RECORD 答辩稿（最简版）

> 背稿用，全程约 60 秒。所有 commit hash、文件名、错误信息都来自 `docs/INTEGRATION_RECORD.md`。

---

## 一句话定位

> 「这份文档记录的是**三条线 push 完之后到 CYD 屏幕真正亮起来**这段集成期发生的所有问题和解决方案。一共三件大事 + 一个最终决定。」

---

## 三件大事（按时间顺序讲）

### ① 合并冲突解错，CYD 文件被误删

- 合并 `a5bceb2` 时把 Line C 那一侧（`d9ea00b`）的文件删了，丢了 **`scenelingo_dashboard.py` 主程序 + 13 个 TASK_C 记录，共 14 个文件**。
- **修复**：不 revert merge（会牵连 Line A 文档），直接
  ```
  git checkout 7b8b5a2 -- <14个文件>
  ```
  拉回，新建恢复 commit `34aadc6`。

### ② Web 按钮全部失灵

- 同一次合并里，`web/index.html` 留了 **5 处未解决的 `<<<<<<< HEAD` 冲突标记** 就被提交。
- 浏览器解析 `<script>` 直接 syntax error，**Analyze / Save / Refresh 全废**。
- **修复**：`git checkout d9ea00b -- web/index.html` 取完整版，再补 Scene Words 改名，提交 `eb7ff2f`。

### ③ CYD 真实 API 上不去：Wi-Fi 与 LVGL 抢内存

Mock UI 跑通后想切真实 API，遇到两组互斥 OOM：

- **顺序 A**（`init_display → connect_wifi`）：LVGL 先吃内存，Wi-Fi NVS 申请失败 → `OSError: WiFi Out of Memory`。
- **顺序 B**（`connect_wifi → init_display`）：Wi-Fi 先占 DMA 区，LVGL 拿不到 15KB **DMA-capable + 连续** 的 frame buffer → `MemoryError: Unable to allocate memory for frame buffer (15360)`。

用 `esp32.idf_heap_info(esp32.HEAP_DATA)` 查根因：

- 85KB 的 DMA 内部 SRAM 区被 Wi-Fi 占满（free = 4 字节）
- 113KB 区有 59KB 连续，但**不是 DMA-capable**
- 这块 CYD **没有 PSRAM**，搬不到 SPIRAM

试过的缓解全部失败：`gc.collect()`、预占 16KB 占位、`wlan.config(rxbuf=4096)`。彻底修需要重编 LVGL MicroPython 固件，hackathon 时间窗内来不及。

---

## 最终决定（演示话术）

> 「**CYD 留在 mock 模式演 UI**（Home / Insight / Dashboard 三页 LVGL 界面），**Web 端承担真实 NLP / 存储闭环**。两边架构完全相同，CYD 把 Wi-Fi 内存问题修好之后改 4 行配置（`API_BASE`、`WIFI_SSID`、`WIFI_PASSWORD`、`AUTO_CONNECT_WIFI=True`、`USE_MOCK_DATA=False`）就能切真实数据。」

---

## 当前演示流程（4 步）

1. Laptop 起后端：
   ```
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
2. 浏览器双击 `web/index.html`
3. Coffee Shop 文本 → **Analyze Text** → **Save Word/Phrase** → **Refresh Dashboard**，30 秒走完整闭环
4. CYD 上电自动跑 `:main.py`（mock 模式），屏幕展示 Scene Words Home + 三个可点击按钮（Real-world / Story / Dashboard），呈现产品形态

---

## 收尾（一句话）

> 「整体端到端跑通了，**真实数据闭环在 Web 端展示，CYD 展示完整 UI 形态**。CYD ↔ 后端的实时联动是受 ESP32 内存限制留作后续优化的，**不是架构问题**。」

---

## 关键 commit 速查

| Commit | 做了什么 |
| --- | --- |
| `a5bceb2` | 出问题的合并（误删 14 个 Line C 文件 + 留下 web 冲突标记） |
| `34aadc6` | Restore Line C files lost in merge a5bceb2 |
| `eb7ff2f` | Resolve unresolved merge conflict markers in web/index.html |
| `95aefdb` | Integrate three lines: rename to Scene Words, fix CYD WiFi OOM, document deployment |
| `6139757` | Lock CYD to mock mode; document Wi-Fi/LVGL memory conflict |
