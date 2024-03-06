from cobs import cobs
import serial

ser = serial.Serial('/dev/ttyUSB2', 57600, timeout=0.1)  # open serial port
print("Using serial port", ser.name)         # check which port was really used

def test(original):
    encoded = cobs.encode(original)
    print("encoded  =", encoded)
    ser.write(encoded)
    received = ser.read(256)
    print("received =", received)
    decoded = cobs.decode(received)
    print("decoded  =", decoded)
    print("original =", original)

    if received != encoded:
        print("Fail: receive")
    elif decoded != original:
        print("Fail: decode")
    else:
        print("Pass")


test(b'Hello world\x00This is a test')
test(b'\x00'*25)
test(b'\x00'*255)

ser.close()             # close port

