"""
Get yourself a cat fact over 4G!
"""

import lte
import time
import requests
from machine import Pin, UART

MOBILE_APN = "iot.1nce.net"

# Initialize the LTE connection
con = lte.LTE(MOBILE_APN,
              uart=UART(0, tx=Pin(16, Pin.OUT), rx=Pin(17, Pin.IN)),
              reset_pin=Pin(18, Pin.OUT),
              netlight_pin=Pin(19, Pin.IN),
              netlight_led=Pin(25, Pin.OUT)
              )

con.start_ppp()

try:
    t_start = time.time()
    request = requests.get('http://catfact.ninja/fact').json()
    fact = request['fact']
    print(f'Cat fact: {fact}')

finally:
    t_end = time.time()

    print(f"Took: {t_end - t_start} seconds")

    print("Disconnecting...")
    con.stop_ppp()
    print("Done!")

