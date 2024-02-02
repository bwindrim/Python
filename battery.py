import sys
import time
import RPi.GPIO as GPIO
from datetime import datetime

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# Define GPIO signals to use
battery = [6,12,13,26]

GPIO.setup(battery, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def getBatteryLevel(numReads):
    "Read the battary level via the GPIOs"
    
    level = 0

    for i in range(numReads):
        for pin in battery:
            level += (1 - GPIO.input(pin))

    return level

state = []
for pin in battery:
    state.append(GPIO.input(pin))
print ("state = ", state)

print("battery 1 (GPIO6)  = ", not GPIO.input(6))
print("battery 2 (GPIO12) = ", not GPIO.input(12))
print("battery 3 (GPIO13) = ", not GPIO.input(13))
print("battery 4 (GPIO26) = ", not GPIO.input(26))
 
try:
    prevLevel = 100
    while True:
        level = getBatteryLevel(20)
        
        if level < prevLevel:
            # datetime object containing current date and time
            now = datetime.now()

            # dd/mm/YY H:M:S
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

            print ("level = ", level, "at", dt_string)
            prevLevel = level
            
        time.sleep(5)
except KeyboardInterrupt:
    print ("Done.")
GPIO.cleanup()
