import gc
import time
import os

from micropython import const
import machine
import network
import lvgl as lv
import lcd_bus
import ili9341
import xpt2046
import touch_cal_data
import task_handler


# ==================== API / Wi-Fi 配置 ====================
# C2 要求 API_BASE 放在文件顶部。CYD 访问 laptop 后端时不能使用 localhost。
API_BASE = "http://192.168.137.1:8000"

# 不要把真实 Wi-Fi 密码提交到 Git。联调时只在本地临时替换，或通过串口临时运行。
WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"

# CYD 内部 SRAM 不够同时驻留 Wi-Fi 驱动 + LVGL 帧缓冲（详见
# docs/INTEGRATION_RECORD.md 的"CYD Wi-Fi/LVGL 内存冲突"小节），所以默认
# 关闭自动联网；CYD 走 mock 演示 UI，真实 NLP/存储闭环由 Web 端承载。
AUTO_CONNECT_WIFI = False

# 与 AUTO_CONNECT_WIFI 配套：mock 模式下 init_display 能稳定拿到 DMA 帧缓冲，
# Home / Insight / Dashboard 三个页面用 MOCK_ANALYSIS / MOCK_DASHBOARD 渲染。
USE_MOCK_DATA = True

# ==================== C11 联调切换指南 ====================
# 切换到真实 API 只需修改以下 4 项（切勿把真实密码和 IP 提交到 Git）：
#
#   API_BASE         = "http://<laptop 局域网 IP>:8000"
#   WIFI_SSID        = "<Wi-Fi 名称>"
#   WIFI_PASSWORD    = "<Wi-Fi 密码>"
#   AUTO_CONNECT_WIFI = True
#   USE_MOCK_DATA    = False
#
# 后端启动命令（在 laptop 上执行）：
#   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
#
# 查找 laptop 局域网 IP：
#   Windows : ipconfig  -> 找 "IPv4 地址"
#   Mac/Linux: ifconfig -> 找 "inet "
#
# 联调顺序（C11 验收步骤）：
#   1. CYD 进入 Dashboard，点 Refresh -> 看到真实数据
#   2. Web 保存一个 word
#   3. CYD Refresh Dashboard -> 看到 Web 保存的 word
#   4. CYD 点击 keyword 保存 phrase
#   5. Web Refresh Dashboard -> 看到 CYD 保存的 phrase
#
# 遇到 API probe FAILED：
#   - 后端是否用 --host 0.0.0.0 启动
#   - CYD 和 laptop 是否同一 Wi-Fi
#   - API_BASE 是否是 laptop 局域网 IP（不是 localhost）
#   - Windows 防火墙是否拦截 8000 端口


# ==================== CYD 显示 / 触摸配置 ====================
# 这些引脚和方向参数沿用 C0 的 touch_color_test.py，避免改坏硬件初始化路径。
_DISPLAY_WIDTH = const(240)
_DISPLAY_HEIGHT = const(320)
_DISPLAY_ROT = const(0x20)
_DISPLAY_BGR = const(1)
_DISPLAY_RGB565_BYTE_SWAP = const(1)
_ALLOW_TOUCH_CAL = const(1)

_SPI_BUS_HOST = const(1)
_SPI_BUS_MOSI = const(13)
_SPI_BUS_MISO = const(12)
_SPI_BUS_SCK = const(14)
_INDEV_BUS_HOST = const(2)
_INDEV_BUS_MOSI = const(32)
_INDEV_BUS_MISO = const(39)
_INDEV_BUS_SCK = const(25)
_INDEV_DEVICE_FREQ = const(2000000)
_INDEV_DEVICE_CS = const(33)
_DISPLAY_BUS_FREQ = const(24000000)
_DISPLAY_BUS_DC = const(2)
_DISPLAY_BUS_CS = const(15)
_DISPLAY_BACKLIGHT_PIN = const(21)


# ==================== C12 小屏幕显示规则常量 ====================
# C12 要求：每屏最多 3-5 个主要元素，按钮要大，长文本优先截断。
# 所有截断和上限统一从这里读取，修改一处即影响所有页面，不需要逐页调整。
_C12_MAX_KW      = const(5)   # 每屏 keyword 上限（Insight View）
_C12_MAX_PH      = const(3)   # 每屏 phrase 上限（Insight View / Dashboard）
_C12_MAX_WORDS   = const(5)   # Dashboard saved_words 最多显示条数
_C12_KW_CHARS    = const(14)  # keyword 按钮文本截断长度（适配 108px 宽按钮）
_C12_PH_CHARS    = const(30)  # phrase 按钮文本截断长度（适配 210px 宽按钮）
_C12_SUM_CHARS   = const(48)  # summary 截断长度（最多 1 句）
_C12_LABEL_CHARS = const(40)  # Dashboard 普通标签文本截断长度


