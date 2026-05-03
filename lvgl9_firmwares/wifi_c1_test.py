import network
import time


# 这个文件只用于 Task C1 的网络连通性验证。
# 它不负责 SceneLingo 业务页面，也不请求后端 API；
# 这里只确认 CYD 能连上热点，并打印后续 API 联调需要的网络字段。

# C1 配置区。
# 这里不要填写 eduroam，因为 eduroam 是 WPA2-Enterprise，
# 当前 CYD MicroPython 固件没有暴露企业网 EAP 配置参数。
# 推荐使用 Windows Mobile Hotspot、手机热点，或学校提供的普通 WPA2 IoT 网络。
# 提交代码前保持 CHANGE_ME，占位符不要替换成真实 Wi-Fi 密码。
WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"

# Windows Mobile Hotspot 通常会把 laptop 的热点侧地址设为 192.168.137.1。
# CYD 后续访问 FastAPI 后端时，不能使用 localhost，需要使用这个局域网 IP。
LAPTOP_IP = "192.168.137.1"
API_BASE = "http://%s:8000" % LAPTOP_IP


def connect_wifi(timeout_s=25):
    # STA_IF 表示让 ESP32 作为 Wi-Fi 客户端连接到热点。
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # 如果板子已经连接到 Wi-Fi，就直接打印当前网络信息，避免重复连接。
    if wlan.isconnected():
        print("Already connected")
        print_network_info(wlan)
        return wlan

    print("Connecting to Wi-Fi:", WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    # MicroPython 在连接过程中会返回数字状态码。
    # 常见结果：1010 表示已连接；负数或长时间不变通常表示连接失败或认证失败。
    start = time.time()
    while not wlan.isconnected() and time.time() - start < timeout_s:
        print("status:", wlan.status())
        time.sleep(1)

    # 连接失败时只打印状态并返回 None，避免网络问题导致 CYD 业务程序崩溃。
    if not wlan.isconnected():
        print("Wi-Fi failed")
        print("status:", wlan.status())
        return None

    print("Wi-Fi connected")
    print_network_info(wlan)
    return wlan


def print_network_info(wlan):
    # ifconfig 返回：IP、子网掩码、网关、DNS。
    # C1 主要记录 CYD_IP，并确认它和 LAPTOP_IP 在同一个局域网网段。
    ip, mask, gateway, dns = wlan.ifconfig()
    print("CYD_IP:", ip)
    print("NETMASK:", mask)
    print("GATEWAY:", gateway)
    print("DNS:", dns)
    print("API_BASE:", API_BASE)

    # Windows Mobile Hotspot 的典型网段是 192.168.137.x。
    # 如果 CYD 也拿到 192.168.137.x，说明它可以尝试访问 laptop 的后端。
    if ip.startswith("192.168.137.") and LAPTOP_IP == "192.168.137.1":
        print("Same hotspot subnet: OK")
    elif ip.split(".")[:3] == LAPTOP_IP.split(".")[:3]:
        print("Same /24 subnet: OK")
    else:
        print("Subnet check: verify laptop and CYD are on the same network")


# 直接运行本文件时，立即执行 C1 Wi-Fi 连通性测试。
connect_wifi()
