#!/bin/sh
set -e

sudo touch /boot/ssh
sudo cp ./innexgo-client.json /mnt/
sudo cp ./wpa_supplicant.conf /mnt/

