#!/bin/sh

STATUS=/tmp/prod-setup.done
DHCPOUT=/tmp/dhcp_out.txt
WGETOUT=/tmp/wget_out.txt
IFINFO=/tmp/ifinfo.txt

if [ -f ${STATUS} ]; then
    echo "Nothing to do - everything is already done."
    exit 0
fi

host_ip=$1
if [ "${host_ip}" = "" ]; then
    host_ip=192.168.1.19
fi

echo " configuring the SSH server "
cp /tftpboot/tools/sshd_config /etc/ssh/
sudo /etc/init.d/ssh restart
sleep 1

echo " configuring the USB disk "
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

# There are two kinds of dhcp server for linux
echo " *** Stopping dhcp server temprarily *** "
if [ -f /etc/init.d/dhcp3-server ]; then
    /etc/init.d/dhcp3-server stop >/dev/null 2>&1
elif [ -f /etc/init.d/isc-dhcp-server ]; then
    /etc/init.d/isc-dhcp-server stop >/dev/null 2>&1
else
    echo " There is no DHCP server "
fi

echo " *** Killing dhclient threads *** "
if [ -f /etc/init.d/dhcp3-server ]; then
    sudo killall -9 dhcpd3 >/dev/null 2>&1
elif [ -f /etc/init.d/isc-dhcp-server ]; then
    sudo killall -9 dhcpd >/dev/null 2>&1
else
    sudo killall -9 dhclient >/dev/null 2>&1
fi

#clear route table
echo " *** clearing route table *** "
ip route flush table main >/dev/null 2>&1

echo " *** Ethernet ports Configuration *** "
echo " >> searching an Ethernet port with IP address by DHCP for linking to internet "
grep ":" /proc/net/dev | awk -F: '{print $1}' | grep -v lo > /tmp/iface
ifaces=`cat /tmp/iface`
echo " current existed ethernet: "$ifaces

for iface in $ifaces; do
    ifconfig $iface down
done

dhcp_iface=xth0
dhcp_found=0
for iface in $ifaces; do
    echo " Starting doing DHCP client "
    echo " Right now, the Ethernet interface: "$iface
    #ifconfig $iface 0.0.0.0 up
    ip addr flush dev ${iface}
    sudo timeout 60 dhclient $iface >/dev/null 2>${DHCPOUT}; erron=$?
    sleep 1
    sudo ifconfig
    if [ $erron -eq 0 ]; then
        NODHCP=`grep -c "No working leases in persistent database" ${DHCPOUT}`
        if [ ${NODHCP} -eq 0 ]; then
            dhcp_iface=${iface}
            timeout 15 wget -q -O ${WGETOUT} http://www.baidu.com/ >/dev/null 2>&1
            wget_status=$?
            #echo -n "wget_status: $wget_status"
            if [ $wget_status -eq 0 ]; then
                sudo ifconfig > ${IFINFO}
                networkdomain=`grep -c "192\.168\.1\." ${IFINFO}`
                if [ ${networkdomain} -eq 0 ]; then
                    echo " dhcp_iface: "$dhcp_iface
                    dhcp_found=1
                    break
                else
                    echo " The network domain got from the DHCP sever is in the same DUT domain, warning !! "
                fi
            fi
        fi
    fi
    killall -9 dhclient
    ifconfig $iface down
done

if [ ${dhcp_found} -eq 0 ]; then
    echo "No DHCP server found. exiting..."
    exit 2
fi

#find first "free" eth interface for device production
prod_iface=`cat /tmp/iface | grep -v $dhcp_iface`
echo " prod_iface: "$prod_iface

sudo ip addr flush dev $prod_iface
sudo ip addr add ${host_ip}/24 dev $prod_iface
sudo ifconfig $prod_iface up
sudo ifconfig

timeout 15 wget -q -O ${WGETOUT} http://www.baidu.com/ >/dev/null 2>&1

wget_status=$?
echo -n "wget_status: $wget_status\n"

if [ $wget_status -eq 0 ]; then
    touch ${STATUS}
    echo $prod_iface > ${STATUS}
    if [ -f /etc/init.d/dhcp3-server ]; then
        sed -i -e "s,^INTERFACES=.*$,INTERFACES=\"${prod_iface}\",g" /etc/default/dhcp3-server
        /etc/init.d/dhcp3-server start >/dev/null 2>&1
    elif [ -f /etc/init.d/isc-dhcp-server ]; then
        sed -i -e "s,^INTERFACES=.*$,INTERFACES=\"${prod_iface}\",g" /etc/default/isc-dhcp-server
        /etc/init.d/isc-dhcp-server start >/dev/null 2>&1
    else
        echo 'Failed to start DHCP server'
    fi
else
    echo "Can't link to baidu website"
    exit 1
fi

if [ -f /etc/init.d/atftpd ]; then
    if ! /etc/init.d/atftpd restart; then
        echo 'Failed to start TFTP server'
        exit 1
    fi
fi

rm ${DHCPOUT} ${WGETOUT}
exit $wget_status
