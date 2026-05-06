# Task C15 记录 - CYD 配色升级：英格兰绿·乡村色系

日期：2026-05-05

## 目标

按照 `LINE_C_CONTENT_DEMO_QA_TASKS.md` 的 Task C15 要求，将 `lvgl9_firmwares/scenelingo_dashboard.py` 的硬编码颜色全部替换为语义化常量，使 CYD 屏幕配色与 `web/index.html` 的英格兰绿视觉体系保持一致。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 主要改动文件 | `lvgl9_firmwares/scenelingo_dashboard.py` |
| 新增记录文档 | `docs/TASK_C15_RECORD.md` |
| 是否修改后端 | 否 |
| 是否修改 Web | 否 |

---

## 改动详情

### 1. 新增 C15 配色常量块

在 `_C12_*` 常量块之后、Mock 数据之前追加：

```python
# ==================== C15 配色常量 - 英格兰绿·乡村色系 ====================
_COL_BG_HEX         = const(0x0e1a0a)  # 深森林绿背景（原深蓝黑 0x101418）
_COL_PRIMARY_HEX    = const(0x3a6624)  # 英格兰绿主按钮（nav / Back / Refresh）
_COL_PRIMARY_LT_HEX = const(0x4e8030)  # 稍浅绿（Insight View keyword 按钮）
_COL_ACCENT_HEX     = const(0xb8891a)  # 铜金（phrase 按钮 / 保存成功提示）
_COL_TEXT_HEX       = const(0xf0ead8)  # 暖象牙白主文字（原纯白）
_COL_MUTED_HEX      = const(0x7a9a6a)  # 灰绿色次要文字（副标题、区块标签）
_COL_DANGER_HEX     = const(0xcc3333)  # 深红（保存失败提示）
```

`const()` 存储 int，函数内再调 `lv.color_hex()` 转换，避免模块级调用 LVGL API（显示未初始化时报错）。

### 2. `set_common_screen()` — 背景色

```python
# 旧
scr.set_style_bg_color(lv.color_hex(0x101418), lv.PART.MAIN)
# 新
scr.set_style_bg_color(lv.color_hex(_COL_BG_HEX), lv.PART.MAIN)
```

背景从冷调深蓝黑改为深森林绿，CYD 深色屏幕下英格兰乡村感更强。

### 3. `add_title()` / `add_label()` — 主文字色

```python
# 旧
label.set_style_text_color(lv.color_white(), 0)
# 新
label.set_style_text_color(lv.color_hex(_COL_TEXT_HEX), 0)
```

纯白 → 暖象牙白（`#f0ead8`），与 Web 端 `--sw-text` 色调一致，减少深色背景下的视觉刺激。

### 4. `add_button()` — 新增 `bg_color` 参数

```python
# 旧签名
def add_button(parent, text, y, cb, width=190, height=44, x_ofs=0):
    btn.set_style_bg_color(lv.color_hex(0x2F6FED), lv.PART.MAIN)

# 新签名
def add_button(parent, text, y, cb, width=190, height=44, x_ofs=0, bg_color=None):
    btn.set_style_bg_color(lv.color_hex(bg_color if bg_color is not None else _COL_PRIMARY_HEX), lv.PART.MAIN)
```

不传 `bg_color` 时使用 `_COL_PRIMARY_HEX`（英格兰深绿），与旧 API 完全兼容，现有调用无需修改。

### 5. 全局替换次要文字色

共 6 处 `lv.color_hex(0x8899AA)` 全部换为 `lv.color_hex(_COL_MUTED_HEX)`：

| 位置 | 用途 |
| --- | --- |
| `_render_home()` 副标题 | "Learn English in Context" |
| `_render_insight()` Keywords 区块标题 | "Top Keywords" |
| `_render_insight()` Phrases 区块标题 | "Useful Phrases" |
| `_render_dashboard()` Saved Words 区块标题 | "Saved Words" |
| `_render_dashboard()` Saved Phrases 区块标题 | "Saved Phrases" |
| `_render_dashboard()` 数据来源状态行 | "mock" / "live" |

冷调蓝灰 → 灰绿色（`#7a9a6a`），与深森林绿背景搭配更协调。

### 6. `set_status()` — 新增 `color_hex` 参数

```python
# 旧
def set_status(text):
    if status_label is not None:
        status_label.set_text(text)

# 新
def set_status(text, color_hex=None):
    if status_label is not None:
        status_label.set_text(text)
        if color_hex is not None:
            status_label.set_style_text_color(lv.color_hex(color_hex), 0)
```

不传 `color_hex` 时行为不变，完全向后兼容。

### 7. `handle_save()` — 状态消息带颜色语义

```python
set_status("Nothing to save", _COL_MUTED_HEX)   # 灰绿：无操作
set_status("Saved: " + item_text[:12], _COL_ACCENT_HEX)  # 铜金：成功
set_status("Save failed", _COL_DANGER_HEX)        # 深红：失败
```

三种反馈通过颜色直觉传达结果，无需文字也能快速判断。

### 8. Insight View 按钮三色系

```python
# keyword 按钮 — 稍浅绿，与 nav 按钮区分层级
add_button(..., bg_color=_COL_PRIMARY_LT_HEX)

# phrase 按钮 — 铜金，视觉上暗示"更完整的表达"
add_button(..., bg_color=_COL_ACCENT_HEX)
```

| 按钮类型 | 颜色 | 十六进制 |
| --- | --- | --- |
| nav / Back / Refresh | 英格兰深绿 | `#3a6624` |
| keyword 按钮 | 稍浅绿 | `#4e8030` |
| phrase 按钮 | 铜金 | `#b8891a` |

---

## C15 验收结果

| 验收项 | 结果 |
| --- | --- |
| 模块级不调用 `lv.color_hex()`（常量为 int） | 通过 |
| 背景色为深森林绿（`#0e1a0a`） | 通过 |
| 主文字为暖象牙白（`#f0ead8`） | 通过 |
| 次要文字为灰绿色（`#7a9a6a`），共 6 处 | 通过 |
| nav/Back/Refresh 按钮为英格兰深绿（`#3a6624`） | 通过 |
| keyword 按钮为稍浅绿（`#4e8030`） | 通过 |
| phrase 按钮为铜金（`#b8891a`） | 通过 |
| 保存成功状态行铜金色 | 通过 |
| 保存失败状态行深红色 | 通过 |
| `add_button()` 不传 `bg_color` 时行为不变 | 通过（默认值 None → PRIMARY） |
| 文件中无硬编码颜色 hex（`0x101418`、`0x2F6FED`、`0x8899AA` 等） | 通过 |
