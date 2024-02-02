import sys
import time
import subprocess
import RPi.GPIO as GPIO
from datetime import datetime

# Use BCM GPIO references instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# Define GPIO signals to use
battery = [6,12,13,26]

GPIO.setup(battery, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def piwatcher_status():
    "Query PiWatcher to reset watchdog timer"
    result = subprocess.run(["/usr/local/bin/piwatcher", "status"], capture_output=True)
    print("PiWatcher status =", result)
    
def piwatcher_wake(seconds):
    "Set the wake interval for PiWatcher"
    result = subprocess.run(["/usr/local/bin/piwatcher", "wake", str(seconds)], capture_output=True)
    print("PiWatcher wake =", result)
    
def piwatcher_watch(seconds):
    "Set the watchdog timeout interval for PiWatcher"
    #result = "not run"
    result = subprocess.run(["/usr/local/bin/piwatcher", "watch", str(seconds)], capture_output=True)
    print("PiWatcher watch =", result)
    
def system_shutdown():
    "Shut down the system"
    print("Shutting down")
    subprocess.run(["/usr/sbin/shutdown", "now"])
    
def getBatteryLevel(numReads):
    "Read the battery level via the GPIOs"
    
    level = 0

    for i in range(numReads):
        for pin in battery:
            level += (1 - GPIO.input(pin))

    return level

def hours(num):
    "Returns the duration in seconds of the specified number of hours"
    return num*60*60

# main program 
try:
    # Set a default wakeup of 4 hours. This will apply if the system is
    # forcibly restarted by the watchdog.
    piwatcher_wake(60) #(hours(4))
    piwatcher_watch(120)     # set 2-minute watchdog timeout
    
    while True:
        piwatcher_status()  # reset the watchdog

        level = 60 # getBatteryLevel(20)
        
        if level <= 20: # 1 battery bar or less
            # battery is critically low, shut down for 24 hours,
            # don't stop to take pictures
            piwatcher_wake(hours(24))
            system_shutdown()
        elif level <= 40: # 2 battery bars
            # battery is low, shut down for 6 hours but take a photo first
            piwatcher_wake(hours(6))
            system_shutdown()
        elif level <= 60: # 3 battery bars
            # battery is adequate, shut down for 24 hours
            piwatcher_wake(60)
            system_shutdown()
            
        time.sleep(30) # sleep interval shouldn't be longer than half the watchdog time
        
except KeyboardInterrupt:
    piwatcher_watch(0) # disable the watchdog
    print ("Done.")
    GPIO.cleanup()
