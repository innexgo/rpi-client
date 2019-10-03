#!/bin/python3

# purpose:
# reboot every night at 12am
# if file in home directory called update
# git pull and update

import os
import sys
import time
import subprocess

UPDATE_NOW_PATH = '~/updatenow'

def update():
    retcode = subprocess.call(['git', 'pull'])
    return retcode == 0


subprocess.popen(['python3', 'client.py'])

while True:
    if os.path.isfile(UPDATE_NOW_PATH):
        successfulUpdate = update()
        if successfulUpdate:
            print('special update completed successfully')
            os.remove(UPDATE_NOW_PATH)
            subprocess.call(['sudo', 'shutdown', '-r', 'now'])
        else:
            print("git pull failed. network most likely disconnected. Waiting 5 min to try again")
            time.sleep(5*60)
            continue
    else:
        # sleep 10 min
        time.sleep(10*60)
