import paho.mqtt.client as mqtt
import time

client_name = "pi400"
broker_name = "192.168.3.1"

def on_message(client, userdata, message):
    print("message received", str(message.payload.decode("utf-8")))
    print("message topic =", message.topic)
    print("message qos =", message.qos)
    print("message retain flag =", message.retain)

def on_log(client, userdata, level, buf):
    print("log: ",buf)

client = mqtt.Client(client_name)
client.on_message=on_message
client.on_log=on_log
client.connect(broker_name)

client.publish("house/light","ON")

client.loop_start() #start the loop
print("Subscribing to topic","house/bulbs/bulb1")
client.subscribe("birdboxes/birdbox1/battery_level")
print("Publishing message to topic","house/bulbs/bulb1")
client.publish("house/bulbs/bulb1","ON")
time.sleep(400) # wait
client.loop_stop() #stop the loop
