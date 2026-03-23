import json
import os
import signal
import sys
import time

import adafruit_dht
import board
import paho.mqtt.client as mqtt

# ── Load config ────────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

if not os.path.exists(CONFIG_PATH):
    print("ERROR: config.json not found. Copy config.example.json to config.json and fill in your settings.")
    sys.exit(1)

with open(CONFIG_PATH) as f:
    config = json.load(f)

MQTT_HOST = config["mqtt_host"]
MQTT_PORT = config["mqtt_port"]
MQTT_USER = config["mqtt_user"]
MQTT_PASS = config["mqtt_pass"]
DHT_PIN = getattr(board, f"D{config['gpio_pin']}")
READ_INTERVAL = config["read_interval"]
DEVICE_ID = config["device_id"]
DEVICE_NAME = config["device_name"]

# ── MQTT topics ────────────────────────────────────────────────
TOPIC_PREFIX = f"homeassistant/sensor/{DEVICE_ID}"
STATE_TOPIC = f"{TOPIC_PREFIX}/state"

DISCOVERY = [
    {
        "topic": f"{TOPIC_PREFIX}_temperature/config",
        "payload": {
            "name": "Temperature",
            "device_class": "temperature",
            "unit_of_measurement": "\u00b0C",
            "value_template": "{{ value_json.temperature }}",
            "state_topic": STATE_TOPIC,
            "unique_id": f"{DEVICE_ID}_temperature",
            "device": {
                "identifiers": [DEVICE_ID],
                "name": DEVICE_NAME,
                "manufacturer": "DIY",
                "model": "Pi Zero 2W + DHT11",
            },
        },
    },
    {
        "topic": f"{TOPIC_PREFIX}_humidity/config",
        "payload": {
            "name": "Humidity",
            "device_class": "humidity",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.humidity }}",
            "state_topic": STATE_TOPIC,
            "unique_id": f"{DEVICE_ID}_humidity",
            "device": {
                "identifiers": [DEVICE_ID],
                "name": DEVICE_NAME,
                "manufacturer": "DIY",
                "model": "Pi Zero 2W + DHT11",
            },
        },
    },
]


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT broker")
        publish_discovery(client)
    else:
        print(f"MQTT connection failed: {rc}")


def publish_discovery(client):
    for item in DISCOVERY:
        client.publish(
            item["topic"],
            json.dumps(item["payload"]),
            retain=True,
        )
    print("Published HA discovery config")


def main():
    dht = adafruit_dht.DHT11(DHT_PIN)

    client = mqtt.Client(
        client_id=DEVICE_ID,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect

    def shutdown(sig, frame):
        print("\nShutting down...")
        dht.exit()
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    consecutive_errors = 0

    while True:
        try:
            temperature = dht.temperature
            humidity = dht.humidity

            if temperature is not None and humidity is not None:
                payload = json.dumps({
                    "temperature": round(temperature, 1),
                    "humidity": round(humidity, 1),
                })
                client.publish(STATE_TOPIC, payload)
                print(f"Published: {payload}")
                consecutive_errors = 0
            else:
                print("Sensor returned None, skipping")

        except RuntimeError as e:
            consecutive_errors += 1
            print(f"Read error ({consecutive_errors}): {e}")
            if consecutive_errors >= 10:
                print("Too many consecutive errors, reinitializing sensor")
                dht.exit()
                time.sleep(2)
                dht = adafruit_dht.DHT11(DHT_PIN)
                consecutive_errors = 0

        time.sleep(READ_INTERVAL)


if __name__ == "__main__":
    main()
