import serial
import time

def send_at_command(command=None, expected_response="OK", payload=None, timeout=2):
    if command:
        cmd_str = 'AT+' + command + '\r'
    else:
        cmd_str = 'AT'
    modem.write(cmd_str.encode())
    time.sleep(0.1)  # Small delay to allow modem to process
    
    start_time = time.time()

    if payload:
        # Wait for the '>' prompt before sending data
        # ToDo: add timeout
        while True:
            if modem.in_waiting > 0:
                response = modem.read(1)
                if b'>' == response:
                    modem.write(payload)
                    break
        
    response = b""
    
    while (time.time() - start_time) < timeout:
        if modem.in_waiting > 0:
            response += modem.read(modem.in_waiting)
            if expected_response in response.decode():
                return response.decode()
    
    return response.decode()

apn = "iot.1nce.net"
pdp_context = 1
ssl_version = 3 # 3 == TLS 1.2
auth_mode = 1 # 0 == no authentication
ssl_context = 1
client_index = 0
ignore_local_time = True
ca_cert = "isrgrootx1.pem"
use_ssl = True
username = "oisl_brian"
password = "Oisl2023"
topic = b"BWtest/topic"
message = b"Hi there, MQTT from SIMCom A7683E!"
retained = True
enable_SNI = True
qos = 1
timeout = 60
clean_session = True

with serial.Serial(port='/dev/ttyAMA0', baudrate=115200, timeout=1) as modem:
    # Initialize the modem
    print("Initializing modem...")
    print(send_at_command(f'CMEE=2'))  # Enable verbose error messages

    # Configure and activate PDP context
    print("Configuring PDP context...")
    print(send_at_command(f'CGDCONT=1,"IP","{apn}"'))  # Configure PDP context
    print(send_at_command(f'CGACT=1,{pdp_context}'))  # Activate PDP context

    # Verify IP address
    print("Checking IP address...")
    print(send_at_command(f'CGPADDR={pdp_context}'))

    # Configure TLS/SSL
    print("Configuring MQTT over TLS/SSL...")
    print(send_at_command(f'CSSLCFG="sslversion",{ssl_context},{ssl_version}')) # set SSL version to All
    print(send_at_command(f'CSSLCFG="authmode",{ssl_context},{auth_mode}')) # set authentication mode
    print(send_at_command(f'CSSLCFG="ignorelocaltime",{ssl_context},{int(ignore_local_time)}'))
    print(send_at_command(f'CSSLCFG="cacert",{ssl_context},"{ca_cert}"'))  # Use CA root certificate for HiveMQ
    print(send_at_command(f'CSSLCFG="enableSNI",{ssl_context},{int(enable_SNI)}'))

    # Start MQTT session
    print("Starting MQTT...")
    print(send_at_command(f'CMQTTSTART'))
    time.sleep(2)
    print(send_at_command(f'CMQTTACCQ={client_index},"BWtestClient0",{int(use_ssl)}'))
    print(send_at_command(f'CMQTTSSLCFG={client_index},{ssl_context}'))

    # Connect to MQTT broker
    print("Connecting to MQTT broker...")
    #print(send_at_command(f'CMQTTCONNECT={client_index},"tcp://broker.hivemq.com:8883",{timeout},{int(clean_session)}'))
    print(send_at_command(f'CMQTTCONNECT={client_index},"tcp://8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud:8883",{timeout},{int(clean_session)},"{username}","{password}"'))
    time.sleep(3)

    # Publish and be damned
    print(send_at_command(f'CMQTTTOPIC={client_index},{len(topic)}', payload=topic, timeout=1))  # Send topic
    print(send_at_command(f'CMQTTPAYLOAD={client_index},{len(message)}', payload=message, timeout=1))  # Send payload
    print(send_at_command(f'CMQTTPUB={client_index},{qos},{timeout},{int(retained)}'))  # Publish the message
    time.sleep(3)

    # Disconnect and stop MQTT
    print(send_at_command(f'CMQTTDISC={client_index}')) # disconnect from the broker
    print(send_at_command(f'CMQTTREL={client_index}'))  # release the client
    print(send_at_command(f'CMQTTSTOP'))

    # Deactivate PDP context
    print("Deactivating PDP context...")
    print(send_at_command(f'CGACT=0,{pdp_context}'))
