import serial
from cobs import cobs
from serial.threaded import Packetizer
import queue
from queue import Queue

def encode_packet(payload):
    packet = bytearray(len(payload) + 1)
    packet[0] = len(payload)
    packet[1:] = payload
    return bytes(packet)

def decode_packet(packet):
    LEN = packet[0]
    data = packet[1:LEN+1]
    if len(data) != LEN:
        print("len(", data, ") !=", LEN, "packet =", packet)
    assert len(data) == LEN
    metadata = packet[LEN+1:]
    return data, metadata

def encode_command(id, payload=b''):
    packet = bytearray(len(payload) + 3)
    packet[0] = 0
    packet[1] = 1 + len(payload)
    packet[2] = id
    packet[3:] = payload
#     print("command packet = ", packet)
    return bytes(packet)


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
        self.incoming: Queue[bytes] = Queue()
        self.responses: Queue[bytes] = Queue()


    def handle_packet(self, packet):
        """Process received packets by decoding from COBS"""
        received = bytes(packet)            # convert from bytearray
        decoded = cobs.decode(received)     # decode from COBS
        if len(decoded) == 0:
            return # discard empty packets
        self.in_history.append(decoded)
        # Decide which queue the packet should be sent to:
        # If the first byte of the decoded packet is zero then...
        if (decoded[0] == 0):
            # ...its head segment is empty and hence doesn't contain a PORP
            # datagram, so this must be a an ACK, NACK, or other response.
            self.responses.put(decoded)
        else:
            # ...otherwise this must be an incoming Lattice datagram,
            # possibly with attached metadata.
            self.incoming.put(decoded)

    def send_packet(self, packet, timeout=1):
        self.original = packet                 # store for comparison
        self.out_history.append(packet)        # store in the history list
        self.encoded = cobs.encode(packet)     # encode to COBS
#         print("encoded  =", self.encoded)
        self.transport.write(self.encoded+b'\x00') # append the packet delimiter
        response = self.recv_response(timeout=timeout) # wait for ACK
        if response == None:
            print("send_packet(timeout=", timeout,"), timout")
#         print("response =", response)
#         assert response == b'\x00'   # ack should be empty packet
        return response

    def recv_incoming(self, timeout=30):
        try:
            packet = self.incoming.get(timeout=timeout)
        except queue.Empty:
            packet = None
        
        return packet
        
    def recv_response(self, timeout=1):
        try:
            packet = self.responses.get(timeout=timeout)
        except queue.Empty:
            packet = None
        
        return packet
        
def handle_metadata(metadata):
    attr_dict = {}
    length = len(metadata)
    while length >= 2:
        attr_len = metadata[0]
        attr_id = metadata[1]
        attr = metadata[2:attr_len+1]
        print("id =", attr_id, "attr =", attr)
        attr_dict[attr_id] = attr
        metadata = metadata[attr_len+1:]
        length = len(metadata)
    return attr_dict