# ==================== Mock 数据 ====================
# C3 把 4 个 MVP context 的 mock 数据集中放在这里。
# UI 页面只调用 fetch_context() / fetch_dashboard()，后续换真实 API 时不需要重写页面。
MOCK_CONTEXTS = {
    "real-world": [
        {"id": "coffee_shop", "title": "Coffee Shop"},
        {"id": "doctor_pharmacy", "title": "Doctor / Pharmacy"},
    ],
    "story": [
        {"id": "kings_cross", "title": "King's Cross"},
        {"id": "baker_street", "title": "Baker Street"},
    ],
}

# 每个 context 都有自己的 Insight mock，确保点击 4 个入口都能看到合理内容。
MOCK_ANALYSES = {
    "coffee_shop": {
        "detected_context": {"id": "coffee_shop", "title": "Coffee Shop"},
        "keywords": ["latte", "milk", "size", "order", "receipt"],
        "phrases": ["Can I Get", "to go", "with milk"],
        "summary": "This looks like Coffee Shop. Focus on latte, milk, size.",
    },
    "doctor_pharmacy": {
        "detected_context": {"id": "doctor_pharmacy", "title": "Doctor / Pharmacy"},
        "keywords": ["doctor", "pain", "cough", "fever", "medicine"],
        "phrases": ["I have a", "twice a day", "make an appointment"],
        "summary": "This looks like Doctor / Pharmacy. Focus on symptoms and medicine.",
    },
    "kings_cross": {
        "detected_context": {"id": "kings_cross", "title": "King's Cross"},
        "keywords": ["train", "station", "platform", "ticket", "luggage"],
        "phrases": ["which platform", "catch the train", "lost my ticket"],
        "summary": "This looks like King's Cross. Focus on travel and station words.",
    },
    "baker_street": {
        "detected_context": {"id": "baker_street", "title": "Baker Street"},
        "keywords": ["detective", "clue", "case", "client", "mystery"],
        "phrases": ["tell me everything", "what happened", "look for clues"],
        "summary": "This looks like Baker Street. Focus on clues and detective questions.",
    },
}

MOCK_ANALYSIS = MOCK_ANALYSES["coffee_shop"]

MOCK_DASHBOARD = {
    "saved_words": [
        {"item_text": "latte"},
        {"item_text": "milk"},
        {"item_text": "platform"},
    ],
    "saved_phrases": [
        {"item_text": "Can I Get"},
        {"item_text": "which platform"},
    ],
    "top_context": "coffee_shop",
    "recent_keywords": ["latte", "milk", "order"],
    "review_today": 3,
}


# ==================== 全局 UI 状态 ====================
display = None
indev = None
lv_task_handler = None
screen_history = []
current_route = None
current_source_type = "real-world"
status_label = None


