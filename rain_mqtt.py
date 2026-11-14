"""Check in with Chatty over MQTT (the node network).

Every minute this posts a heartbeat, and it posts the latest rain numbers
whenever the bucket tips (checked every 10 seconds) and with each heartbeat:

    chatty/nodes/rain/status   {"state": "online", "every": 60, "ts": ..., "title": "Rain node"}
    chatty/nodes/rain/data     {"rain_in": ..., "rain_mm": ..., "rate_mm_hr": ..., "tip_count": ...}

Both are "retained", so anything that connects later (Chatty after a
restart, the word clock) gets the latest right away. If this Pi drops off
WiFi or loses power, the broker posts {"state": "offline"} for it (the
"last will"), and Chatty shows "Rain node went quiet".

Finding Chatty: broker_link.py tries her home address, chatty-node.local
and her Tailscale address, learns which WiFi she's on from her `chatty/hub`
note, and follows her when she moves (see broker_link.py). The heartbeat says
how it reached her ("via": "lan" or "tailscale").

Settings (environment, e.g. in /etc/rain-node.env):
    MQTT_HOST   broker address (default chatty-node.local, Chatty's Pi)
    MQTT_PORT   default 1883
    NODE_NAME   default "rain"
    MQTT_HOSTS, MQTT_TAILSCALE, MQTT_SCAN: see broker_link.py

Needs: sudo apt install python3-paho-mqtt
"""
import json
import os
import socket
import time

import paho.mqtt.client as mqtt

import broker_link
import sd_notify
from rain_common import latest

PORT = int(os.getenv("MQTT_PORT", "1883"))
NAME = os.getenv("NODE_NAME", "rain")
EVERY = 60    # heartbeat, seconds
POLL = 10     # how often to look for new tips, seconds

STATUS = f"chatty/nodes/{NAME}/status"
DATA = f"chatty/nodes/{NAME}/data"


link = None


def status(state="online"):
    body = {"state": state, "every": EVERY, "ts": int(time.time()),
            "title": "Rain node", "host": socket.gethostname()}
    if link is not None:
        body.update(link.info())
    return json.dumps(body)


connected = False


def on_connect(client, userdata, flags, *rest):
    global connected
    connected = True
    client.publish(STATUS, status(), qos=1, retain=True)
    try:
        reading = latest()
        if reading:
            client.publish(DATA, json.dumps(reading), qos=1, retain=True)
    except Exception as e:
        print("Couldn't read the rain log:", repr(e), flush=True)


def on_disconnect(*args):
    global connected
    if connected:
        print("Lost the broker, retrying", flush=True)
    connected = False


def make_client():
    cid = f"{NAME}-{socket.gethostname()}"
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cid)
    except AttributeError:  # paho-mqtt 1.x
        client = mqtt.Client(client_id=cid)
    client.will_set(STATUS, json.dumps({"state": "offline"}), qos=1, retain=True)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    return client


def main():
    global link
    client = make_client()
    link = broker_link.BrokerLink(client, port=PORT, keepalive=60)
    link.start()
    sd_notify.ready()
    last_beat = 0.0
    last_tips = None
    while True:
        sd_notify.watchdog()
        now = time.monotonic()
        try:
            reading = latest()
        except Exception as e:
            print("Couldn't read the rain log:", repr(e), flush=True)
            reading = {}
        tips = reading.get("tip_count")
        beat = now - last_beat >= EVERY
        if connected and (beat or tips != last_tips):
            if beat:
                client.publish(STATUS, status(), qos=1, retain=True)
                last_beat = now
            if reading:
                client.publish(DATA, json.dumps(reading), qos=1, retain=True)
            last_tips = tips
        time.sleep(POLL)


if __name__ == "__main__":
    main()
