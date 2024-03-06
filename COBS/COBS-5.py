from cobs import cobs
import serial
from sys import stdin
from serial.threaded import Packetizer, ReaderThread
import queue
from queue import Queue

def encode_porp(payload):
    packet = bytearray(len(payload) + 1)
    packet[0] = len(payload)
    packet[1:] = payload
    return bytes(packet)

def decode_porp(packet):
    LEN = packet[0]
    data = packet[1:LEN+1]
    if len(data) != LEN:
        print("len(", data, ") !=", LEN, "packet =", packet)
    assert len(data) == LEN
    metadata = packet[LEN+1:]
    return data, metadata

success_count = 0
failure_count = 0


class Porp(Packetizer):
    """
    Read COBS-encoded binary packets from serial port.
    Packets are expected to be terminated with a delimiter byte (zero).

    The class also keeps track of the transport.
    """

    def __init__(self):
        super().__init__() # call the base class initialiser
        self.out_history = []
        self.in_history = []
        self.incoming = Queue()
        self.sent_count = 0
        self.received_count = 0


    def handle_packet(self, packet):
        """Process received packets by decoding from COBS"""
        received = bytes(packet)            # convert from bytearray
        decoded = cobs.decode(received)     # decode from COBS
#         print("received =", received, "decoded  =", decoded)
        
        self.in_history.append(decoded)
        self.incoming.put(decoded)
        self.received_count += 1

    def send_packet(self, packet):
        self.original = packet                 # store for comparison
        self.out_history.append(packet)        # store in the history list
        self.encoded = cobs.encode(packet)     # encode to COBS
#         print("encoded  =", self.encoded)
        self.transport.write(self.encoded+b'\x00') # append the packet delimiter
        self.sent_count += 1

    def recv_packet(self):
        return self.incoming.get(timeout=5)
        
        
def test(src, dst):
    global success_count, failure_count
    for line in open("/usr/share/dict/words", "r"):
        stripped = line.rstrip('\n')        # strip any trailing newline(s)
        original = bytes(stripped, 'utf-8') # convert text to bytes
        print(stripped, ": ", end='')
        src.send_packet(encode_porp(original))
        try:
            packet = dst.recv_packet()
#                     print(packet)
            data, metadata = decode_porp(packet)
    #         print("data =", data, "metadata =", metadata, "metadata length =", len(metadata))

            if data != original:
                print("*** fail:", data, "!=", original, "***")
                failure_count += 1
            else:
                print(str(data, encoding='utf-8'))
                success_count += 1
        except queue.Empty:
            print("*** timeout ***")
    
try:
    with serial.Serial('/dev/ttyUSB0', 57600, timeout=0.5) as ser:  # open serial port
        print("Using serial port", ser.name)         # print which port was really used

        with ReaderThread(ser, Porp) as porp:  # reader thread to handle incoming packets
            test(porp, porp)
#             while True:
#                 line = stdin.readline()
except KeyboardInterrupt:
#     print(ser.is_open)
    print()
    print("sent      =", porp.sent_count)
    print("received  =", porp.received_count)
    print("successes =", success_count)
    print("failures  =", failure_count)
    assert not ser.is_open # the serial port should have been automatically closed
