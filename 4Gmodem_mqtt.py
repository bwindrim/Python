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

def set_verbosity(level):
    print(send_at_command(f'CMEE={level}'))  # Enable verbose error messages

def pdp_open(apn):
    context_num = 1
    print(send_at_command(f'CGDCONT=1,"IP","{apn}"'))  # Configure PDP context
    print(send_at_command(f'CGACT=1,{context_num}'))  # Activate PDP context
    return context_num

def pdp_close(context_num):
    print(send_at_command(f'CGACT=0,{context_num}'))

def ssl_config(ca_cert, ssl_version = 4, auth_mode = 0, ignore_local_time = True, enable_SNI = False):
    ssl_context = 1
    print(send_at_command(f'CSSLCFG="sslversion",{ssl_context},{ssl_version}')) # set SSL version to All
    print(send_at_command(f'CSSLCFG="authmode",{ssl_context},{auth_mode}')) # set authentication mode
    print(send_at_command(f'CSSLCFG="ignorelocaltime",{ssl_context},{int(ignore_local_time)}'))
    print(send_at_command(f'CSSLCFG="cacert",{ssl_context},"{ca_cert}"'))  # Use CA root certificate for HiveMQ
    print(send_at_command(f'CSSLCFG="enableSNI",{ssl_context},{int(enable_SNI)}'))
    return ssl_context

def mqtt_session_start():
    print(send_at_command(f'CMQTTSTART'))
    time.sleep(2)

def mqtt_session_stop():
    print(send_at_command(f'CMQTTSTOP'))

def mqtt_client_open(client_id, ssl_context = None):
    client_index = 0
    use_ssl =  (ssl_context != None)
    print(send_at_command(f'CMQTTACCQ={client_index},"{client_id}",{int(use_ssl)}'))
    if use_ssl:
        print(send_at_command(f'CMQTTSSLCFG={client_index},{ssl_context}'))
    return client_index

def mqtt_client_close(client):
    print(send_at_command(f'CMQTTREL={client}'))  # release the client

def mqtt_client_connect(client, url, port = 1883, timeout = 60, clean_session = True, username = None, password = None):
    if username:
        if password:
            credentials = f',"{username}","{password}"'
        else:
            credentials = f',"{username}"'
    else:
        credentials = ''
    print(send_at_command(f'CMQTTCONNECT={client},"tcp://{url}:{port}",{timeout},{int(clean_session)}{credentials}'))
    time.sleep(3)

def mqtt_client_disconnect(client):
    print(send_at_command(f'CMQTTDISC={client}')) # disconnect from the broker

def mqtt_publish(client, topic, message, qos, retained=False, timeout=1):
    print(send_at_command(f'CMQTTTOPIC={client},{len(topic)}', payload=topic, timeout=timeout))  # Send topic
    print(send_at_command(f'CMQTTPAYLOAD={client},{len(message)}', payload=message, timeout=timeout))  # Send payload
    print(send_at_command(f'CMQTTPUB={client},{qos},{timeout},{int(retained)}'))  # Publish the message
    time.sleep(3)

with serial.Serial(port='/dev/ttyAMA0', baudrate=115200, timeout=1) as modem:
    # Initialize the modem
    print("Initializing modem...")
    set_verbosity(2)
    
    # Configure and activate PDP context
    print("Configuring PDP context...")
    pdp_context = pdp_open("iot.1nce.net")

    # Verify IP address
    print("Checking IP address...")
    print(send_at_command(f'CGPADDR={pdp_context}'))

    # Configure TLS/SSL
    print("Configuring MQTT over TLS/SSL...")
    ssl_context = ssl_config("isrgrootx1.pem", ssl_version=3, auth_mode=1, ignore_local_time=True, enable_SNI=True)

    # Start MQTT session
    print("Starting MQTT...")
    mqtt_session_start()

    client = mqtt_client_open("BWtestClient0", ssl_context)

    # Connect to MQTT broker
    print("Connecting to MQTT broker...")
    mqtt_client_connect(client, "8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud", port = 8883, username = "oisl_brian", password = "Oisl2023")
    
    # Publish and be damned
    mqtt_publish(client, b"BWtest/topic", b"Hi there, MQTT from SIMCom A7683E!", 1, retained=True)

    # Disconnect and stop MQTT
    mqtt_client_disconnect(client)
    mqtt_client_close(client)
    mqtt_session_stop()

    # Deactivate PDP context
    print("Deactivating PDP context...")
    pdp_close(pdp_context)
