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
import pigpio
from wavePWM import PWM

#import gpiozero

# Use BCM GPIO references
# instead of physical pin numbers
#GPIO.setmode(GPIO.BCM)

# Connect to pigpiod daemon
pig = pigpio.pi()
#pig = pigpio.pi("bullseye32lite")


# Define GPIO signals to use
# Physical pins 11,15,16,18
# GPIO17,GPIO22,GPIO23,GPIO24
StepPins = [17,18,27,22] # motor 0
#StepPins = [4,25,24,23] # motor 1
#StepPins = [13,12,6,5] # motor 2
#StepPins = [20,26,16,19] # motor 3

# Set all pins as output
# and set to off
for pin in StepPins:
    pig.set_mode(pin, pigpio.OUTPUT)
    pig.write(pin, 0)

# Define advanced sequence
# as shown in manufacturers datasheet
ON = 1
Seq = [[ON,0,0,ON],
       [ON,0,0,0],
       [ON,ON,0,0],
       [0,ON,0,0],
       [0,ON,ON,0],
       [0,0,ON,0],
       [0,0,ON,ON],
       [0,0,0,ON]]
       
StepCount = len(Seq)
StepDir = -1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

# Read wait time from command line
if len(sys.argv)>1:
  WaitTime = int(sys.argv[1])/float(1000)
else:
  WaitTime = 10/float(1000)

# Initialise variables
StepCounter = 0

pwm = PWM(pig) # Use default frequency
pwm.set_frequency(10000)

try:
    print("Running, WaitTime = ", WaitTime, "s")
    # Start main loop
    while True:
        #print (StepCounter)
        #print (Seq[StepCounter])

        for pin, value in zip(StepPins, Seq[StepCounter]):
            pwm.set_pulse_length_in_fraction(pin, value)
            #pig.write(pin, value)
        #      StepCounter += StepDir

        # If we reach the end of the sequence
        # start again
        StepCounter = (StepCounter + StepDir) % StepCount

        pwm.update() # Apply all the changes
        
        # Wait before moving on
        time.sleep(WaitTime)
except KeyboardInterrupt:
    print ("Done.")
    for pin in StepPins:
        pig.write(pin, 0)
    pig.stop()
    
