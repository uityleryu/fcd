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

VTYSH_EN = True
UPDATEUB_EN = True
UPDATEDIAG_EN = True
SSDFDISK_EN = True
WRITEFAKEBIN_EN = True
VERCHECK_EN = True
SETDIAGDF_EN = True
LOADLCMFW_EN = True

IMAG_VER = "v4.1.16-preload-rc10"
BOARDNAME = "usw-100g-mfg"


class USALPINEDiagloader(ScriptBase):
    def __init__(self):
        super(USALPINEDiagloader, self).__init__()

        self.bootloader_prompt = "UDC"
        self.diagsh1 = "UBNT> "
        self.diagsh2 = "DIAG# "
        self.lcmfw = "/tmp/lcmfw.bin"
        self.lcmfwver = "v3.0.4-0-gf89bc2b"

    def stop_at_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        time.sleep(1)

    def boot_diag_from_spi(self):
        cmdset = [
            "sf probe; sf read $loadaddr_payload 0x200000 0x3e00000",
            "setenv fitbootconf 0x08000004#udc@1",
            "run bootargsrecovery",
            "bootm $fitbootconf"
        ]
        for idx in range(len(cmdset)):
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmdset[idx])

    def set_lnx_net(self):
        log_debug("Starting to configure the networking ... ")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)

        if VTYSH_EN is True:
            cmdset = [
                "/etc/init.d/gfl start",
                "/etc/init.d/npos start",
                "vtysh",
                "configure terminal",
                "interface swp1",
                "no shutdown",
                "switchport access vlan 1",
                "exit",
                "bridge-domain 1",
                "vlan 1 swp1",
                "exit",
                "interface bridge 1",
                "no shutdown",
                "exit",
                "exit",
                "exit",
                "ifconfig br1 {0}".format(self.dutip),
                "ifconfig | grep -C 5 br1"
            ]
            for idx in range(len(cmdset)):
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmdset[idx], self.linux_prompt)
                time.sleep(1)
        else:
            cmd = "ifconfig eth0 {}".format(self.dutip)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

    def lnx_netcheck(self):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd_retry(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)

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

        self.stop_at_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run delenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        msg(5, "Clearing the U-Boot environmental variables ...")

        self.stop_at_uboot()
        self.boot_diag_from_spi()
        msg(10, "Recovery booting ...")

        self.login(username="root", password="ubnt", timeout=100)
        self.set_lnx_net()
        self.lnx_netcheck()
        msg(20, "Linux networking is good ...")

        rtmsg = self.pexp.expect_get_output("cat /usr/lib/version", self.linux_prompt)
        match = re.findall(IMAG_VER, rtmsg)
        if match:
            UPDATEUB_EN = False
            UPDATEDIAG_EN = False
        else:
            UPDATEUB_EN = True
            UPDATEDIAG_EN = True

        if UPDATEUB_EN is True:
            log_debug("downloading FW U-boot")
            cmd = "tftp -g -r images/f060-fw-boot.img -l /tmp/boot.img {0}".format(self.tftp_server)
            self.pexp.expect_lnxcmd_retry(300, self.linux_prompt, cmd, self.linux_prompt)
            self.is_dutfile_exist("/tmp/boot.img")
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
            msg(30, "FW U-boot download completing ...")

        if UPDATEDIAG_EN is True:
            log_debug("downloading the FW DIAG")
            cmd = "tftp -g -r images/f060-fw-uImage -l /tmp/uImage {0}".format(self.tftp_server)
            self.pexp.expect_lnxcmd_retry(300, self.linux_prompt, cmd, self.linux_prompt)
            self.is_dutfile_exist("/tmp/uImage")
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
            cmd = "flashcp -v /tmp/uImage {0}".format("/dev/mtd5")
            self.pexp.expect_lnxcmd_retry(600, self.linux_prompt, cmd, self.linux_prompt)
            msg(40, "FW DIAG download completing ...")

        if SSDFDISK_EN is True:
            cmd = "tftp -g -r tools/usw_leaf/{0} -l /tmp/{0} {1}".format("fwdiag-ssd.sh", self.tftp_server)
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)
            self.is_dutfile_exist("/tmp/fwdiag-ssd.sh")

            '''
                To check if the SSD component is existed
            '''
            self.is_dutfile_exist("/dev/sda")

            cmdset = [
                "sh /tmp/fwdiag-ssd.sh partition",
                "sh /tmp/fwdiag-ssd.sh format",
                "reboot"
            ]
            for idx in range(len(cmdset)):
                self.pexp.expect_lnxcmd(30, self.linux_prompt, cmdset[idx], self.linux_prompt)

            self.stop_at_uboot()
            self.boot_diag_from_spi()
            self.login(username="root", password="ubnt", timeout=100)
            self.set_lnx_net()
            self.lnx_netcheck()
            msg(50, "SSD partition and format completing ...")

        if WRITEFAKEBIN_EN is True:
            cmd = "tftp -g -r tools/usw_leaf/{0} -l /tmp/{0} {1}".format("fake.bin", self.tftp_server)
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)
            self.is_dutfile_exist("/tmp/fake.bin")

            cmd = "dd if=/tmp/fake.bin of=/dev/mtdblock4"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)
            msg(60, "Writing fake content to EEPROM completing ...")

        if VERCHECK_EN is True:
            self.pexp.expect_lnxcmd(20, self.linux_prompt, "cat /usr/lib/version", IMAG_VER)
            cmd = "echo {0} > /logs/boardname".format(BOARDNAME)
            self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)
            self.pexp.expect_lnxcmd(20, self.linux_prompt, "cat /logs/boardname", BOARDNAME)
            msg(70, "Boardname setting completing ...")

        if LOADLCMFW_EN is True:
            log_debug("loading LCM FW to DUT")
            cmd = "tftp -g -r images/f060-fw-lcm -l {0} {1}".format(self.lcmfw, self.tftp_server)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            self.is_dutfile_exist(self.lcmfw)
            self.pexp.expect_lnxcmd(60, self.linux_prompt, "/etc/init.d/upydiag.sh", self.diagsh1)

            log_debug("downloading LCM FW")
            self.pexp.expect_lnxcmd(60, self.diagsh1, "diag", self.diagsh2)
            self.pexp.expect_lnxcmd(10, self.diagsh2, "lcm LCM1P3 state dfu", self.diagsh2)
            cmd = "lcm LCM1P3 dfu {}".format(self.lcmfw)
            self.pexp.expect_lnxcmd(300, self.diagsh2, cmd, self.diagsh2)
            cmd = "lcm LCM1P3 state init"
            self.pexp.expect_lnxcmd(120, self.diagsh2, cmd, self.diagsh2)
            cmd = "lcm LCM1P3 sys version"
            self.pexp.expect_lnxcmd_retry(15, self.diagsh2, cmd, self.lcmfwver)
            msg(80, "LCM FW upgrade completing ...")

        if SETDIAGDF_EN is True:
            self.pexp.expect_lnxcmd(20, self.diagsh2, "shell", self.linux_prompt)
            self.pexp.expect_lnxcmd(20, self.linux_prompt, "reboot", self.linux_prompt)
            self.stop_at_uboot()
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargsextra diag; saveenv")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv bootargsextra")
            msg(90, "Set DIAG boot as default completing ...")

        msg(100, "Completing firmware upgrading ...")

        self.close_fcd()


def main():
    us_alpine_diagloader = USALPINEDiagloader()
    us_alpine_diagloader.run()

if __name__ == "__main__":
    main()
