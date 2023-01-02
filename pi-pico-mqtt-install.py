import network
import mip
import time

# update with your Wi-Fi network's configuration
WIFI_SSID = "chittellas"
WIFI_PASSWORD = "Winner99$"

wlan = network.WLAN(network.STA_IF)

print(f"Connecting to Wi-Fi SSID: {WIFI_SSID}")

wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

while not wlan.isconnected():
    time.sleep(0.5)

print(f"Connected to Wi-Fi SSID: {WIFI_SSID}")

mip.install("https://raw.githubusercontent.com/micropython/micropython-lib/master/micropython/umqtt.simple/umqtt/simple.py")
