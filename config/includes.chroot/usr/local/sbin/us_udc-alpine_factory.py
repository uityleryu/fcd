#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

sys.path.append("/tftpboot/tools")

from usw_leaf.decrypt import Decrypt
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

SIM_PCYL_LNX_EN = False
SIM_PCYL_UB_EN = False
UB_WR_DUMMY_EN = True
PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
SETBOARDNAME_EN = True
FWUPDATE_EN = True
DATAVERIFY_EN = True
VTSYCHECK_EN = False
AUTODIAG_EN = False


class USUDCALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USUDCALPINEFactoryGeneral, self).__init__()

        self.ver_extract()
        self.bootloader_prompt = "UDC"
        self.devregpart = "/dev/mtdblock4"
        self.diagsh1 = "UBNT> "
        self.diagsh2 = "DIAG# "
        self.eepmexe = "x86-64k-ee"
        self.helperexe = "helper_AL324_release_udc"
        self.helper_path = "usw_leaf"
        self.dcrp = None

        # Dummy data for SPI flash
        self.dummydata = {
            'f060': "fcecda77861cfcecda77861d{0}0777".format("f060"),
            'f062': "fcecda77861cfcecda77861d{0}0777".format("f062"),
            'f063': "fcecda77861cfcecda77861d{0}0777".format("f063")
        }

        # LCM FW
        self.lcmfwver = {
            'f060': "v4.1.0-0-ge3e3c7d",
            'f062': "v4.1.0-0-ge3e3c7d",
            'f063': "v4.0.8-0-ga1015ad"
        }

        # FW image
        self.fwimage = {
            'f060': "UDC.alpinev2.v4.1.44.f3fcf1b.200414.1926",
            'f062': "UDC.alpinev2.v4.1.44.f3fcf1b.200414.1926",
            'f063': "UDC.alpinev2.v4.1.43.cf99e68.200313.0925"
        }

        # number of Ethernet
        ethnum = {
            'f060': "73",
            'f062': "129",
            'f063': "73"
        }

        # number of WiFi
        wifinum = {
            'f060': "0",
            'f062': "0",
            'f063': "0"
        }

        # number of Bluetooth
        btnum = {
            'f060': "1",
            'f062': "1",
            'f063': "1"
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

        self.netif = {
            'f060': "ifconfig eth0 ",
            'f062': "ifconfig eth0 ",
            'f063': "ifconfig eth0 "
        }

        # DIAG board name
        self.brdname = {
            'f060': "usw-100g-mfg",
            'f062': "usw-spine-rev1-mfg",
            'f063': "usw-100g-mfg"
        }

    def ub_write_dummy_data(self):
        dutdata = self.dummydata[self.board_id]

        for i in range(0, len(dutdata), 2):
            wbdata = dutdata[i : i + 2]
            iint = int(i / 2)
            ihex = hex(iint)
            cmd = "setexpr pointer $loadaddr + {0}".format(ihex)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            cmd = "mw.b $pointer 0x{0}".format(wbdata)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        time.sleep(1)
        log_debug(" reading the dummpy data from the temp memory ... ")
        cmd = "md.b $loadaddr 0x10"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        time.sleep(1)
        cmd = "sf probe; sf erase 0x1f0000 +0x10"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        log_debug(" writing the dummpy data in the EEPROM ... ")
        cmd = "sf update $loadaddr 0x1f0000 0x10"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        time.sleep(1)
        log_debug(" cleaning the temp memory ... ")
        cmd = "mw.q $loadaddr 0xffffffffffffffff"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "setexpr next_loadaddr $loadaddr + 8"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "mw.q $next_loadaddr 0xffffffffffffffff"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "md.b $loadaddr 0x10"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        cmd = "sf read $loadaddr 0x1f0000 0x10"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(1)
        log_debug(" reading the dummpy data from the EEPROM ... ")
        cmd = "md.b $loadaddr 0x10"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

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
        self.dcrp.stop_at_uboot()
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

        if self.board_id == "f060":
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
        elif self.board_id == "f062":
            qsfp_port = "swp32"

            cmdset = [
                "/etc/init.d/gfl start",
                "/etc/init.d/zebra start",
                "vtysh",
                "sh daemons",
                "configure terminal",
                "interface {0}".format(qsfp_port),
                "no shutdown",
                "no switchport",
                "ip addr {0}/24".format(self.dutip),
                "no shutdown",
                "end",
                "exit",
                "ifconfig | grep -C 5 {0}".format(qsfp_port)
            ]

        for idx in range(len(cmdset)):
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmdset[idx], self.linux_prompt)

    def lnx_netcheck(self, netifen=False):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()

    def fwupdate(self):
        log_debug("wget formal FW starting ... ")
        os.chdir(self.fwdir)
        self.create_http_server()
        fw_url = "http://{0}:{1}/{2}-fw.bin".format(self.tftp_server, self.http_port, self.board_id)
        cmd = "cd /tmp; wget {0}".format(fw_url)
        self.pexp.expect_lnxcmd(100, self.linux_prompt, cmd, self.linux_prompt)
        self.chk_lnxcmd_valid()

        cmd = "mv /tmp/{0}-fw.bin /tmp/upgrade.bin".format(self.board_id)
        self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt)
        self.chk_lnxcmd_valid()
        self.stop_http_server()
        log_debug("wget formal FW finishing ... ")

        cmd = "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin"
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, "Firmware version")
        self.rtc = self.login(username="root", timeout=150)

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "info")
        self.chk_lnxcmd_valid()

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, "qrid=" + self.qrcode)
        self.pexp.expect_only(10, self.linux_prompt)
        self.chk_lnxcmd_valid()
        '''
            Adding sleep to wait for the LCM FW being upgraded completed
        '''
        time.sleep(90)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "lcm-ctrl -t dump", self.lcmfwver[self.board_id], retry=20)
        self.chk_lnxcmd_valid()

        rtmsg = self.pexp.expect_get_output("cat /usr/lib/version", self.linux_prompt)
        match = re.findall(self.fwimage[self.board_id], rtmsg)
        if not match:
            error_critical("The version of FW image is not correct")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        self.dcrp = Decrypt(self.pexp)

        if SIM_PCYL_LNX_EN is True:
            self.pexp.expect_action(10, "", "")
            self.pexp.expect_action(10, "", "reboot")

        if SIM_PCYL_UB_EN is True:
            self.pexp.expect_action(10, "", "reset")

        self.dcrp.stop_at_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run delenv")

        if UB_WR_DUMMY_EN is True:
            self.ub_write_dummy_data()

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

        self.dcrp.stop_at_uboot()
        self.boot_recovery_spi()
        msg(5, "Boot from SPI recovery image ...")

        rtc = self.login(username="root", timeout=100)
        '''
            If the DUT hasn't been signed, it has to do the switch network configuration by using vtysh CLI
        '''
        if rtc == 1:
            self.set_lnx_net()
        else:
            cmd = "ifconfig br1 {0}".format(self.dutip)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()
            cmd = "ifconfig | grep -C 5 br1"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

        self.lnx_netcheck()
        msg(10, "Boot up to linux console and network is good ...")

        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            self.erase_eefiles()
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
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

        if SETBOARDNAME_EN is True:
            cmd = "echo {0} > /logs/boardname".format(self.brdname[self.board_id])
            self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()
            self.is_dutfile_exist("/logs/boardname")

        if FWUPDATE_EN is True:
            self.pexp.expect_lnxcmd(600, self.linux_prompt, "reboot", self.linux_prompt)
            self.dcrp.stop_at_uboot()
            self.boot_recovery_spi()
            rtc = self.login(username="root", timeout=150)
            if rtc == 1:
                error_critical("The DUT has been registered!!!")

            self.lnx_netcheck()
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_EN is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if VTSYCHECK_EN is True:
            self.pexp.expect_lnxcmd(600, self.linux_prompt, "reboot", self.linux_prompt)
            self.login(username="root", timeout=100)

            postexp = [
                self.fwimage[self.board_id],
                self.lcmfwver[self.board_id]
            ]
            self.pexp.expect_lnxcmd(10, "UBNT", "show version", postexp)

        if AUTODIAG_EN is True:
            self.pexp.expect_lnxcmd(10, "UBNT", "reboot", "UBNT")
            self.dcrp.stop_at_uboot()
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootcmd run hddualfitrecovery")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargsextra diag")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "saveenv")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    usudc_factory_general = USUDCALPINEFactoryGeneral()
    usudc_factory_general.run()

if __name__ == "__main__":
    main()
