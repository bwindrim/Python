import serial
import time

class MQTTClient:
    def __init__(self, client_id, server, port = 0, user=None, password=None, keepalive=60, ssl=False, ssl_params={}):
        """
        Initialize the MQTT client.

        Args:
            client_id (str): The client ID for the MQTT connection.
            server (str): The MQTT server URL.
            port (int): The port to connect to the MQTT server.
            user (str): The username for the MQTT connection.
            password (str): The password for the MQTT connection.
            keepalive (int): The keepalive interval in seconds. (0 < keepalive <= 64800)
            ssl (bool): Whether to use SSL for the connection.
            ssl_params (dict): SSL parameters for the connection.
        """
        assert 0 < keepalive <= 64800
        self.client_id = client_id
        self.server_url = server
        if port == 0:
            self.port = 8883 if ssl else 1883
        else:
            self.port = port
        self.connected = False
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
        self.use_ssl = ssl
        if ssl:
            self.ssl_context = 1 # ToDo: just use client_index?
            self.ca_cert = ssl_params['ca_cert']
            self.ssl_version = ssl_params['ssl_version']
            self.auth_mode = ssl_params['auth_mode']
            self.ignore_local_time = ssl_params['ignore_local_time']
            self.enable_SNI = ssl_params['enable_SNI']

    def _send_at_command(self, command, expected_response="OK", payload=None):
        """
        Send an AT command to the modem and wait for the expected response.

        Args:
            command (str): The AT command to send.
            expected_response (str): The expected response from the self.modem.
            payload (bytes): Optional payload to send after the command.
            timeout (int): Timeout in seconds to wait for the response.

        Returns:
            str: The response from the self.modem.
        """
        cmd_str = command + '\r\n'
        self.modem.write(cmd_str.encode())
        time.sleep(0.1)  # Small delay to allow modem to process
        
        start_time = time.time()

        if payload:
            # Wait for the '>' prompt before sending data
            # ToDo: add timeout
            while True:
                if self.modem.in_waiting > 0:
                    response = self.modem.read(1)
                    print(response.decode(), end="")
                    if b'>' == response:
                        self.modem.write(payload)
                        print(payload.decode(), end="")
                        break
            
        response = b""
        
        while (time.time() - start_time) < self.timeout:
            if self.modem.in_waiting > 0:
                response += self.modem.read(self.modem.in_waiting)
                if expected_response in response.decode():
                    break
        
        print(response.decode(), end="")

    def connect(self, apn="iot.1nce.net", clean_session = True, timeout = 2): # ToDO: default timeout should be 0
        """
        Connect to the MQTT broker.

        Args:
            apn (str): The Access Point Name for the PDP context.
            clean_session (bool): Whether to start a clean session.
            timeout (int): Timeout in seconds for the connection. (0 <= timeout)

        Returns:
            bool: True if connected to a persistent session, False otherwise.
        """
        if self.user:
            if self.password:
                credentials = f',"{self.user}","{self.password}"'
            else:
                credentials = f',"{self.user}"'
        else:
            credentials = ''
        self.timeout = timeout

        self.modem = serial.Serial(port='/dev/ttyAMA0', baudrate=115200, timeout=timeout)
        self.context_num = 1
        self._send_at_command(f'AT+CGDCONT=1,"IP","{apn}"') # Configure PDP context
        self._send_at_command(f'AT+CGACT=1,{self.context_num}')  # Activate PDP context
        self._send_at_command(f'AT+CMQTTSTART')             # Start MQTT session
        time.sleep(2)

        self._send_at_command(f'AT+CMQTTACCQ={self.client_index},"{self.client_id}",{int(self.use_ssl)}')
        if self.use_ssl:
            self.ssl_context = 1 # ToDo: just use client_index?
            self._send_at_command(f'AT+CSSLCFG="sslversion",{self.ssl_context},{self.ssl_version}')    # set SSL version
            self._send_at_command(f'AT+CSSLCFG="authmode",{self.ssl_context},{self.auth_mode}')        # set authentication mode
            self._send_at_command(f'AT+CSSLCFG="ignorelocaltime",{self.ssl_context},{int(self.ignore_local_time)}')
            self._send_at_command(f'AT+CSSLCFG="cacert",{self.ssl_context},"{self.ca_cert}"')          # Set CA root certificate
            self._send_at_command(f'AT+CSSLCFG="enableSNI",{self.ssl_context},{int(self.enable_SNI)}') # Set Server Name Indication
            self._send_at_command(f'AT+CMQTTSSLCFG={self.client_index},{self.ssl_context}')       # Set SSL context for MQTT

        if self.lw_topic:
            self._send_at_command(f'AT+CMQTTWILLTOPIC={self.client_index},{len(self.lw_topic)}', payload=self.lw_topic)  # Send topic
            self._send_at_command(f'AT+CMQTTWILLMSG={self.client_index},{len(self.lw_msg)},{self.lw_qos}', payload=self.lw_msg)  # Send payload

        self._send_at_command(f'AT+CMQTTCONNECT={self.client_index},"tcp://{self.server_url}:{self.port}",{self.keepalive},{int(clean_session)}{credentials}')
        time.sleep(3)
        self.connected = True
        return False # ToDO: return true if connected to a persistent session?
    
    def disconnect(self):
        """
        Disconnect from the MQTT broker and release the client.
        """
        if self.connected:
            if self.client_index != None:
                self._send_at_command(f'AT+CMQTTDISC={self.client_index}') # disconnect from the broker
                self._send_at_command(f'AT+CMQTTREL={self.client_index}')  # release the client
                self.client_index = None
            self._send_at_command(f'AT+CMQTTSTOP')             # Stop MQTT session
            self._send_at_command(f'AT+CGACT=0,{self.context_num}') # Deactivate PDP context
            self.modem.close()
            self.connected = False

    def set_last_will(self, topic, msg, retain=False, qos=0):
        """
        Set the last will message to be sent by the broker when the client disconnects unexpectedly.

        Args:
            topic (bytes): The topic for the last will message. (0 < len(topic) <= 1024)
            msg (bytes): The message payload. (0 < len(msg) <= 1024)
            retain (bool): Whether to retain the message. (retain must be False)
            qos (int): The Quality of Service level. (0 <= qos <= 2)
        """
        assert 0 <= qos <= 2
        assert topic
        assert 0 < len(topic) <= 1024
        assert 0 < len(msg) <= 1024 # note: will message is limited to 1024 bytes
        assert retain == False, "retain=True is not supported by SimCOMM A76xx for last will"
        self.lw_topic = topic
        self.lw_msg = msg
        self.lw_qos = qos
        self.lw_retain = retain

    def set_callback(self, f):
        """
        Set the callback function to handle incoming messages.

        Args:
            f (function): The callback function.
        """
        self.cb = f

    def publish(self, topic, msg, retain=False, qos=0, pub_timeout=60):
        """
        Publish a message to a topic.

        Args:
            topic (bytes): The topic to publish to. (0 < len(topic) <= 1024)
            msg (bytes): The message payload. (0 < len(msg) <= 10240)
            retain (bool): Whether to retain the message.
            qos (int): The Quality of Service level. (0 <= qos <= 2)
        """
        assert 0 <= qos <= 2
        assert 0 < len(topic) <= 1024
        assert 0 < len(msg) <= 10240
        self._send_at_command(f'AT+CMQTTTOPIC={self.client_index},{len(topic)}', payload=topic)  # Send topic
        self._send_at_command(f'AT+CMQTTPAYLOAD={self.client_index},{len(msg)}', payload=msg)  # Send payload
        self._send_at_command(f'AT+CMQTTPUB={self.client_index},{qos},{pub_timeout},{int(retain)}')  # Publish the message
        time.sleep(3)

    def subscribe(self, topic, qos=0):
        """
        Subscribe to a topic.

        Args:
            topic (bytes): The topic to subscribe to. (0 < len(topic) <= 1024)
            qos (int): The Quality of Service level. (0 <= qos <= 2)
        """
        assert self.cb != None
        assert 0 <= qos <= 2
        assert 0 < len(topic) <= 1024
        print(f'subscribing to {topic}')
        self._send_at_command(f'AT+CMQTTSUB={self.client_index},{len(topic)},{qos}', payload=topic)  # Subscribe to the topic

    def wait_msg(self):
        """
        Wait for a message to be received.
        """
        pass

    def check_msg(self):
        """
        Check for a message to be received.
        """
        if self.modem.in_waiting > 0:
            msg = self.modem.read(self.modem.in_waiting)
            self.cb(msg)

def test():
    # Start MQTT session
    ssl_params = {'ca_cert': 'isrgrootx1.pem', 'ssl_version': 3, 'auth_mode': 1, 'ignore_local_time': True, 'enable_SNI': True}
    client = MQTTClient("BWtestClient0", "8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud", port = 8883, user = "oisl_brian", password = "Oisl2023", ssl=True, ssl_params=ssl_params)

    client.set_last_will(b"BWtest/lastwill", b"Goodbye, cruel world!", qos=1)

    # Connect to MQTT broker
    client.connect()

    # Subscribe to a topic
    client.set_callback(lambda msg: print(msg))
    #client.subscribe(b"BWtest/topic", qos=1)

    # Publish and be damned
    msg = b"Hi there yet again, MQTT from SIMCom A7683E!"
    client.publish(b"BWtest/topic", msg, retain=True)

    # Disconnect and stop MQTT
    client.disconnect()

test()
