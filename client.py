#!/usr/bin/env python3

import os
import sys
import time
import json
import mfrc522
import datetime
import requests
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
    courseRequest = requests.get(
            f'{protocol}://{hostname}/course/'
            f'?locationId={locationId}&apiKey={apiKey}'
                    )
    if courseRequest.ok:
        courses = courseRequest.json()
    else:
        print('request to server for courses failed')
        courses = []

    periodsRequest = requests.get(
            f'{protocol}://{hostname}/period/?apiKey={apiKey}'
                    )
    if periodsRequest.ok:
        periods = sorted(periodsRequest.json(), key = lambda i: i['initialTime'])
    else:
        print('request to server for periods failed')
        periods = []
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

                # TODO add dings
                if uidstatus == reader.MI_OK:
                    # Convert uid to int
                    cardId = int(bytes(uid).hex(), 16)
                    print(f'logged {cardId}')
                    if currentCourse is None:
                        # There's not a class at the moment
                        noSessionRequest = requests.get(
                            f'{protocol}://{hostname}/encounter/new/'
                            f'?locationId={locationId}&cardId={cardId}'
                            f'&apiKey={apiKey}'
                        )
                        if noSessionRequest.ok:
                            encounter = noSessionRequest.json()
                            print(encounter)
                        else:
                            print('request was unsuccessful')
                    else:
                        # There is a class at the moment
                        courseId = currentCourse['id']
                        sessionEncounterRequest = requests.get(
                            f'{protocol}://{hostname}/encounter/new/'
                            f'?locationId={locationId}&courseId={courseId}&cardId={cardId}'
                            f'&apiKey={apiKey}'
                        )
                        if sessionEncounterRequest.ok:
                            encounter = sessionEncounterRequest.json()
                            print(encounter)
                        else:
                            print('request was unsuccessful')
                time.sleep(0.5)
    except KeyboardInterrupt:
        RPi.GPIO.cleanup()
