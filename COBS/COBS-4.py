from cobs import cobs
import serial
from sys import stdin
from serial.threaded import Packetizer, ReaderThread

def encode_porp(payload):
    packet = bytearray(len(payload) + 1)
    packet[0] = len(payload)
    packet[1:] = payload
    return bytes(packet)

def decode_porp(packet):
    LEN = packet[0]
    data = packet[:LEN+1]
    assert len(data) == LEN+1
    metadata = packet[LEN+1:]
#     print("LEN =", LEN, "len =", len(data), "data =", data, "metadata =", metadata)
    return data, metadata

sent_count = 0
received_count = 0

class Porp(Packetizer):
    """
    Read COBS-encoded binary packets from serial port.
    Packets are expected to be terminated with a delimiter byte (zero).

    The class also keeps track of the transport.
    """

    def __init__(self):
        super().__init__() # call the base class initialiser
        self.original = None
        self.out_history = []
        self.in_history = []

    def handle_packet(self, packet):
        """Process received packets by decoding from COBS"""
        global received_count
#         print("packet   =", packet)
        received = bytes(packet)            # convert from bytearray
        print("received =", received)
        decoded = cobs.decode(received)     # decode from COBS
        print("decoded  =", decoded)
        
        self.in_history.append(decoded)
        
        data, metadata = decode_porp(decoded)
        print("data =", data, "metadata =", metadata, "metadata length =", len(metadata))
        
        if self.original:
            print("original =", self.original)

#             if received != self.encoded:
#                 print("Fail: receive")
#             elif decoded != self.original:
#                 print("Fail: decode")
            if data != self.original:
                print("Fail: decode")
            else:
                print("Pass")
            self.original = None
        received_count += 1

    def send_packet(self, packet):
        global sent_count
        self.original = packet                 # store for comparison
        self.out_history.append(packet)        # store in the history list
        self.encoded = cobs.encode(packet)     # encode to COBS
        print("encoded  =", self.encoded)
        self.transport.write(self.encoded+b'\x00') # append the packet delimiter
        sent_count += 1

try:
    with serial.Serial('/dev/ttyUSB0', 57600, timeout=0.5) as ser:  # open serial port
        print("Using serial port", ser.name)         # print which port was really used

        with ReaderThread(ser, Porp) as porp:  # reader thread to handle incoming packets
#             while True:
#                 line = stdin.readline()
            for line in open("/usr/share/dict/words", "r"):
                stripped = line.rstrip('\n')        # strip any trailing newline(s)
                original = bytes(stripped, 'utf-8') # convert text to bytes
#                 packet = bytearray(len(original) + 1)
#                 packet[0] = len(original)
#                 packet[1:] = original
                porp.send_packet(encode_porp(original))
#                 print("sent_count =", sent_count, "received_count =", received_count)
                while sent_count > received_count:
                    pass
except KeyboardInterrupt:
#     print(ser.is_open)
    assert not ser.is_open # the serial port should have been automatically closed
