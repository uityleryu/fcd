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

    def update_nor(self):
        # cmd = "sf probe; sf erase 0x0 0x1C0000; sf write {} 0x0 0x1C0000".format(self.mem_addr)
        # log_debug(cmd)
        # self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        # self.pexp.expect_only(60, "Erased: OK")
        # self.pexp.expect_only(60, "Written: OK")

        if self.erasecal == "True":
            log_debug("Will Delete Calibration data")
        #     cal_offset = "0x1C0000"
        #     cmd = "sf erase 0x1C0000 0x070000"
        #     log_debug("Erase calibration data ...")
        #     log_debug(cmd)
        #     self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        #     self.pexp.expect_only(60, "Erased: OK")

        if self.erase_devreg == "True":
            log_debug("Will Delete DevReg data")
            # devreg_offset = "0x80000"
            # cmd = "sf erase 0x80000 0x010000"
            # log_debug("Erase devreg data ...")
            # log_debug(cmd)
            # self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
            # self.pexp.expect_only(60, "Erased: OK")

    def stop_uboot(self, timeout=30):
        self.set_bootloader_prompt(">")
        # if self.pexp is None:
        #     error_critical(msg="No pexpect obj exists!")
        # else:
        #     log_debug(msg="Stopping U-boot")
        #     self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot", action="")
        #     try:
        #         self.pexp.expect_action(timeout=5, exptxt=self.bootloader_prompt, action="")
        #     except Exception as e:
        #         self.set_bootloader_prompt("=>")
        #         log_debug(msg="Changed uboot prompt to =>")
        #         self.pexp.expect_action(timeout=5, exptxt=self.bootloader_prompt, action="")
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
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf probe; sf erase 0x0 0x2000000; sf write 0x80001000 0x0 0x2000000")
        ## Uboot of BSP
        # SF: Detected mx25l25635e with page size 256 Bytes, erase size 64 KiB, total 32 MiB
        # SF: 393216 bytes @ 0x0 Erased: OK
        # device 0 offset 0x0, size 0x2c3f0
        # SF: 181232 bytes @ 0x0 Written: OK
        # =>

        ## Uboot of FW
        # SF: Detected mx25l25635e with page size 256 Bytes, erase size 64 KiB, total 32 MiB
        # SF: 16777216 bytes @ 0x0 Erased: OK
        # uboot>
        
        self.pexp.expect_only(240, "Erased: OK")
        # self.pexp.expect_only(120, "Written: OK")    #BSP uboot, have "Written", FW Uboot have no Written
        # Uboot, if you enter the "Enter", uboot will run previous command so "^c" is to avoid to re-run re-program flash again
        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "^c")

    def is_mfg_uboot(self):
        ret = self.pexp.expect_get_output("version", self.bootloader_prompt)
        log_debug("verison ret: "+str(ret))
        if "U-Boot " not in ret:
            return False
        return True

    def reset_uboot(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        # self.pexp.expect_only(120, "BusyBox")

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
        self.update_nor()

        msg(no=20, out='Setting up IP address in u-boot ...')
        self.set_boot_netenv()

        msg(no=30, out='Checking network connection to tftp server in u-boot ...')
        self.is_network_alive_in_uboot(retry=8)

        msg(no=50, out='flash back to T1 kernel and u-boot ...')
        self.write_img()

        msg(no=80, out='Waiting for T1 booting ...')
        self.reset_uboot()
        
        self.pexp.expect_only(60, "Booting kernel from Legacy Image at")

        msg(no=100, out="Back to T1 has completed")
        self.close_fcd()

def main():
    mt7628_mfg_general = MT7628MFGGeneral()
    mt7628_mfg_general.run()

if __name__ == "__main__":
    main()
