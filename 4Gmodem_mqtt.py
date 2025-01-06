import serial
from serial.threaded import Packetizer, ReaderThread
import queue
from queue import Queue


with serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5) as ser1:  # open serial port
    pass
    #with ReaderThread(ser1, Porp) as src:  # reader thread to handle incoming packets
