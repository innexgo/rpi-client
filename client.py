#!/usr/bin/env python3

import os
import sys
import time
import json
import datetime
import requests
import threading


def isPi():
    return sys.implementation._multiarch == 'arm-linux-gnueabihf'


# if raspberry pi
if isPi():
    import RPi.GPIO as GPIO
    import mfrc522


courses = None
periods = None

apiKey = None
protocol = None
hostname = None
locationId = None

currentPeriod = None
currentCourse = None

soundInitialized = False
soundPin = 21


def currentMillis():
    return round(1000 * time.time())


def printMillis(millis):
    print(datetime.datetime.fromtimestamp(millis / 1000.0))

# setInterval for python


def setInterval(func, sec):
    def func_wrapper():
        setInterval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


def beep(hertz, time):
    # Set up soundPins for buzzer
    if not soundInitialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(soundPin, GPIO.OUT)

    p = GPIO.PWM(soundPin, hertz)
    p.start(50.0)
    sleep(time)
    p.stop()


def beepUp():
    beep(1000, 0.1)
    beep(2000, 0.1)


def beepDown():
    beep(2000, 0.1)
    beep(1000, 0.1)

def beepFlat():
    beep(2000, 0.2)

def beepError():
    beep(1000, 0.1)
    sleep(0.05)
    beep(1000, 0.1)
    sleep(0.05)
    beep(1000, 0.1)

def beepNetError():
    for i in range(0, 4):
        beep(1000, 0.01)
        sleep(0.05)

def updateInfo():
    global currentCourse
    global currentPeriod

    millis = currentMillis()

    if periods is not None:
        # get first period that is current
        currentPeriod = next(
            filter(
                lambda p: (millis > p['initialTime']
                           and millis < p['endTime']),
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
                lambda c: (c['period'] == currentPeriod['period']),
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

    try:
        millis = currentMillis()
        courseRequest = requests.get(f'{protocol}://{hostname}/course/',
                                     params={
                                         'locationId': locationId,
                                         'apiKey': apiKey})
        if courseRequest.ok:
            courses = courseRequest.json()
        else:
            print('request to server for courses failed')
            courses = []

        periodsRequest = requests.get(f'{protocol}://{hostname}/period/',
                                      params={'apiKey': apiKey})
        if periodsRequest.ok:
            periods = sorted(
    periodsRequest.json(),
     key=lambda i: i['initialTime'])
        else:
            print('request to server for periods failed')
            periods = []
    except requests.exceptions.RequestException:
        print(
            f'fetching data failed, could not connect to {protocol}://{hostname}')
        courses = []
        periods = []
        beepNetError()
    updateInfo()


def sendEncounterWithCard(cardId):
    try:
        if currentCourse is None:
            # There's not a class at the moment
            newEncounterRequest = requests.get(f'{protocol}://{hostname}/encounter/new/',
                                            params={'apiKey': apiKey,
                                                    'locationId': locationId,
                                                    'cardId': cardId})
            if newEncounterRequest.ok:
                encounter = newEncounterRequest.json()
                print('logged encounter')
                print(encounter)
                beepFlat()
            else:
                print('request was unsuccessful')
        else:
            # There is a class at the moment
            courseId = currentCourse['id']
            newEncounterRequest = requests.get(f'{protocol}://{hostname}/encounter/new/',
                                               params={'apiKey': apiKey,
                                                       'locationId': locationId,
                                                       'courseId': courseId,
                                                       'cardId': cardId})
            if newEncounterRequest.ok:
                encounter = newEncounterRequest.json()
                print(f'logged encounter at class {currentCourse["subject"]}')
                print(encounter)

                sessionRequest = requests.get(f'{protocol}://{hostname}/session/',
                                              params={'apiKey': apiKey,
                                                      'inEncounterId': encounter['id']})
                if sessionRequest.ok:
                    # We find the number of sign ins caused by this encounter.
                    # If none, it was a sign out
                    wasSignOut = len(sessionRequest.json()) == 0
                    if wasSignOut:
                        beepDown()
                    else:
                        beepUp()

            else:
                print('request was unsuccessful')
                beepError()
    except requests.exceptions.RequestException:
        print(
            f'Sending encounter failed, could not connect to {protocol}://{hostname}')
        beepNetError()


# Load the config file
with open('innexgo-client.json') as configfile:
    config=json.load(configfile)

    hostname=config['hostname']
    protocol=config['protocol']
    apiKey=config['apiKey']
    locationId=config['locationId']

    if apiKey is None or hostname is None or locationId is None:
        print('error reading the json')
        sys.exit()

    updateInfoInfrequent()
    setInterval(updateInfoInfrequent, 30);
    setInterval(updateInfo, 5)

    if isPi():
        try:
            reader=mfrc522.MFRC522()

            # We are now in business
            print('ready')
            beepUp()
            while True:
                (detectstatus, tagtype)=reader.MFRC522_Request(reader.PICC_REQIDL)
                if detectstatus == reader.MI_OK:
                    (uidstatus, uid)=reader.MFRC522_Anticoll()

                    # TODO add dings
                    if uidstatus == reader.MI_OK:
                        # Convert uid to int
                        cardId=int(bytes(uid).hex(), 16)
                        print(f'logged {cardId}')
                        sendEncounterWithCard(cardId)
                time.sleep(0.5)
        except KeyboardInterrupt:
            GPIO.cleanup()
