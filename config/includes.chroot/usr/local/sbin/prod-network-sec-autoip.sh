#!/bin/sh

STATUS=/tmp/prod-setup.done
WGETOUT=/tmp/wget_out.txt

if [ -f ${STATUS} ]; then
    echo 'Setup already done'
    exit 0
fi

#set up $prod_iface with "reduced" subnet
#ifconfig $prod_iface 169.254.1.19 netmask 255.255.0.0
#ip alias to acces device at default IP address (192.168.1.20)
#ifconfig $prod_iface:1 192.168.1.19 netmask 255.255.255.240
#route add -net 192.168.1.16 netmask 255.255.255.240 dev $prod_iface:1

MY_IP=192.168.1.19/24
if ! (ip addr | grep -q $MY_IP) && ! ip addr add $MY_IP dev eth1; then
    echo 'Failed to assign IP address to eth1'
    exit 1
fi
# MY_IP=169.254.1.19/16
# if ! (ip addr | grep -q $MY_IP) && ! ip addr add $MY_IP dev eth1; then
#     echo 'Failed to assign IP address to eth1'
#     exit 1
# fi

ip link set eth1 up

#wget -q -O ${WGETOUT} -T 10 http://www.ubnt.com/ >/dev/null 2>&1
#wget_status=$?
#rm -f ${WGETOUT}
#if [ "$wget_status" != 0 ]; then
#    echo "Internet connectivity problem: wget failed with $wget_status"
#    exit 1
#fi

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
    ln -sf $MDIR /home/user/Desktop/
fi

if ! /etc/init.d/atftpd restart; then
    echo 'Failed to start TFTP server'
    exit 1
fi

echo 'Setup successful'
touch "$STATUS"
exit 0
