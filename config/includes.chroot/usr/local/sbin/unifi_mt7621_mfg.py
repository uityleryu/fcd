#!/usr/bin/python3
import re
import sys
import os
import time
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


'''
addr_map_usw: erased partition is uboot+uboot-evn+factory+ee+bs+cfg+kernel0
it means erase flash from 0x0 to kenel0 where depend on the model.
format : board_id: (start_addr, len)
'''
addr_map_usw = {'ed10': ('0x0', '0x8d0000'),
                'ed11': ('0x0', '0x8d0000')}

'''
addr_map_uap: partitially erase partition, the order is bs2kernel0 -> factory -> uboot
format : board_id: {partition: (start_addr, len)}
'''
addr_map_uap = {
                  'ec25': {
                    'uboot': ('0', '0x60000'),
                    'factory': ('0x70000', '0x10000'),
                    'bs': ('0x90000', '0x10000'),
                    'kernel0': ('0x1a0000', '0xf30000')
                  },
                  'ec26': {
                    'uboot': ('0', '0x60000'),
                    'factory': ('0x70000', '0x10000'),
                    'bs': ('0x90000', '0x10000'),
                    'kernel0': ('0x1a0000', '0xf30000')
                  }
                }


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

    def erase_partition(self, flash_addr, size):
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

    def write_img(self, flash_addr):
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
        self.pexp.expect_action(10, self.bootloader_prompt, "mtk network on")
        self.pexp.expect_action(10, self.bootloader_prompt, "set ipaddr " + self.dutip)
        self.pexp.expect_action(10, self.bootloader_prompt, "set serverip " + self.tftp_server)

    def transfer_img(self, filename):
        img = os.path.join(self.image, filename)
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 84000000 " +img)
        self.pexp.expect_only(60, "Bytes transferred = "+img_size)

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

        if self.board_id in addr_map_uap:
            log_debug("Back to T1 with UAP rule")
            msg(no=40, out='flash back to calibration kernel ...')
            self.transfer_img(self.board_id+"-mfg.kernel")

            flash_addr = addr_map_uap[self.board_id]['kernel0'][0]
            flash_size = addr_map_uap[self.board_id]['kernel0'][1]
            log_debug("kernel from {} ,len {}".format(flash_addr, flash_size))
            self.erase_partition(flash_addr=flash_addr, size=flash_size)
            self.write_img(flash_addr=flash_addr)

            msg(no=50, out='Erase bootselect partition ...')
            flash_addr = addr_map_uap[self.board_id]['bs'][0]
            flash_size = addr_map_uap[self.board_id]['bs'][1]
            log_debug("bs from {} to {}".format(flash_addr, flash_size))
            self.erase_partition(flash_addr=flash_addr, size=flash_size)

            if self.erasecal == "True":
                msg(no=60, out='Erase calibration data ...')
                flash_addr = addr_map_uap[self.board_id]['factory'][0]
                flash_size = addr_map_uap[self.board_id]['factory'][1]
                log_debug("cal from {} ,len {}".format(flash_addr, flash_size))
                self.erase_partition(flash_addr=flash_addr, size=flash_size)

            msg(no=70, out='flash back to calibration u-boot ...')
            self.transfer_img(self.board_id+"-mfg.uboot")
            flash_addr = addr_map_uap[self.board_id]['uboot'][0]
            flash_size = addr_map_uap[self.board_id]['uboot'][1]
            log_debug("uboot from {} ,len {}".format(flash_addr, flash_size))
            self.erase_partition(flash_addr=flash_addr, size=flash_size)
            self.write_img(flash_addr=flash_addr)

        else:
            log_debug("Back to T1 with USW rule")
            msg(no=40, out='flash back to T1 image...')
            self.transfer_img(self.board_id+"-mfg.bin")

            flash_addr = addr_map_usw[self.board_id][0]
            flash_size = addr_map_usw[self.board_id][1]
            self.erase_partition(flash_addr, flash_size)
            self.write_img(flash_addr)

        msg(no=80, out='Waiting for Calibration Linux ...')

        self.pexp.expect_action(10, self.bootloader_prompt, "reset")

        if self.board_id in addr_map_uap:
            self.pexp.expect_only(120, "BusyBox")
        else:
            self.pexp.expect_action(120, "Please press Enter to activate this console","")
            self.pexp.expect_action(30, "", "")
            self.pexp.expect_action(30, "UBNT login: ", "ubnt")
            self.pexp.expect_action(30, "Password: ", "ubnt")
            self.pexp.expect_only(30, "BusyBox v1.25.1")

        msg(no=100, out="Back to ART has completed")


def main():
    mt7621_mfg_general = MT7621MFGGeneral()
    mt7621_mfg_general.run()


main()
