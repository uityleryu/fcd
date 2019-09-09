#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import re
import stat
import filecmp

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
FWUPDATE_EN = True
DATAVERIFY_EN = True


class USUDCALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USUDCALPINEFactoryGeneral, self).__init__()

        self.ver_extract()
        self.bootloader_prompt = "UDC"
        self.devregpart = "/dev/mtdblock4"
        self.diagsh1 = "UBNT> "
        self.diagsh2 = "DIAG# "
        self.eepmexe = "x86-64k-ee"
        self.helperexe = "helper_f060_AL324_release"
        self.lcmfwver = "v3.0.4-0-gf89bc2b"
        self.helper_path = "usw_leaf"

        # number of Ethernet
        ethnum = {
            'f060': "73"
        }

        # number of WiFi
        wifinum = {
            'f060': "0"
        }

        # number of Bluetooth
        btnum = {
            'f060': "1"
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

        self.netif = {
            'f060': "ifconfig eth0 "
        }

    def stop_at_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        time.sleep(1)

    def boot_recovery_spi(self):
        cmdset = [
            "sf probe; sf read $loadaddr_payload 0x200000 0x3e00000",
            "setenv fitbootconf 0x08000004#udc@1",
            "run bootargsrecovery",
            "bootm $fitbootconf"
        ]
        for idx in range(len(cmdset)):
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmdset[idx])

    def ubupdate(self):
        self.stop_at_uboot()
        self.set_boot_net()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "bootupd done")
        self.pexp.expect_only(30, "variables are deleted from flash using the delenv script")
        time.sleep(1)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def set_boot_net(self):
        cmdset = [
            "setenv ipaddr {0}".format(self.dutip),
            "setenv serverip {0}".format(self.tftp_server),
            "setenv tftpdir images/{0}-fw-".format(self.board_id)
        ]
        for idx in range(len(cmdset)):
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmdset[idx])

        time.sleep(2)
        cmd = "ping {0}".format(self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

    def set_lnx_net(self):
        log_debug("Starting to configure the networking ... ")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)

        cmdset = [
            "/etc/init.d/gfl start",
            "/etc/init.d/npos start",
            "vtysh",
            "configure terminal",
            "interface swp1",
            "no shutdown",
            "switchport access vlan 1",
            "exit",
            "bridge-domain 1",
            "vlan 1 swp1",
            "exit",
            "interface bridge 1",
            "no shutdown",
            "exit",
            "exit",
            "exit",
            "ifconfig br1 {0}".format(self.dutip),
            "ifconfig | grep -C 5 br1"
        ]

        for idx in range(len(cmdset)):
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmdset[idx], self.linux_prompt)
            time.sleep(1)

    def set_lnx_net_devreg(self):
        log_debug("Starting to configure the networking ... ")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)

        cmdset = [
            "vtysh",
            "configure terminal",
            "in swp1",
            "no switchport",
            "switchport mode access",
            "switchport access vlan 1",
            "exit",
            "bridge-domain 1",
            "vlan 1 swp1",
            "exit",
            "exit",
            "exit",
            "ifconfig br1 {0}".format(self.dutip),
            "ifconfig | grep -C 5 br1"
        ]

        for idx in range(len(cmdset)):
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmdset[idx], self.linux_prompt)
            time.sleep(1)

    def lnx_netcheck(self, netifen=False):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd_retry(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)

    def fwupdate(self):
        log_debug("tftp get formal FW starting ... ")
        srcp = "images/{0}-fw.bin".format(self.board_id)
        self.tftp_get(remote=srcp, local="/tmp/upgrade.bin", timeout=600)
        log_debug("tftp get formal FW finishing ... ")

        cmd = "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin"
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, "Firmware version")
        self.login(username="root", password="ubnt", timeout=100)

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "info")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, "qrid=" + self.qrcode)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(90)
        self.pexp.expect_lnxcmd_retry(10, self.linux_prompt, "lcm-ctrl -t dump", self.lcmfwver, retry=15)

    def check_registered(self):
        #rtmsg = self.pexp.expect_get_output("hexdump /dev/mtd4 | head", self.linux_prompt)
        #match = re.findall("0008000 4255 544e", rtmsg)
        rtmsg = self.pexp.expect_get_output("cat /proc/ubnthal/system.info", self.linux_prompt)
        match = re.findall("qrid=000000", rtmsg)
        if match:
            log_debug("The board hasn't been signed")
            return False
        else:
            log_debug("The board has been signed")
            return True

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        self.stop_at_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run delenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

        self.stop_at_uboot()
        self.boot_recovery_spi()
        msg(5, "Boot from SPI recovery image ...")

        self.login(username="root", password="ubnt", timeout=80)
        '''
            If the DUT hasn't been signed, it has to do the switch network configuration by using vtysh CLI
        '''
        rtc = self.check_registered()
        if rtc is False:
            self.set_lnx_net()
        else:
            cmd = "ifconfig br1 {0}".format(self.dutip)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            cmd = "ifconfig | grep -C 5 br1"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

        self.lnx_netcheck()
        msg(10, "Boot up to linux console and network is good ...")

        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
            ============ Registration End ============
        '''

        if FWUPDATE_EN is True:
            self.pexp.expect_lnxcmd(600, self.linux_prompt, "reboot", self.linux_prompt)
            self.login(username="root", password="ubnt", timeout=100)
            self.lnx_netcheck()
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_EN is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    usudc_factory_general = USUDCALPINEFactoryGeneral()
    usudc_factory_general.run()

if __name__ == "__main__":
    main()
