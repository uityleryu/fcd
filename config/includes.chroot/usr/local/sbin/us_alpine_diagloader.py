#!/usr/bin/python3
import sys
import time
import os
import stat
import filecmp
import re

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


UPDATEUB_EN = True
BOOTTFTP_EN = True

DIAG_VER = "usw-100g-v1.0.10"
IMAG_VER = "USW-100G_v1.0.7_20190722"
BOARDNAME = "usw-leaf-rev8"


class USALPINEDiagloader(ScriptBase):
    def __init__(self):
        super(USALPINEDiagloader, self).__init__()

        self.bootloader_prompt = "UDC"
        self.diagsh1 = "UBNT"
        self.diagsh2 = "DIAG"

    def stop_at_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        time.sleep(1)

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv tftpdir images/" + self.board_id + "-diag-")
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

    def lnx_netcheck(self):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd_retry(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)

    # loading the diag U-boot and diag recovery image basing on formal FW
    def load_diag_ub_uimg(self):
        self.login(username="ubnt", password="ubnt", timeout=100)

        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.lnx_netcheck()

        cmd = "tftp -g -r images/{0}-diag-uImage -l /tmp/uImage.r {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, self.linux_prompt)

        cmd = "tftp -g -r images/{0}-diag-boot.img -l /tmp/boot.img {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, self.linux_prompt)

        postexp = [
            r"Erasing blocks:.*\(100%\)",
            r"Writing data:.*\(100%\)",
            r"Verifying data:.*\(100%\)",
            self.linux_prompt
        ]
        cmd = "flashcp -v /tmp/boot.img {0}".format("/dev/mtd0")
        self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, self.linux_prompt)
        msg(20, "U-boot loading successfully")

        postexp = [
            r"Erasing blocks:.*\(100%\)",
            r"Writing data:.*\(100%\)",
            r"Verifying data:.*\(100%\)",
            self.linux_prompt
        ]
        cmd = "flashcp -v /tmp/uImage.r {0}".format("/dev/mtd5")
        self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, postexp)
        msg(20, "uImage loading successfully")

        self.pexp.expect_lnxcmd(60, self.linux_prompt, "reboot", self.linux_prompt)

    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        expit = [
            "Jun 19 2019 - 18:36:28",    # BSP U-boot-1
            "Jul 22 2019 - 11:59:31",    # BSP U-boot-2
            "Jul 03 2019 - 05:58:38"     # FW U-boot
        ]
        rt = self.pexp.expect_get_index(30, expit)
        if rt == 2:
            log_debug("Detect the FW U-boot version")
            self.load_diag_ub_uimg()
            msg(40, "Diag U-boot/uImage updating completing ...")
        else:
            pass

        self.stop_at_uboot()
        if BOOTTFTP_EN is True:
            self.set_boot_net()
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run boottftp")
        else:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootspi")

        self.pexp.expect_only(40, "Starting kernel")
        self.pexp.expect_only(80, "Welcome to UBNT PyShell")
        self.pexp.expect_lnxcmd(10, self.diagsh1, "diag", self.diagsh2)
        self.pexp.expect_lnxcmd(10, self.diagsh2, "npsdk speed 0 10", self.diagsh2)
        self.pexp.expect_lnxcmd(10, self.diagsh2, "shell", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth1 down", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 " + self.dutip, self.linux_prompt)
        self.lnx_netcheck()
        msg(50, "network configuration done in U-Boot ...")

        if UPDATEUB_EN is True:
            log_debug("downloading diag U-boot")
            cmd = "tftp -g -r images/f060-diag-boot.img -l /tmp/boot.img {0}".format(self.tftp_server)
            self.pexp.expect_lnxcmd_retry(300, self.linux_prompt, cmd, self.linux_prompt)
            log_debug("flashing diag U-boot")
            postexp = [
                r"Erasing blocks:.*\(50%\)",
                r"Erasing blocks:.*\(100%\)",
                r"Writing data:.*\(50%\)",
                r"Writing data:.*\(100%\)",
                r"Verifying data:.*\(50%\)",
                r"Verifying data:.*\(100%\)",
                self.linux_prompt
            ]
            cmd = "flashcp -v /tmp/boot.img {0}".format("/dev/mtd0")
            self.pexp.expect_lnxcmd_retry(600, self.linux_prompt, cmd, self.linux_prompt)

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "/ubnt/diag-ssd.sh format", "done")
        msg(70, "SSD format Completing ...")

        src_path = os.path.join(self.fwdir, self.board_id + "-diag-dt.img")
        dst_path = os.path.join(self.tftpdir, "dt.img")
        if os.path.isfile(dst_path) is not True:
            os.symlink(src_path, dst_path)

        src_path = os.path.join(self.fwdir, self.board_id + "-diag-uImage")
        dst_path = os.path.join(self.tftpdir, "uImage")
        if os.path.isfile(dst_path) is not True:
            os.symlink(src_path, dst_path)

        cmd = "/ubnt/diag-ssd.sh tftp {0}".format(self.tftp_server)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)
        self.pexp.expect_lnxcmd(20, self.linux_prompt, "reboot", self.linux_prompt)
        self.pexp.expect_only(40, "Starting kernel")
        self.pexp.expect_only(80, "Welcome to UBNT PyShell")
        self.pexp.expect_lnxcmd(20, self.diagsh1, "diag", self.diagsh2)
        self.pexp.expect_lnxcmd(20, self.diagsh2, "show version", DIAG_VER)
        self.pexp.expect_lnxcmd(20, self.diagsh2, "shell", self.linux_prompt)
        self.pexp.expect_lnxcmd(20, self.linux_prompt, "cat /etc/version", IMAG_VER)
        cmd = "/ubnt/boardname.sh {}".format(BOARDNAME)
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)
        self.pexp.expect_lnxcmd(20, self.linux_prompt, "cat /logs/boardname", BOARDNAME)

        msg(100, "Completing firmware upgrading ...")

        self.close_fcd()


def main():
    us_alpine_diagloader = USALPINEDiagloader()
    us_alpine_diagloader.run()

if __name__ == "__main__":
    main()