def connect_wifi(timeout_s=20):
    # C2 只提供 Wi-Fi 连接函数，不强制自动联网；网络失败时返回 None，UI 继续使用 mock。
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # CYD 内存紧张：Wi-Fi 默认 rxbuf 会吃掉很多连续堆，导致后面 LVGL 帧缓冲申请失败。
    # 调到 4KB 够 HTTP polling 用，给 LVGL 留够内存。失败/不支持就忽略。
    try:
        wlan.config(rxbuf=4096)
    except Exception:
        pass

    if wlan.isconnected():
        print_network_info(wlan)
        return wlan

    if WIFI_SSID == "CHANGE_ME" or WIFI_PASSWORD == "CHANGE_ME":
        print("Wi-Fi not configured; using mock data.")
        return None

    print("Connecting Wi-Fi:", WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    start = time.time()
    while not wlan.isconnected() and time.time() - start < timeout_s:
        print("Wi-Fi status:", wlan.status())
        time.sleep(1)

    if not wlan.isconnected():
        print("Wi-Fi failed:", wlan.status())
        return None

    print_network_info(wlan)
    return wlan


def print_network_info(wlan):
    # C1/C2 需要记录 CYD IP，并确认它和 laptop API 地址在同一网段。
    ip, mask, gateway, dns = wlan.ifconfig()
    print("CYD_IP:", ip)
    print("NETMASK:", mask)
    print("GATEWAY:", gateway)
    print("DNS:", dns)
    print("API_BASE:", API_BASE)


# ==================== C4 HTTP Helper ====================
# C4 要求所有 API 请求集中管理。UI 按钮和页面函数不直接 import requests，
# 只调用 fetch_contexts() / fetch_context() / fetch_dashboard() / save_item()。
def _build_url(path):
    # 统一拼接 URL，避免每个接口自己处理斜杠。
    if not path.startswith("/"):
        path = "/" + path
    return API_BASE + path


def _import_requests():
    # 不同 MicroPython 固件可能叫 requests 或 urequests，这里集中兼容。
    try:
        import requests
        return requests
    except ImportError:
        import urequests
        return urequests


def _post_json(requests, url, payload):
    # 部分 urequests 支持 json=，部分只支持 data=；这里统一兜底。
    try:
        return requests.post(url, json=payload)
    except TypeError:
        import ujson
        return requests.post(
            url,
            data=ujson.dumps(payload),
            headers={"Content-Type": "application/json"},
        )


def _json_from_response(response):
    # urequests / requests 的 json 支持不完全一致，所以这里集中处理。
    try:
        return response.json()
    except Exception:
        try:
            import ujson
            return ujson.loads(response.text)
        except Exception as exc:
            print("JSON parse failed:", exc)
            return None


def _request_json(method, path, payload=None):
    # 真正的 HTTP 请求只在这个函数里发生。
    # 失败时返回 None；上层 fetch_* 函数负责选择 mock fallback。
    if USE_MOCK_DATA:
        print("Mock %s:" % method, path, payload if payload else "")
        return None

    url = _build_url(path)
    response = None

    try:
        requests = _import_requests()

        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = _post_json(requests, url, payload or {})
        else:
            print("Unsupported HTTP method:", method)
            return None

        # CPython requests / MicroPython urequests 都常见 status_code 字段。
        status = getattr(response, "status_code", 200)
        if status >= 400:
            print(method, "failed:", path, status)
            return None

        return _json_from_response(response)
    except Exception as exc:
        print(method, "error:", path, exc)
        return None
    finally:
        # C4 验收要求请求结束后尽量关闭 response，避免 ESP32 内存泄漏。
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


def api_get(path):
    # C4 对外 GET helper。换后端 IP 时只改文件顶部 API_BASE。
    return _request_json("GET", path)


def api_post(path, payload):
    # C4 对外 POST helper。按钮回调不要直接发 HTTP，只调用 save_item()。
    if USE_MOCK_DATA:
        print("Mock POST:", path, payload)
        return {"saved": True, "mock": True}
    return _request_json("POST", path, payload)


def fetch_contexts():
    # C3 默认直接返回 mock；真实后端失败时也返回 mock，避免 CYD 黑屏或卡死。
    # C4 要求请求失败有 fallback，所以这里不把 None 继续传给 UI。
    if USE_MOCK_DATA:
        return MOCK_CONTEXTS

    data = api_get("/contexts")
    if data:
        return {
            "real-world": data.get("real_world", MOCK_CONTEXTS["real-world"]),
            "story": data.get("story", MOCK_CONTEXTS["story"]),
        }
    return MOCK_CONTEXTS


def fetch_context(context_id):
    # 后端 /context/{id} 返回 seed_keywords / seed_phrases；这里统一转成 Insight 可用字段。
    # API 失败时回退到对应 context 的 mock Insight。
    if USE_MOCK_DATA:
        return mock_context(context_id)

    data = api_get("/context/" + context_id)
    if data:
        return normalize_context(data)
    return mock_context(context_id)


def fetch_dashboard():
    # C3 默认直接返回 mock dashboard；Refresh 时也能立刻显示复习数据。
    # API 失败时回退到 mock dashboard，保证 Refresh 不会黑屏。
    if USE_MOCK_DATA:
        return MOCK_DASHBOARD

    data = api_get("/dashboard")
    return data if data else MOCK_DASHBOARD


def save_item(item_text, item_type, source_context):
    # C10 要求 payload 必须包含三个字段：
    #   item_text    — 保存的词或短语原文
    #   item_type    — 必须是 "word" 或 "phrase"，不能传错
    #   source_context — 当前 context 的 id（如 "coffee_shop"）
    payload = {
        "item_text": item_text,
        "item_type": item_type,
        "source_context": source_context,
    }

    result = api_post("/save_item", payload)
    # mock 模式下同步更新内存中的 MOCK_DASHBOARD，
    # 保证点击保存后立刻 Refresh Dashboard 能看到新条目。
    if USE_MOCK_DATA and result and result.get("saved"):
        add_mock_saved_item(item_text, item_type)
    return result


def mock_context(context_id):
    # 返回新的 dict，避免 UI 保存或改字段时污染全局 mock。
    source = MOCK_ANALYSES.get(context_id, MOCK_ANALYSIS)
    return {
        "detected_context": dict(source["detected_context"]),
        "keywords": list(source["keywords"]),
        "phrases": list(source["phrases"]),
        "summary": source["summary"],
    }


def add_mock_saved_item(item_text, item_type):
    # mock 模式下在内存中模拟后端保存行为：
    # word 插入 saved_words 列表头部，phrase 插入 saved_phrases 列表头部。
    # review_today 递增，保证 Dashboard 每次保存后统计数字有变化。
    # 注意：这只影响内存，重启设备后数据丢失（mock 不持久化）。
    if item_type == "word":
        MOCK_DASHBOARD["saved_words"].insert(0, {"item_text": item_text})
    elif item_type == "phrase":
        MOCK_DASHBOARD["saved_phrases"].insert(0, {"item_text": item_text})
    MOCK_DASHBOARD["review_today"] = MOCK_DASHBOARD.get("review_today", 0) + 1


def normalize_context(data):
    # C13：/context/{id} 返回字段可能用 keywords/phrases 或 seed_keywords/seed_phrases，
    # 这里统一做 fallback 转换，兼容线 A 两种命名方式，CYD UI 层无需关心。
    return {
        "detected_context": {
            "id": data.get("id", "coffee_shop"),
            "title": data.get("title", "Context"),
        },
        "keywords": data.get("keywords") or data.get("seed_keywords") or MOCK_ANALYSIS["keywords"],
        "phrases": data.get("phrases") or data.get("seed_phrases") or MOCK_ANALYSIS["phrases"],
        "summary": data.get("summary", MOCK_ANALYSIS["summary"]),
    }


# ==================== C13 API 契约 - 给线 A 的反馈 ====================
# 以下是 CYD 对各接口字段的最低要求，供线 A 后端参考。
# 线 C 不要求修改数据库结构，只反馈 CYD 显示层的字段依赖。
#
# ── GET /contexts ──────────────────────────────────────────────────────
#   期望格式：
#     {"real_world": [{"id": "coffee_shop", "title": "Coffee Shop"}, ...],
#      "story":      [{"id": "kings_cross",  "title": "King's Cross"}, ...]}
#   注意：CYD 内部将 real_world（下划线）映射为 real-world（连字符），线 A 无需改动。
#
# ── GET /context/{id} ──────────────────────────────────────────────────
#   接受以下任意一种格式（normalize_context() 统一处理两种命名）：
#     方案 A：{"id": "...", "title": "...", "keywords": [...], "phrases": [...], "summary": "..."}
#     方案 B：{"id": "...", "title": "...", "seed_keywords": [...], "seed_phrases": [...], "summary": "..."}
#   字段长度建议（超出 CYD 会按 C12 常量截断显示）：
#     keywords  每项建议 ≤ 14 字符（_C12_KW_CHARS），否则按钮文字截断
#     phrases   每项建议 ≤ 30 字符（_C12_PH_CHARS），否则按钮文字截断
#     summary   建议 1 句，CYD 只显示第一句前 48 字符（_C12_SUM_CHARS）
#
# ── GET /dashboard ─────────────────────────────────────────────────────
#   期望格式：
#     {"saved_words":  [{"item_text": "latte"}, ...],
#      "saved_phrases": [{"item_text": "Can I Get"}, ...],
#      "top_context":  "coffee_shop",
#      "review_today": 3}
#   注意：每个 item 的字段名必须是 item_text（完全匹配），CYD 不做字段别名处理。
#         top_context 为字符串 context id；review_today 为整数。
#
# ── POST /save_item ────────────────────────────────────────────────────
#   CYD 发送：
#     {"item_text": "latte", "item_type": "word", "source_context": "coffee_shop"}
#     item_type 只会是 "word" 或 "phrase"，不会传其他值。
#   期望返回：{"saved": true}
#   注意：saved 字段必须为布尔 true（不是字符串 "true"），
#         否则 CYD 判定失败并显示 "Save failed"。


# ==================== C14 Web-CYD 联调点 - 给线 B 的反馈 ====================
# 线 B 负责 Web 输入和 Web Dashboard。CYD 和 Web 共用同一套后端 API，
# 通过 GET /dashboard 读取、POST /save_item 写入来保持数据同步。
# 线 C 不修改 web/index.html，只列出需要线 B 帮忙验证的联调点。
#
# ── 共享数据模型 ────────────────────────────────────────────────────────
#   写入方：Web（用户在网页输入文本提交）和 CYD（用户点击 keyword / phrase 按钮）
#   读取方：Web Dashboard 和 CYD Dashboard View
#   数据流：
#     Web 保存 → POST /save_item → 后端存储
#                                       ↑ 共用
#     CYD 保存 → POST /save_item → 后端存储
#     GET /dashboard ← Web 读取（刷新页面）
#     GET /dashboard ← CYD 读取（点击 Refresh 按钮）
#
# ── 线 B 需要帮忙验证的联调点 ──────────────────────────────────────────
#   1. Web 保存一个 word 后，CYD 点 Refresh Dashboard 能看到该 word
#      → CYD 依赖 saved_words[].item_text 字段
#   2. CYD 点击 keyword 保存 word 后，Web 刷新 Dashboard 能看到该 word
#      → Web Dashboard 需要展示 saved_words[].item_text
#   3. CYD 点击 phrase 保存 phrase 后，Web 刷新 Dashboard 能看到该 phrase
#      → Web Dashboard 需要展示 saved_phrases[].item_text
#
# ── Web 页面字段适配 CYD 展示 ──────────────────────────────────────────
#   CYD 显示的 Dashboard 字段（均来自 GET /dashboard 响应）：
#     saved_words[].item_text   — 显示为 "Words: latte, milk"
#     saved_phrases[].item_text — 显示为 "Phrases: Can I Get"
#     top_context               — 显示为 "Top: coffee_shop"
#     review_today              — 显示为 "Review Today: 3"
#   CYD 当前不显示的字段（Web 可自由使用）：
#     recent_keywords、source_context、created_at 等
#
# ── 注意事项 ────────────────────────────────────────────────────────────
#   - Web 的 POST /save_item 请求也需要包含 source_context 字段，
#     否则后端无法记录来源 context，top_context 统计可能为空。
#   - CYD 不读取 Web 页面的任何 HTML / JS 状态，只通过 API 同步数据。
#   - 线 C 不修改 web/index.html。


def init_display():
    # 业务文件独立初始化屏幕和触摸，不依赖 touch_color_test.py。
    global display, indev, lv_task_handler

    if display is not None:
        return

    spi_bus = machine.SPI.Bus(
        host=_SPI_BUS_HOST,
        mosi=_SPI_BUS_MOSI,
        miso=_SPI_BUS_MISO,
        sck=_SPI_BUS_SCK,
    )
    indev_bus = machine.SPI.Bus(
        host=_INDEV_BUS_HOST,
        mosi=_INDEV_BUS_MOSI,
        miso=_INDEV_BUS_MISO,
        sck=_INDEV_BUS_SCK,
    )
    indev_device = machine.SPI.Device(
        spi_bus=indev_bus,
        freq=_INDEV_DEVICE_FREQ,
        cs=_INDEV_DEVICE_CS,
    )
    display_bus = lcd_bus.SPIBus(
        spi_bus=spi_bus,
        freq=_DISPLAY_BUS_FREQ,
        dc=_DISPLAY_BUS_DC,
        cs=_DISPLAY_BUS_CS,
    )

    display = ili9341.ILI9341(
        data_bus=display_bus,
        display_width=_DISPLAY_WIDTH,
        display_height=_DISPLAY_HEIGHT,
        backlight_pin=_DISPLAY_BACKLIGHT_PIN,
        backlight_on_state=ili9341.STATE_PWM,
        color_space=lv.COLOR_FORMAT.RGB565,
        color_byte_order=ili9341.BYTE_ORDER_BGR if _DISPLAY_BGR else ili9341.BYTE_ORDER_RGB,
        rgb565_byte_swap=_DISPLAY_RGB565_BYTE_SWAP,
    )
    display._ORIENTATION_TABLE = (_DISPLAY_ROT, 0x0, 0x0, 0x0)
    display.set_rotation(lv.DISPLAY_ROTATION._0)
    display.set_power(True)
    display.init(1)
    display.set_backlight(100)

    indev = xpt2046.XPT2046(device=indev_device)
    if not indev.is_calibrated and _ALLOW_TOUCH_CAL:
        indev.calibrate()
        indev._cal.save()

    lv_task_handler = task_handler.TaskHandler()


def set_common_screen(scr):
    # 小屏幕默认不滚动，页面内容控制在 3-5 个主要元素。
    scr.set_style_bg_color(lv.color_hex(0x101418), lv.PART.MAIN)
    scr.set_style_bg_opa(lv.OPA._100, lv.PART.MAIN)
    scr.remove_flag(lv.obj.FLAG.SCROLLABLE)


def add_title(parent, text):
    label = lv.label(parent)
    label.set_text(text)
    label.set_width(220)
    label.align(lv.ALIGN.TOP_MID, 0, 12)
    label.set_style_text_color(lv.color_white(), 0)
    label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
    return label


def add_label(parent, text, y, height=28):
    label = lv.label(parent)
    label.set_text(text)
    label.set_width(220)
    label.set_height(height)
    label.align(lv.ALIGN.TOP_MID, 0, y)
    label.set_style_text_color(lv.color_white(), 0)
    label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
    try:
        label.set_long_mode(lv.label.LONG.WRAP)
    except Exception:
        pass
    return label


def add_button(parent, text, y, cb, width=190, height=44, x_ofs=0):
    # 统一的大按钮，方便手指点击，也方便后续 C5-C10 复用。
    # x_ofs 支持水平偏移，C8 keyword 2 列布局使用 ±59px 偏移实现双列。
    btn = lv.button(parent)
    btn.set_size(width, height)
    btn.align(lv.ALIGN.TOP_MID, x_ofs, y)
    btn.set_style_bg_color(lv.color_hex(0x2F6FED), lv.PART.MAIN)
    btn.set_style_radius(6, lv.PART.MAIN)
    btn.remove_flag(lv.obj.FLAG.SCROLLABLE)
    btn.add_event_cb(lambda event: cb() if event.get_code() == lv.EVENT.CLICKED else None,
                     lv.EVENT.ALL, None)

    label = lv.label(btn)
    label.set_text(text)
    label.center()
    return btn


def set_status(text):
    global status_label
    if status_label is not None:
        status_label.set_text(text)


# ==================== C5 Screen Navigation ====================
# C5 要求四个页面之间可以来回切换，且每页都有明确的返回路径。
# 导航层只负责页面跳转和历史记录，不直接操作 LVGL 组件。
# 页面渲染交给 _render_* 系列函数，保持导航逻辑和 UI 逻辑分离。

def show_home():
    # 进入 Home 时清空历史栈，避免返回路径越积越深。
    global screen_history
    screen_history = []
    _set_route("home", None)
    _render_home()


def show_context_select(source_type):
    # source_type 决定显示 real-world 还是 story 的 context 列表。
    _set_route("context_select", source_type)
    _render_context_select(source_type)


def show_insight(data):
    # data 是 fetch_context() 返回的 Insight 数据，页面直接渲染，不再发 HTTP。
    _set_route("insight", data)
    _render_insight(data)


def show_dashboard():
    # Dashboard 每次渲染时都会调用 fetch_dashboard()，Refresh 按钮复用这个函数。
    _set_route("dashboard", None)
    _render_dashboard()


def go_to(route, arg=None):
    # 页面跳转时把当前路由压入历史栈，Back 按钮统一调用 go_back() 弹出。
    global current_route
    if current_route is not None:
        screen_history.append(current_route)
    _render_route(route, arg)


def go_back():
    # 历史栈非空则返回上一页；栈空时兜底回 Home，避免卡死在当前页。
    if screen_history:
        route, arg = screen_history.pop()
        _render_route(route, arg)
    else:
        show_home()


def _set_route(route, arg):
    # 更新全局当前路由，供 go_to() 压栈时读取。
    global current_route
    current_route = (route, arg)


def _render_route(route, arg=None):
    # 路由分发器：根据 route 字符串决定调用哪个渲染函数。
    # 未知路由时兜底回 Home，防止出现空白黑屏。
    _set_route(route, arg)
    if route == "home":
        _render_home()
    elif route == "context_select":
        _render_context_select(arg)
    elif route == "insight":
        _render_insight(arg)
    elif route == "dashboard":
        _render_dashboard()
    else:
        _render_home()


# ==================== C6 Home Screen ====================
# C6 要求：三个大按钮，文案不挤出屏幕，手指可以点中。
# 屏幕布局从上到下：标题 -> 副标题 -> Real-world -> Story -> Dashboard -> 状态行。

def _render_home():
    scr = lv.obj()
    set_common_screen(scr)

    # 主标题居中，字体沿用默认大字体，保证在小屏幕上清晰可读。
    add_title(scr, "Scene Words")

    # 副标题提示用户这是场景化英语学习工具，文字短小不占位。
    sub = add_label(scr, "Learn English in Context", 46, 22)
    sub.set_style_text_color(lv.color_hex(0x8899AA), 0)

    # 三个主按钮间距 56px，保证手指不会误点相邻按钮。
    # Real-world 进入真实场景的 Context Select。
    add_button(scr, "Real-world", 86, lambda: go_to("context_select", "real-world"))
    # Story 进入故事场景的 Context Select。
    add_button(scr, "Story", 146, lambda: go_to("context_select", "story"))
    # Dashboard 直接跳转到复习列表页面。
    add_button(scr, "Dashboard", 206, lambda: go_to("dashboard"))

    # 底部状态行：Mock 模式显示 "Mock"，真实 API 模式显示后端 IP，方便联调时确认。
    mode = "Mock" if USE_MOCK_DATA else "API " + API_BASE.replace("http://", "")
    add_label(scr, mode, 268, 28)

    lv.screen_load(scr)


# ==================== C7 Context Select Screen ====================
# C7 要求：显示 4 个 context 入口（real-world / story 各 2 个）。
# 点击任意 context 优先请求真实 API，失败时用 mock context 进入 Insight View。
# Back 按钮必须能回到 Home。

# source_type 到显示标题的映射，避免直接显示内部 key。
_SOURCE_TYPE_LABELS = {
    "real-world": "Real-world",
    "story": "Story",
}


def _render_context_select(source_type):
    global current_source_type
    current_source_type = source_type or "real-world"

    scr = lv.obj()
    set_common_screen(scr)

    # 标题显示当前场景类型（Real-world / Story），让用户明确知道在哪一层。
    type_label = _SOURCE_TYPE_LABELS.get(current_source_type, "Context")
    add_title(scr, type_label)

    # 副标题提示用户操作，字号小、颜色淡，不抢主按钮的视觉重心。
    sub = add_label(scr, "Select a context", 46, 22)
    sub.set_style_text_color(lv.color_hex(0x8899AA), 0)

    # 按 context 列表渲染按钮，最多显示 4 个，超出部分不显示（小屏幕限制）。
    # 按钮宽度 210px，高度 48px，间距 64px，手指易点中。
    contexts = fetch_contexts().get(current_source_type, [])
    y = 84
    for context in contexts[:4]:
        context_id = context.get("id", "coffee_shop")
        title = context.get("title", context_id)
        # 用默认参数捕获 context_id，避免 lambda 闭包陷阱。
        add_button(scr, title, y,
                   lambda context_id=context_id: open_context(context_id),
                   210, 48)
        y += 64

    # Back 按钮固定在屏幕底部，返回 Home（C5 的 go_back() 历史栈弹出）。
    add_button(scr, "Back", 270, go_back, 100, 38)
    lv.screen_load(scr)


def open_context(context_id):
    # 优先请求真实 API（fetch_context 内部处理失败 + mock fallback）。
    # 无论成功还是失败都能拿到 data，不会传 None 给 Insight View 导致黑屏。
    data = fetch_context(context_id)
    go_to("insight", data)


# ==================== C8 Insight View ====================
# C8 要求：context 标题 + 至少 5 个可点击 keyword（保存为 word）
#          + 至少 3 个可点击 phrase（保存为 phrase）+ summary + Back。
# keyword 采用 2 列布局（每列宽 108px，x 偏移 ±59px）节省纵向空间。
# phrase 采用全宽按钮（210px）保证长文本可读，截断到 30 字符防止撑破布局。
# summary 只取第一句最多 48 字符，避免占用过多纵向空间。

def _render_insight(data):
    global status_label
    data = data or MOCK_ANALYSIS
    context = data.get("detected_context", {})
    context_id = context.get("id", "coffee_shop")
    title = context.get("title", "Context")
    # C12 规则：keyword 最多 _C12_MAX_KW 个，超出部分不显示，防止超出屏幕高度。
    keywords = (data.get("keywords") or [])[:_C12_MAX_KW]
    # C12 规则：phrase 最多 _C12_MAX_PH 个。
    phrases = (data.get("phrases") or [])[:_C12_MAX_PH]
    summary = data.get("summary", "")

    scr = lv.obj()
    set_common_screen(scr)

    # 页面标题显示 context 名称（例如 "Coffee Shop"）。
    add_title(scr, title)

    # "Top Keywords" 区块标签，灰色小字，与按钮区分视觉层级。
    kw_hdr = add_label(scr, "Top Keywords", 36, 16)
    kw_hdr.set_style_text_color(lv.color_hex(0x8899AA), 0)

    # keyword 按钮 2 列排列：偶数索引左列（x=-59），奇数索引右列（x=+59）。
    # 每 2 个关键词占一行，行高 30px。
    # 用 lambda 默认参数捕获 kw，避免闭包陷阱（同 C7 context 按钮写法）。
    y_kw = 55
    for i, kw in enumerate(keywords):
        if i > 0 and i % 2 == 0:
            y_kw += 30
        x_ofs = -59 if i % 2 == 0 else 59
        # C12：keyword 文本截断到 _C12_KW_CHARS 字符，适配 108px 按钮宽度。
        add_button(scr, kw[:_C12_KW_CHARS], y_kw,
                   lambda kw=kw: handle_save(kw, "word", context_id),
                   108, 26, x_ofs)

    # "Useful Phrases" 区块标签。
    y_ph_hdr = y_kw + 30
    ph_hdr = add_label(scr, "Useful Phrases", y_ph_hdr, 16)
    ph_hdr.set_style_text_color(lv.color_hex(0x8899AA), 0)

    # phrase 按钮全宽（210px），截断到 30 字符防止长 phrase 撑破布局。
    # 用 lambda 默认参数捕获 ph，避免闭包陷阱。
    y_ph = y_ph_hdr + 18
    for ph in phrases:
        # C12：phrase 文本截断到 _C12_PH_CHARS 字符，防止长 phrase 撑破 210px 按钮。
        add_button(scr, ph[:_C12_PH_CHARS], y_ph,
                   lambda ph=ph: handle_save(ph, "phrase", context_id),
                   210, 26)
        y_ph += 28

    # C12：summary 只取第一句，截断到 _C12_SUM_CHARS 字符（最多 1 句）。
    summary_short = (summary.split(".")[0])[:_C12_SUM_CHARS] if summary else ""
    add_label(scr, summary_short, y_ph + 4, 16)

    # 状态行：显示保存结果，供 handle_save() 回写（Saved / Save failed 等）。
    status_label = add_label(scr, "", y_ph + 22, 14)

    # Back 按钮固定在状态行下方，返回 Context Select。
    add_button(scr, "Back", y_ph + 38, go_back, 90, 28)

    lv.screen_load(scr)


# ==================== C10 Save Interaction ====================
# C10 要求：点击 keyword 保存为 word，点击 phrase 保存为 phrase。
# item_type 必须正确传入（"word" / "phrase"），source_context 为当前 context id。
# 保存成功显示 "Saved: <item>"，保存失败显示 "Save failed"，页面不崩溃。
# 按钮回调 -> handle_save() -> save_item() -> api_post("/save_item", payload)。

def handle_save(item_text, item_type, source_context):
    # 空文本不发请求（例如 mock 数据中 keyword 列表为空时的防御）。
    if not item_text:
        set_status("Nothing to save")
        return

    # C10 核心：调用 save_item() 向后端发送 POST /save_item。
    # item_type 必须是 "word" 或 "phrase"，由调用方（按钮回调）保证传入正确值。
    result = save_item(item_text, item_type, source_context)

    if result and result.get("saved"):
        # 成功时显示保存的内容前 12 字符，方便用户确认点的是哪个词。
        set_status("Saved: " + item_text[:12])
    else:
        # 真实 API 失败时明确提示，但 Insight View 保持可用，不崩溃不跳页。
        set_status("Save failed")


# ==================== C11 API 联调辅助 ====================
# C11 在真实 API 模式下，启动时调用 probe_api() 快速验证后端可达。
# 结果只打印到串口（mpremote / Thonny REPL），不影响 UI 启动流程。

def probe_api():
    # 发一次 GET /dashboard 作为连通性探测。
    # 成功返回 True，失败返回 False；失败时打印排查提示，但不阻塞 UI。
    print("--> C11 probe:", API_BASE + "/dashboard")
    result = api_get("/dashboard")
    if result is not None:
        print("--> API probe OK")
        return True
    print("--> API probe FAILED. Check: API_BASE / Wi-Fi / firewall / --host 0.0.0.0")
    return False


# ==================== C9 Dashboard View ====================
# C9 要求：分区显示 Saved Words / Saved Phrases / Top Context / Review Today，
# 以及 Refresh（重新拉取 /dashboard）和 Back 按钮。
# Refresh 直接复用 _render_dashboard()，不需要额外封装。
# 网络失败时 fetch_dashboard() 自动 fallback 到 MOCK_DASHBOARD，页面不黑屏。

def _render_dashboard():
    global status_label

    # fetch_dashboard() 在网络失败时返回 MOCK_DASHBOARD，保证此处不为 None。
    data = fetch_dashboard()

    # C12 规则：saved words 最多显示 _C12_MAX_WORDS 个，小屏幕不宜过多。
    words = data.get("saved_words", [])[:_C12_MAX_WORDS]
    # C12 规则：saved phrases 最多显示 _C12_MAX_PH 个。
    phrases = data.get("saved_phrases", [])[:_C12_MAX_PH]
    top_context = str(data.get("top_context") or "-")
    review_today = str(data.get("review_today", 0))

    # 将列表转为逗号分隔文本，C12 规则截断到 _C12_LABEL_CHARS 字符防止换行过多。
    word_text = ", ".join(item.get("item_text", "") for item in words) or "None yet"
    phrase_text = ", ".join(item.get("item_text", "") for item in phrases) or "None yet"

    scr = lv.obj()
    set_common_screen(scr)

    # 页面标题。
    add_title(scr, "Dashboard")

    # Saved Words 区块：灰色小标题 + 内容标签（可换行，高 32px）。
    sw_hdr = add_label(scr, "Saved Words", 36, 16)
    sw_hdr.set_style_text_color(lv.color_hex(0x8899AA), 0)
    # C12：标签文本截断到 _C12_LABEL_CHARS 字符，防止换行挤占其他元素空间。
    add_label(scr, word_text[:_C12_LABEL_CHARS], 55, 32)

    # Saved Phrases 区块：灰色小标题 + 内容标签。
    sp_hdr = add_label(scr, "Saved Phrases", 92, 16)
    sp_hdr.set_style_text_color(lv.color_hex(0x8899AA), 0)
    add_label(scr, phrase_text[:_C12_LABEL_CHARS], 111, 32)

    # 统计信息：Top Context 和 Review Today。
    add_label(scr, "Top: " + top_context[:24], 148, 22)
    add_label(scr, "Review Today: " + review_today, 174, 22)

    # 数据来源状态行：mock 模式显示 "mock"，真实 API 显示 "live"。
    # 方便联调时快速确认 CYD 拿到的是 mock 还是真实数据。
    source = "mock" if USE_MOCK_DATA else "live"
    status_label = add_label(scr, source, 200, 16)
    status_label.set_style_text_color(lv.color_hex(0x8899AA), 0)

    # Refresh 和 Back 并排放在底部，节省纵向空间。
    # Refresh 左偏 x=-57，重新调用 _render_dashboard() 拉取最新 /dashboard 数据。
    add_button(scr, "Refresh", 222, lambda: _render_dashboard(), 106, 38, -57)
    # Back 右偏 x=+57，返回上一页（通常是 Home）。
    add_button(scr, "Back", 222, go_back, 90, 38, 57)

    lv.screen_load(scr)


def main():
    gc.collect()

    # Wi-Fi 必须先于 LVGL 初始化连接：LVGL 启动后会占用大量 DMA 区，
    # 之后再 init wifi 驱动会抛 "WiFi Out of Memory"。当前 CYD 内存
    # 实际不够同时跑 Wi-Fi + LVGL，所以默认 AUTO_CONNECT_WIFI=False；
    # 这里保留正确顺序，以便未来固件优化后能直接打开。
    if AUTO_CONNECT_WIFI:
        connect_wifi()

    init_display()

    # 真实 API 模式下启动时探测后端连通性，结果打印到串口方便排查。
    # mock 模式下跳过探测，保证离线也能正常启动。
    if not USE_MOCK_DATA:
        probe_api()

    show_home()

    # 启动诊断信息，方便联调时通过串口快速确认环境。
    print("--> Scene Words CYD dashboard ready.")
    print("--> MicroPython:", os.uname().release)
    print("--> LVGL: %s.%s" % (lv.version_major(), lv.version_minor()))
    print("--> API_BASE:", API_BASE)
    print("--> USE_MOCK_DATA:", USE_MOCK_DATA)
    print("--> AUTO_CONNECT_WIFI:", AUTO_CONNECT_WIFI)


main()
