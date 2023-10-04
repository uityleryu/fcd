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
    e580: UWB-XG
'''


class UAPWIFIBASESTATIONMFG(ScriptBase):
    def __init__(self):
        super(UAPWIFIBASESTATIONMFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.bootloader_prompt = "\(IPQ\) #"

    def enter_uboot(self):
        rt = self.pexp.expect_action(30, "Hit any key to stop autoboot|Autobooting in 2 seconds, press", "\x1b\x1b")

        retry = 2
        while retry > 0:
            if rt != 0:
                error_critical("Failed to detect device")

            try:
                self.pexp.expect_action(10, self.bootloader_prompt, "\x1b\x1b")
                break
            except Exception as e:
                self.bootloader_prompt = "=>"
                log_debug("Change prompt to {}".format(self.bootloader_prompt))
                retry -= 1

        self.set_ub_net()
        self.is_network_alive_in_uboot()

    def update_art(self):
        cmd = "sf probe; tftpboot 0x44000000 images/{}-art.bin".format(self.board_id)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, "Bytes transferred")

        cmd = "sf erase 0x0 0x2000000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "sf write 0x44000000 0x0 $filesize"
        self.pexp.expect_ubcmd(400, self.bootloader_prompt, cmd)

        self.pexp.expect_ubcmd(400, self.bootloader_prompt, "reset")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        self.enter_uboot()
        msg(30, "Enter U-Boot successfully ...")
        self.update_art()
        self.enter_uboot()

        msg(100, "Update ART image successfully ...")
        self.close_fcd()


def main():
    factory = UAPWIFIBASESTATIONMFG()
    factory.run()


if __name__ == "__main__":
    main()
