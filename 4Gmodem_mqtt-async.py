import asyncio
import serial_asyncio
from datetime import datetime

def extract_numeric_values(response):
    try:
        parts = response.split(':')[1].split(',')
        values = tuple(map(int, parts[:3]))
        return values
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid response format: {response}") from e

class AsyncMQTTClient:
    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=20, ssl=False, ssl_params={}):
        self.client_id = client_id
        self.server_url = server
        self.port = port if port else (8883 if ssl else 1883)
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
            self.ssl_context = 1
            self.ca_cert = ssl_params['ca_cert']
            self.ssl_version = ssl_params['ssl_version']
            self.auth_mode = ssl_params['auth_mode']
            self.ignore_local_time = ssl_params['ignore_local_time']
            self.enable_SNI = ssl_params['enable_SNI']
        self.reader = None
        self.writer = None

    async def _readline_stripped(self):
        """
        Read a line from the serial reader, handle EOF, and return the stripped string.
        Raises EOFError if the connection is closed.
        """
        while True:
            line = await self.reader.readline()
            if not line:  # EOF
                raise EOFError("Serial connection closed while reading response")
            result = line.decode(errors="ignore").strip()
            print(f'Rx: {result}')
            if result != "":
                return result


    async def _send_at_command(self, command, body="", result_handler=None, payload=None):
        """ Send an AT command to the modem and handle the response.
        Args:
            command (str): The AT command to send (without 'AT+' prefix).
            body (str): The body of the command, if any.
            result_handler (callable): A function to handle the result line.
            payload (bytes): Optional payload to send after the command.
        Returns:
            The result of the command, if any.
        Raises:
            ValueError: If the command fails with an ERROR response.
            EOFError: If the connection is closed while reading the response.
        """
        # Construct the AT command string and send it.
        cmd_str = 'AT+' + command + body + '\r'
        print(f'Tx: {cmd_str}')
        self.writer.write(cmd_str.encode())
        await self.writer.drain() # Ensure the command is sent

        # We've sent the command, now we wait for the echo. However,
        # we may not get an echo if the command is not recognized and
        # some commands may not echo back.
        # In addition, we may receive unsolicited responses before the echo.
        while True:
            line = await self._readline_stripped()
            if line == cmd_str.strip(): # wait for the command to be echoed back
                break
            elif line.startswith('+'): # unsolicited response
                # Handle unsolicited response
                await self._handle_unsolicited_response(line)
            elif line == 'OK' or line == 'ERROR':
                # If we get OK or ERROR, we can stop waiting for the echo
                break
            else:
                # If we get an unexpected line, we can log it and continue
                print(f'Unexpected response: {line}')

        # If payload is needed, wait for '>' prompt
        if payload:
            # Read until the '>' prompt is seen
            prompt = await self.reader.readuntil(b'>')
            if not prompt.endswith(b'>'):
                raise EOFError("Serial connection closed or prompt not found while waiting for '>' prompt")
            self.writer.write(payload) # now send the payload
            await self.writer.drain() # Ensure the payload is sent

        # Now we wait for the response
        # Initialize result to None, it will be set if we get a result
        result = None
        # Read response lines
        line = await self._readline_stripped() # Read the first response line
        assert line != "" # Ensure we got a response
        # Check for an early result, i.e. one that preceeds the OK or ERROR response
        if line.startswith('+' + command + ':'):
            # Early result, may be for OK or ERROR
            result = result_handler(line) # stash the result
            line = await self._readline_stripped() # get next line
        # Check for ERROR response
        if line == "ERROR":
            if result:
                raise ValueError(f"Command {command} failed with result: {result}", result)
            else:
                raise ValueError(f"Command {command} failed with ERROR response")
        # Check for OK response
        if line == 'OK':
            if result_handler and result is None: # we're still expecting an explicit result
                # Assume that the result will come in the next line
                line = await self._readline_stripped()  # get next line
                assert line.startswith('+' + command + ':')
                # Late result, only for OK
                try:
                    result = result_handler(line) # stash the result
                    if result != 0:
                        raise ValueError(f"Command {command} failed with result: {result}", result)
                except Exception as e:
                    print(f"Result handler exception: {e} line = {line}")
                    raise e
            return result
        # Handle unsolicited responses
        if line.startswith('+'):
            # Handle unsolicited response
            await self._handle_unsolicited_response(line)

    async def _handle_unsolicited_response(self, response):
        topic = b''
        payload = b''
        print(f'Unsolicited: {response}')
        if response.startswith('+CMQTTRXSTART:'):
            id, topic_total_len, payload_total_len = extract_numeric_values(response)
            while True:
                line = await self.reader.readline()
                decoded = line.decode(errors="ignore").strip()
                print(f'Rx: {decoded}')
                if decoded.startswith('+CMQTTRXTOPIC:'):
                    id, topic_sub_len = extract_numeric_values(decoded)
                    topic += await self.reader.readexactly(topic_sub_len)
                    topic_total_len -= topic_sub_len
                    print(topic.decode(), end="")
                elif decoded.startswith('+CMQTTRXPAYLOAD:'):
                    id, payload_sub_len = extract_numeric_values(decoded)
                    payload += await self.reader.readexactly(payload_sub_len)
                    payload_total_len -= payload_sub_len
                    print(payload.decode(), end="")
                elif decoded.startswith('+CMQTTRXEND:'):
                    assert topic_total_len == 0
                    assert payload_total_len == 0
                    if self.cb:
                        self.cb(topic, payload)
                    else:
                        print(f"Received message for {topic}: {payload}")
                    break

    async def connect(self, apn="iot.1nce.net", clean_session=True, timeout=2, port='/dev/ttyAMA0', baudrate=115200):
        credentials = ''
        if self.user:
            if self.password:
                credentials = f',"{self.user}","{self.password}"'
            else:
                credentials = f',"{self.user}"'
        self.timeout = timeout
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=port, baudrate=baudrate) # Connect to the serial port
        await self._send_at_command('CGDCONT', f'=1,"IP","{apn}"')
        await self._send_at_command('CGACT', f'=1,1')
        try:
            await self._send_at_command('CMQTTSTART', result_handler=lambda s: int(extract_numeric_values(s)[0]))
            await self._send_at_command('CMQTTACCQ', f'={self.client_index},"{self.client_id}",{int(self.use_ssl)}')
            if self.use_ssl:
                await self._send_at_command('CSSLCFG', f'="sslversion",1,{self.ssl_version}')
                await self._send_at_command('CSSLCFG', f'="authmode",1,{self.auth_mode}')
                await self._send_at_command('CSSLCFG', f'="ignorelocaltime",1,{int(self.ignore_local_time)}')
                await self._send_at_command('CSSLCFG', f'="cacert",1,"{self.ca_cert}"')
                await self._send_at_command('CSSLCFG', f'="enableSNI",1,{int(self.enable_SNI)}')
                await self._send_at_command('CMQTTSSLCFG', f'=0,1')
            if self.lw_topic:
                await self._send_at_command('CMQTTWILLTOPIC', f'=0,{len(self.lw_topic)}', payload=self.lw_topic)
                await self._send_at_command('CMQTTWILLMSG', f'=0,{len(self.lw_msg)},{self.lw_qos}', payload=self.lw_msg)
        except ValueError as e:
            # An immediate ERROR from CMQTTSTSTART or CMQTTACCQ implies that we're already connected.
            # ToDo: we should really stop and restart, in case the client ID has changed.
            if len(e.args) != 1:
                raise e
        try:
            await self._send_at_command('CMQTTCONNECT', f'=0,"tcp://{self.server_url}:{self.port}",{self.keepalive},{int(clean_session)}{credentials}',
                                    result_handler=lambda s: int(extract_numeric_values(s)[1]))
        except ValueError as e:
            # An error code of 19 from CMQTTCONNECT means "Already connected", so we can ignore it
            # ToDo: we should really disconnect and reconnect.
            if 19 != e.args[1]:
                raise e
        self.connected = True
        return False

    async def disconnect(self):
        if self.connected:
            await self._send_at_command('CMQTTDISC', f'=0', result_handler=lambda s: int(extract_numeric_values(s)[1]))
            await self._send_at_command('CMQTTREL', f'=0')
            await self._send_at_command('CMQTTSTOP', result_handler=lambda s: int(s))
            await self._send_at_command('CGACT', f'=0,1')
            self.writer.close()
            await self.writer.wait_closed()
            self.connected = False

    def set_last_will(self, topic, msg, retain=False, qos=0):
        assert 0 <= qos <= 2
        assert topic
        assert 0 < len(topic) <= 1024
        assert 0 < len(msg) <= 1024
        assert retain == False, "retain=True is not supported by SimCOMM A76xx for last will"
        self.lw_topic = topic
        self.lw_msg = msg
        self.lw_qos = qos
        self.lw_retain = retain

    def set_callback(self, f):
        self.cb = f

    async def publish(self, topic, msg, retain=False, qos=0, pub_timeout=60):
        assert 0 <= qos <= 2
        assert 0 < len(topic) <= 1024
        assert 0 < len(msg) <= 10240
        await self._send_at_command('CMQTTTOPIC', f'=0,{len(topic)}', payload=topic)
        await self._send_at_command('CMQTTPAYLOAD', f'=0,{len(msg)}', payload=msg)
        await self._send_at_command('CMQTTPUB', f'=0,{qos},{pub_timeout},{int(retain)}', result_handler=lambda s: int(extract_numeric_values(s)[1]))

    async def subscribe(self, topic, qos=0):
        assert self.cb is not None
        assert 0 <= qos <= 2
        assert 0 < len(topic) <= 1024
        await self._send_at_command('CMQTTSUB', f'=0,{len(topic)},{qos}', payload=topic, result_handler=lambda s: int(extract_numeric_values(s)[1]))

    async def unsubscribe(self, topic):
        assert 0 < len(topic) <= 1024
        await self._send_at_command('CMQTTUNSUB', f'=0,{len(topic)},1', payload=topic, result_handler=lambda s: int(extract_numeric_values(s)[1]))

    async def check_msg(self):
        # Non-blocking check for messages
        # You may want to implement a background task for this
        pass

