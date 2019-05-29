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


PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = False

diagsh = ""


class USALPINEDiagloader(ScriptBase):
    def __init__(self):
        super(USALPINEDiagloader, self).__init__()
        global diagsh

        self.bootloader_prompt = "UDC"
        diagsh = "UBNT"

    def stop_at_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        time.sleep(1)

    def lnx_netcheck(self):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd_retry(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)

    # loading the diag U-boot and diag recovery image basing on formal FW
    def load_diag_ub_uimg(self):
        self.login(username="ubnt", password="ubnt", timeout=100)
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
            "May 06 2019 - 12:15:33",
            "May 17 2019 - 13:22:41",
            "May 16 2019 - 09:50:32"
        ]
        rt = self.pexp.expect_get_index(30, expit)
        if rt == 2:
            log_debug("Detect the FW U-boot version")
            self.load_diag_ub_uimg()
        elif rt == -1:
            error_critical("Timeout can't find the correct U-boot!!")
        else:
            log_debug("Find the correct U-boot version")

        msg(40, "Diag U-boot/uImage updating completing ...")

        self.stop_at_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootspi")
        self.pexp.expect_only(40, "Starting kernel")
        self.pexp.expect_only(80, "Welcome to UBNT PyShell")
        self.pexp.expect_lnxcmd(10, diagsh, "diag", "DIAG")
        self.pexp.expect_lnxcmd(10, "DIAG", "npsdk speed 0 10", "DIAG")
        self.pexp.expect_lnxcmd(10, "DIAG", "shell", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth1 down", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 " + self.dutip, self.linux_prompt)
        self.lnx_netcheck()
        msg(50, "network configuration done in U-Boot ...")

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
        msg(100, "Completing firmware upgrading ...")

        self.close_fcd()


def main():
    us_alpine_diagloader = USALPINEDiagloader()
    us_alpine_diagloader.run()

if __name__ == "__main__":
    main()
