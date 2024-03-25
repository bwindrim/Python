import serial
from serial.threaded import ReaderThread
import random
from random import randrange, randbytes
import time

import porp
from porp import Porp

# Ensure that we always generate the same "random" test data,
# for reproducability.
random.seed(0)

ACK  = b'\x00\x01\x00'

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

# Start of attribute IDs.
attAvgStrength = 96
attMinStrength = 97
attDetectedErrors = 98
attCodingMode = 99

metaString = {}
metaString[attAvgStrength] = "Average bit strength"
metaString[attMinStrength] = "Minimum bit strength"
metaString[attDetectedErrors] = "Num detected errors"
metaString[attCodingMode] = "Coding mode"

metaDecode = {}
metaDecode[attAvgStrength]    = lambda payload : str(int.from_bytes(payload, 'little'))
metaDecode[attMinStrength]    = lambda payload : str(int.from_bytes(payload, 'little'))
metaDecode[attDetectedErrors] = lambda payload : str(int.from_bytes(payload, 'little'))
metaDecode[attCodingMode]     = lambda payload : hex(int.from_bytes(payload, 'little'))

def print_metadata(attrs):
    for key in attrs.keys():
        print (metaString[key], "=", metaDecode[key](attrs[key]))


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
            # Strip any trailing newline(s) and convert text to bytes.
            original = bytes(line.rstrip('\n'), 'utf-8')
            encoded = porp.encode_packet(original)
            resp = src.send_packet(encoded)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK  # ack should be empty packet

            packet = dst.recv_incoming()
            
            if packet != None:
                data, metadata = porp.decode_packet(packet)

                if data != original:
                    if len(data) != len(original):
                        print("*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("*** bit errors: received", data, "!= sent", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
                    successes += 1
            else:
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
    assert limit > 0
    
    try:
        while limit > 0:
            limit -= 1
            original = randbytes(randrange(1, 20))
            encoded = porp.encode_packet(original)
            resp = src.send_packet(encoded)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK   # should be an ACK

            packet = dst.recv_incoming()
            
            if packet != None:
                data, metadata = porp.decode_packet(packet)

                if data != original:
                    if len(data) != len(original):
                        print("*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("*** bit errors:", data, "!=", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
                    successes += 1
            else:
                print("*** timeout ***")
                failures += 1
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def test3(src, dst, channel_mode=1, limit=1):
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
    assert limit > 0
    
    try:
        for val in [0x00, 0xFF]:
            original = bytes([val] * limit)
#             print("original =", original)
            encoded = porp.encode_packet(original)
            resp = src.send_packet(encoded, timeout=30)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK   # should be an ACK

            packet = dst.recv_incoming()
            
            if packet != None:
                data, metadata = porp.decode_packet(packet)

                if data != original:
                    if len(data) != len(original):
                        print("*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("*** bit errors:", data, "!=", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
                    successes += 1
            else:
                print("*** timeout ***")
                failures += 1
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def test4(src, dst, channel_mode=1, limit=1):
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
    assert limit > 0
    
    try:
        for bit in range(limit*4, limit*8):
            array = bytearray(limit)
            array[bit//8] ^= 0x1 << (bit % 8)
            original = bytes(array)
            print("bit", bit)
            encoded = porp.encode_packet(original)
            resp = src.send_packet(encoded, timeout=30)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK   # should be an ACK

            packet = dst.recv_incoming()
            
            if packet != None:
                data, metadata = porp.decode_packet(packet)

                if data != original:
                    if len(data) != len(original):
                        print("bit", bit, "*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("bit", bit, "*** bit errors:", data, "!=", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
                    successes += 1
            else:
                print("*** timeout ***")
                failures += 1
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def test5(src, dst, channel_mode=1, limit=1):
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
    assert limit > 0
    
    try:
        while limit > 0:
            limit -= 1
            original = randbytes(10)
            encoded = porp.encode_packet(original)
            resp = src.send_packet(encoded)
            if resp == None:
                print("Timeout on send")
            else:
                assert resp == ACK   # should be an ACK
            
            packet = dst.recv_incoming()
            
            if packet != None:
                data, metadata = porp.decode_packet(packet)

                if data != original:
                    if len(data) != len(original):
                        print("*** length missmatch:", data, "!=", original, "***")
                    else:
                        print("*** bit errors:", data, "!=", original, "*** count =", count_bit_errors(data,original))
                    failures += 1
                else:
                    print("metadata =", metadata)
                    attrs = porp.handle_metadata(metadata)
                    print_metadata (attrs)
                    successes += 1
            else:
                print("*** timeout ***")
                failures += 1
    except KeyboardInterrupt:
        pass
    
    return successes, failures

def auto_calibrate(porp, iterations=None):
    if iterations == None:
        reply = porp.send_packet(porp.encode_command(cmdAutoCalibrate), timeout=10)
    else:
        reply = porp.send_packet(porp.encode_command(cmdAutoCalibrate, iterations.to_bytes(2, byteorder='little')), timeout=10)
    print("auto_calibrate(), reply =", reply)
    data, metadata = porp.decode_packet(reply)
    if len(metadata) > 0:
        attrs = handle_metadata(metadata)
        print ("attrs =", attrs)
    return attrs[cmdAutoCalibrate]

def set_channel_mode(conn, channelMode):
    reply = conn.send_packet(porp.encode_command(cmdSetChannelMode, channelMode.to_bytes(2, byteorder="little")))
    assert reply == porp.encode_command(cmdSetChannelMode)
    return reply

def get_channel_mode(conn):
    reply = conn.send_packet(porp.encode_command(cmdGetChannelMode))
    data, metadata = porp.decode_packet(reply)
    if len(metadata) > 0:
        attrs = porp.handle_metadata(metadata)
        print ("attrs =", attrs)
    return attrs[cmdGetChannelMode]

def query_channel_mode(conn):
    reply = conn.send_packet(porp.encode_command(cmdQueryChannelMode))
    data, metadata = porp.decode_packet(reply)
    if len(metadata) > 0:
        attrs = porp.handle_metadata(metadata)
        print ("attrs =", attrs)
    return attrs[cmdQueryChannelMode]

def enable_coding_mode(conn, syncMarker):
    reply = conn.send_packet(porp.encode_command(cmdEnableRxCodingMode, syncMarker.to_bytes(4, byteorder="little")))
    if reply != porp.encode_command(cmdEnableRxCodingMode):
        print ("reply =", reply)
    assert reply == porp.encode_command(cmdEnableRxCodingMode)
    return reply
    
BaudRate = 57600

def run_test(dev1, dev2, test, *args):
    global success_count, failure_count
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

    print("sent      =", len(src.out_history))
    print("received  =", len(dst.in_history))
    assert not ser1.is_open # the serial port should have been automatically closed
    assert not ser2.is_open # the serial port should have been automatically closed
    return good, bad

success_count = 0
failure_count = 0
num_modes = 12
usb0 = {}
usb1 = {}
# mode_list = [12, 14]
mode_list = [i for i in range(0, num_modes, 2)]
# mode_list = range(0, 10, 1)
# mode_list = [14]
test_list = [test1, test2, test3, test4, test5]
repeats = 5
for test in test_list:
    for mode in mode_list:
        usb0[mode] = run_test("USB0", "USB1", test, mode, repeats)
        usb1[mode] = run_test("USB1", "USB0", test, mode, repeats)

print()
print("successes =", success_count)
print("failures  =", failure_count)

print("USB0 is src:", usb0)
print("USB1 is src:", usb1)
