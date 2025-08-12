#!/usr/bin/python
#--------------------------------------
#    ___  ___  _ ____          
#   / _ \/ _ \(_) __/__  __ __ 
#  / , _/ ___/ /\ \/ _ \/ // / 
# /_/|_/_/  /_/___/ .__/\_, /  
#                /_/   /___/   
#
#    Stepper Motor Test
#
# A simple script to control
# a stepper motor.
#
# Author : Matt Hawkins
# Date   : 28/09/2015
#
# http://www.raspberrypi-spy.co.uk/
#
#--------------------------------------

# Import required libraries
import sys
import time
import RPi.GPIO as GPIO

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# Define GPIO signals to use
# Physical pins 11,15,16,18
# GPIO17,GPIO22,GPIO23,GPIO24
StepPins = [[17,18,27,22], # motor 0
            [4,25,24,23], # motor 1
            [5,6,12,13], # motor 2 (reversed)
            [19,16,26,20]] # motor 3 (reversed)

for pins in StepPins:
    # Set all pins as output
    GPIO.setup(pins, GPIO.OUT)
    # and set to off
    GPIO.output(pins, False)

# Define advanced sequence
# as shown in manufacturers datasheet
Seq = [[1,0,0,1],
       [1,0,0,0],
       [1,1,0,0],
       [0,1,0,0],
       [0,1,1,0],
       [0,0,1,0],
       [0,0,1,1],
       [0,0,0,1]]
       
StepCount = len(Seq)
StepDir = -1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

# Read wait time from command line
if len(sys.argv)>1:
  WaitTime = int(sys.argv[1])/float(1000)
else:
  WaitTime = 2/float(1000)

# Initialise variables
StepCounter = 0

try:
    print("Running, WaitTime = ", WaitTime, "s")
    # Start main loop
    while True:

        #print (StepCounter)
        #print (Seq[StepCounter])

        for pins in StepPins:
            GPIO.output(pins, Seq[StepCounter])
        #      StepCounter += StepDir

        # If we reach the end of the sequence
        # start again
        StepCounter = (StepCounter + StepDir) % StepCount

        # Wait before moving on
        time.sleep(WaitTime)
except KeyboardInterrupt:
    print ("Done.")
    GPIO.cleanup()
    