async def upload_cert(client, filename):
    with open(filename, 'rb') as f:
        data = f.read()
        await client._send_at_command('CCERTDOWN', f'="{filename}",{len(data)}', payload=data)

def sub_cb(topic, msg):
    parts = topic.decode().split('/')
    if parts[0] == 'BWtest' and parts[1] == 'topic':
        print(f'sub_cb({parts}, {msg})')
    else:
        print(f'sub_cb({topic}, {msg})')

async def test():
    topic1 = b"BWtest/topic"
    topic2 = b"BWtest/timestamp"
    ssl_params = {'ca_cert': 'isrgrootx1.pem', 'ssl_version': 3, 'auth_mode': 1, 'ignore_local_time': True, 'enable_SNI': True}
    client = AsyncMQTTClient("BWtestClient0", "8d5ec6984ed54a29ac7794546055635d.s1.eu.hivemq.cloud", port=8883, user="oisl_brian", password="Oisl2023", ssl=True, ssl_params=ssl_params)
    client.set_last_will(b"BWtest/lastwill", b"Pi Python connection broken", qos=1)
    await client.connect()
    client.set_callback(sub_cb)
    await client.subscribe(topic1, qos=1)

    try:
        while True:
            now = datetime.now()
            payload2 = f'Pi Python at: {now.strftime("%Y-%m-%d %H:%M:%S")}'
            print(f'Publishing to {topic2}: {payload2}')
            await client.publish(topic2, payload2.encode("utf-8"), retain=True, qos=1)
            print("Publish done")
            start_time = asyncio.get_event_loop().time()
            wait_interval = 15 * 60
            while asyncio.get_event_loop().time() - start_time < wait_interval:
                await asyncio.sleep(1)
                # You may want to implement message checking here
    except KeyboardInterrupt:
        pass

    await client.unsubscribe(topic1)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test())