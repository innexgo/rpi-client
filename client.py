#!/usr/bin/env python

import os
import sys
import time
import json
import mfrc522
import datetime
import requests
import operator
import threading
import RPi.GPIO

courses = None
periods = None

apiKey = None
protocol = None
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

def printMillis(millis):
    print(datetime.datetime.fromtimestamp(millis/1000.0))

def updateInfo():
    global currentCourse
    global currentPeriod

    millis = currentMillis()

    if periods is not None:
        # get first period that is current
        currentPeriod = next(
            filter(
                lambda p : (millis > p['initialTime'] and millis < p['endTime']),
                periods
            ),
            None
        )
    else:
        print('period is none')
        currentCourse = None

    if (courses is not None) and (currentPeriod is not None):
        # get course with current location and period
        currentCourse = next(
            filter(
                lambda c : (c['period'] == currentPeriod['period']),
                courses
            ),
            None
        )
    else:
        print('courses is none or currentPeriod is none')
        currentCourse = None

def updateInfoInfrequent():
    global periods
    global courses

    millis = currentMillis()
    courses = requests.get(
            f'{protocol}://{hostname}/course/?locationId={locationId}&apiKey={apiKey}'
                    ).json()

    periods = requests.get(
            f'{protocol}://{hostname}/period/?apiKey={apiKey}'
                    ).json()
    periods = sorted(periods, key = lambda i: i['initialTime'])
    updateInfo()

# Load the config file
with open('innexgo-client.json') as configfile:
    config = json.load(configfile)

    hostname = config['hostname']
    protocol = config['protocol']
    apiKey = config['apiKey']
    locationId = config['locationId']

    if apiKey is None or hostname is None or locationId is None:
        print('error reading the json')
        sys.exit()

    setInterval(updateInfoInfrequent, 1);


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
        Rpi.GPIO.cleanup()
