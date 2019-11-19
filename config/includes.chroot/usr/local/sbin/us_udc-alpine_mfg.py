#!/usr/bin/python3

import sys
import time
import os
import stat
import filecmp
import re

sys.path.append("/tftpboot/tools")

from usw_leaf.decrypt import Decrypt
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

'''
    The image version has a special character so it need an escaped character to +
'''
IMAG_VER = "UDC.alpinev2.v4.1.23.61d1326.191016.1405"
BOARDNAME = "usw-100g-mfg"


class USALPINEDiagloader(ScriptBase):
    def __init__(self):
        super(USALPINEDiagloader, self).__init__()

        self.bootloader_prompt = "UDC"
        self.diagsh1 = "UBNT> "
        self.diagsh2 = "DIAG# "
        self.lcmfw = "/tmp/lcmfw.bin"
        self.lcmfwver = "v3.0.4-0-gf89bc2b"
        self.dcrp = None

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
        else:
            cmd = "ifconfig eth0 {}".format(self.dutip)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

    def lnx_netcheck(self):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()

    def run(self):
        """
        Main procedure of factory
        """
        global WRITEFAKEBIN_EN
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        self.dcrp = Decrypt(self.pexp)

        self.dcrp.stop_at_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run delenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        msg(5, "Clearing the U-Boot environmental variables ...")

        self.dcrp.stop_at_uboot()
        self.boot_diag_from_spi()
        msg(10, "Recovery booting ...")

        rtc = self.dcrp.lnx_login(timeout=100)
        '''
            If the DUT hasn't been signed, it has to do the switch network configuration by using vtysh CLI
        '''
        if rtc == 1:
            self.set_lnx_net()
        else:
            WRITEFAKEBIN_EN = False
            cmd = "ifconfig br1 {0}".format(self.dutip)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

            cmd = "ifconfig | grep -C 5 br1"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

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
            os.chdir(self.fwdir)
            self.create_http_server()

        if UPDATEUB_EN is True:
            log_debug("wget FW U-boot starting ... ")
            fw_url = "http://{0}:{1}/{2}-fw-boot.img".format(self.tftp_server, self.http_port, self.board_id)
            cmd = "cd /tmp; wget {0}".format(fw_url)
            self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

            cmd = "mv /tmp/{0}-fw-boot.img /tmp/boot.img".format(self.board_id)
            self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()
            log_debug("wget FW U-boot finishing ... ")

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
            self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()
            msg(30, "FW U-boot download completing ...")

        if UPDATEDIAG_EN is True:
            log_debug("wget FW DIAG starting ... ")
            fw_url = "http://{0}:{1}/{2}-fw-uImage".format(self.tftp_server, self.http_port, self.board_id)
            cmd = "cd /tmp; wget {0}".format(fw_url)
            self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

            cmd = "mv /tmp/{0}-fw-uImage /tmp/uImage".format(self.board_id)
            self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()
            self.stop_http_server()
            log_debug("wget FW DIAG finishing ... ")

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
            self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()
            msg(40, "FW DIAG download completing ...")

        if SSDFDISK_EN is True:
            srcp = "tools/usw_leaf/fwdiag-ssd.sh"
            dstp = "/tmp/fwdiag-ssd.sh"
            self.tftp_get(remote=srcp, local=dstp, timeout=30)

            '''
                To check if the SSD component is existed
            '''
            self.is_dutfile_exist("/dev/sda")

            cmd = "sh /tmp/fwdiag-ssd.sh partition"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

            postexp = [
                "/dev/sda1     2048   133119   131072   64M",
                "/dev/sda2   133120  2230271  2097152    1G",
                "/dev/sda3  2230272  4327423  2097152    1G",
                "/dev/sda4  4327424  4589567   262144  128M",
                "/dev/sda5  4589568  4720639   131072   64M",
                "/dev/sda6  4720640 58626254 53905615 25.7G",
                self.linux_prompt
            ]

            cmd = "sh /tmp/fwdiag-ssd.sh format"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, postexp)
            self.chk_lnxcmd_valid()

            postexp = [
                "sda1      64M boot",
                "sda2       1G",
                "sda3       1G",
                "sda4     128M persistent",
                "sda5      64M recovery",
                "sda6    25.7G data",
                self.linux_prompt
            ]

            cmd = "lsblk -o NAME,SIZE,LABEL"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, postexp)
            self.chk_lnxcmd_valid()

            self.pexp.expect_lnxcmd(30, self.linux_prompt, "reboot", self.linux_prompt)

            self.dcrp.stop_at_uboot()
            self.boot_diag_from_spi()
            rtc = self.dcrp.lnx_login(timeout=100)
            '''
                If the DUT hasn't been signed, it has to do the switch network configuration by using vtysh CLI
            '''
            if rtc == 1:
                self.set_lnx_net()
            else:
                WRITEFAKEBIN_EN = False
                cmd = "ifconfig br1 {0}".format(self.dutip)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
                self.chk_lnxcmd_valid()

                cmd = "ifconfig | grep -C 5 br1"
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
                self.chk_lnxcmd_valid()

            self.lnx_netcheck()
            msg(50, "SSD partition and format completing ...")

        if WRITEFAKEBIN_EN is True:
            srcp = "tools/usw_leaf/fake.bin"
            dstp = "/tmp/fake.bin"
            self.tftp_get(remote=srcp, local=dstp, timeout=30)

            cmd = "dd if=/tmp/fake.bin of=/dev/mtdblock4"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()
            msg(60, "Writing fake content to EEPROM completing ...")

        if VERCHECK_EN is True:
            rtmsg = self.pexp.expect_get_output("cat /usr/lib/version", self.linux_prompt)
            match = re.findall(IMAG_VER, rtmsg)
            if not match:
                error_critical("The version of DIAG image is not correct")

            cmd = "echo {0} > /logs/boardname".format(BOARDNAME)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            self.chk_lnxcmd_valid()

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /logs/boardname", BOARDNAME)
            self.chk_lnxcmd_valid()
            msg(70, "Boardname setting completing ...")

        if LOADLCMFW_EN is True:
            log_debug("loading LCM FW to DUT")
            srcp = "images/f060-fw-lcm"
            self.tftp_get(remote=srcp, local=self.lcmfw, timeout=60)
            self.pexp.expect_lnxcmd(60, self.linux_prompt, "/etc/init.d/upydiag.sh", self.diagsh1)

            self.pexp.expect_lnxcmd(60, self.diagsh1, "diag", self.diagsh2)
            cmd = "lcm LCM1P3 sys version"
            rtmsg = self.pexp.expect_get_output(cmd, self.diagsh2)
            match = re.findall(self.lcmfwver, rtmsg)
            if match:
                log_debug("The version of the testing LCM FW is correct")
            else:
                log_debug("downloading LCM FW")
                cmd = "lcm LCM1P3 state dfu"
                self.pexp.expect_lnxcmd(10, self.diagsh2, cmd, self.diagsh2)
                cmd = "lcm LCM1P3 dfu {}".format(self.lcmfw)
                self.pexp.expect_lnxcmd(300, self.diagsh2, cmd, self.diagsh2)
                cmd = "lcm LCM1P3 state init"
                self.pexp.expect_lnxcmd(120, self.diagsh2, cmd, self.diagsh2)
                cmd = "lcm LCM1P3 sys version"
                self.pexp.expect_lnxcmd(15, self.diagsh2, cmd, self.lcmfwver, retry=5)
                msg(80, "LCM FW upgrade completing ...")

        if SETDIAGDF_EN is True:
            self.pexp.expect_lnxcmd(20, self.diagsh2, "shell", self.linux_prompt)
            self.pexp.expect_lnxcmd(20, self.linux_prompt, "reboot", self.linux_prompt)
            self.dcrp.stop_at_uboot()
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
