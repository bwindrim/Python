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
import asyncio
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

# Define half-stepping sequence
Seq = [[1,0,0,1],
       [1,0,0,0],
       [1,1,0,0],
       [0,1,0,0],
       [0,1,1,0],
       [0,0,1,0],
       [0,0,1,1],
       [0,0,0,1]]

StepCount = len(Seq)
StepDir = 1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

# Read wait time from command line
if len(sys.argv)>1:
  WaitTime = int(sys.argv[1])/float(1000)
else:
  WaitTime = 2/float(1000)

async def stepper_task(pins, name, wait_time, step_dir):
    step_counter = 0
    print(f"Starting {name}, WaitTime = {wait_time}s")
    while True:
        GPIO.output(pins, Seq[step_counter])
        step_counter = (step_counter + step_dir) % StepCount
        await asyncio.sleep(wait_time)

async def main():
    tasks = [
        asyncio.create_task(stepper_task(StepPins[0], "motor 0", WaitTime, -2)),
        asyncio.create_task(stepper_task(StepPins[1], "motor 1", WaitTime, 2)),
        asyncio.create_task(stepper_task(StepPins[2], "motor 2", WaitTime, 2)),
        asyncio.create_task(stepper_task(StepPins[3], "motor 3", WaitTime, -2)),
    ]
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Done.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
