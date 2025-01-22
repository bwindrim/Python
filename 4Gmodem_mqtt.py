import serial
import time

def extract_numeric_values(response):
    """
    Extracts up to three numeric values from a string of the form "+CMQTTRXSTART: 0,12,44".

    Args:
        response (str): The input string.

    Returns:
        tuple: A tuple containing the extracted integers (up to three).
    """
    try:
        # Split the string by ':' and then by ','
        parts = response.split(':')[1].split(',')
        # Convert the parts to integers and limit to 3 values
        values = tuple(map(int, parts[:3]))
        return values
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid response format: {response}") from e


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

    def _send_at_command(self, command, body= "", result_handler=None, payload=None):
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
        cmd_str = 'AT+' + command + body +'\r'
        encoded_cmd = cmd_str.encode()
        self.modem.write(encoded_cmd)
        time.sleep(0.1)  # Small delay to allow modem to process
        
        response = None
        result = None

        # Process one line at a time until we get a response
        while True:
            # Process a line, one character at a time
            word = b""
            char = self.modem.read(1)
            complete_line = char # bytes type
            #print(char.decode(), end="")
            if b'>' == char:
                if payload:
                    self.modem.write(payload)
                    #print(payload.decode(), end="")
                    complete_line += payload # + '\n'
            elif char == b'+':
                # get word
                char = self.modem.read(1)
                #print(char.decode(), end="")
                while char.isalpha():
                    word += char
                    char = self.modem.read(1)
                    #print(char.decode(), end="")
                if word.decode() == command:
                    # Solicited response
                    result = self.modem.readline()
                    char = b'\n'
                    #print("Solicited response", result.decode(), end="")
                    complete_line += word + result
                else:
                    # Unsolicited response
                    complete_line += word + char + self.modem.readline()
                    #print("Unsolicited response", complete_line.decode(), end="")
                    self.handle_unsolicited_response(complete_line)
                    pass
                # get rest of line
                pass
            elif char.isalpha():
                # get rest of word
                while char.isalpha():
                    word += char
                    char = self.modem.read(1)
                    #print(char.decode(), end="")
                complete_line = word + char + self.modem.readline()
                if word == b'ERROR':
                    response = False
                elif word == b'OK':
                    response = True
                elif word == b'AT':
                    # The echoed command line includes an extra '\r' at the end, so strip both
                    assert complete_line.strip() == cmd_str.encode().strip()
                    pass # ignore echo
                else:
                    print(f"Unknown response: {word}")
            elif char == b'\n':
                pass # ignore newlines
            elif char == b'\r':
                pass # ignore carriage returns
            else:
                print(f"Unexpected char: {char}")
            
            print(complete_line.decode(), end="")
            
            # Check if we have a response
            if response is not None:
                if response == False:
                    if result is None:
                        return -1
                    else:
                        print("result =", result_handler(result.strip()))
                        return result_handler(result.strip())
                else:
                    if result_handler is not None:
                        if result is None:
                            pass
                        else:
                            print("result =", result_handler(result.strip()))
                            return result_handler(result.strip())
                    else:
                        return 0
            else:
                # Wait for the next line
                pass

    def handle_unsolicited_response(self, response):
        """
        Handle an unsolicited response from the modem.

        Args:
            response (str): The unsolicited response from the modem.
        """
        topic = b''
        payload = b''
        response = response.decode().strip()
        print(response)
        #assert response.startswith('+') # Unsolicited responses should start with '+'
        if response.startswith('+CMQTTRXSTART:'):
            # MQTT message received
            id, topic_total_len, payload_total_len = extract_numeric_values(response)
            #print(F"MQTT message received: id={id}, topic_len={topic_total_len}, msg_len={payload_total_len}")

            while True:
                response = self.modem.readline().decode().strip()
                print(response)
                if response.startswith('+CMQTTRXTOPIC:'):
                    # MQTT message received
                    id, topic_sub_len = extract_numeric_values(response)
                    #print(F"MQTT topic received: id={id}, topic_len={topic_sub_len}")
                    topic += self.modem.read(topic_sub_len)
                    topic_total_len -= topic_sub_len
                    print(topic.decode(), end="")
                elif response.startswith('+CMQTTRXPAYLOAD:'):
                    id, payload_sub_len = extract_numeric_values(response)
                    #print(F"MQTT payload received: id={id}, payload_len={payload_sub_len}")
                    payload += self.modem.read(payload_sub_len)
                    payload_total_len -= payload_sub_len
                    print(payload.decode(), end="")
                elif response.startswith('+CMQTTRXEND:'):
                    assert topic_total_len == 0
                    assert payload_total_len == 0
                    self.cb(topic, payload)
                    break

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

        self.modem = serial.Serial(port='/dev/ttyAMA0', baudrate=115200) #, timeout=timeout)
        self.context_num = 1
        self._send_at_command('CGDCONT', f'=1,"IP","{apn}"') # Configure PDP context
        self._send_at_command('CGACT', f'=1,{self.context_num}')  # Activate PDP context
        self._send_at_command('CMQTTSTART', result_handler=lambda s: int(s))             # Start MQTT session

        self._send_at_command('CMQTTACCQ', f'={self.client_index},"{self.client_id}",{int(self.use_ssl)}')
        if self.use_ssl:
            self.ssl_context = 1 # ToDo: just use client_index?
            self._send_at_command('CSSLCFG', f'="sslversion",{self.ssl_context},{self.ssl_version}')    # set SSL version
            self._send_at_command('CSSLCFG', f'="authmode",{self.ssl_context},{self.auth_mode}')        # set authentication mode
            self._send_at_command('CSSLCFG', f'="ignorelocaltime",{self.ssl_context},{int(self.ignore_local_time)}')
            self._send_at_command('CSSLCFG', f'="cacert",{self.ssl_context},"{self.ca_cert}"')          # Set CA root certificate
            self._send_at_command('CSSLCFG', f'="enableSNI",{self.ssl_context},{int(self.enable_SNI)}') # Set Server Name Indication
            self._send_at_command('CMQTTSSLCFG', f'={self.client_index},{self.ssl_context}')       # Set SSL context for MQTT

        if self.lw_topic:
            self._send_at_command('CMQTTWILLTOPIC', f'={self.client_index},{len(self.lw_topic)}', payload=self.lw_topic)  # Send topic
            self._send_at_command('CMQTTWILLMSG', f'={self.client_index},{len(self.lw_msg)},{self.lw_qos}', payload=self.lw_msg)  # Send payload

        self._send_at_command('CMQTTCONNECT', f'={self.client_index},"tcp://{self.server_url}:{self.port}",{self.keepalive},{int(clean_session)}{credentials}',
        result_handler=lambda s: int(s.split(b',')[1]))  # Connect to the broker
        self.connected = True
        return False # ToDO: return true if connected to a persistent session?
    
    def disconnect(self):
        """
        Disconnect from the MQTT broker and release the client.
        """
        if self.connected:
            if self.client_index != None:
                self._send_at_command('CMQTTDISC', f'={self.client_index}', result_handler=lambda s: int(s.split(b',')[1])) # disconnect from the broker
                self._send_at_command('CMQTTREL', f'={self.client_index}')  # release the client
                self.client_index = None
            self._send_at_command('CMQTTSTOP', result_handler=lambda s: int(s))             # Stop MQTT session
            self._send_at_command('CGACT', f'=0,{self.context_num}') # Deactivate PDP context
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
        self._send_at_command('CMQTTTOPIC', f'={self.client_index},{len(topic)}', payload=topic)  # Send topic
        self._send_at_command('CMQTTPAYLOAD', f'={self.client_index},{len(msg)}', payload=msg)  # Send payload
        self._send_at_command('CMQTTPUB', f'={self.client_index},{qos},{pub_timeout},{int(retain)}', result_handler=lambda s: int(s.split(b',')[1]))  # Publish the message

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
        #print(f'subscribing to {topic}')
        self._send_at_command('CMQTTSUB', f'={self.client_index},{len(topic)},{qos}', payload=topic, result_handler=lambda s: int(s.split(b',')[1]))  # Subscribe to the topic

    def unsubscribe(self, topic, qos=0):
        """
        Unsubscribe from a topic.

        Args:
            topic (bytes): The topic to subscribe to. (0 < len(topic) <= 1024)
        """
        assert self.cb != None
        assert 0 <= qos <= 2
        assert 0 < len(topic) <= 1024
        #print(f'unsubscribing from {topic}')
        self._send_at_command('CMQTTUNSUB', f'={self.client_index},{len(topic)},1', payload=topic, result_handler=lambda s: int(s.split(b',')[1]))  # Subscribe to the topic

    def wait_msg(self):
        """
        Wait for a message to be received.
        """
        msg = self.modem.readline()
        self.handle_unsolicited_response(msg)

    def check_msg(self):
        """
        Check for a message to be received.
        """
        if self.modem.in_waiting > 0:
            msg = self.modem.readline()
            self.handle_unsolicited_response(msg)

# Received messages from subscriptions will be delivered to this callback
def sub_cb(topic, msg):
    print(f'sub_cb({topic}, {msg})')


def test():
    # Start MQTT session
    ssl_params = {'ca_cert': 'isrgrootx1.pem', 'ssl_version': 3, 'auth_mode': 1, 'ignore_local_time': True, 'enable_SNI': True}
    client = MQTTClient("BWtestClient0", "8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud", port = 8883, user = "oisl_brian", password = "Oisl2023", ssl=True, ssl_params=ssl_params)

    client.set_last_will(b"BWtest/lastwill", b"Goodbye, cruel world!", qos=1)

    # Connect to MQTT broker
    client.connect()

    # Publish and be damned
    msg = b"Hi there yet again, MQTT from SIMCom A7683E!"
    client.publish(b"BWtest/topic", msg, retain=True)

    # Subscribe to a topic
    client.set_callback(sub_cb)
    client.subscribe(b"BWtest/topic", qos=1)

    start_time = time.time()
    while time.time() - start_time < 30:
        client.check_msg()
        time.sleep(1)

    client.unsubscribe(b"BWtest/topic")

    # Disconnect and stop MQTT
    client.disconnect()

test()
