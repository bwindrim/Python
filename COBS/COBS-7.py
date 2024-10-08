from cobs import cobs
import serial
from serial.threaded import Packetizer, ReaderThread
import queue
from queue import Queue
import random
from random import randrange, randbytes
import time
import sys

# Ensure that we always generate the same "random" test data,
# for reproducability.
random.seed(0)

ACK  = b'\x00\x01\x00'
# NACK = b'\x00\x01\x01'

# Start of command/response IDs.
cmdGetVersionInfo = 32
cmdTransmitCW = 33
cmdTransmitOff = 34
cmdAutoCalibrate = 35
cmdGetThreshold = 36
cmdSetThreshold = 37
cmdGetChannelMode = 38
cmdSetChannelMode = 39
cmdGetRxGain = 40
cmdSetRxGain = 41
cmdGetControlBits = 64
cmdSetControlBits = 65
cmdEnableRxCodingMode = 66
cmdQueryChannelMode = 67
cmdGetRxVariance = 68
cmdSetRxScaling = 69

# Start of attribute IDs.
attAvgStrength = 96
attMinStrength = 97
attDetectedErrors = 98
attCodingMode = 99
attVariance = 100

metaString = {}
metaString[attAvgStrength] = "Average bit strength"
metaString[attMinStrength] = "Minimum bit strength"
metaString[attDetectedErrors] = "Num detected errors"
metaString[attCodingMode] = "Coding mode"
metaString[attVariance] = "Variance"

metaDecode = {}
metaDecode[attAvgStrength]    = lambda payload : str(int.from_bytes(payload, 'little'))
metaDecode[attMinStrength]    = lambda payload : str(int.from_bytes(payload, 'little'))
metaDecode[attDetectedErrors] = lambda payload : str(int.from_bytes(payload, 'little'))
metaDecode[attCodingMode]     = lambda payload : hex(int.from_bytes(payload, 'little'))
metaDecode[attVariance]       = lambda payload : str(float(int.from_bytes(payload, 'little'))/float(0xFFFF))

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

    def send_packet(self, packet, timeout=1):
        self.original = packet                 # store for comparison
        self.out_history.append(packet)        # store in the history list
        self.encoded = cobs.encode(packet)     # encode to COBS
#         print("encoded  =", self.encoded)
        self.transport.write(self.encoded+b'\x00') # append the packet delimiter
        try:
            response = self.responses.get(timeout=timeout) # wait for ACK
        except queue.Empty:
            print("send_packet(timeout=", timeout,"), timout")
            response = None
#         print("response =", response)
#         assert response == b'\x00'   # ack should be empty packet
        return response

    def recv_incoming(self, timeout=30):
        return self.incoming.get(timeout=timeout)
        
    def recv_response(self, timeout=1):
        return self.responses.get(timeout=timeout)
        
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

def print_metadata(attrs):
    for key in attrs.keys():
        print (metaString[key], "=", metaDecode[key](attrs[key]))
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
                        print("*** bit errors: received", data, "!= sent", original, "*** count =", count_bit_errors(data,original))
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
#     enable_coding_mode(src, 0x1ACFFC1D)
    set_channel_mode(src, channel_mode)
    set_channel_mode(dst, channel_mode)
    get_channel_mode(src)
    get_channel_mode(dst)
    query_channel_mode(src)
    query_channel_mode(dst)
#     auto_calibrate(src)
#     auto_calibrate(dst, 50)
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
                assert resp == ACK   # should be an ACK
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

def test3(src, dst, channel_mode=1, limit=1):
    successes = 0
    failures = 0
    print("test3: channel mode is", channel_mode)
#     enable_coding_mode(src, 0x1ACFFC1D)
    set_channel_mode(src, channel_mode)
    set_channel_mode(dst, channel_mode)
    get_channel_mode(src)
    get_channel_mode(dst)
    query_channel_mode(src)
    query_channel_mode(dst)
#     auto_calibrate(src)
#     auto_calibrate(dst, 50)
    assert limit > 0
    
    try:
        for val in [0x00, 0xFF]:
            original = bytes([val] * limit)
#             print("original =", original)
            encoded = encode_porp(original)
            resp = src.send_packet(encoded, timeout=30)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK   # should be an ACK
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

def test4(src, dst, channel_mode=1, limit=1):
    successes = 0
    failures = 0
    print("test4: channel mode is", channel_mode)
#     enable_coding_mode(src, 0x1ACFFC1D)
    set_channel_mode(src, channel_mode)
    set_channel_mode(dst, channel_mode)
    get_channel_mode(src)
    get_channel_mode(dst)
    query_channel_mode(src)
    query_channel_mode(dst)
