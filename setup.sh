#!/bin/sh
set -e

sudo touch /mnt/ssh
sudo cp ./innexgo-client.json /mnt/
sudo cp ./wpa_supplicant.conf /mnt/

