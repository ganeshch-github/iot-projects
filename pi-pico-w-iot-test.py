# module imports
import machine
import network
import ssl
import time
import ubinascii
import ujson
from machine import Pin, Timer
import ntptime
from simple import MQTTClient

#Path to settings file
PICO_SETTINGS = 'pi-pico-settings.json'

# Initializing pico

def initialize_pi(settings):
    global WIFI_SSID, WIFI_PASSWORD
    global MQTT_CLIENT_KEY, MQTT_CLIENT_CERT, MQTT_BROKER, MQTT_BROKER_CA, MQTT_CLIENT_ID 
    global MQTT_LED_TOPIC, MQTT_BUTTON_TOPIC

    f = open(settings, "r")
    pico_settings = ujson.load(f)
    
    
    # WIFI Settings
    WIFI_SSID = pico_settings['WIFI_SSID']
    WIFI_PASSWORD = pico_settings['WIFI_PASSWORD']
    # MQTT client and broker constants
    MQTT_CLIENT_KEY = pico_settings['MQTT_CLIENT_KEY']
    MQTT_CLIENT_CERT = pico_settings['MQTT_CLIENT_CERT']
    MQTT_BROKER = pico_settings['MQTT_BROKER']
    MQTT_BROKER_CA = pico_settings['MQTT_BROKER_CA']
    MQTT_CLIENT_ID = ubinascii.hexlify(machine.unique_id())
    # MQTT topic constants
    MQTT_LED_TOPIC = "picow/led"
    MQTT_BUTTON_TOPIC = "picow/button"
    
    


# function that reads PEM file and return byte array of data
def read_pem(file):
    with open(file, "r") as input:
        text = input.read().strip()
        split_text = text.split("\n")
        base64_text = "".join(split_text[1:-1])

        return ubinascii.a2b_base64(base64_text)


# callback function to handle received MQTT messages
def on_mqtt_msg(topic, msg):
    # convert topic and message from bytes to string
    topic_str = topic.decode()
    decoded_msg = ujson.loads(msg.decode())
    msg_str = decoded_msg["message"]
    
    print(f"RX: {topic_str}\n\t{msg_str}")

    # process message
    if topic_str is MQTT_LED_TOPIC:
        if msg_str is "on":
            led.on()
        elif msg_str is "off":
            led.off()
        elif msg_str is "toggle":
            led.toggle()


# callback function to handle changes in button state
# publishes "released" or "pressed" message
def publish_mqtt_button_msg(t):
    topic_str = MQTT_BUTTON_TOPIC
    msg_str = "released" if button.value() else "pressed"

    print(f"TX: {topic_str}\n\t{msg_str}")
    mqtt_client.publish(topic_str, msg_str)


# callback function to periodically send MQTT ping messages
# to the MQTT broker
def send_mqtt_ping(t):
    print("TX: ping")
    mqtt_client.ping()


def connect_to_wlan():
    wlan = network.WLAN(network.STA_IF)
    print(f"Connecting to Wi-Fi SSID: {WIFI_SSID}")
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    while not wlan.isconnected():
        time.sleep(0.5)

    print(f"Connected to Wi-Fi SSID: {WIFI_SSID}")
    # update the current time on the board using NTP
    ntptime.settime()


def connect_to_mqtt():
    # read the data in the private key, public certificate, and
    # root CA files
    global mqtt_client, mqtt_ping_timer
    print (f"MQTT_CLIENT_KEY {MQTT_CLIENT_KEY}")
    key = read_pem(MQTT_CLIENT_KEY)
    cert = read_pem(MQTT_CLIENT_CERT)
    ca = read_pem(MQTT_BROKER_CA)
    mqtt_client = MQTTClient(
        MQTT_CLIENT_ID,
        MQTT_BROKER,
        keepalive=60,
        ssl=True,
        ssl_params={
            "key": key,
            "cert": cert,
            "server_hostname": MQTT_BROKER,
            "cert_reqs": ssl.CERT_REQUIRED,
            "cadata": ca,
        },
    )
    
    print(f"Connecting to MQTT broker: {MQTT_BROKER}")
    mqtt_client.set_callback(on_mqtt_msg)
    mqtt_client.connect()
    mqtt_client.subscribe(MQTT_LED_TOPIC)

    print(f"Connected to MQTT broker: {MQTT_BROKER}")

    # create timer for periodic MQTT ping messages for keep-alive
    mqtt_ping_timer = Timer(
        mode=Timer.PERIODIC, period=mqtt_client.keepalive * 1000, callback=send_mqtt_ping
    )

    # main loop, continuously check for incoming MQTT messages
    while True:
        mqtt_client.check_msg()




# read the data in the private key, public certificate, and
# root CA files

# create pin objects for on-board LED and external button
led = Pin("LED", Pin.OUT)
button = Pin(3, Pin.IN, Pin.PULL_UP)

# register callback function to handle changes in button state
button.irq(publish_mqtt_button_msg, Pin.IRQ_FALLING | Pin.IRQ_RISING)

# turn on-board LED on
led.on()

initialize_pi(PICO_SETTINGS)
connect_to_wlan()
connect_to_mqtt()
