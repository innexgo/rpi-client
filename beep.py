#!/usr/bin/python3
#######
# This program would generate PWM on GPIO 40 Pin 26 of P1
# with 50% Dutycyle at 1kHz
#######
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setup(40,GPIO.OUT)
#p=GPIO.PWM(40,1)
#p.start(50.0)
GPIO.output(40,False)
input("Press Enter key to Stop 1kHz PWM @ 50% duty cycle")
GPIO.output(40,True)
input("Press Enter key to Stop 1kHz PWM @ 50% duty cycle")
GPIO.cleanup()
