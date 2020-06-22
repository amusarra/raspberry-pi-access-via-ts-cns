#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This Python script test_keypad_pin_lcd.py check if the the PIN code that inserted with the key pad
it's correct and display the instructions on the LCD 16x2 display.

MIT License

Raspberry Pi - Access via Smart Card TS-CNS

Copyright (c) 2020 Antonio Musarra's Blog - https://www.dontesta.it

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in the
Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__ = "Antonio Musarra"
__copyright__ = "Copyright 2020 Antonio Musarra's Blog"
__credits__ = ["Antonio Musarra"]
__version__ = "1.0.0"
__license__ = "MIT"
__maintainer__ = "Antonio Musarra"
__email__ = "antonio.musarra@gmail.com"
__status__ = "Development"

from pad4pi import rpi_gpio
from modules.PCF8574 import PCF8574_GPIO
from modules.Adafruit_LCD1602 import Adafruit_CharLCD

import time
import sys

# Check I2C address via command i2cdetect -y 1
PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.

# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print("I2C Address Error !")
        exit(1)

# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], GPIO=mcp)

KEYPAD = [
    [1, 2, 3, "A"],
    [4, 5, 6, "B"],
    [7, 8, 9, "C"],
    ["*", 0, "#", "D"]
]

ROW_PINS = [18, 12, 20, 21]  # BCM numbering
COL_PINS = [10, 22, 27, 17]  # BCM numbering

entered_pin = ""
correct_pin = "1234"


# CleanUp the resources
def cleanup():
    global keypad

    lcd.clear()
    lcd.message("Goodbye...\n")
    lcd.backlight = False
    keypad.cleanup()


# Check entered PIN code
def check_pin(key):
    global entered_pin, correct_pin

    if len(entered_pin) == len(correct_pin) or key == "#":
        if entered_pin == correct_pin:
            correct_pin_entered()
        else:
            incorrect_pin_entered()


# Display info on corrected PIN code and exit
def correct_pin_entered():
    lcd.clear()
    lcd.message("Access granted\n")
    lcd.message("Accepted PIN\n")

    print("PIN accepted. Access granted.")

    time.sleep(5)
    cleanup()
    sys.exit()


# Construct the entered PIN code
def digit_entered(key):
    global entered_pin, correct_pin

    entered_pin += str(key)
    print(entered_pin)

    lcd.clear()
    lcd.message("PIN: " + entered_pin + "\n")
    lcd.message("# to confirm")

    check_pin(key)


# Display info on in-corrected PIN code and exit
def incorrect_pin_entered():
    lcd.clear()
    lcd.message("Access denied\n")
    lcd.message("Incorrect PIN\n")

    print("Incorrect PIN. Access denied.")

    time.sleep(5)
    cleanup()
    sys.exit()


# Initialize the I2C LCD 1602 Display
def initialize_lcd():
    mcp.output(3, 1)  # turn on LCD backlight
    lcd.begin(16, 2)  # set number of LCD lines and columns

    lcd.message("Enter your PIN\n")
    lcd.message("Press * to clear")


# Manage no PIN code key
def non_digit_entered(key):
    global entered_pin

    if key == "*" and len(entered_pin) > 0:
        entered_pin = entered_pin[:-1]

        lcd.clear()
        lcd.message("PIN: " + entered_pin + "\n")
        lcd.message("# to confirm")

        print(entered_pin)

    if key == "#" and len(entered_pin) > 0:
        check_pin(key)


# Press handler key
def key_pressed(key):
    try:
        int_key = int(key)
        if 0 <= int_key <= 9:
            digit_entered(key)
    except ValueError:
        non_digit_entered(key)


try:
    factory = rpi_gpio.KeypadFactory()
    keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

    keypad.registerKeyPressHandler(key_pressed)

    initialize_lcd()

    print("Enter your PIN:")
    print("Press * to clear previous digit.")
    print("Press # to confirm.")

    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Goodbye")
finally:
    cleanup()
