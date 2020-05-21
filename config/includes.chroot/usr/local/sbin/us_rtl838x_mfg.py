#!/usr/bin/python3
import sys
import time
import os
import stat
import filecmp
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class USW_RTL838X_MFG(ScriptBase):
    def __init__(self):
        super(USW_RTL838X_MFG, self).__init__()

        # script specific vars
        self.bootloader_prompt = "uboot>"
        self.fwimg = self.board_id + "-t1.bin"

        self.empty_eeprom_md5sum = "fcd6bcb56c1689fcef28b57c22475bad"
        self.RFW_baudrate = "115200" # Release FirmWare baudrate
        self.T1_baudrate = "9600"    # T1 image baudrate

    def open_console(self, baudrate):
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b " + baudrate
        log_debug(msg=pexpect_cmd)
        self.pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=self.pexpect_obj)
        time.sleep(1)

    def close_console(self):
        self.pexpect_obj.close()

    def stop_at_uboot(self):
        self.pexp.expect_action(60, "Hit Esc key to stop autoboot", "\x1b")

    def setenv_uboot(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        #time.sleep(1)
        #self.pexp.expect_action(10, self.bootloader_prompt, "ping " + self.tftp_server)
        #self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

    def enter_urescue(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_action(10, self.bootloader_prompt, "bootubnt ubntrescue")

        # FIXME: workaround for usw-agg
        time.sleep(5)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ethaddr 00:00:00:00:00:1" + self.row_id)

        self.pexp.expect_action(15, self.bootloader_prompt, "bootubnt")
        self.pexp.expect_only(60, "Listening for TFTP transfer on")

    def fwupload(self):
        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir + "/" + self.fwimg,
               self.dutip]
        cmdj = ' '.join(cmd)
        time.sleep(3)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Signature Verfied, Success.")

    def fwupgrade(self):
        self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(120, "done")

    def imagecheck(self):
        self.pexp.expect_lnxcmd(240, "Please press Enter to activate this console", "")
        self.login()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /lib/build.properties", post_exp=self.linux_prompt)

    def eerase_eeprom(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if=/dev/zero ibs=1k skip=16320 count=64 of=/dev/mtdblock6", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "md5sum /dev/mtd6", post_exp=self.empty_eeprom_md5sum)

    def run(self):
        """
        Main procedure of backtoT1
        """
        self.fcd.common.config_stty(self.dev)

        self.open_console(baudrate=self.RFW_baudrate)
        msg(5, "Open serial port with baudrate " + self.RFW_baudrate + " successfully ...")

        self.stop_at_uboot()
        msg(10, "Enter uboot ...")

        self.setenv_uboot()
        msg(20, "Configure uboot network environment done ...")

        self.enter_urescue()
        msg(30, "Enter urescue mode and wait FW uploading ...")

        self.fwupload()
        msg(40, "Uploading firmware is done ...")

        self.fwupgrade()
        msg(50, "Upgrading firmware is done ...")

        #self.close_console()
        #msg(55, "Close console ...")
        #
        #self.open_console(baudrate=self.T1_baudrate)
        #msg(60, "Open serial port with baudrate " + self.T1_baudrate + " successfully ...")

        self.imagecheck()
        msg(70, "Boot into T1 image successfully ...")

        self.eerase_eeprom()
        msg(80, "eeprom partition is empty ...")

        msg(100, "Completing backtoT1 ...")
        self.close_fcd()

def main():
    usw_rtl838x_mfg = USW_RTL838X_MFG()
    usw_rtl838x_mfg.run()

if __name__ == "__main__":
    main()