#     auto_calibrate(src)
#     auto_calibrate(dst, 50)
    assert limit > 0
    
    try:
        for bit in range(limit*4, limit*8):
            array = bytearray(limit)
            array[bit//8] ^= 0x1 << (bit % 8)
            original = bytes(array)
#             original = bytes([val] * (limit-1)) + bytes([val ^ 0x1])
#             print("original =", original, "len =", len(original))
            print("bit", bit)
            encoded = encode_porp(original)
            resp = src.send_packet(encoded, timeout=30)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK   # should be an ACK
            try:
                packet = dst.recv_incoming()
                data, metadata = decode_porp(packet)

                if data != original:
                    if len(data) != len(original):
                        print("bit", bit, "*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("bit", bit, "*** bit errors:", data, "!=", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
                    successes += 1
            except queue.Empty:
                print("*** timeout ***")
                failures += 1
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def test5(src, dst, channel_mode=1, limit=1):
    successes = 0
    failures = 0
    print("test5: channel mode is", channel_mode)
#    enable_coding_mode(src, 0x1ACFFC1D)
#    enable_coding_mode(dst, 0x1ACFFC1D)
    set_channel_mode(src, channel_mode)
    set_channel_mode(dst, channel_mode)
    get_channel_mode(src)
    get_channel_mode(dst)
    query_channel_mode(src)
    query_channel_mode(dst)
#     auto_calibrate(src)
#     auto_calibrate(dst, 50)
    assert limit > 0
    
    try:
        while limit > 0:
            limit -= 1
            original = randbytes(10)
            encoded = encode_porp(original)
            resp = src.send_packet(encoded)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK   # should be an ACK
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
                    print("metadata =", metadata)
                    attrs = handle_metadata(metadata)
                    print_metadata (attrs)
                    successes += 1
            except queue.Empty:
                print("*** timeout ***")
                failures += 1
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def auto_calibrate(porp, iterations=None):
    if iterations == None:
        reply = porp.send_packet(encode_command(cmdAutoCalibrate), timeout=10)
    else:
        reply = porp.send_packet(encode_command(cmdAutoCalibrate, iterations.to_bytes(2, byteorder='little')), timeout=10)
    print("auto_calibrate(), reply =", reply)
    data, metadata = decode_porp(reply)
    if len(metadata) > 0:
        attrs = handle_metadata(metadata)
        print ("attrs =", attrs)
    return attrs[cmdAutoCalibrate]

def set_rx_gain(porp, rxGain):
    reply = porp.send_packet(encode_command(cmdSetRxGain, rxGain.to_bytes(2, byteorder="little")))
    assert reply == encode_command(cmdSetRxGain)
    return reply

def get_rx_gain(porp):
    reply = porp.send_packet(encode_command(cmdGetRxGain))
    data, metadata = decode_porp(reply)
    if len(metadata) > 0:
        attrs = handle_metadata(metadata)
        print ("attrs =", attrs)
    return attrs[cmdGetRxGain]

def set_channel_mode(porp, channelMode):
    reply = porp.send_packet(encode_command(cmdSetChannelMode, channelMode.to_bytes(2, byteorder="little")))
    assert reply == encode_command(cmdSetChannelMode)
    return reply

def get_channel_mode(porp):
    reply = porp.send_packet(encode_command(cmdGetChannelMode))
    data, metadata = decode_porp(reply)
    if len(metadata) > 0:
        attrs = handle_metadata(metadata)
        print ("attrs =", attrs)
    return attrs[cmdGetChannelMode]

def query_channel_mode(porp):
    reply = porp.send_packet(encode_command(cmdQueryChannelMode))
    data, metadata = decode_porp(reply)
    if len(metadata) > 0:
        attrs = handle_metadata(metadata)
        print ("attrs =", attrs)
    return attrs[cmdQueryChannelMode]

def enable_coding_mode(porp, syncMarker):
    reply = porp.send_packet(encode_command(cmdEnableRxCodingMode, syncMarker.to_bytes(4, byteorder="little")))
    if reply != encode_command(cmdEnableRxCodingMode):
        print ("reply =", reply)
    else:
        print("Enable coding mode returned success")
    assert reply == encode_command(cmdEnableRxCodingMode)
    return reply
    
def set_scaling(porp, scaling=-1):
    if scaling < 0: # send with no argument == reset to default
        reply = porp.send_packet(encode_command(cmdSetRxScaling))
    else:
        reply = porp.send_packet(encode_command(cmdSetRxScaling, scaling.to_bytes(2, byteorder="little")))
    assert reply == encode_command(cmdSetRxScaling)
    return reply

BaudRate = 57600

def run_test(dev1, dev2, test, *args):
    global success_count, failure_count
    with serial.Serial(dev1, BaudRate, timeout=0.5) as ser1:  # open serial port
        print("Serial port1 (src) =", ser1.name)         # print which port was really used
        with serial.Serial(dev2, BaudRate, timeout=0.5) as ser2:  # open serial port
            print("Serial port2 (dst) =", ser2.name)         # print which port was really used

            with ReaderThread(ser1, Porp) as src:  # reader thread to handle incoming packets
                with ReaderThread(ser2, Porp) as dst:  # reader thread to handle incoming packets
                    set_scaling(src) # reset scaling to default
                    set_scaling(dst) # reset scaling to default
                    set_rx_gain(src, 40)
                    set_rx_gain(dst, 40)
                    enable_coding_mode(src, 0x1ACFFC1D)
                    enable_coding_mode(dst, 0x1ACFFC1D)
                    start_time = time.time()
                    good, bad =  test(src, dst, *args) # pass the trailing arguments to the test function
                    print("--- %s seconds ---" % (time.time() - start_time))
                    success_count += good
                    failure_count += bad

    print("sent      =", len(src.out_history))
    print("received  =", len(dst.in_history))
#     print("sent      =", src.out_history)
#     print("received  =", dst.in_history)
    assert not ser1.is_open # the serial port should have been automatically closed
    assert not ser2.is_open # the serial port should have been automatically closed
    return good, bad

success_count = 0
failure_count = 0
num_modes = 12
usb0 = {}
usb1 = {}
# mode_list = [12, 13, 14, 15]
mode_list = [i for i in range(0, num_modes, 1)]
# mode_list = range(1, 11, 2)
# mode_list = range(12)
# mode_list = [1]
repeats = 5
for mode in mode_list:
    usb0[mode] = run_test(sys.argv[1], sys.argv[2], test5, mode, repeats)
    usb1[mode] = run_test(sys.argv[2], sys.argv[1], test5, mode, repeats)

print()
print("successes =", success_count)
print("failures  =", failure_count)

print("USB0 is src:", usb0)
print("USB1 is src:", usb1)
