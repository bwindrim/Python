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
# for pin in StepPins:
#     pig.set_mode(pin, pigpio.OUTPUT)
#     pig.write(pin, 0)

# Define advanced sequence
# as shown in manufacturers datasheet
FULL = 1.0
TQTR = 0.75
HALF = 0.5
OQTR = 0.25
OFF  = 0.0
ON = FULL
# Seq = [[FULL,OFF, OFF, FULL],
#        [FULL,OFF, OFF, OFF ],
#        [FULL,FULL,OFF, OFF ],
#        [OFF, FULL,OFF, OFF ],
#        [OFF, FULL,FULL,OFF ],
#        [OFF, OFF, FULL,OFF ],
#        [OFF, OFF, FULL,FULL],
#        [OFF, OFF, OFF, FULL]]
       
# Seq = [[HALF,OFF, OFF, HALF],
#        [FULL,OFF, OFF, OFF ],
#        [HALF,HALF,OFF, OFF ],
#        [OFF, FULL,OFF, OFF ],
#        [OFF, HALF,HALF,OFF ],
#        [OFF, OFF, FULL,OFF ],
#        [OFF, OFF, HALF,HALF],
#        [OFF, OFF, OFF, FULL]]
       
Seq = [[HALF,OFF, OFF, HALF], # 0.0
       [TQTR,OFF, OFF, OQTR], # 0.0625
       [FULL,OFF, OFF, OFF ], # 0.125
       [TQTR,OQTR,OFF, OFF ], # 0.1875
       [HALF,HALF,OFF, OFF ], # 0.25
       [OQTR,TQTR,OFF, OFF ], # 0.3125
       [OFF, FULL,OFF, OFF ], # 0.375
       [OFF, TQTR,OQTR,OFF ], # 0.4375
       [OFF, HALF,HALF,OFF ], # 0.5
       [OFF, OQTR,TQTR,OFF ], # 0.5625
       [OFF, OFF, FULL,OFF ], # 0.625
       [OFF, OFF, TQTR,OQTR], # 0.6875
       [OFF, OFF, HALF,HALF], # 0.75
       [OFF, OFF, OQTR,TQTR], # 0.8125
       [OFF, OFF, OFF, FULL], # 0.875
       [OQTR,OFF, OFF, TQTR]  # 0.9375
       ]
MiniSeq = [
    FULL,
    TQTR,
    HALF,
    OQTR,
    OFF,
    -OQTR,
    -HALF,
    -TQTR,
    -FULL,
    -TQTR,
    -HALF,
    -OQTR,
    OFF,
    OQTR,
    HALF,
    TQTR
    ]

def subShade(pos):
    ""
#    ipos = int(pos)
#    return max(0, inv*MiniSeq[(ipos + n) % 16])
#     pos = (pos + n/16.0) % 1.0
#     slope = 1.0 - 2.0*pos
#     vline = abs(slope)
#     deepv = 2.0*vline - 1.0
#     ideepv = inv*deepv
#     val = max(0.0, ideepv)
#    return val
    return -1.0 + 2*abs(1.0 - 2.0*pos)

def shader(rev):
    "TBD"
    posA = rev % 1.0 # pos is fractional part of revolution
    posB = (rev + 0.25) % 1.0
    phaseA = subShade(posA)
    phaseB = subShade(posB)
    return [max(0.0, phaseA),
            max(0.0, phaseB),
            max(0.0, -phaseA),
            max(0.0, -phaseB)]


StepCount = len(Seq)
StepDir = 1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

# Read wait time from command line
if len(sys.argv)>1:
  rateHz = int(sys.argv[1])
else:
  rateHz = 4000

#WaitTime = 1.0/rateHz

# Initialise variables
#StepCounter = 0
rotCount = 0.0
pwm = PWM(pig, frequency=50000) # 50KHz = 20us/cycle

try:
    print("Running, WaitTime = ", 1.0/rateHz, "s, rate =", rateHz, "Hz")
    # Start main loop
    while True:
        #print (StepCounter)
        #print (Seq[StepCounter])

#        print(shader(rotCount))
        for pin, value in zip(StepPins, shader(rotCount)):
            pwm.set_pulse_length_in_micros(pin, int(value*20))
            #print("pin =", pin, "value =", value)
            #pig.write(pin, value)
        #      StepCounter += StepDir

        # If we reach the end of the sequence
        # start again
#        StepCounter = (StepCounter + StepDir) % StepCount
#        rotCount += 0.0625*StepDir
        rotCount += 0.03125*StepDir
        
        pwm.update() # Apply all the changes
        
        
        # Wait before moving on
        time.sleep(1.0/rateHz)
except KeyboardInterrupt:
    pwm.cancel()
    for pin in StepPins:
        pig.write(pin, 0)
    pig.stop()
    print ("Done.")
    
