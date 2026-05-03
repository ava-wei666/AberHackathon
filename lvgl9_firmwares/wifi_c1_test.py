import network
import time


# C1 config.
# Do not use eduroam here; use a normal WPA2 hotspot/Wi-Fi.
WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"

# Windows Mobile Hotspot usually gives the laptop this address.
LAPTOP_IP = "192.168.137.1"
API_BASE = "http://%s:8000" % LAPTOP_IP


def connect_wifi(timeout_s=25):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("Already connected")
        print_network_info(wlan)
        return wlan

    print("Connecting to Wi-Fi:", WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    start = time.time()
    while not wlan.isconnected() and time.time() - start < timeout_s:
        print("status:", wlan.status())
        time.sleep(1)

    if not wlan.isconnected():
        print("Wi-Fi failed")
        print("status:", wlan.status())
        return None

    print("Wi-Fi connected")
    print_network_info(wlan)
    return wlan


def print_network_info(wlan):
    ip, mask, gateway, dns = wlan.ifconfig()
    print("CYD_IP:", ip)
    print("NETMASK:", mask)
    print("GATEWAY:", gateway)
    print("DNS:", dns)
    print("API_BASE:", API_BASE)

    if ip.startswith("192.168.137.") and LAPTOP_IP == "192.168.137.1":
        print("Same hotspot subnet: OK")
    elif ip.split(".")[:3] == LAPTOP_IP.split(".")[:3]:
        print("Same /24 subnet: OK")
    else:
        print("Subnet check: verify laptop and CYD are on the same network")


connect_wifi()
