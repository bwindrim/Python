from sense_hat import SenseHat
sense = SenseHat()

yellow = (128, 128, 16)
blue = (16, 16, 128)

sense.set_rotation(180)

sense.show_message("Hello world", scroll_speed=0.2, back_colour=blue, text_colour=yellow)
sense.clear(blue)

