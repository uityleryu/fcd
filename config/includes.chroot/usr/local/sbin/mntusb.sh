#!/bin/sh


echo " configuring the USB disk "
MDIR=/media/usbdisk
MDIRKEYS=/media/usbdisk/keys

echo "umountting..."
umount -f /media/usbdisk

echo "remove old"
rm -f /home/user/Desktop/usbdisk
rm -f /home/user/Desktop/keys

mkdir -p $MDIR


#if ! grep -q usbdisk /proc/mounts; then
if true; then
    echo "find usb from dev list"
    udev=$(find /dev/disk/by-id -name 'usb-*' | xargs -n1 readlink -f \
            | grep 1 | head -1)
    if [ -z "$udev" ]; then
        udev=$(find /dev/disk/by-id -name 'usb-*' | xargs -n1 readlink -f \
               | grep -v '[0-9]' | head -1)
    fi
    
    echo "udev: $udev"

    if [ -z "$udev" ]; then
        echo 'Cannot find USB storage device'
        exit 1
#    elif ! mount "$udev" $MDIR; then
#        echo 'Cannot mount USB storage device'
#        exit 1
    else
       mount -v -n "$udev" $MDIR
       RET=$?
       echo "mount result: $RET"
       if [ ! $RET ];  then
           echo 'Cannot mount USB storage device'
          exit 1
       else
           echo "RET is good"
       fi
    fi
    echo "ln onto Desktop"
    ln -sf $MDIR /home/user/Desktop/
    ln -sf $MDIRKEYS /home/user/Desktop/
    RET=$(ls $MDIRKEYS)
    echo "result: $RET"
fi

echo "done!"

