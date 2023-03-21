#!/usr/bin/python3
import os
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical
import time

class MT7628MFGGeneral(ScriptBase):
    """
    command parameter description for BackToT1
    command: python3
    para0:   script
    para1:   slot ID
    para2:   UART device number
    para3:   FCD host IP
    para4:   system ID
    para5:   Erase calibration data selection
    ex: [script, 1, 'ttyUSB1', '192.168.1.19', 'eb23', True]
    """
    def __init__(self):
        super(MT7628MFGGeneral, self).__init__()
        
        self.bspimg = "images/" + self.board_id + "-nor.bin"

    def stop_uboot(self, timeout=30):
        self.set_bootloader_prompt(">")
        self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot", action="")

    def set_boot_netenv(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ethaddr " + self.premac)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def write_img(self):
        log_debug(msg="Write BSP image")
        
        cmd = "tftpboot 0x80001000 {}".format(self.bspimg)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        # let LCM stop work
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "mw 0x10000060 0x44050414; mw 0x10000600 0x40; mw 0x10000620 0xfc032c71;")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf probe; sf erase 0x0 0x1000000; sf write 0x80001000 0x0 0x1000000")
        ## Uboot of BSP
        # sf probe; sf erase 0x0 0x1000000; sf write 0x80001000 0x0 0x1000000;
        # SF: Detected mx25l12805d with page size 256 Bytes, erase size 64 KiB, total 16 MiB
        # SF: 16777216 bytes @ 0x0 Erased: OK
        # device 0 whole chip
        # SF: 16777216 bytes @ 0x0 Written: OK
        # =>


        ## Uboot of FW
        # SF: Detected mx25l25635e with page size 256 Bytes, erase size 64 KiB, total 32 MiB
        # SF: 16777216 bytes @ 0x0 Erased: OK
        # uboot>
        
        self.pexp.expect_only(240, "Erased: OK")
        # self.pexp.expect_only(120, "Written: OK")    #BSP uboot, have "Written", FW Uboot have no Written
        # Uboot, if you enter the "Enter", uboot will run previous command so "^c" is to avoid to re-run re-program flash again
        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "^c")

    def reset_uboot(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        # self.pexp.expect_only(120, "BusyBox")

    def t1_image_check(self):
        self.pexp.expect_lnxcmd(120, "br-lan:", "dmesg -n1", "#", retry=0)

    def run(self):
        """
        Main procedure of back to ART
        """
        # Connect into DU using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        
        msg(no=10, out="Waiting - PULG in the device...")
        self.stop_uboot()

        msg(no=20, out='Setting up IP address in u-boot ...')
        self.set_boot_netenv()

        msg(no=30, out='Checking network connection to tftp server in u-boot ...')
        self.is_network_alive_in_uboot(retry=8)

        msg(no=50, out='flash back to T1 kernel and u-boot ...')
        self.write_img()

        msg(no=80, out='Waiting for T1 booting ...')
        self.reset_uboot()
        
        # self.pexp.expect_only(60, "Booting kernel from Legacy Image at")
        # Check if we are in T1 image
        self.t1_image_check()
        msg(90, 'Check T1 image done ...')

        msg(no=100, out="Back to T1 has completed")
        self.close_fcd()

def main():
    mt7628_mfg_general = MT7628MFGGeneral()
    mt7628_mfg_general.run()

if __name__ == "__main__":
    main()
