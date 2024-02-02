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
from math import sin, cos, pi

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
# for pin in StepPins:
#     pig.set_mode(pin, pigpio.OUTPUT)
#     pig.write(pin, 0)


def subShade(pos):
    ""
    return 2*abs(1.0 - 2.0*pos) - 1.0

def subShade2(pos):
    ""
    assert(pos >= 0.0)
    assert(pos < 1.0)
    val = cos(4*pi*pos)/2.0 + 0.5
    if pos < 0.25:
        return val
    elif pos < 0.75:
        return -val
    else:
        return val

def subShade3(pos):
    ""
    assert(pos >= 0.0)
    assert(pos < 1.0)
    val = sin(4*pi*pos)/2.0 + 0.5
    if pos < 0.5:
        return val
    else:
        return -val

def shader(rev):
    "TBD"
    posA = rev % 1.0 # pos is fractional part of revolution
    posB = (rev + 0.25) % 1.0
    phaseA = subShade2(posA)
    phaseB = subShade2(posB)
#    print(posA, subShade(posA),phaseA)
    return [max(0.0, phaseA),
            max(0.0, phaseB),
            max(0.0, -phaseA),
            max(0.0, -phaseB)]


StepDir = 1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

# Read wait time from command line
if len(sys.argv)>1:
  rateHz = int(sys.argv[1])
else:
  rateHz = 4000

# Initialise variables
rotation = 0.0
pwm = PWM(pig, frequency=50000) # 50KHz = 20us/cycle
rpm = 10.0 # output shaft revolutions per minute
rps = rpm*16.032/60 # inner motor revolutions per second (1/16.032 gearing)
cps = rps*32.0 # step cycles per second (32 cycles per inner motor revolution)
rotStep = cps/rateHz # fraction of a cycle per iteration
print("rotStep =", rotStep, "StepDir/32 =", StepDir/32.0)
try:
    print("Running, WaitTime = ", 1.0/rateHz, "s, rate =", rateHz, "Hz")
    # Start main loop
    while rotation < 8*16.032:
#        shader(rotation)
#        print(shader(rotation))
        for pin, value in zip(StepPins, shader(rotation)):
            pwm.set_pulse_length_in_micros(pin, int(value*20))
        rotation += StepDir/64.0
#        rotation += rotStep
        pwm.update() # Apply all the changes
        # Wait before moving on
        time.sleep(1.0/rateHz)
except KeyboardInterrupt:
    pass
pwm.cancel()
for pin in StepPins:
    pig.write(pin, 0)
pig.stop()
print ("Done.")
    
