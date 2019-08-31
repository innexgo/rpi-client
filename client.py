#!/usr/bin/env python

from time import sleep
import sys
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
    while True:
        id, text = reader.read()
        print(id)
except KeyboardInterrupt:
    GPIO.cleanup()
    raise
