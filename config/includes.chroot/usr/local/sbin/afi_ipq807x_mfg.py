#!/usr/bin/python3
import time
from distutils.util import strtobool

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, msg

class AFIIPQ807XMFG(ScriptBase):
    def __init__(self):
        super(AFIIPQ807XMFG, self).__init__()
        self.bootloader_prompt = "IPQ807x#"
        self.UPDATE_UBOOT_KERNEL = True
        self.ERASE_DEVRAG        = bool(strtobool(self.erase_devreg))
        self.ERASE_CAL           = bool(strtobool(self.erasecal))
        self.CHECK_T1_FW         = True

    def init_uboot(self):
        self.pexp.expect_ubcmd(30, "to stop", "")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        time.sleep(3)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_ubcmd(10, "is alive", "")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "imgaddr=0x44000000")

    def update_uboot_kernel(self):
        self.init_uboot()
        sstr = [
            "tftpboot",
            "$imgaddr",
            "images/" + self.board_id + "-mfg.img"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, sstrj)
        self.pexp.expect_only(60, "Bytes transferred")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "source $imgaddr:script")
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "")
        if self.ERASE_DEVRAG is True:
            msg(30, "Erase devreg data")
            self.erase_devreg_data()

        if self.ERASE_CAL is True:
            msg(40, "Erase calibration data")
            self.erase_cal_data()  
 
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        self.pexp.expect_only(10, "resetting")

    def erase_devreg_data(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf erase 0x610000 0x10000")
        self.pexp.expect_ubcmd(30, "Erased: OK", "")

    def erase_cal_data(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf erase 0x5d0000 0x40000")
        self.pexp.expect_ubcmd(30, "Erased: OK", "")

    def check_t1_fw(self):
        self.pexp.expect_lnxcmd(60, "Please press Enter to activate this console", "", retry=1)
        self.pexp.expect_only(10, "Amplifi-ALN BSP image", "")

    def run(self):
        msg(5, "Open serial port")
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)

        if self.UPDATE_UBOOT_KERNEL is True:
            msg(10, "Update the U-boot/Kernel")
            self.update_uboot_kernel()

        if self.CHECK_T1_FW is True:
            msg(50, "Check T1 FW")
            self.check_t1_fw()

        msg(100, "BackToT1 done")
        self.close_fcd()

def main():
    afi_ipq807x_mfg = AFIIPQ807XMFG()
    afi_ipq807x_mfg.run()

if __name__ == "__main__":
    main()
