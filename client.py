#!/usr/bin/env python

import os
import sys
import time
import mfrc522
import requests
import RPi.GPIO as GPIO

# Load the config file
with open('/boot/innexgo-client.json') as configfile:
    config = json.load(configfile)

    apiKey = config['apiKey']
    hostname = config['hostname']
    locationId = config['locationId']


    # now we can get scanning
    reader = mfrc522.MFRC522()

    try:
        while True:
            (detectstatus, tagtype) = reader.MFRC522_Request(reader.PICC_REQIDL)
            if detectstatus == reader.MI_OK:
                (uidstatus, uid) = reader.MFRC522_Anticoll()
                if uidstatus == reader.MI_OK:
                    print(uid[0], uid[1], uid[2], uid[3])

                time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
