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

def PDPOpen(apn):
    context_num = 1
    print(send_at_command(f'CGDCONT=1,"IP","{apn}"'))  # Configure PDP context
    print(send_at_command(f'CGACT=1,{context_num}'))  # Activate PDP context
    return context_num

def PDPClose(context_num):
    print(send_at_command(f'CGACT=0,{context_num}'))

def SSLConfig(ca_cert, ssl_version = 4, auth_mode = 0, ignore_local_time = True, enable_SNI = False):
    ssl_context = 1
    print(send_at_command(f'CSSLCFG="sslversion",{ssl_context},{ssl_version}')) # set SSL version to All
    print(send_at_command(f'CSSLCFG="authmode",{ssl_context},{auth_mode}')) # set authentication mode
    print(send_at_command(f'CSSLCFG="ignorelocaltime",{ssl_context},{int(ignore_local_time)}'))
    print(send_at_command(f'CSSLCFG="cacert",{ssl_context},"{ca_cert}"'))  # Use CA root certificate for HiveMQ
    print(send_at_command(f'CSSLCFG="enableSNI",{ssl_context},{int(enable_SNI)}'))
    return ssl_context

def MQTTStart():
    print(send_at_command(f'CMQTTSTART'))
    time.sleep(2)

def MQTTStop():
    print(send_at_command(f'CMQTTSTOP'))

def MQTTSetVerbosity(level):
    print(send_at_command(f'CMEE={level}'))  # Enable verbose error messages

class MQTTClient:
    def __init__(self, client_id, server, port = 1883, user=None, password=None, keepalive=0, ssl=False, ssl_params={}): #, port, baudrate=115200, timeout=1):
        #self.baudrate = baudrate
        #self.timeout = timeout
        #self.serial = serial.Serial(port, baudrate, timeout=timeout)
        #self.mqtt_configured = False
        self.client_id = client_id
        self.server_url = server
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.ssl_params = ssl_params
        self.client_index = 0
        print(send_at_command(f'CMQTTACCQ={self.client_index},"{self.client_id}",{int(ssl)}'))
        if ssl:
            ssl_context = ssl_params['ssl_context']
            print(send_at_command(f'CMQTTSSLCFG={self.client_index},{ssl_context}'))


    def close(self):
        print(send_at_command(f'CMQTTREL={self.client_index}'))  # release the client

    def connect(self, clean_session = True, timeout = 60):
        if self.user:
            if self.password:
                credentials = f',"{self.user}","{self.password}"'
            else:
                credentials = f',"{self.user}"'
        else:
            credentials = ''
        print(send_at_command(f'CMQTTCONNECT={self.client_index},"tcp://{self.server_url}:{self.port}",{timeout},{int(clean_session)}{credentials}'))
        time.sleep(3)
        return False # ToDO: return true if connected to a persistent session?
    
    def disconnect(self):
        print(send_at_command(f'CMQTTDISC={self.client_index}')) # disconnect from the broker

    def publish(self, topic, message, qos, retained=False, timeout=1):
        print(send_at_command(f'CMQTTTOPIC={self.client_index},{len(topic)}', payload=topic, timeout=timeout))  # Send topic
        print(send_at_command(f'CMQTTPAYLOAD={self.client_index},{len(message)}', payload=message, timeout=timeout))  # Send payload
        print(send_at_command(f'CMQTTPUB={self.client_index},{qos},{timeout},{int(retained)}'))  # Publish the message
        time.sleep(3)

with serial.Serial(port='/dev/ttyAMA0', baudrate=115200, timeout=1) as modem:
    # Initialize the modem
    print("Initializing modem...")
    MQTTSetVerbosity(2)
    
    # Configure and activate PDP context
    print("Configuring PDP context...")
    pdp_context = PDPOpen("iot.1nce.net")

    # Verify IP address
    print("Checking IP address...")
    print(send_at_command(f'CGPADDR={pdp_context}'))

    # Configure TLS/SSL
    print("Configuring MQTT over TLS/SSL...")
    ssl_context = SSLConfig("isrgrootx1.pem", ssl_version=3, auth_mode=1, ignore_local_time=True, enable_SNI=True)

    # Start MQTT session
    print("Starting MQTT...")
    MQTTStart()

    client = MQTTClient("BWtestClient0", "8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud", port = 8883, user = "oisl_brian", password = "Oisl2023", ssl=True, ssl_params={'ssl_context': ssl_context})

    # Connect to MQTT broker
    print("Connecting to MQTT broker...")
    client.connect()
    
    # Publish and be damned
    client.publish(b"BWtest/topic", b"Hi there, MQTT from SIMCom A7683E!", 1, retained=True)

    # Disconnect and stop MQTT
    client.disconnect()
    client.close()
    MQTTStop()

    # Deactivate PDP context
    print("Deactivating PDP context...")
    PDPClose(pdp_context)
