#!/usr/bin/env python3

import os
import sys
import time
import json
import pathlib
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

active = None
apiKey = None
hostname = None
locationId = None


sector = 10
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
    soundChannel = GPIO.PWM(soundPin, hertz)
    soundChannel.start(50.0)
    time.sleep(duration)
    soundChannel.stop()
    GPIO.output(soundPin, GPIO.HIGH)

def beepActive(duration):
    GPIO.output(soundPin, GPIO.LOW)
    time.sleep(duration)
    GPIO.output(soundPin, GPIO.HIGH)

def beepUp():
    if active:
        beepActive(0.3)
    else:
        beep(1000, 0.1)
        beep(2000, 0.1)

def beepDown():
    if active:
        beepActive(0.15)
        time.sleep(0.05)
        beepActive(0.15)
    else:
        beep(2000, 0.1)
        beep(1000, 0.1)

def beepFlat():
    beep(2000, 0.2)

def beepError():
    if active:
        for i in range(0, 3):
            beepActive(0.1)
            time.sleep(0.05)
    else:
        for i in range(0, 3):
            beep(1000, 0.1)
            time.sleep(0.05)

def beepNetError():
    if active:
        for i in range(0, 6):
            beepActive(0.01)
            time.sleep(0.05)
    else:
        for i in range(0, 6):
            beep(1000, 0.01)
            time.sleep(0.05)

def sendEncounter(studentId):
    try:
        attendsRequest = requests.get(f'{hostname}/api/misc/attends/',
                                           params={'apiKey': apiKey,
                                                   'locationId': locationId,
                                                   'manual': False,
                                                   'studentId': studentId})
        if attendsRequest.ok:
            # If the session returned was complete, then it must be a signOut
            responseJson = attendsRequest.json()
            
            if 'complete' in responseJson:
                wasSignOut = attendsRequest.json()['complete']
                if wasSignOut:
                    logging.info(f'Encounter: Successfully signed out student {studentId}')
                    beepDown()
                else:
                    logging.info(f'Encounter: Successfully signed in student {studentId}')
                    beepUp()
            else:
                logging.error(f'No "complete" field found in response {attendsRequest.content}')
                beepError()
        else:
            logging.error(f'Encounter: HTTP Error: {attendsRequest.content}')
            beepError()
    except requests.exceptions.RequestException:
        logging.error(f'Encounter: Could not connect to {hostname}')
        beepNetError()

# Load the config file
with open('/boot/innexgo-client.json') as configfile:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(soundPin, GPIO.OUT)
    # Configure logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(f'{pathlib.Path.home()}/client-log.txt'),
                            logging.StreamHandler()
                        ])

    # Configure configs
    config=json.load(configfile)

    hostname=config['hostname']
    apiKey=config['apiKey']
    locationId=config['locationId']
    active=config['active']

    if apiKey is None or hostname is None or locationId is None or active is None:
        print('error reading the json')
        sys.exit()

    if isPi():
        try:
            reader=mfrc522.MFRC522(debugLevel='DEBUG')

            # We are now in business
            beepUp()
            logging.info('==== STARTED ===')
            while True:
                (detectstatus, tagtype)=reader.MFRC522_Request(reader.PICC_REQIDL)
                if detectstatus == reader.MI_OK:
                    (uidstatus, uid) = reader.MFRC522_Anticoll()
                    if uidstatus == reader.MI_OK:
                        logging.info(f'RFID: Detected Tag {uid}')

                        # Select and read tag
                        reader.MFRC522_SelectTag(uid)
                        data = reader.MFRC522_Read(sector)

                        if data is not None and len(data) >= 4:
                            studentId = int.from_bytes(bytes(data[0:4]), byteorder="little")
                            logging.info(f'RFID: Got studentId {studentId}')
                            sendEncounter(studentId)
                            time.sleep(0.1)
                        else:
                            logging.error(f'RFID: Error reading tag data')
                            beepError()
                    else:
                        logging.error(f'RFID: Error reading tag info')
                        beepError()
                else:
                    time.sleep(0.05)
        except KeyboardInterrupt:
            GPIO.cleanup()
