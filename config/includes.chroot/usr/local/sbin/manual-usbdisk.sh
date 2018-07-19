#!/bin/sh
#set -v

MDIR=/media/usbdisk
mkdir -p $MDIR
if ! grep -q usbdisk /proc/mounts; then
    udev=$(find /dev/disk/by-id -name 'usb-*' | xargs -n1 readlink -f \
            | grep 1 | head -1)
    if [ -z "$udev" ]; then
        udev=$(find /dev/disk/by-id -name 'usb-*' | xargs -n1 readlink -f \
               | grep -v '[0-9]' | head -1)
    fi
    if [ -z "$udev" ]; then
        echo 'Cannot find USB storage device'
        exit 1
    elif ! mount "$udev" $MDIR; then
        echo 'Cannot mount USB storage device'
        exit 1
    fi
    ln -sf $MDIR /home/ubuntu/Desktop/
fi

