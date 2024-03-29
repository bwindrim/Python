import time
from sense_hat import SenseHat
from math import sin, radians, fabs, pow, ceil

BLACK   = (0.0, 0.0, 0.0)
WHITE   = (1.0, 1.0, 1.0)
RED     = (1.0, 0.0, 0.0)
GREEN   = (0.0, 1.0, 0.0)
BLUE    = (0.0, 0.0, 1.0)
YELLOW  = (1.0, 1.0, 0.0)
CYAN    = (0.0, 1.0, 1.0)
MAGENTA = (1.0, 0.0, 1.0)

# Configure the number of WS2812 LEDs, pins and brightness.
NUM_PIXELS = 64 
np = [BLACK] * NUM_PIXELS

g_gamma = 1.0
g_brightness = 255.0*pow(1.0, g_gamma) # global brightness setting, range 0.0 - 255.0

# def hue_to_rgb(h):
#     r =       abs(h * 6.0 - 3.0) - 1.0
#     g = 2.0 - abs(h * 6.0 - 2.0)
#     b = 2.0 - abs(h * 6.0 - 4.0)
# #    return saturate(r), saturate(g), saturate(b)
#     return max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b))

def hsl_to_rgb(h, s, l):
    # calculate r, g, &b weightings from hue
    r =       abs(h * 6.0 - 3.0) - 1.0
    g = 2.0 - abs(h * 6.0 - 2.0)
    b = 2.0 - abs(h * 6.0 - 4.0)
    # clamp the weightings to the normalised range (0-1)
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    # apply saturation and luminance to the colour mix
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    r = (r - 0.5) * c + l
    g = (g - 0.5) * c + l
    b = (b - 0.5) * c + l
    return (r, g, b)

def gamma(encoded):
    return (ceil(pow(encoded[0], g_gamma)*g_brightness),
            ceil(pow(encoded[1], g_gamma)*g_brightness),
            ceil(pow(encoded[2], g_gamma)*g_brightness))

# Fixed gamma 2.0 function - doesn't save much time wrt. gamma()
def gamma_2(encoded):
    return (ceil(encoded[0]*encoded[0]*g_brightness),
            ceil(encoded[1]*encoded[1]*g_brightness),
            ceil(encoded[2]*encoded[2]*g_brightness))

def shader_rgb1(time, x, y):
    # treat time in seconds as degrees of angle
#    assert(y == 0)
    angle = radians(time + x)*6.0 # map 60 seconds to full circle
    return ((1.0 + sin(angle*1.0))/2, (1.0 + sin(-angle*2.0))/2, (1.0 + sin(angle*3.0))/2)

def shader_hsl1(time, x, y):
    # hue ranges from 0 to 1 over the course of a minute, then wraps
    hue = (time + x) % 8.0 / 8.0
    sat = (1.0 + y) / 16.0
    return hsl_to_rgb(hue, 1.0, sat)

def shader_hsl2(time, x, y):
    # saturation ranges from 0 to 1 over the course of a minute, then wraps
    s = time % 60.0 / 60.0
    return hsl_to_rgb(2/3, s, x/59.0)

def shader_hsl3(time, x, y):
    # hue ranges from 0 to 1 over the course of a minute, then wraps
#    print("x =", x, "y =", y)
    hue = (time*20 + x) % 15.0 / 15.0
    return hsl_to_rgb(hue, 1.0, (y + 1) / 8)

def grayscale1(time, x, y): # grey ramp
    return ((x / 59.0), (x / 59.0), (x / 59.0))

def render(shader, gamma, time, width, height=1):
#    print("time =", time)
    for i, c in enumerate(shader(time, x, y) for y in range(height) for x in range(width)):
        np[i] = gamma(c)
        
sense = SenseHat()

start = time.time()*1000.0 # get millisecond counter
loop_prev = start
render_max = 0
while True:
    loop_start = time.time()*1000.0
    delta = (loop_start - start)/1000.0 # compute time difference in seconds
    #print("delta =", delta)
    loop_prev = loop_start
    render(shader_hsl1, gamma, delta, 8, 8)
    sense.set_pixels(np)
    render_time = time.time()*1000.0 - loop_start
    if render_time > render_max:
        render_max = render_time
        print("render time =", render_time, "ms")
        pressure = sense.get_pressure()
        print(pressure)
#    assert(render_time < 65)
   # time.sleep_ms(100 - render_time)

