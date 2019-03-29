#!/usr/bin/python3
import sys
import time
import os
import stat
import filecmp
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

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv tftpdir images/" + self.board_id + "-diag-")
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

    def ubupdate(self):
        self.stop_at_uboot()
        self.set_boot_net()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "bootupd done")
        self.pexp.expect_only(30, "variables are deleted from flash using the delenv script")
        time.sleep(1)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

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

        msg(10, "Updating diagnostic U-boot ...")
        self.ubupdate()
        self.stop_at_uboot()
        msg(40, "Diagnostic U-boot updating completing ...")

        self.set_boot_net()
        msg(50, "network configuration done in U-Boot ...")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run boottftp")
        self.pexp.expect_only(40, "Starting kernel")
        self.pexp.expect_only(80, "Welcome to UBNT PyShell")
        self.pexp.expect_lnxcmd(10, diagsh, "exit", self.linux_prompt)
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

        self.pexp.expect_lnxcmd(30, self.linux_prompt, "/ubnt/diag-ssd.sh tftp " + self.tftp_server, self.linux_prompt)
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
