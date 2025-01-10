import serial
import time

class SimCOMSocket:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.connected = False

    def send_at_command(self, command, expected_response="OK", timeout=5):
        self.ser.write((command + "\r\n").encode())
        end_time = time.time() + timeout
        response = ""
        while time.time() < end_time:
            if self.ser.in_waiting > 0:
                response += self.ser.read(self.ser.in_waiting).decode()
                if expected_response in response:
                    return response
        raise Exception(f"Timeout waiting for response to command: {command}")

    def connect(self, apn):
        self.send_at_command("AT+CSQ")
        self.send_at_command("AT+CREG?")
        self.send_at_command("AT+CGATT=1")
        self.send_at_command(f'AT+CGDCONT=1,"IP","{apn}"')
        self.send_at_command("AT+CGACT=1,1")
        self.connected = True

    def socket(self):
        if not self.connected:
            raise Exception("Modem not connected")
        return SimCOMSocketInstance(self.ser)

class SimCOMSocketInstance:
    def __init__(self, ser):
        self.ser = ser
        self.cid = None

    def connect(self, host, port):
        self.cid = self.send_at_command('AT+NETOPEN', '+NETOPEN: 0')
        self.send_at_command(f'AT+CIPOPEN=0,"TCP","{host}",{port}', 'OK')

    def send(self, data):
        self.send_at_command(f'AT+CIPSEND=0,{len(data)}', '>')
        self.ser.write(data)
        self.send_at_command("", 'SEND OK')

    def recv(self, bufsize):
        response = self.send_at_command(f'AT+CIPRXGET=2,0,{bufsize}', '+CIPRXGET: 2')
        start = response.find('\r\n') + 2
        end = response.rfind('\r\n')
        return response[start:end].encode()

    def close(self):
        self.send_at_command('AT+CIPCLOSE=0', 'OK')
        self.send_at_command('AT+NETCLOSE', '+NETCLOSE: 0')

# Example usage
if __name__ == "__main__":
    modem = SimCOMSocket(port='/dev/ttyUSB0')
    modem.connect(apn='your_apn')
    sock = modem.socket()
    sock.connect('example.com', 80)
    sock.send(b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
    response = sock.recv(1024)
    print(response)
    sock.close()