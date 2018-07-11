#!/bin/sh
#set -v

# Network Manger is invoking when Xubuntu is up
# This application will interfere with our network interface control manually
echo " *** Stop the network mangager *** "
sudo systemctl stop NetworkManager.service

STATUS=/tmp/prod-network.done
DHCPOUT=/tmp/dhcp_out.txt
WGETOUT=/tmp/wget_out.txt

if [ -f ${STATUS} ]; then
    echo "Nothing to do - everything is already done."
    exit 0
fi

# mount tmpfs on /tftpboot, to get rid of tftp timeout
mount -t tmpfs tmpfs /tftpboot
(cd /tftpboot.src; tar cf - * | tar xf - -C /tftpboot)
chmod -R 777 /tftpboot

host_ip=$1
if [ "${host_ip}" = "" ]; then
    host_ip=192.168.1.19
fi

# There are two kinds of dhcp server for linux
echo " *** Stopping dhcp server temprarily *** "
if [ -f /etc/init.d/dhcp3-server ]; then
    /etc/init.d/dhcp3-server stop >/dev/null 2>&1
elif [ -f /etc/init.d/isc-dhcp-server ]; then
    /etc/init.d/isc-dhcp-server stop >/dev/null 2>&1
fi

echo " *** Killing dhclient threads *** "
sudo killall -9 dhclient >/dev/null 2>&1
if [ -f /etc/init.d/dhcp3-server ]; then
    sudo killall -9 dhcpd3 >/dev/null 2>&1
elif [ -f /etc/init.d/isc-dhcp-server ]; then
    sudo killall -9 dhcpd >/dev/null 2>&1
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
    echo " Right now is dhclient: "$iface
    ifconfig $iface 0.0.0.0 up
    sudo timeout 15 dhclient $iface >/dev/null 2>${DHCPOUT}; erron=$?
    if [ $erron -eq 0 ]; then
        NODHCP=`grep -c "No working leases in persistent database" ${DHCPOUT}`
        if [ ${NODHCP} -eq 0 ]; then
            dhcp_iface=${iface}
            echo " dhcp_iface: "$dhcp_iface
            dhcp_found=1
            break
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

#echo "External link: *$dhcp_iface*"

#echo "Internal link: *$prod_iface*"

#set up $prod_iface with "reduced" subnet
ifconfig $prod_iface ${host_ip} netmask 255.255.255.224 up

wget -q -O ${WGETOUT} http://www.baidu.com/ >/dev/null 2>&1

wget_status=$?
echo -n "wget_status: $wget_status"

if [ $wget_status -eq 0 ]; then
    touch ${STATUS}
    if [ -f /etc/init.d/dhcp3-server ]; then
        sed -i -e "s,^INTERFACES=.*$,INTERFACES=\"${prod_iface}\",g" /etc/default/dhcp3-server
        /etc/init.d/dhcp3-server start >/dev/null 2>&1
    elif [ -f /etc/init.d/isc-dhcp-server ]; then
        sed -i -e "s,^INTERFACES=.*$,INTERFACES=\"${prod_iface}\",g" /etc/default/isc-dhcp-server
        /etc/init.d/isc-dhcp-server start >/dev/null 2>&1
    fi
fi

rm ${DHCPOUT} ${WGETOUT}
exit $wget_status
