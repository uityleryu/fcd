#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
NEED_UBUPDATE_EN = True
FWUPDATE_EN = True
DATAVERIFY_EN = True


class USUDCALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USUDCALPINEFactoryGeneral, self).__init__()

        self.ver_extract('UniFiSwitch', 'USW-LEAF')
        self.bootloader_prompt = "UDC"
        self.devregpart = "/dev/mtdblock4"
        self.diagsh = "UBNT"
        self.eepmexe = "x86-64k-ee"
        self.helperexe = "helper_f060_AL324_release"
        self.lcmfwver = "v2.0.1-0-g8cc9eeb"
        self.prodl = "usw_leaf"

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
            'f060': "0"
        }

        flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
            'flashed_dir'     : flashed_dir
        }

        self.netif = {
            'f060': "ifconfig eth0 "
        }

    def stop_at_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        time.sleep(1)

    def ubupdate(self):
        self.stop_at_uboot()
        self.set_boot_net()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "bootupd done")
        self.pexp.expect_only(30, "variables are deleted from flash using the delenv script")
        time.sleep(1)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv tftpdir images/" + self.board_id + "-fw-")
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

    def lnx_netcheck(self, netifen=False):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth1 down", self.linux_prompt)
        if netifen is True:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
            time.sleep(2)

        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)

    def fwupdate(self):
        cmd = "tftp -g -r images/{0}-fw-uImage -l /tmp/uImage.r {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, self.linux_prompt)

        cmd = "tftp -g -r images/{0}-fw-boot.img -l /tmp/boot.img {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd_retry(300, self.linux_prompt, cmd, self.linux_prompt)

        log_debug("Is flashing U-boot")
        postexp = [
            r"Erasing blocks:.*\(50%\)",
            r"Erasing blocks:.*\(100%\)",
            r"Writing data:.*\(50%\)",
            r"Writing data:.*\(100%\)",
            r"Verifying data:.*\(50%\)",
            r"Verifying data:.*\(100%\)",
            self.linux_prompt
        ]
        cmd = "flashcp -v /tmp/boot.img {0}".format("/dev/mtd0")
        self.pexp.expect_lnxcmd_retry(600, self.linux_prompt, cmd, self.linux_prompt)

        log_debug("Is flashing recovery image")
        postexp = [
            r"Erasing blocks:.*\(50%\)",
            r"Erasing blocks:.*\(100%\)",
            r"Writing data:.*\(50%\)",
            r"Writing data:.*\(100%\)",
            r"Verifying data:.*\(50%\)",
            r"Verifying data:.*\(100%\)",
            self.linux_prompt
        ]
        cmd = "flashcp -v /tmp/uImage.r {0}".format("/dev/mtd5")
        self.pexp.expect_lnxcmd_retry(600, self.linux_prompt, cmd, postexp)

        self.pexp.expect_lnxcmd(60, self.linux_prompt, "reboot", self.linux_prompt)

        self.login(username="ubnt", password="ubnt", timeout=80)

        log_debug("Starting to do fwupdate ... ")

        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        cmd = "ping -c 1 {0}".format(self.tftp_server)
        self.pexp.expect_lnxcmd_retry(20, self.linux_prompt, cmd, postexp)

        cmd = "tftp -g -r images/{0}-fw.bin -l /tmp/upgrade.bin {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, self.linux_prompt)

        postexp = [
            "Firmware version",
        ]
        cmd = "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin"
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, postexp)
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

        msg(5, "Boot from tftp with installer ...")
        # detect the BSP U-boot
        expit = [
            "May 06 2019 - 12:15:33",    # BSP U-boot-1
            "May 17 2019 - 13:22:41",    # BSP U-boot-2
            "May 16 2019 - 09:50:32"     # FW U-boot
        ]
        rt = self.pexp.expect_get_index(30, expit)
        if rt == 2:
            log_debug("Detect the FW U-boot version")
            self.load_diag_ub_uimg()
        elif rt == -1:
            error_critical("Timeout can't find the correct U-boot!!")
        else:
            log_debug("Find the correct U-boot version")

        self.pexp.expect_only(80, "Welcome to UBNT PyShell")
        self.pexp.expect_lnxcmd(10, self.diagsh, "diag", "DIAG")
        self.pexp.expect_lnxcmd(10, "DIAG", "npsdk speed 0 10", "DIAG")
        self.pexp.expect_lnxcmd(10, "DIAG", "shell", self.linux_prompt)

        self.lnx_netcheck(True)
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
