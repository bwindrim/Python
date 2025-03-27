import paho.mqtt.client as mqtt
import time

client_name = "pi5"
broker_name = "Pi2B" # is the Mosquitto server only accessible over WireGuard?(no)

def on_message(client, userdata, message):
    print(message.topic, "=", message.payload.decode("utf-8"), end='')
    if message.retain:
        print(" (retained)")
    else:
        print("")

def on_log(client, userdata, level, buf):
    return

client = mqtt.Client(client_name)
client.on_message=on_message
client.on_log=on_log
client.connect(broker_name)
client.subscribe("birdboxes/#")

client.loop_forever()
