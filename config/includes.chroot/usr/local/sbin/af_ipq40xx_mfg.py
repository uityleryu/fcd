#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil


class UAPIPQ40XXMFG(ScriptBase):
    def __init__(self):
        super(UAPIPQ40XXMFG, self).__init__()
        #self.ver_extract()
        self._init_vars()

    def _init_vars(self):

        # U-boot prompt
        self.ubpmt = {
            'dc9b': "\(IPQ40xx\) # "
        }

        # linux console prompt
        self.lnxpmt = {
            'dc9b': "root@OpenWrt"
        }

        self.artimg = {
            'dc9b': "dc9b-mfg.bin"
        }

        baseip = 20
        self.prod_dev_ip = "192.168.1." + str((int(self.row_id) + baseip))

        self.tftpdir = self.tftpdir + "/"
        self.uap_dir = os.path.join(self.fcd_toolsdir, "uap")
        self.common_dir = os.path.join(self.fcd_toolsdir, "common")

        self.kernel_address =  "0x0"
        self.kernel_size =  "0x170000"
        self.rootfs_address = "0x180000"
        self.rootfs_size = "0x1d00000"

        self.fcd.common.config_stty(self.dev)

    def _stop_uboot(self):
        self.pexp.expect_action(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "")

    def _set_uboot_network(self):
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv ipaddr " + self.prod_dev_ip)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv serverip " + self.tftp_server)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "ping " + self.tftp_server)
        self.pexp.expect_only(30, "host " + self.tftp_server + " is alive")
        time.sleep(1)

    def run(self):
        """
        Main procedure of factory
        """

        msg(1, "Start Procedure")
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Stop U-boot")
        self._stop_uboot()
        time.sleep(3)
        self._set_uboot_network()

        msg(10, "Get ART Image")

        cmd = "tftpboot 84000000 images/" + self.artimg[self.board_id]
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "usetprotect spm off; sf probe")

        msg(30, "Erase Kernel")

        cmd = "sf erase {0} {1}".format(self.kernel_address, self.kernel_size)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)

        msg(40, "Write Kernel")

        cmd = "sf write 0x84000000 {0} {1}".format(self.kernel_address, self.kernel_size)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        time.sleep(5)

        if self.erasecal == "True":
            self.pexp.expect_action(30, self.ubpmt[self.board_id], "sf erase 0x170000 0x10000")
            time.sleep(5)

        msg(50, "Clean RootFS")

        cmd = "sf erase {0} {1}".format(self.rootfs_address, self.rootfs_size)
        self.pexp.expect_action(300, self.ubpmt[self.board_id], cmd)
        time.sleep(5)

        msg(60, "Write RootFS")

        cmd = "sf write 0x84180000 {0} {1}".format(self.rootfs_address, self.rootfs_size)
        self.pexp.expect_action(180, self.ubpmt[self.board_id], cmd)
        time.sleep(5)

        self.pexp.expect_action(600, self.ubpmt[self.board_id], "printenv\r")

        self.pexp.expect_action(10, self.ubpmt[self.board_id], "re\r")
        time.sleep(60)

        msg(90, "Reboot")

        self.pexp.expect_only(120, "Linux version 4.4.60")

        msg(100, "Back to ART has completed")


def main():
    ubb_ipq840xx_mfg = UAPIPQ40XXMFG()
    ubb_ipq840xx_mfg.run()

if __name__ == "__main__":
    main()
