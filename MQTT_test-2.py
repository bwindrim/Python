import paho.mqtt.client as mqtt
import time

client_name = "pi400"
#broker_name = "192.168.3.1" # is the Mosquitto server only accessible over WireGuard?
#broker_name = "192.168.58.23" # is the Mosquitto server only accessible over WireGuard?
broker_name = "Pi2B" # is the Mosquitto server only accessible over WireGuard?(no)

def on_message(client, userdata, message):
    if message.retain:
        print(message.topic, "=", str(message.payload.decode("utf-8")), "(retained)")
    else:
        print(message.topic, "=", str(message.payload.decode("utf-8")), "(live)")
    #print("message qos =", message.qos, "retain flag =", message.retain)

def on_log(client, userdata, level, buf):
    #print("log: ",buf)
    return

client = mqtt.Client(client_name)
client.on_message=on_message
client.on_log=on_log
client.connect(broker_name)

#client.loop_start() # start the loop in a thread
client.subscribe("birdboxes/birdbox1/initial_status")
client.subscribe("birdboxes/birdbox1/initial_battery_level")
client.subscribe("birdboxes/birdbox1/initial_stay_up")
client.subscribe("birdboxes/birdbox1/startup_time")
client.subscribe("birdboxes/birdbox1/shutdown_time")
client.subscribe("birdboxes/birdbox1/wake_time")
client.subscribe("birdboxes/birdbox1/force_up")

client.subscribe("birdboxes/birdbox1/status")
client.subscribe("birdboxes/birdbox1/stay_up")
client.subscribe("birdboxes/birdbox1/battery_level")
#time.sleep(4000) # wait
#client.loop_stop() #stop the loop
client.loop_forever()
