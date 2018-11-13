#!/bin/busybox sh

set -e

. "/bin/ubios-udm-common.sh"

export  WAN_IP="192.168.1.20"
export  WAM_MASK="24"
# NOTE WAN interface is a bridge device
export  WAN_IF="br0"
export  IPTABLES_CONF="/tmp/iptables.conf"
export  SYSTEM_CONF="/tmp/system.cfg"
export  SYSTEM_CONF_OLD="/tmp/system.cfg.old"

function detect_board(){
    local board_id="$(get_ubnthal_system "systemid")"
    local conf_id=""

    case ${board_id} in
        ea11)
            conf_id="udm"
            ;;
        ea13)
            conf_id="udm-se"
            ;;
        ea15)
            conf_id="udm-pro"
            ;;
        *)
            conf_id="unknown"
    esac
    echo "${conf_id}"
}

## UDM support
function wireless_fcd_udm_start(){

    local conf=""
    cp -vf ${SYSTEM_CONF} ${SYSTEM_CONF_OLD}
    cat << EOF > ${SYSTEM_CONF}
# wlans (radio)
radio.status=enabled
radio.countrycode=840
aaa.status=enabled
wireless.status=enabled
radio.outdoor=disabled
radio.1.phyname=ra0
radio.1.ack.auto=disabled
radio.1.acktimeout=64
radio.1.ampdu.status=enabled
radio.1.clksel=1
radio.1.countrycode=840
radio.1.cwm.enable=0
radio.1.cwm.mode=0
radio.1.forbiasauto=0
radio.1.channel=auto
radio.1.ieee_mode=11nght20
radio.1.mode=master
radio.1.rate.auto=enabled
radio.1.rate.mcs=auto
radio.1.rfscan=disabled
radio.1.ubntroam.status=disabled
radio.1.bcmc_l2_filter.status=enabled
radio.1.bgscan.status=disabled
radio.1.antenna.gain=0
radio.1.antenna=-1
radio.1.txpower_mode=auto
radio.1.txpower=auto
radio.1.hard_noisefloor.status=disabled
radio.1.devname=ra0
radio.1.status=enabled
radio.2.phyname=rai0
radio.2.ack.auto=disabled
radio.2.acktimeout=64
radio.2.ampdu.status=enabled
radio.2.clksel=1
radio.2.countrycode=840
radio.2.cwm.enable=0
radio.2.cwm.mode=0
radio.2.forbiasauto=0
radio.2.channel=auto
radio.2.ieee_mode=11naht40
radio.2.mode=master
radio.2.rate.auto=enabled
radio.2.rate.mcs=auto
radio.2.rfscan=disabled
radio.2.ubntroam.status=disabled
radio.2.bcmc_l2_filter.status=enabled
radio.2.bgscan.status=disabled
radio.2.antenna.gain=0
radio.2.antenna=-1
radio.2.txpower_mode=auto
radio.2.txpower=auto
radio.2.hard_noisefloor.status=disabled
radio.2.devname=rai0
radio.2.status=enabled
aaa.1.pmf.status=disabled
aaa.1.pmf.mode=0
aaa.1.ft.status=disabled
aaa.1.br.devname=br0
aaa.1.devname=ra0
aaa.1.driver=madwifi
aaa.1.ssid=martin
aaa.1.status=enabled
aaa.1.verbose=2
aaa.1.wpa=2
aaa.1.eapol_version=2
aaa.1.wpa.group_rekey=3600
aaa.1.wpa.1.pairwise=CCMP
aaa.1.wpa.key.1.mgmt=WPA-PSK
aaa.1.wpa.psk=ubntubnt
aaa.1.id=5be47038202ca102c614bd07
aaa.1.radius.macacl.status=disabled
aaa.1.hide_ssid=false
wireless.1.mode=master
wireless.1.devname=ra0
wireless.1.id=5be47038202ca102c614bd07
wireless.1.status=enabled
wireless.1.authmode=1
wireless.1.l2_isolation=disabled
wireless.1.is_guest=false
wireless.1.security=none
wireless.1.addmtikie=disabled
wireless.1.ssid=martin
wireless.1.hide_ssid=false
wireless.1.mac_acl.status=enabled
wireless.1.mac_acl.policy=deny
wireless.1.wmm=enabled
wireless.1.uapsd=disabled
wireless.1.parent=ra0
wireless.1.puren=0
wireless.1.pureg=1
wireless.1.usage=user
wireless.1.wds=disabled
wireless.1.mcast.enhance=0
wireless.1.autowds=disabled
wireless.1.vport=disabled
wireless.1.vwire=disabled
wireless.1.schedule_enabled=disabled
wireless.1.bga_filter=enabled
wireless.1.dtim_period=1
aaa.1.iapp_key=758cea17c32e9aabf93aa75ab8210f41
aaa.2.pmf.status=disabled
aaa.2.pmf.mode=0
aaa.2.ft.status=disabled
aaa.2.br.devname=br0
aaa.2.devname=rai0
aaa.2.driver=madwifi
aaa.2.ssid=martin
aaa.2.status=enabled
aaa.2.verbose=2
aaa.2.wpa=2
aaa.2.eapol_version=2
aaa.2.wpa.group_rekey=3600
aaa.2.wpa.1.pairwise=CCMP
aaa.2.wpa.key.1.mgmt=WPA-PSK
aaa.2.wpa.psk=ubntubnt
aaa.2.id=5be47038202ca102c614bd07
aaa.2.radius.macacl.status=disabled
aaa.2.hide_ssid=false
wireless.2.mode=master
wireless.2.devname=rai0
wireless.2.id=5be47038202ca102c614bd07
wireless.2.status=enabled
wireless.2.authmode=1
wireless.2.l2_isolation=disabled
wireless.2.is_guest=false
wireless.2.security=none
wireless.2.addmtikie=disabled
wireless.2.ssid=martin
wireless.2.hide_ssid=false
wireless.2.mac_acl.status=enabled
wireless.2.mac_acl.policy=deny
wireless.2.wmm=enabled
wireless.2.uapsd=disabled
wireless.2.parent=rai0
wireless.2.puren=0
wireless.2.pureg=1
wireless.2.usage=user
wireless.2.wds=disabled
wireless.2.mcast.enhance=0
wireless.2.autowds=disabled
wireless.2.vport=disabled
wireless.2.vwire=disabled
wireless.2.schedule_enabled=disabled
wireless.2.bga_filter=enabled
wireless.2.dtim_period=1
aaa.2.iapp_key=758cea17c32e9aabf93aa75ab8210f41
# mesh
mesh.status=disabled
# bandsteering
bandsteering.status=disabled
# ubntroam
ubntroam.status=disabled
# stamgr
stamgr.status=disabled
# connectivity
connectivity.status=disabled
# vlan
vlan.status=disabled
# qos
qos.status=disabled
# netconf
netconf.status=enabled
netconf.1.status=enabled
netconf.1.devname=ra0
netconf.1.ip=0.0.0.0
netconf.1.autoip.status=disabled
netconf.1.promisc=enabled
netconf.1.up=disabled
netconf.2.status=enabled
netconf.2.devname=rai0
netconf.2.ip=0.0.0.0
netconf.2.autoip.status=disabled
netconf.2.promisc=enabled
netconf.2.up=disabled
# syslog
syslog.status=enabled
syslog.level=7
EOF
    brctl addif "${WAN_IF}" "ra0"
    brctl addif "${WAN_IF}" "rai0"
    /etc/init.d/S44ubntconf restart
}

