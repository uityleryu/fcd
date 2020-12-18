#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.common import Common
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

'''
    e7f9: LBE-5AC
'''


class AMAR9342MFG(ScriptBase):
    def __init__(self):
        super(AMAR9342MFG, self).__init__()
        self.bootloader_prompt = "ar7240>"
        self.uboot_art_img = "{}/{}-art-uboot.bin".format(self.image, self.board_id)

        self.grp1 = ["e7f9"]
        self.grp2 = []
        self.grp3 = []

        self.mfgtype = {
            "e7f9": "bin"
        }

        self.uboot_w_app = 0

    def stop_uboot(self):
        self.pexp.expect_action(120, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_action(30, self.bootloader_prompt, "")

    def flash_unlock(self):
        log_debug("Unlocking flash ... ")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "protect off all")
        self.pexp.expect_only(30, "Un-Protect Flash Bank")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubntctrl enabled")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "ubnt_hwp SPM off")

        if self.uboot_w_app == 1:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "go ${ubntaddr} usetprotect spm off")

    def update_uboot(self):
        cmd = "tftp 81000000 {}".format(self.uboot_art_img)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, self.uboot_art_img)
        self.pexp.expect_only(30, "Bytes transferred =")

        if self.board_id in self.grp1:
            cmd = "erase 9f000000 +0x50000; cp.b 0x81000000 0x9f000000 0x40000"
        elif self.board_id in self.grp2:
            cmd = "erase 9f000000 +0x50000; cp.b \$fileaddr 0x9f000000 \$filesize"
        elif self.board_id in self.grp3:
            cmd = "erase 0x9f000000 +0xff0000; cp.b 0x81000000 0x9f000000 0xff0000"

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "reset")
        self.stop_uboot()
        self.set_ub_net()
        self.is_network_alive_in_uboot()

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        self.stop_uboot()
        self.set_ub_net()
        self.is_network_alive_in_uboot()

        self.flash_unlock()
        msg(10, "Update ART U-boot ...")
        self.update_uboot()

        if self.mfgtype[self.board_id] == "bin":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv NORDCHK 1")
            time.sleep(5)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue -f -e")
            self.pexp.expect_only(30, "Starting TFTP server...")
            time.sleep(1)
            fw_path = os.path.join(self.fwdir, self.fwimg_mfg)
            cmd = "atftp --option \"mode octet\" -p -l {} {} 2>&1 > /dev/null".format(fw_path, self.dutip)
            log_debug("host cmd:" + cmd)
            self.fcd.common.xcmd(cmd)
            self.pexp.expect_only(60, "Firmware Version:")
            msg(30, "Firmware loaded")
            self.pexp.expect_only(60, "Copying partition 'u-boot' to flash memory:")
            msg(40, "Flashing u-boot ...")
            self.pexp.expect_only(60, "Copying partition 'kernel' to flash memory:")
            msg(50, "Flashing kernel ...")
            self.pexp.expect_only(60, "Copying partition 'rootfs' to flash memory:")
            msg(80, "Flashing rootfs ...")
            self.pexp.expect_only(200, "Firmware update complete.")
            msg(90, "Flashing Completed")

        self.pexp.expect_action(120, "login:", "root")
        self.pexp.expect_action(120, "Password:", "5up")

        cmd = "dd if=/dev/zero seek=20492 bs=1 count=2 of=/dev/mtdblock5"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)
        cmd = "hexdump -s 20492 -n 16 /dev/mtdblock5"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, post_exp="000500c 0000")
        msg(100, "Back to ART Completed")


def main():
    mfg = AMAR9342MFG()
    mfg.run()

if __name__ == "__main__":
    main()
