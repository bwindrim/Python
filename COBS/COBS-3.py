from cobs import cobs
import serial
from sys import stdin

ser = serial.Serial('/dev/ttyUSB0', 57600, timeout=0.5)  # open serial port
print("Using serial port", ser.name)         # check which port was really used

def send(original):
    encoded = cobs.encode(original)
    print("encoded  =", encoded)
    ser.write(encoded+b'\x00')

try:
    while True:
        line = stdin.readline()
        stripped = line.rstrip('\n')        # strip any trailing newline(s)
        original = bytes(stripped, 'utf-8') # convert to bytes
        encoded = cobs.encode(original)     # encode to COBS
        print("encoded  =", encoded)
        ser.write(encoded+b'\x00')          # append the packet terminator
        received = ser.read(256)            # read back the echoed packet
        print("received =", received)
        received = received[:-1]            # strip the packet terminator
        decoded = cobs.decode(received)     # decode from COBS
        print("decoded  =", decoded)
        print("original =", original)

        if received != encoded:
            print("Fail: receive")
        elif decoded != original:
            print("Fail: decode")
        else:
            print("Pass")
except KeyboardInterrupt:
    ser.close()             # close port

