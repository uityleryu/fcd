#!/usr/bin/python3
import re
import sys
import os
import time
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

# kernel start addr
kenel_start_addr = {'ed10': "0x1a0000",
                    'ec25': "0x1a0000",
                    'ec26': "0x1a0000",
                    'ed11': "0x1a0000"}
# kernel size
kernel_size = {'ed10': "0xe60000",
               'ec25': "0x1e60000",
               'ec26': "0x1e60000",
               'ed11': "0xe60000"}


class MT7621MFGGeneral(ScriptBase):
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
        super(MT7621MFGGeneral, self).__init__()

    def sf_erase(self, flash_addr, size):
        """
        run cmd in uboot :[sf erase flash_addr size]
        Arguments:
            flash_addr {string}
            size {string}
        """
        log_debug(msg="Initializing sf => sf probe")
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="sf probe")

        earse_cmd = "sf erase " + flash_addr + " " + size
        log_debug(msg="run cmd " + earse_cmd)
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=earse_cmd)
        self.pexp.expect_only(timeout=90, exptxt="Erased: OK")
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=" ")

    def sf_write(self, flash_addr):
        """
        run cmd in uboot :[sf write address size]
        Arguments:
            address {string}
        """
        log_debug(msg="Initializing sf => sf probe")
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="sf probe")

        cmd = "sf write ${fileaddr} " + flash_addr + " ${filesize}"
        log_debug(msg="run cmd " + cmd)
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(timeout=90, exptxt=self.bootloader_prompt)
        self.pexp.expect_action(timeout=10, exptxt="", action=" ")

    def stop_uboot(self, timeout=30):
        if self.pexp is None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot", action="")
            self.pexp.expect_action(timeout=timeout, exptxt=self.bootloader_prompt, action="")

    def is_network_alive_in_uboot(self, retry=1):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.tftp_server)
            extext_list = ["host " + self.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=30, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def set_boot_netenv(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "set ipaddr " + self.dutip)
        self.pexp.expect_action(10, self.bootloader_prompt, "set serverip " + self.tftp_server)

    def flash_uboot(self):
        img = os.path.join(self.image, self.board_id+"-mfg.uboot")
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 84000000 " +img)
        self.pexp.expect_action(60, "Bytes transferred = "+img_size, "")

        self.sf_erase("0", "0x60000")
        self.sf_write("0")

    def flash_kernel(self):
        img = os.path.join(self.image, self.board_id+"-mfg.kernel")
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 84000000 " +img)
        self.pexp.expect_only(60, "Bytes transferred = "+img_size)

        address = kenel_start_addr[self.board_id]
        size = kernel_size[self.board_id]
        self.sf_erase(address, size)
        self.sf_write(address)


    def run(self):
        """
        Main procedure of back to ART
        """

        # Connect into DU using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        self.set_bootloader_prompt("MT7621 #")

        msg(no=1, out="Waiting - PULG in the device...")
        self.stop_uboot()

        msg(no=20, out='Setting up IP address in u-boot ...')
        self.set_boot_netenv()

        msg(no=30, out='Checking network connection to tftp server in u-boot ...')
        if self.is_network_alive_in_uboot(retry=3) is not True:
            error_critical("FAILED to ping tftp server in u-boot")

        msg(no=40, out='flash back to calibration kernel ...')
        self.flash_kernel()

        msg(no=60, out='Erase bootselect partition ...')
        self.sf_erase("0x90000", "0x10000")

        msg(no=70, out='flash back to calibration u-boot ...')
        self.flash_uboot()

        msg(no=80, out='Waiting for Calibration Linux ...')
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")
        self.pexp.expect_action(120, "BusyBox v1.12.1 ", "")

        msg(no=100, out="Back to ART has completed")


def main():
    mt7621_mfg_general = MT7621MFGGeneral()
    mt7621_mfg_general.run()


main()
