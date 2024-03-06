from cobs import cobs
import serial
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
    assert len(data) == LEN
    metadata = packet[LEN+1:]
    return data, metadata

def encode_command(id, payload=b''):
    packet = bytearray(len(payload) + 3)
    packet[0] = 0
    packet[1] = 1 + len(payload)
    packet[2] = id
    packet[3:] = payload
    print("packet = ", packet)
    return bytes(packet)

sent_count = 0
received_count = 0
success_count = 0
failure_count = 0

incoming = Queue()

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

    def handle_packet(self, packet):
        """Process received packets by decoding from COBS"""
        global received_count
        global failure_count
        global success_count
        received = bytes(packet)            # convert from bytearray
#         print("received =", received)
        decoded = cobs.decode(received)     # decode from COBS
#         print("decoded  =", decoded)
        
        self.in_history.append(decoded)
        incoming.put(decoded)
        received_count += 1

    def send_packet(self, packet):
        global sent_count
        self.original = packet                 # store for comparison
        self.out_history.append(packet)        # store in the history list
        self.encoded = cobs.encode(packet)     # encode to COBS
#         print("encoded  =", self.encoded)
        self.transport.write(self.encoded+b'\x00') # append the packet delimiter
        sent_count += 1

def handle_metadata(metadata):
    attr_dict = {}
    length = len(metadata)
    while length >= 2:
        attr_len = metadata[0]
        attr_id = metadata[1]
        attr = metadata[2:attr_len+1]
        print("id =", attr_id, "attr =", attr)
        attr_dict[attr_id] = attr
        metadata = metadata[attr_len:]
        length = len(metadata)
    return attr_dict

def send(packet):
    porp.send_packet(packet)
    return incoming.get(timeout=5)

try:
    with serial.Serial('/dev/ttyUSB0', 57600, timeout=0.5) as ser:  # open serial port
        print("Using serial port", ser.name)         # print which port was really used

        with ReaderThread(ser, Porp) as porp:  # reader thread to handle incoming packets
            channelMode = 2
            ack = send(encode_command(4, channelMode.to_bytes(2, byteorder="little")))
            print("ack =", ack)
            assert ack == b'\x00'
            try:
                reply = send(encode_command(5))
                data, metadata = decode_porp(reply)
                print("data =", data, "metadata =", metadata, "metadata length =", len(metadata))
                if len(metadata) > 0:
                    attrs = handle_metadata(metadata)
                    print ("attrs =", attrs)
            except queue.Empty:
                print("*** timeout ***")
except KeyboardInterrupt:
#     print(ser.is_open)
    print("sent      =", sent_count)
    print("received  =", received_count)
    print("successes =", success_count)
    print("failures  =", failure_count)
    assert not ser.is_open # the serial port should have been automatically closed
