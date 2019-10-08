#!/bin/bash


# This file to be run on host to set up raspberry pi
set -e

if [[ $# -ne 2 ]]; then
    echo "Illegal number of parameters, need 1 drive and 1 hostname of the device"
    exit 2
fi

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

DRIVE=$1

mkdir -p mnt
mount "${DRIVE}1" mnt
touch mnt/ssh
echo "dtparam=spi=on" >> mnt/config.txt

# Copy files into the boot
cp innexgo-client.json mnt/
cp wpa_supplicant.conf mnt/

umount mnt

# Mount ext4 part on the mount directory
mount "${DRIVE}2" mnt

# clone to here
git clone https://github.com/innexgo/rpi-client mnt/home/pi/rpi-client
chown -R pi:pi mnt/home/pi/rpi-client

# Start at boot
echo "@reboot /home/pi/rpi-client/wrapper.py" >> mnt/var/spool/cron/crontabs/pi

# Set the hostname
echo $2 > mnt/etc/hostname
sed -i "s/raspberrypi/$2/g" mnt/etc/hosts


umount mnt

rmdir mnt