function ethernet_fcd_udm_start(){

    local eth_if="eth1"
    local sw_dev="switch0"

    # turn off udapi-server
    /etc/init.d/S45ubios-udapi-server stop
    # reset network settings
    /etc/init.d/S*ubios-udm-init stop
    # stop crond
    /etc/init.d/S40crond stop

    # save iptables
    iptables-save > ${IPTABLES_CONF}

    # flush iptables
    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT
    iptables -t nat -F
    iptables -t mangle -F
    iptables -F
    iptables -X

    # WAN port VLAN (group CPU port 6 and edge port 5)
    swconfig dev ${sw_dev} set reset 1
    swconfig dev switch0 set enable_acl 0
    swconfig dev ${sw_dev} vlan 1 set ports '5 6'
    swconfig dev ${sw_dev} port 5 set enable_vlan 1
    swconfig dev ${sw_dev} port 6 set enable_vlan 1

    # Setup snake test
    swconfig dev ${sw_dev} vlan 2 set ports '1 2'
    swconfig dev ${sw_dev} vlan 3 set ports '3 4'
    swconfig dev ${sw_dev} port 1 set enable_vlan 1
    swconfig dev ${sw_dev} port 2 set enable_vlan 1
    swconfig dev ${sw_dev} port 3 set enable_vlan 1
    swconfig dev ${sw_dev} port 4 set enable_vlan 1

    # Apply configuration
    swconfig dev ${sw_dev} set apply 1

    # Settup WAN interface

    # Bridge setup
	brctl addbr "${WAN_IF}"
    brctl addif "${WAN_IF}" "${eth_if}"
    ifconfig ${eth_if} down
    ip addr add "${WAN_IP}/${WAM_MASK}" dev ${WAN_IF}
    ip link set ${WAN_IF} up
    ifconfig ${eth_if} down
    sleep 1
    ifconfig ${eth_if} up
}

function wireless_fcd_udm_stop(){
    cp -vf ${SYSTEM_CONF_OLD} ${SYSTEM_CONF}
    /etc/init.d/S44ubntconf restart
}

function ethernet_fcd_udm_stop(){
    # start crond
    /etc/init.d/S40crond start
    # restart network settings
    /etc/init.d/S*ubios-udm-init restart
     # turn on udapi-server
    /etc/init.d/S45ubios-udapi-server start
     # restore iptables
    iptables-restore < ${IPTABLES_CONF}

}

### Main
function main(){

    local model_id=$(detect_board)
    local op=${1}

    if [ "${op}" != "start" ] && [ "${op}" != "stop" ]; then
		echo "Usage: ${0} {start|stop}"
        return 1
    fi

    #NOTE : run ethernet function first as it's responsible for bridge initialization
	case ${model_id} in
		udm)
			ethernet_fcd_udm_${op}
            wireless_fcd_udm_${op}
			;;
		udm-se|udm-pro)
			echo "The device ${model_id} is not supported yet."
			;;
		*)
			echo "Unknown model ${model_id}"
			return 1
	esac

	return 0
}

main $@

exit $?
