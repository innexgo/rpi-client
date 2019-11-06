#!/usr/bin/env python3

import os
import sys
import time
import json
import logging
import datetime
import requests
import threading


def isPi():
    return sys.implementation._multiarch == 'arm-linux-gnueabihf'


# if raspberry pi
if isPi():
    import RPi.GPIO as GPIO
    import mfrc522
else:
    print('not a pi lmao')


# Server Requests
apiKey = None
protocol = None
hostname = None
locationId = None


# RFID read
rfidKey = None


soundInitialized = False
soundPin = 40

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


def beep(hertz, duration):

    # Set up soundPins for buzzer
    if not soundInitialized:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(soundPin, GPIO.OUT)
    soundChannel = GPIO.PWM(soundPin, hertz)
    soundChannel.start(50.0)
    time.sleep(duration)
    soundChannel.stop()


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
    time.sleep(0.05)
    beep(1000, 0.1)
    time.sleep(0.05)
    beep(1000, 0.1)

def beepNetError():
    for i in range(0, 4):
        beep(1000, 0.01)
        time.sleep(0.05)


def sendEncounterWithStudentID(studentId):
    try:
        newEncounterRequest = requests.get(f'{protocol}://{hostname}/api/encounter/new/',
                                           params={'apiKey': apiKey,
                                                   'locationId': locationId,
                                                   'studentId': studentID})
        if newEncounterRequest.ok:
            encounter = newEncounterRequest.json()
            print(encounter)

            sessionRequest = requests.get(f'{protocol}://{hostname}/api/session/',
                                          params={'apiKey': apiKey,
                                                  'inEncounterId': encounter['id']})
            if sessionRequest.ok:
                print('============================================')
                # We find the number of sign ins caused by this encounter.
                # If none, it was a sign out
                wasSignOut = len(sessionRequest.json()) == 0
                if wasSignOut:
                    beepDown()
                else:
                    beepUp()
            else:
                print(sessionRequest.content)

        else:
            print('request was unsuccessful')
            beepError()
    except requests.exceptions.RequestException:
        print(
            f'Sending encounter failed, could not connect to {protocol}://{hostname}')
        beepNetError()



def sendEncounterWithCard(cardId):
    try:
        newEncounterRequest = requests.get(f'{protocol}://{hostname}/api/encounter/new/',
                                           params={'apiKey': apiKey,
                                                   'locationId': locationId,
                                                   'cardId': cardId})
        if newEncounterRequest.ok:
            encounter = newEncounterRequest.json()
            print(encounter)

            sessionRequest = requests.get(f'{protocol}://{hostname}/api/session/',
                                          params={'apiKey': apiKey,
                                                  'inEncounterId': encounter['id']})
            if sessionRequest.ok:
                print('============================================')
                # We find the number of sign ins caused by this encounter.
                # If none, it was a sign out
                wasSignOut = len(sessionRequest.json()) == 0
                if wasSignOut:
                    beepDown()
                else:
                    beepUp()
            else:
                print(sessionRequest.content)

        else:
            print('request was unsuccessful')
            beepError()
    except requests.exceptions.RequestException:
        print(
            f'Sending encounter failed, could not connect to {protocol}://{hostname}')
        beepNetError()


# Load the config file
with open('/boot/innexgo-client.json') as configfile:
    config=json.load(configfile)

    hostname=config['hostname']
    protocol=config['protocol']
    apiKey=config['apiKey']
    locationId=config['locationId']
    rfidKey=config['rfidKey']

    if apiKey is None or hostname is None or locationId is None or rfidKey is None:
        print('error reading the json')
        sys.exit()


    # Now we enable logging
    logging.basicConfig(filename="~/client.log",
                        format='%(asctime)s %(message)s',
                        filemode='w')

    if isPi():
        try:
            reader=mfrc522.MFRC522(debugLevel='DEBUG')

            # We are now in business
            print('ready')
            beepUp()
            while True:
                (detectstatus, tagtype)=reader.MFRC522_Request(reader.PICC_REQIDL)
                if detectstatus == reader.MI_OK:
                    (uidstatus, uid)=reader.MFRC522_Anticoll()

                    if uidstatus == reader.MI_OK:

                        cardId=int(bytes(uid).hex(), 16)
                        print(f'logged {cardId}')

                        # Select the scanned tag
                        reader.MFRC522_SelectTag(uid)

                        # Authenticate
                        authStatus = reader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, rfidKey, uid)

                        # Check if authenticated
                        if authStatus == reader.MI_OK:

                            # Read Sector 1
                            addr, data = reader.MFRC522_Read(1)

                            MIFAREReader.MFRC522_StopCrypto1()
                        else:
                            print("Authentication error")

                        # Convert uid to int

                        sendEncounterWithCard(cardId)
                time.sleep(0.1)
        except KeyboardInterrupt:
            GPIO.cleanup()
