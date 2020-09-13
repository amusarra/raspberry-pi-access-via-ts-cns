#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This Python script activate_de_activate_relay.py implements a relay activation and deactivation
mechanism through the TUI (Text-based User Interface).

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

import time

import RPi.GPIO as GPIO

# Dictionary of relationship between relay identification and BCM pin
dict_relay_bcm = {
    1: 23,
    2: 24,
    3: 25,
    4: 16
}


# Initialize the GPIO for the relay module
def initialize_relay():
    GPIO.setmode(GPIO.BCM)
    for relay_id, bcm_value in dict_relay_bcm.items():
        GPIO.setup(bcm_value, GPIO.OUT, initial=GPIO.HIGH)


# Activate the relay
def activate_relay(relay_id):
    if 1 <= relay_id <= 4:
        GPIO.output(dict_relay_bcm[relay_id], GPIO.LOW)

        print(f"Activate Relay {str(relay_id)}")


# De-Activate the relay
def de_activate_relay(relay_id):
    if 1 <= relay_id <= 4:
        GPIO.output(dict_relay_bcm[relay_id], GPIO.HIGH)

        print(f"DeActivate Relay {str(relay_id)}")


# CleanUp the resources
def cleanup():
    GPIO.cleanup()


try:
    initialize_relay()

    activate_relay(1)
    time.sleep(5)
    activate_relay(2)
    time.sleep(5)
    activate_relay(3)
    time.sleep(5)
    activate_relay(4)

    time.sleep(10)

    de_activate_relay(1)
    time.sleep(5)
    de_activate_relay(2)
    time.sleep(5)
    de_activate_relay(3)
    time.sleep(5)
    de_activate_relay(4)

except KeyboardInterrupt:
    print("Goodbye")
finally:
    cleanup()
