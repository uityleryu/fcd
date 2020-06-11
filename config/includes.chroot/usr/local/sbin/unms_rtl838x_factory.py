#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
SECCHK_EN = True


class UNMSRTL838XFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UNMSRTL838XFactoryGeneral, self).__init__()

        self.ver_extract()
        self.bootloader_prompt = "RTL838x#"
        self.devregpart = "/dev/mtdblock6"
        self.helperexe = "helper_RTL838x_release"
        self.helper_path = "unms-slite"

        # board model
        self.bdmd = {
            'eed0': "UNMS_S_LITE"
        }

        # number of Ethernet
        ethnum = {
            'eed0': "3"
        }

        # number of WiFi
        wifinum = {
            'eed0': "0"
        }

        # number of Bluetooth
        btnum = {
            'eed0': "0"
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

        self.netif = {
            'eed0': "ifconfig eth0 "
        }

    def stop_at_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit Esc key to stop autoboot", "\033\033")

    def uboot_config(self):
        cmdset = [
            "setenv ipaddr {0}".format(self.dutip),
            "setenv serverip {0}".format(self.tftp_server),
            "setenv boardmodel {0}".format(self.bdmd[self.board_id]),
            "setenv burnNum 0",
            "setenv telnet 0",
            "saveenv",
            "reset"
        ]
        for idx in range(len(cmdset)):
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmdset[idx])

        self.stop_at_uboot()

        cmd = "rtk network on".format(self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "ping {0}".format(self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

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

        msg(1, "Stop at U-Boot ...")
        self.stop_at_uboot()
        self.uboot_config()

        msg(5, "Upgrading U-Boot ...")
        cmd = "upgrade loader {0}/{1}-uboot.img".format(self.image, self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        wmsg = "Upgrade loader image \[{0}/{1}-uboot.img\] success".format(self.image, self.board_id)
        self.pexp.expect_only(30, wmsg)

        cmd = "reset"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        self.stop_at_uboot()

        msg(10, "Upgrading DIAG image ...")
        cmd = "upgrade runtime {0}/{1}-fw.bin".format(self.image, self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        wmsg = "Upgrade runtime image \[{0}/{1}-fw.bin\] success".format(self.image, self.board_id)
        self.pexp.expect_only(210, wmsg)

        msg(15, "Loading cfg and log parts ...")
        cmd = "tftpboot 0x81000000 {0}/{1}/esx_cfg.part".format(self.tools, self.helper_path)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred = 1048576")
        cmd = "flwrite name JFFS2_CFG 0x81000000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "tftpboot 0x81000000 {0}/{1}/esx_log.part".format(self.tools, self.helper_path)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred = 1048576")
        cmd = "flwrite name JFFS2_LOG 0x81000000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "boota"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        '''
            In this case, the UNMS-S-LITE will boot up to DIAG image as default.
            And the DIAG image will start running another shell.
            And it only could accept the "\r" as an Enter key in this shell.
        '''
        self.pexp.expect_lnxcmd(30, "UBNT_Diag", "exit\r", self.linux_prompt)
        self.set_lnx_net("eth0")
        self.is_network_alive_in_linux()

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

        if SECCHK_EN is True:
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "reboot")
            self.pexp.expect_lnxcmd(30, "UBNT_Diag", "sectest\r", "security test pass")

        msg(100, "Completing ...")
        self.close_fcd()

def main():
    unms_factory_general = UNMSRTL838XFactoryGeneral()
    unms_factory_general.run()

if __name__ == "__main__":
    main()
