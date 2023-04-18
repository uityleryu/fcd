#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os
import re

'''
    ea3d: UDM-Enterprise
    ea3e: UXG-Enterprise
'''


class RovR_AL324_BSPFACTORY(ScriptBase):
    def __init__(self):
        super(RovR_AL324_BSPFACTORY, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.bootloader_prompt = ">"
        self.linux_prompt = "#"
        self.bsp_fw_prompt = "root@alpine:~#"

        # active port
        self.activeport = {
            'ea3d': "al_eth3",
            'ea3e': "al_eth3",
        }
        # ethernet interface
        self.netif = {
            'ea3d': "eth0",
            'ea3e': "eth0",
        }
        self.INIT_RECOVERY_IMAGE = True
        self.FW_UPGRADE = True
        self.UPDATE_UBOOT = True
        self.BOOT_RECOVERY_IMAGE = True

    def set_boot_net(self):
        # import pdb; pdb.set_trace()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv sysid")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv model")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "rtl83xx")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ethact " + self.activeport[self.board_id])

    def set_recovery_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv sysid")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv model")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "rtl83xx")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ethact " + self.activeport[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargs pci=pcie_bus_perf console=ttyS0,115200")

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-bsp-uboot.img"),
            dest=os.path.join(self.tftpdir, "boot.img")
        )
        self.pexp.expect_action(10, self.bootloader_prompt, "run bootupd")  # tranfer img and update
        self.pexp.expect_only(120, "delenv script")

    def boot_recovery_image(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        time.sleep(2)
        self.set_recovery_net()
        self.is_network_alive_in_uboot(retry=9, timeout=10)

        # copy recovery image
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-bsp-recovery"),
            dest=os.path.join(self.tftpdir, "bspuImage")
        )
        self.pexp.expect_action(60, self.bootloader_prompt, "tftpboot 0x08000004 bspuImage")
        self.pexp.expect_only(40, "Bytes transferred")
        self.pexp.expect_action(30, self.bootloader_prompt, "cp.b $fdtaddr $loadaddr_dt 7ffc")
        self.pexp.expect_action(30, self.bootloader_prompt, "fdt addr $loadaddr_dt")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootm 0x08000004 - $fdtaddr")

    def init_recovery_image(self):
        self.pexp.expect_only(20, "Starting kernel")
        self.pexp.expect_only(20, "Starting udapi-bridge: OK")
        self.pexp.expect_only(20, "boot: boot1 boot2 boot3 boot4")
        self.pexp.expect_lnxcmd(60, self.linux_prompt, "\015")

    def fw_upgrade(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip))
        self.is_network_alive_in_linux(ipaddr=self.tftp_server)
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-bsp-fw.tar"),
            dest=os.path.join(self.tftpdir, "upgrade.tar")
        )
        self.pexp.expect_action(10, self.linux_prompt, "cd /tmp")
        self.pexp.expect_lnxcmd(240, self.linux_prompt, "tftp -g -r upgrade.tar " + self.tftp_server,post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(40, self.linux_prompt, "sync",post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(40, self.linux_prompt, "ls upgrade.tar",post_exp="upgrade.tar")
        self.pexp.expect_lnxcmd(360, self.linux_prompt, "flash-factory.sh",post_exp=self.bsp_fw_prompt)

    def run(self):
        """
                Main procedure of factory
                """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        # self.fcd.common.print_current_fcd_version()
        self.ver_extract()
        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")
        if self.UPDATE_UBOOT is True:
            self.update_uboot()
            self.pexp.expect_action(10, self.bootloader_prompt, "reset")
            msg(20, "Finish boot updating")

        if self.BOOT_RECOVERY_IMAGE is True:
            msg(40, "Updating FW")
            self.boot_recovery_image()

        if self.INIT_RECOVERY_IMAGE is True:
            self.init_recovery_image()
            msg(60, "Boot up to linux console and network is good ...")
        if self.FW_UPGRADE is True:
            self.fw_upgrade()
            msg(80, "Boot up to linux console and network is good ...")
        output = self.pexp.expect_get_output(action="cat /sys/firmware/devicetree/base/soc/board-cfg/id", prompt="",
                                             timeout=3)
        log_debug(output)
        output = self.pexp.expect_get_output(action="cat /lib/version", prompt="", timeout=3)
        log_debug(output)

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    rovr_al324_bspfactory = RovR_AL324_BSPFACTORY()
    rovr_al324_bspfactory.run()


if __name__ == "__main__":
    main()
