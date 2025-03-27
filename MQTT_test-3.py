import paho.mqtt.client as mqtt
import time

client_name = "pi400"
#broker_name = "192.168.3.1" # is the Mosquitto server only accessible over WireGuard?
#broker_name = "192.168.58.23" # is the Mosquitto server only accessible over WireGuard?
broker_name = "Pi2B" # is the Mosquitto server only accessible over WireGuard?(no)

bb_subscribe_list = [
"initial_status",
"initial_battery_level",
"initial_battery2_level",
"initial_stay_up",
"startup_time",
"shutdown_time",
"wake_time",
"force_up",
"message",
"status",
"stay_up",
"battery_level",
"battery2_level"
]

def on_message(client, userdata, message):
    print(message.topic, "=", str(message.payload.decode("utf-8")), end='')
    if message.retain:
        print(" (retained)")
    else:
        print("")

def on_log(client, userdata, level, buf):
    #print("log: ",buf)
    return

def list_subscribe(root, topic, subscribe_list):
    "Subscribe to a list of MQTT topics"
    for subtopic in subscribe_list:
        # print (i)
        client.subscribe(root + '/' + topic + '/' + subtopic)

client = mqtt.Client(client_name)
client.on_message=on_message
client.on_log=on_log
client.connect(broker_name)
client.subscribe("birdboxes/#")

#list_subscribe("birdboxes","birdbox1", bb_subscribe_list)
#list_subscribe("birdboxes","birdbox3", bb_subscribe_list)
# list_subscribe("birdboxes","testbed", bb_subscribe_list)

# client.publish("birdboxes/testbed/force_up", "1")

client.loop_forever()
