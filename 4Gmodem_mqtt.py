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


def MQTTStart(apn):
    context_num = 1
    print(send_at_command(f'CGDCONT=1,"IP","{apn}"'))  # Configure PDP context
    print(send_at_command(f'CGACT=1,{context_num}'))  # Activate PDP context
    print(send_at_command(f'CMQTTSTART'))
    time.sleep(2)

def MQTTStop():
    context_num = 1
    print(send_at_command(f'CMQTTSTOP'))
    print(send_at_command(f'CGACT=0,{context_num}'))


class MQTTClient:
    def __init__(self, client_id, server, port = 0, user=None, password=None, keepalive=0, ssl=False, ssl_params={}): #, port, baudrate=115200, timeout=1):
        #self.baudrate = baudrate
        #self.timeout = timeout
        #self.serial = serial.Serial(port, baudrate, timeout=timeout)
        self.client_id = client_id
        self.server_url = server
        if port == 0:
            self.port = 8883 if ssl else 1883
        else:
            self.port = port
        self.cb = None
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.ssl_params = ssl_params
        self.client_index = 0
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False
        print(send_at_command(f'CMQTTACCQ={self.client_index},"{self.client_id}",{int(ssl)}'))
        if ssl:
            self.ssl_context = 1 # ToDo: just use client_index?
            ca_cert = ssl_params['ca_cert']
            ssl_version = ssl_params['ssl_version']
            auth_mode = ssl_params['auth_mode']
            ignore_local_time = ssl_params['ignore_local_time']
            enable_SNI = ssl_params['enable_SNI']
            print(send_at_command(f'CSSLCFG="sslversion",{self.ssl_context},{ssl_version}')) # set SSL version to All
            print(send_at_command(f'CSSLCFG="authmode",{self.ssl_context},{auth_mode}')) # set authentication mode
            print(send_at_command(f'CSSLCFG="ignorelocaltime",{self.ssl_context},{int(ignore_local_time)}'))
            print(send_at_command(f'CSSLCFG="cacert",{self.ssl_context},"{ca_cert}"'))  # Use CA root certificate for HiveMQ
            print(send_at_command(f'CSSLCFG="enableSNI",{self.ssl_context},{int(enable_SNI)}'))

            print(send_at_command(f'CMQTTSSLCFG={self.client_index},{self.ssl_context}'))

    def connect(self, clean_session = True, timeout = 60): # ToDO: default timeout should be 0
        if self.user:
            if self.password:
                credentials = f',"{self.user}","{self.password}"'
            else:
                credentials = f',"{self.user}"'
        else:
            credentials = ''
        self.timeout = timeout

        if self.lw_topic:
            print(send_at_command(f'CMQTTWILLTOPIC={self.client_index},{len(self.lw_topic)}', payload=self.lw_topic, timeout=self.timeout))  # Send topic
            print(send_at_command(f'CMQTTWILLMSG={self.client_index},{len(self.lw_msg)},{self.lw_qos}', payload=self.lw_msg, timeout=self.timeout))  # Send payload

        print(send_at_command(f'CMQTTCONNECT={self.client_index},"tcp://{self.server_url}:{self.port}",{timeout},{int(clean_session)}{credentials}'))
        time.sleep(3)
        return False # ToDO: return true if connected to a persistent session?
    
    def disconnect(self):
        if self.client_index != None:
            print(send_at_command(f'CMQTTDISC={self.client_index}')) # disconnect from the broker
            print(send_at_command(f'CMQTTREL={self.client_index}'))  # release the client
            self.client_index = None

    def set_last_will(self, topic, msg, retain=False, qos=0):
        assert 0 <= qos <= 2
        assert topic
        self.lw_topic = topic
        self.lw_msg = msg
        self.lw_qos = qos
        self.lw_retain = retain

    def set_callback(self, f):
        self.cb = f

    def publish(self, topic, msg, retain=False, qos=0):
        print(send_at_command(f'CMQTTTOPIC={self.client_index},{len(topic)}', payload=topic, timeout=self.timeout))  # Send topic
        print(send_at_command(f'CMQTTPAYLOAD={self.client_index},{len(msg)}', payload=msg, timeout=self.timeout))  # Send payload
        print(send_at_command(f'CMQTTPUB={self.client_index},{qos},{self.timeout},{int(retain)}'))  # Publish the message
        time.sleep(3)

    def subscribe(self, topic, qos=0):
        assert self.cb != None
        print(send_at_command(f'CMQTTSUB={self.client_index},{len(topic)},{qos}', payload=topic, timeout=self.timeout))  # Subscribe to the topic

with serial.Serial(port='/dev/ttyAMA0', baudrate=115200, timeout=1) as modem:
    # Start MQTT session
    MQTTStart("iot.1nce.net")

    # Verify IP address
    print(send_at_command(f'CGPADDR=1'))

    ssl_params = {'ca_cert': 'isrgrootx1.pem', 'ssl_version': 3, 'auth_mode': 1, 'ignore_local_time': True, 'enable_SNI': True}
    client = MQTTClient("BWtestClient0", "8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud", port = 8883, user = "oisl_brian", password = "Oisl2023", ssl=True, ssl_params=ssl_params)

    client.set_last_will(b"BWtest/lastwill", b"Goodbye, cruel world!", retain=True, qos=1)
    
    # Connect to MQTT broker
    print("Connecting to MQTT broker...")
    client.connect()
    
    # Publish and be damned
    client.publish(b"BWtest/topic", b"Hi there, MQTT from SIMCom A7683E!", retain=True)

    # Disconnect and stop MQTT
    client.disconnect()
    MQTTStop()
