
﻿
import serial
import time

class SimComMQTT:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = serial.Serial(port, baudrate, timeout=timeout)
        self.mqtt_configured = False

    def send_command(self, command, expected_response="OK", timeout=5):
        """Send an AT command to the modem and wait for the expected response."""
        self.serial.write((command + "\r\n").encode())
        start_time = time.time()
        response = ""

        while time.time() - start_time < timeout:
            if self.serial.in_waiting:
                response += self.serial.read(self.serial.in_waiting).decode()
                if expected_response in response:
                    return response.strip()
        raise TimeoutError(f"Command '{command}' timed out. Response: {response}")

    def configure_mqtt(self, client_id, username, password, broker, port, keep_alive=60):
        """Configure the MQTT connection."""
        self.send_command("AT+CMQTTSTART", expected_response="OK")
        self.send_command(f"AT+CMQTTACCQ=0,\"{client_id}\"")
        self.send_command(f"AT+CMQTTWILL=0,0,0,\"\"")
        self.send_command(f"AT+CMQTTCONNECT=0,\"tcp://{broker}:{port}\",{keep_alive},1,\"{username}\",\"{password}\"")
        self.mqtt_configured = True

    def publish(self, topic, payload, qos=0, retain=False):
        """Publish a message to a topic."""
        if not self.mqtt_configured:
            raise RuntimeError("MQTT not configured. Call configure_mqtt() first.")
        retain_flag = 1 if retain else 0
        self.send_command(f"AT+CMQTTTOPIC=0,{len(topic)}")
        self.send_command(topic, expected_response=">")
        self.send_command(f"AT+CMQTTPAYLOAD=0,{len(payload)}")
        self.send_command(payload, expected_response=">")
        self.send_command(f"AT+CMQTTPUB=0,{qos},{retain_flag}")

    def subscribe(self, topic, qos=0):
        """Subscribe to a topic."""
        if not self.mqtt_configured:
            raise RuntimeError("MQTT not configured. Call configure_mqtt() first.")
        self.send_command(f"AT+CMQTTSUBTOPIC=0,{len(topic)},{qos}")
        self.send_command(topic, expected_response=">")
        self.send_command("AT+CMQTTSUB=0")

    def receive_message(self):
        """Check for incoming messages."""
        response = self.send_command("AT+CMQTTRECV=0,1024", timeout=10)
        if "+CMQTTRECV:" in response:
            _, data = response.split("\n", 1)
            return data.strip()
        return None

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if not self.mqtt_configured:
            raise RuntimeError("MQTT not configured.")
        self.send_command("AT+CMQTTDISC=0")
        self.send_command("AT+CMQTTSTOP")
        self.mqtt_configured = False

    def close(self):
        """Close the serial connection."""
        self.serial.close()


from simcom_mqtt import SimComMQTT

# Initialize the module
mqtt = SimComMQTT(port="/dev/ttyUSB0")

try:
    # Configure MQTT connection
    mqtt.configure_mqtt(
        client_id="test_client",
        username="user",
        password="pass",
        broker="broker.hivemq.com",
        port=1883
    )

    # Publish a message
    mqtt.publish(topic="test/topic", payload="Hello, MQTT!")

    # Subscribe to a topic
    mqtt.subscribe(topic="test/topic")

    # Check for messages
    message = mqtt.receive_message()
    if message:
        print("Received message:", message)

    # Disconnect
    mqtt.disconnect()

finally:
    mqtt.close()
