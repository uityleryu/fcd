#!/usr/bin/python3
import re
import sys
import os
import time
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class USMFGGeneral(ScriptBase):
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
        super(USMFGGeneral, self).__init__()

    def sf_erase(self, address, erase_size):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string}
        """
        log_debug(msg="Initializing sf => sf probe")
        self.pexp.expect_action(timeout=10, exptxt="", action="sf probe")
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)

        earse_cmd = "sf erase " + address + " " + erase_size
        log_debug(msg="run cmd " + earse_cmd)
        self.pexp.expect_action(timeout=10, exptxt="", action=earse_cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)

    def uclearcfg(self):
        """
        run cmd : uclearcfg
        clear linux config data
        """
        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uclearcfg")
        self.pexp.expect_only(timeout=20, exptxt="Done.")
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)
        log_debug(msg="Linux configuration erased")

    def download_and_update_firmware_in_linux(self):
        """
        After update firmware, linux will be restarting
        """
        log_debug(msg="Download " + self.fwimg_mfg + " from " + self.tftp_server)
        self.pexp.expect_action(timeout=10, exptxt="", action="")
        index = self.pexp.expect_get_index(timeout=10, exptxt=r".*" + self.linux_prompt)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Linux Hung!!")
        time.sleep(5)
        for _ in range(3):
            tftp_cmd = "cd /tmp/; tftp -r {0}/{1} -l fwupdate.bin -g {2}".format(
                                                    "images",
                                                    self.fwimg_mfg,
                                                    self.tftp_server)

            self.pexp.expect_action(timeout=10, exptxt="", action=tftp_cmd)
            extext_list = ["Invalid argument", r".*#"]
            index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
            if index == self.pexp.TIMEOUT:
                error_critical(msg="Failed to download Firmware")
            elif index == 0:
                continue
            elif index == 1:
                break
        self.pexp.expect_action(timeout=10, exptxt="", action="syswrapper.sh upgrade2")
        index = self.pexp.expect_get_index(timeout=120, exptxt="Restarting system.")
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to flash firmware !")
        msg(no=40, out="Firmware flashed")

    def stop_uboot(self, timeout=30):
        if self.pexp is None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot", action="")
            self.pexp.expect_action(timeout=timeout, exptxt=self.bootloader_prompt, action="")

    def is_mdk_exist_in_uboot(self):
        is_exist = False
        log_debug(msg="Checking if MDK available in U-boot.")
        self.pexp.expect_action(timeout=10, exptxt="", action="")
        self.pexp.expect_only(timeout=30, exptxt=self.bootloader_prompt)
        self.pexp.expect_action(timeout=10, exptxt="", action="mdk_drv")
        extext_list = ["Found MDK device",
                       "MDK initialized failed",
                       "Unknown command"]
        index = self.pexp.expect_get_index(timeout=30, exptxt=extext_list)
        if index == 0 or index == 1:
            is_exist = True
        elif index == 2 or index == self.pexp.TIMEOUT:
            is_exist = False
            self.pexp.expect_only(timeout=30, exptxt=self.bootloader_prompt)
        return is_exist

    def is_network_alive_in_linux(self):
        time.sleep(3)
        self.pexp.expect_action(timeout=10, exptxt="", action="\nifconfig;ping " + self.tftp_server)
        extext_list = ["ping: sendto: Network is unreachable",
                       r"64 bytes from " + self.tftp_server]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == 0 or index == self.pexp.TIMEOUT:
            self.pexp.expect_action(timeout=10, exptxt="", action="\003")
            return False
        elif index == 1:
            self.pexp.expect_action(timeout=10, exptxt="", action="\003")
            return True

    def is_network_alive_in_uboot(self, retry=1):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.tftp_server)
            extext_list = ["host " + self.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def reset_and_login_linux(self):
        """
        should be called in u-boot
        after login to linux, check if network works, if not, reboot and try again
        """
        self.pexp.expect_action(timeout=10, exptxt="", action="reset")
        is_network_alive = False
        for _ in range(3):
            self.pexp.expect_action(timeout=200, exptxt="Please press Enter to activate this console", action="")
            self.login()
            for retry in range(3):
                is_network_alive = self.is_network_alive_in_linux()
                if is_network_alive is True:
                    break
                else:
                    log_debug("Retry checking network (retry=" + str(retry) + ")")
                    time.sleep(3)
            if is_network_alive is False:
                self.pexp.expect_action(timeout=10, exptxt="", action="reboot")
                continue
            else:
                break
        if is_network_alive is False:
            error_critical(msg="Network is Unreachable")
        else:
            self.pexp.expect_action(timeout=10, exptxt="", action="\003")
            index = self.pexp.expect_get_index(timeout=10, exptxt=r".*" + self.linux_prompt)
            if index == self.pexp.TIMEOUT:
                error_critical(msg="Linux Hung!!")
            self.pexp.expect_action(timeout=10, exptxt="", action="")
            index = self.pexp.expect_get_index(timeout=10, exptxt=r".*" + self.linux_prompt)
            if index == self.pexp.TIMEOUT:
                error_critical(msg="Linux Hung!!")

    def decide_uboot_env_mtd_memory(self):
        """
        decide by output of cmd [print mtdparts]
        Returns:
            [string, string] -- address, size
        """
        self.pexp.expect_action(timeout=10, exptxt="", action="print mtdparts")
        self.pexp.expect_only(timeout=10, exptxt=self.bootloader_prompt)
        output = self.pexp.proc.before
        if self.var.us.flash_mtdparts_64M in output:
            return ("0x1e0000", "0x10000")  # use 64mb flash
        else:
            return ("0xc0000", "0x10000")

    def flash_firmware_no_mdk(self):
        (uboot_env_address, uboot_env_address_size) = self.decide_uboot_env_mtd_memory()

        log_debug(msg="Erasing uboot-env")
        self.sf_erase(address=uboot_env_address, erase_size=uboot_env_address_size)

        self.reset_and_login_linux()
        self.download_and_update_firmware_in_linux()
        self.stop_uboot()

        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uappinit")
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)
        log_debug(msg="Initialize ubnt app by uappinit")
        log_debug(msg="Flashed firmware with no mdk package and currently stopped at u-boot....")

    def flash_firmware_with_mdk(self):
        """
        after flash firmware, DU will be resetting
        """
        log_debug(msg="Starting in the urescue mode to program the firmware")
        self.pexp.expect_action(timeout=10, exptxt="", action="{0}usetbid {1}".format(self.cmd_prefix,
                                                                                      self.board_id))
        self.pexp.expect_only(timeout=10, exptxt="Done.")

        if self.board_id in self.var.us.usw_group_1:
            self.pexp.expect_action(timeout=10, exptxt="", action="mdk_drv")
            self.pexp.expect_only(timeout=30, exptxt=self.bootloader_prompt)
            time.sleep(3)

        self.pexp.expect_action(timeout=10, exptxt="", action="setenv ethaddr " + self.var.us.fake_mac)
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="setenv serverip " +
                                self.tftp_server)
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="setenv ipaddr " +
                                self.var.us.ip)
        if self.is_network_alive_in_uboot(retry=3) is False:
            error_critical(msg="Can't ping the FCD server !")

        self.pexp.expect_action(timeout=10, exptxt="", action="urescue -u")
        extext_list = ["TFTPServer started. Wating for tftp connection...",
                       "Listening for TFTP transfer"]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to start urescue")
        elif index == 0 or index == 1:
            log_debug(msg="TFTP is waiting for file")
        atftp_cmd = "atftp --option \"mode octet\" -p -l {0}/{1}/{2} {3}".format(
                                                                                self.tftpdir,
                                                                                "images",
                                                                                self.fwimg_mfg,
                                                                                self.var.us.ip)
        msg(no=70, out="DUT is requesting the firmware from FCD server")
        log_debug(msg="Run cmd on host:" + atftp_cmd)
        self.fcd.common.xcmd(cmd=atftp_cmd)
        self.pexp.expect_only(timeout=150, exptxt=self.bootloader_prompt)
        log_debug(msg="FCD completed the firmware uploading")
        self.uclearcfg()
        msg(no=80, out="DUT completed erasing the calibration data")

        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uwrite -f")
        self.pexp.expect_only(timeout=20, exptxt="Firmware Version:")
        index = self.pexp.expect_get_index(timeout=300, exptxt="Copying to 'kernel0' partition. Please wait... :  done")
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to flash firmware.")
        index = self.pexp.expect_get_index(timeout=200, exptxt="Firmware update complete.")
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to flash firmware.")
        log_debug(msg="DUT completed programming the firmware into flash, will be rebooting")

        self.pexp.expect_only(timeout=120, exptxt="Verifying Checksum ... OK")

    def run(self):
        """
        Main procedure of back to ART
        """
        self.fcd.common.config_stty(self.dev)

        # Connect into DU using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(no=1, out="Waiting - PULG in the device...")

        self.stop_uboot()
        msg(no=5, out="Go into U-boot")

        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uappinit")
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)
        log_debug(msg="Initialize ubnt app by uappinit")

        if self.is_mdk_exist_in_uboot() is True:
            log_debug(msg="There is MDK available")
            self.flash_firmware_with_mdk()
        else:
            log_debug(msg="There isn't MDK available")
            self.flash_firmware_no_mdk()
            self.flash_firmware_with_mdk()

        msg(no=100, out="Back to ART has completed")


def main():
    us_mfg_general = USMFGGeneral()
    us_mfg_general.run()


if __name__ == "__main__":
    main()
