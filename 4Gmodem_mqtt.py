import serial
import time

# Initialize serial connection to the modem
modem = serial.Serial(
    port='/dev/ttyAMA0',  # Replace with the correct serial port
    baudrate=115200,
    timeout=1
)

def send_at_command(command, expected_response="OK", timeout=2):
    """
    Sends an AT command to the modem and waits for a response.
    """
    modem.write((command + '\r').encode())
    time.sleep(0.1)  # Small delay to allow modem to process
    start_time = time.time()
    response = b""
    
    while (time.time() - start_time) < timeout:
        if modem.in_waiting > 0:
            response += modem.read(modem.in_waiting)
            if expected_response in response.decode():
                return response.decode()
    
    return response.decode()

# Step 1: Initialize the modem
print("Initializing modem...")
print(send_at_command("AT"))
print(send_at_command("AT+CMEE=2"))  # Enable verbose error messages

# Step 2: Configure MQTT settings
print("Configuring MQTT...")
print(send_at_command('AT+CMQTTSTART'))  # Start MQTT service
time.sleep(2)  # Allow the service to initialize

# Set MQTT client ID
print(send_at_command('AT+CMQTTACCQ=0,"myClientID"'))

# Set the MQTT server address and port
print(send_at_command('AT+CMQTTCONNECT=0,"tcp://8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud:8883",60'))

# Optional: Set username and password
# Uncomment the following if the broker requires authentication
# username = "your_username"
# password = "your_password"
# print(send_at_command(f'AT+CMQTTAUTH=0,"{username}","{password}"'))

# Step 3: Publish a message
topic = "test/topic"
message = "Hello, MQTT from SIMCom A7600!"
print(send_at_command(f'AT+CMQTTTOPIC=0,{len(topic)}'))
print(send_at_command(topic, timeout=1))  # Send topic
print(send_at_command(f'AT+CMQTTPAYLOAD=0,{len(message)}'))
print(send_at_command(message, timeout=1))  # Send payload
print(send_at_command('AT+CMQTTPUB=0,1,60'))  # Publish the message

# Step 4: Subscribe to a topic
# print(send_at_command(f'AT+CMQTTSUBTOPIC=0,{len(topic)},1'))
# print(send_at_command(topic, timeout=1))  # Send topic
# print(send_at_command('AT+CMQTTSUB=0'))

# Step 5: Disconnect from the broker and stop MQTT service
print(send_at_command('AT+CMQTTDISC=0,60'))  # Disconnect from the broker
print(send_at_command('AT+CMQTTSTOP'))       # Stop MQTT service

# Close the serial connection
modem.close()
