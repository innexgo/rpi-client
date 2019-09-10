#!/usr/bin/env python

import os
import sys
import time
import json
import mfrc522
import requests
import operator
import threading
import RPi.GPIO

courses = None
periods = None

apiKey = None
hostname = None
locationId = None

currentPeriod = None
currentCourse = None

def currentMillis():
    return round(1000 * time.time())

# setInterval for python
def setInterval(func, sec):
    def func_wrapper():
        setInterval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


updateInfo():
    global currentCourse
    global currentPeriod

    millis = currentMillis()
    currentPeriod = periods.filter(lambda p : p['initialTime'] > millis)
                           .sort(


def updateInfoInfrequent():
    global periods
    global courses
    courses = json.loads(requests.get(hostname + 'course/' +
                                             '?locationId='+locationId +
                                             '&count=20' +
                                             '&apiKey='+apiKey).json())

    periods = json.loads(requests.get(hostname + 'period/' +
                                             '?initialTimeBegin=' +
                                             '&count=20' +
                                             '&apiKey='+apiKey).json())
    updateInfo()

# Load the config file
with open('innexgo-client.json') as configfile:
    config = json.load(configfile)

    apiKey = config['apiKey']
    hostname = config['hostname']
    locationId = config['locationId']

    if apiKey is None or hostname is None or locationId is None:
        print('error reading the json')
        sys.exit()

    courses = 

    # now we can get scanning
    reader = mfrc522.MFRC522()

    try:
        while True:
            (detectstatus, tagtype) = reader.MFRC522_Request(reader.PICC_REQIDL)
            if detectstatus == reader.MI_OK:
                (uidstatus, uid) = reader.MFRC522_Anticoll()
                if uidstatus == reader.MI_OK:
                    print(uid[0], uid[1], uid[2], uid[3])

                time.sleep(0.01)
    except KeyboardInterrupt:
        GPIO.cleanup()
