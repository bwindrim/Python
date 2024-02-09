from cobs import cobs
import serial
from serial.threaded import Packetizer, ReaderThread
import queue
from queue import Queue
import random
from random import randrange, randbytes
import time
# Ensure that we always generate the same "random" test data,
# for reproducability.
random.seed(0)

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

    def send_packet(self, packet):
        self.original = packet                 # store for comparison
        self.out_history.append(packet)        # store in the history list
        self.encoded = cobs.encode(packet)     # encode to COBS
#         print("encoded  =", self.encoded)
        self.transport.write(self.encoded+b'\x00') # append the packet delimiter
        try:
            response = self.responses.get(timeout=1) # wait for ACK
        except queue.Empty:
            response = None
#         print("response =", response)
#         assert response == b'\x00'   # ack should be empty packet
        return response

    def recv_incoming(self):
        return self.incoming.get(timeout=5)
        
    def recv_response(self):
        return self.responses.get(timeout=1)
        
def handle_metadata(metadata):
    attr_dict = {}
    length = len(metadata)
    while length >= 2:
        attr_len = metadata[0]
        attr_id = metadata[1]
        attr = metadata[2:attr_len+1]
#         print("id =", attr_id, "attr =", attr)
        attr_dict[attr_id] = attr
        metadata = metadata[attr_len:]
        length = len(metadata)
    return attr_dict

# def send(packet):
#     porp.send_packet(packet)
#     return incoming.get(timeout=5)

def count_bit_errors(A,B):
    count = 0
    for a, b, in zip(A, B):
        count += (a ^ b).bit_count()
        
    return count

def test1(src, dst, channel_mode=1, limit=0):
    successes = 0
    failures = 0
    print("test1: channel mode is", channel_mode)
    set_channel_mode(src, channel_mode)
    set_channel_mode(dst, channel_mode)
    query_channel_mode(src)
    query_channel_mode(dst)

    try:
        for line in open("/usr/share/dict/words", "r"):
            # strip any trailing newline(s) and convert text to bytes
#             stripped = line.rstrip('\n')
            original = bytes(line.rstrip('\n'), 'utf-8')
            encoded = encode_porp(original)
            resp = src.send_packet(encoded)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == b'\x00'   # ack should be empty packet
            try:
                packet = dst.recv_incoming()
                data, metadata = decode_porp(packet)

                if data != original:
                    if len(data) != len(original):
                        print("*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("*** bit errors:", data, "!=", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
#                     print(str(data, encoding='utf-8'))
                    successes += 1
            except queue.Empty:
                print("*** timeout ***")
                failures += 1
                
            limit -= 1
            if limit == 0:
                break
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def test2(src, dst, channel_mode=1, limit=1):
    successes = 0
    failures = 0
    print("test2: channel mode is", channel_mode)
    set_channel_mode(src, channel_mode)
    set_channel_mode(dst, channel_mode)
    query_channel_mode(src)
    query_channel_mode(dst)
    assert limit > 0
    
    try:
        while limit > 0:
            limit -= 1
            original = randbytes(randrange(1, 20))
            encoded = encode_porp(original)
            resp = src.send_packet(encoded)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == b'\x00'   # ack should be empty packet
            try:
                packet = dst.recv_incoming()
                data, metadata = decode_porp(packet)

                if data != original:
                    if len(data) != len(original):
                        print("*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("*** bit errors:", data, "!=", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
                    successes += 1
            except queue.Empty:
                print("*** timeout ***")
                failures += 1
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def set_channel_mode(porp, channelMode):
    return porp.send_packet(encode_command(6, channelMode.to_bytes(2, byteorder="little")))

def query_channel_mode(porp):
    reply = porp.send_packet(encode_command(8))
    data, metadata = decode_porp(reply)
#     print("data =", data, "metadata =", metadata, "metadata length =", len(metadata))
    if len(metadata) > 0:
        attrs = handle_metadata(metadata)
        print ("attrs =", attrs)

BaudRate = 57600

def run_test(dev1, dev2, test, *args):
    success_count = 0
    failure_count = 0

    with serial.Serial("/dev/tty"+dev1, BaudRate, timeout=0.5) as ser1:  # open serial port
        print("Serial port1 (src) =", ser1.name)         # print which port was really used
        with serial.Serial("/dev/tty"+dev2, BaudRate, timeout=0.5) as ser2:  # open serial port
            print("Serial port2 (dst) =", ser2.name)         # print which port was really used

            with ReaderThread(ser1, Porp) as src:  # reader thread to handle incoming packets
                with ReaderThread(ser2, Porp) as dst:  # reader thread to handle incoming packets
                    start_time = time.time()
                    good, bad =  test(src, dst, *args) # pass the trailing arguments to the test function
                    print("--- %s seconds ---" % (time.time() - start_time))
                    success_count += good
                    failure_count += bad

    print()
    print("sent      =", len(src.out_history))
    print("received  =", len(dst.in_history))
    print("successes =", success_count)
    print("failures  =", failure_count)
    assert not ser1.is_open # the serial port should have been automatically closed
    assert not ser2.is_open # the serial port should have been automatically closed
    return good, bad

num_modes = 12
usb0 = {}
usb1 = {}
mode_list = [6, 7]
# mode_list = range(2, num_modes, 1) 
# mode_list = range(0, 10, 1) 
repeats = 5
for mode in mode_list:
    usb0[mode] = run_test("USB0", "USB1", test2, mode, repeats)
    usb1[mode] = run_test("USB1", "USB0", test2, mode, repeats)

print("USB0 is src:", usb0)
print("USB1 is src:", usb1)
