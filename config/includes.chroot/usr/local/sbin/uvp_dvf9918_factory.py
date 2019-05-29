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
SETUBMACID_EN = True
CHECK_UBOOT_EN = True


class UVPDVF99FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UVPDVF99FactoryGeneral, self).__init__()
        self.ver_extract('UniFiVOIP', 'UVP-FLEX')
        self.devregpart = "/dev/mtdblock2"
        self.user = "root"
        self.bootloader_prompt = "DVF99 #"
        self.linux_prompt = "root@dvf9918:~#"
        self.helperexe = "helper_DVF99_release"
        self.prodl = "uvp"

        # number of Ethernet
        ethnum = {
            'ef0d': "1"
        }

        # number of WiFi
        wifinum = {
            'ef0d': "0"
        }

        # number of Bluetooth
        btnum = {
            'ef0d': "0"
        }

        flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
            'flashed_dir'     : flashed_dir
        }

        self.netif = {
            'ef0d': "ifconfig eth0 "
        }

    def mac_colon_format(self, mac):
        mcf = [
            self.mac[0:2],
            self.mac[2:4],
            self.mac[4:6],
            self.mac[6:8],
            self.mac[8:10],
            self.mac[10:12]
        ]
        mcf = ':'.join(mcf)
        return mcf

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Boot to linux console ...")
        self.pexp.expect_only(10, "U-Boot")
        self.pexp.expect_action(60, "login:", self.user)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)

        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
        time.sleep(3)
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        cmd = "ping -c 1 {0}".format(self.tftp_server)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, postexp)
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

        if SETUBMACID_EN is True:
            mcf = self.mac_colon_format(self.mac)
            cmd = "fw_setenv ethaddr {0}".format(mcf)
            self.pexp.expect_lnxcmd(90, self.linux_prompt, cmd, self.linux_prompt)

        if CHECK_UBOOT_EN is True:
            mcf = self.mac_colon_format(self.mac)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
            self.pexp.expect_action(60, "stop autoboot", "\033")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv")
            self.pexp.expect_only(30, "ethaddr=" + mcf)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "securedev")
            postexp = [
                "program OTP values... ok",
                "verify OTP values... ok",
                "device seems to be partially/secured!"
            ]
            index = self.pexp.expect_get_index(30, postexp)
            log_debug("OTP index: " + str(index))
            if index < 0:
                error_critical("OTP program/verify failed")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        uvp_factory_general = UVPDVF99FactoryGeneral()
        uvp_factory_general.run()

if __name__ == "__main__":
    main()
