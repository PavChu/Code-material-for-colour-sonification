# Write your code here :-)
from microbit import *
import math

# Initialise all the necessary sensor variables.
i2c.write(0x29, b'\x81\xF6', repeat=False)  # Set integrationtime to 24ms.
i2c.write(0x29, b'\x8F\x00', repeat=False)  # Set gain of the sensor to 1X.
i2c.write(0x29, b'\x80\x01', repeat=False)  # Turn the sensor on.
i2c.write(0x29, b'\x80\x03', repeat=False)  # Activate the ADC.
###########################################

# Function to send MIDI data through cable (Transmission the data through pin0)
def Start():
    uart.init(baudrate=31250, bits=8, parity=None, stop=1, tx=pin0)
###########################################

""" Function to convert raw data (RGB) to Kelvin (function licensed by MIT)
    Function was taken from
    https://github.com/adafruit/Adafruit_Python_TCS34725/blob/master/Adafruit_TCS34725/TCS34725.py """

def calculate_color_temperature(r, g, b):
    """Converts the raw R/G/B values to color temperature in degrees Kelvin."""
    # 1. Map RGB values to their XYZ counterparts.
    # Based on 6500K fluorescent, 3000K fluorescent
    # and 60W incandescent values for a wide range.
    # Note: Y = Illuminance or lux
    X = (-0.14282 * r) + (1.54924 * g) + (-0.95641 * b)
    Y = (-0.32466 * r) + (1.57837 * g) + (-0.73191 * b)
    Z = (-0.68202 * r) + (0.77073 * g) + (0.56332 * b)
    # Check for divide by 0 (total darkness) and return None.
    if (X + Y + Z) == 0:
        return None
    # 2. Calculate the chromaticity co-ordinates
    xc = (X) / (X + Y + Z)
    yc = (Y) / (X + Y + Z)
    # Check for divide by 0 again and return None.
    if (0.1858 - yc) == 0:
        return None
    # 3. Use McCamy's formula to determine the CCT
    n = (xc - 0.3320) / (0.1858 - yc)
    # Calculate the final CCT
    cct = (449.0 * (n ** 3.0)) + (3525.0 * (n ** 2.0)) + (6823.3 * n) + 5520.33
    return int(cct)
###########################################

# Declare a function of MIDI Control Change (CC) event.
def midiControlChange(chan, n, value):
    MIDI_CC = 0xB0
    if chan > 15:
        return
    if n > 127:
        return
    if value > 127:
        return
    msg = bytes([MIDI_CC | chan, n, value])
    uart.write(msg)
###########################################

Start()
last_ligh = 0  # Initialise a variable with initial value for light sensor.
last_pot = 0  # Innitialise a variable with initial value for potentiometer.
last_tem = 0  # Initialise a variable with initial value for RGB sensor.
while True:
    i2c.write(0x29, b'\x96', repeat=False)  # Point to red channel register.
    rr = i2c.read(0x29, 1, repeat=False)  # Read one byte from red channel.

    i2c.write(0x29, b'\x98', repeat=False)  # Point to green channel register.
    gg = i2c.read(0x29, 1, repeat=False)  # Read one byte from green channel.

    i2c.write(0x29, b'\x9A', repeat=False)  # Point to blue channel register.
    bb = i2c.read(0x29, 1, repeat=False)  # Read one byte from blue channel.

    # Once we get the raw data stored in rr, gg, bb variables, send them to function.
    # Send RGB raw data [8-bit (0-255)] to the converter function in order to
    # convert them into degrees Kelvin.

    temp = calculate_color_temperature(float(rr[0]), float(gg[0]), float(bb[0]))
    ###########################################

    # Scale the degrees Kelvin value to a number between 0 and 127 and send its value through MIDI CC event.
    if last_tem != temp:  # Compare the current value with the last reading.
        temper = math.floor(math.fabs((temp + 40000) / 80000) * 127)
        midiControlChange(0, 24, temper)
    last_tem = temp  # Set the last reading variable to the value of the current reading.

    # Scale the value from potentiometer to a number between 0 and 127 and send its value through MIDI CC event.
    pot = pin2.read_analog()  # Read the potentiometer value from pin2
    if last_pot != pot:
        velocity = math.floor(pot / 1024 * 127)
        midiControlChange(0, 23, velocity)
    last_pot = pot  # Set the last reading variable to the value of the current reading.

    # Scale the value from light sensor to a number between 0 and 127 and send its value through MIDI CC event.
    current_ligh = display.read_light_level()  # Read the light level value.
    if current_ligh != last_ligh:
        mod_y = math.floor(current_ligh / 255 * 127)
        midiControlChange(0, 22, mod_y)
        last_ligh = current_ligh  # Set the last reading variable to the value of the current reading.
    sleep(40)  # Sleep for 40ms and repeat the while loop