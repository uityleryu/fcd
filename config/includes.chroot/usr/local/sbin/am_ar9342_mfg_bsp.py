#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    FFFFF: 113-00306 NBM2-HP
'''


class AMAR9342MFG(ScriptBase):
    def __init__(self):
        super(AMAR9342MFG, self).__init__()
        self.bootloader_prompt = "ar7240>|ath>"

        self.mfgtype = {
            "fffff": "bin"
        }

    def stop_uboot(self):
        self.pexp.expect_action(120, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_action(30, self.bootloader_prompt, "")

    def flash_unlock(self):
        log_debug("Unlocking flash ... ")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "protect off all")
        self.pexp.expect_only(30, "Un-Protect Flash Bank")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubntctrl enabled")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "ubnt_hwp SPM off")

        '''
            Use the command: setmac to check if it is ART U-Boot or Shipping U-Boot
            This is not a good way but there is no any way could diferentiate between them
        '''
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setmac")
        expect_list = [
            "Unknown command"
        ]
        index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
        if index < 0:
            log_debug("setmac successfully")
            # error_critical("Can't find expected message after usetbrev ... ")
        else:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "go ${ubntaddr} usetprotect spm off")


    def update_image(self):

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv NORDCHK 1")
        time.sleep(5)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue -f")
        self.pexp.expect_only(30, "Starting TFTP server...")
        time.sleep(1)
        fw_path = os.path.join(self.fwdir, self.fwimg_mfg)
        cmd = "atftp --option \"mode octet\" -p -l {} {} 2>&1 > /dev/null".format(fw_path, self.zero_ip)
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
        msg(20, "Update ART image ...")
        self.update_image()

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
