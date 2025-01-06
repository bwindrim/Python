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

apn = "iot.1nce.net"
pdp_context = 1
ssl_version = 4
ssl_context = 0
client_index = 0

# Step 1: Initialize the modem
print("Initializing modem...")
print(send_at_command(f'AT'))
print(send_at_command(f'AT+CMEE=2'))  # Enable verbose error messages

# Step 2: Check SIM and network status
print("Checking SIM and network status...")
print(send_at_command(f'AT+CPIN?'))  # Check SIM status
print(send_at_command(f'AT+CREG?'))  # Check network registration
print(send_at_command(f'AT+CGREG?'))  # Check network registration status

# Step 3: Configure and activate PDP context
print("Configuring PDP context...")
print(send_at_command(f'AT+CGDCONT=1,"IP","{apn}"'))  # Configure PDP context
print(send_at_command(f'AT+CGACT=1,{pdp_context}'))  # Activate PDP context

# Verify IP address
print("Checking IP address...")
print(send_at_command(f'AT+CGPADDR={pdp_context}'))

# Step 4: Start MQTT session
print("Starting MQTT...")
print(send_at_command(f'AT+CMQTTSTART'))  # Start MQTT service
time.sleep(2)  # Allow the service to initialize

# Step 5: Configure MQTT over TLS/SSL
print("Configuring MQTT over TLS/SSL...")
print(send_at_command(f'AT+CSSLCFG="sslversion",{ssl_context}, {ssl_version}')) # set SSL version to All
print(send_at_command(f'AT+CSSLCFG="authmode",{ssl_context}, 1')) # set authentication mode to server only
print(send_at_command(f'AT+CSSLCFG="cacert", {ssl_context}, "isrgrootx1.pem"'))  # Use CA root certificate for HiveMQ
print(send_at_command(f'AT+CMQTTACCQ={client_index},"testClient0",1'))  # Set MQTT client ID, enable SSL by setting third parameter to 1
print(send_at_command(f'AT+CMQTTSSLCFG={client_index},{ssl_context}'))


# Step 6: Connect to MQTT broker
print("Connecting to MQTT broker...")
print(send_at_command(f'AT+CMQTTCONNECT={client_index},"tcp://8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud:8883",60,1'))

# Optional: Set username and password
# Uncomment the following if the broker requires authentication
# username = "your_username"
# password = "your_password"
# print(send_at_command(f'AT+CMQTTAUTH=0,"{username}","{password}"'))

# # Step 7: Publish a message
# topic = "test/topic"
# message = "Hello, MQTT from SIMCom A7600!"
# print(send_at_command(f'AT+CMQTTTOPIC=0,{len(topic)}'))
# print(send_at_command(topic, timeout=1))  # Send topic
# print(send_at_command(f'AT+CMQTTPAYLOAD=0,{len(message)}'))
# print(send_at_command(message, timeout=1))  # Send payload
# print(send_at_command(f'AT+CMQTTPUB=0,1,60'))  # Publish the message

# Step 6: Disconnect and stop MQTT
print(send_at_command(f'AT+CMQTTDISC={client_index}')) # Disconnect from the broker
print(send_at_command(f'AT+CMQTTREL={client_index}'))  # Disconnect from the broker
print(send_at_command(f'AT+CMQTTSTOP'))   # Stop MQTT service

# Step 7: Deactivate PDP context (optional)
print("Deactivating PDP context...")
print(send_at_command(f'AT+CGACT=0,{pdp_context}'))

# Close the serial connection
modem.close()
