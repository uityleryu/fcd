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
        self.init_vars()

    def init_vars(self):
        '''
        AirMax: AME
            dc99: GBE
            dc9a: GBE-LR
        UAP:
            dc98: UAP-UBB
            dc9c: UAP-UBB 831
        AirFiber:
            dc9b: AF60
            dc9e: AF60-LR
        '''
        # U-boot prompt
        self.ubpmt = {
            'dc99': "\(IPQ40xx\) # ",
            'dc9a': "\(IPQ40xx\) # ",
            'dc98': "\(IPQ40xx\) # ",
            'dc9c': "\(IPQ40xx\) # ",
            'dc9b': "\(IPQ40xx\) # ",
            'dc9e': "\(IPQ40xx\) # "
        }

        # linux console prompt
        self.lnxpmt = {
            'dc99': "root@OpenWrt",
            'dc9a': "root@OpenWrt",
            'dc98': "root@OpenWrt",
            'dc9c': "root@OpenWrt",
            'dc9b': "root@OpenWrt",
            'dc9e': "root@OpenWrt"
        }

        self.artimg = {
            'dc99': "dc99-mfg.bin",
            'dc9a': "dc9a-mfg.bin",
            'dc98': "dc98-mfg.bin",
            'dc9c': "dc9c-mfg.bin",
            'dc9b': "dc9b-mfg.bin",
            'dc9e': "dc9b-mfg.bin"
        }

        self.knladdr = {
            'dc99': "0x0",
            'dc9a': "0x0",
            'dc98': "0x0",
            'dc9c': "0x0",
            'dc9b': "0x0",
            'dc9e': "0x0"
        }

        self.knlsz = {
            'dc99': "0x170000",
            'dc9a': "0x170000",
            'dc98': "0x170000",
            'dc9c': "0x170000",
            'dc9b': "0x170000",
            'dc9e': "0x170000"
        }

        self.rfaddr = {
            'dc99': "0x180000",
            'dc9a': "0x180000",
            'dc98': "0x180000",
            'dc9c': "0x180000",
            'dc9b': "0x180000",
            'dc9e': "0x180000"
        }

        self.rfsz = {
            'dc99': "0x1a00000",
            'dc9a': "0x1a00000",
            'dc98': "0x1d00000",
            'dc9c': "0x1d00000",
            'dc9b': "0x1d00000",
            'dc9e': "0x1d00000"
        }

        self.linux_prompt = self.lnxpmt[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]

        self.kernel_address =  self.knladdr[self.board_id]
        self.kernel_size =  self.knlsz[self.board_id]
        self.rootfs_address = self.rfaddr[self.board_id]
        self.rootfs_size = self.rfsz[self.board_id]

    def stop_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "")

    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)

    def run(self):
        """
        Main procedure of factory
        """
        msg(1, "Start Procedure")
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Stop U-boot")
        self.stop_uboot()
        time.sleep(3)
        self.set_uboot_network()

        msg(10, "Get ART Image")
        cmd = "tftpboot 84000000 images/{}".format(self.artimg[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "usetprotect spm off")

        msg(30, "Starting erasing Kernel")
        cmd = "sf probe; sf erase {0} {1}".format(self.kernel_address, self.kernel_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        msg(40, "Starting writing Kernel")
        cmd = "sf probe; sf write 0x84000000 {0} {1}".format(self.kernel_address, self.kernel_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(5)

        if self.erasecal == "True":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf erase 0x170000 0x10000")
            time.sleep(5)

        msg(50, "Clean RootFS")
        cmd = "sf probe; sf erase {0} {1}".format(self.rootfs_address, self.rootfs_size)
        self.pexp.expect_ubcmd(300, self.bootloader_prompt, cmd)
        time.sleep(5)

        msg(60, "Write RootFS")
        cmd = "sf prob; sf write 0x84180000 {0} {1}".format(self.rootfs_address, self.rootfs_size)
        self.pexp.expect_ubcmd(180, self.bootloader_prompt, cmd)
        time.sleep(5)

        self.pexp.expect_ubcmd(600, self.bootloader_prompt, "printenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")
        time.sleep(60)

        msg(90, "Reboot")
        self.pexp.expect_only(120, "Linux version 4.4.60")

        msg(100, "Back to ART has completed")
        self.close_fcd()


def main():
    ubb_ipq840xx_mfg = UAPIPQ40XXMFG()
    ubb_ipq840xx_mfg.run()

if __name__ == "__main__":
    main()
