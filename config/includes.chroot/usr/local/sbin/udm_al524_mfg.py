#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical



class UDM_AL524_MFG(ScriptBase):
    def __init__(self):
        super(UDM_AL524_MFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.mfg_uboot_cal = os.path.join(self.image, self.board_id + "-mfg.bin")
        self.mfg_img = os.path.join(self.image, self.board_id + "-fcd.bin")

        self.bootloader_prompt = "ALPINE_UBNT_UDM_PRO_MAX"
        self.linux_prompt = "#"
        self.activeport = {
            'ea32': "al_eth0"
        }
        self.netif = {
            'ea32': "eth0"
        }
        self.UPDATE_UBOOT = True
        self.BOOT_RECOVERY_IMAGE = True
        self.INIT_RECOVERY_IMAGE = True
        self.FW_UPGRADE = True

    def enter_uboot(self, timeout=60):
        self.pexp.expect_action(40, "to stop", "\033\033")
        log_debug("Setting network in uboot ...")
        # self.set_ub_net(premac="00:11:22:33:44:5" + str(self.row_id))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))
        self.is_network_alive_in_uboot(timeout=15)
    def update_uboot(self):
        log_debug("Transfer uboot image ...")
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-BSP_uboot.img"),
            dest=os.path.join(self.tftpdir, "boot.img")
        )
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(120, "delenv script")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
    def update_uImage(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargs pci=pcie_bus_perf console=ttyS0,115200")
        self.is_network_alive_in_uboot(timeout=15)
        log_debug("Transfer uImage ...")
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-BSP-uImage"),
            dest=os.path.join(self.tftpdir, "uImage")
        )
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot 0x08000004 uImage")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "cp.b $fdtaddr $loadaddr_dt 7ffc")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "fdt addr $loadaddr_dt")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm 0x08000004 - $fdtaddr")
        self.pexp.expect_only(60, "Starting kernel")
    def init_recovery_image(self):
        self.pexp.expect_only(120, "Starting udapi-bridge: OK")
        self.pexp.expect_lnxcmd(60, self.linux_prompt, "\015")
        self.pexp.expect_lnxcmd(60, self.linux_prompt, "\015")


    def fw_upgrade(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip))
        self.is_network_alive_in_linux(ipaddr=self.tftp_server)
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-BSP-fw.tar"),
            dest=os.path.join(self.tftpdir, "upgrade.tar")
        )
        self.pexp.expect_action(10, self.linux_prompt, "cd /tmp")
        self.pexp.expect_lnxcmd(480, self.linux_prompt, "tftp -g -r upgrade.tar " + self.tftp_server,post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(40, self.linux_prompt, "sync")
        self.pexp.expect_lnxcmd(40, self.linux_prompt, "ls upgrade.tar")
        self.pexp.expect_lnxcmd(360, self.linux_prompt, "flash-factory.sh")
        self.pexp.expect_only(120, "Restarting system")
        self.pexp.expect_only(120, "root@alpine:~#")

    def update_kernel(self):
        log_debug("Updating kernel ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run boot_wr_img")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "boot")

    def init_bsp_image(self):
        log_debug("Login kernel ...")
        self.pexp.expect_lnxcmd(120, "BusyBox", "dmesg -n1", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.is_network_alive_in_linux()

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        # self.fcd.common.config_stty(self.dev)
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT is True:
            self.enter_uboot()
            msg(10, "Finish network setting in uboot ...")

            self.update_uboot()
            msg(15, "Finish Update bootloader...")
        if self.BOOT_RECOVERY_IMAGE:
            self.update_uImage()
            msg(30, "Finish uImage updating...")
        if self.INIT_RECOVERY_IMAGE:
            self.init_recovery_image()
            msg(40, "Initial uImage ...")
        if self.FW_UPGRADE is True:
            self.fw_upgrade()
            msg(50, "Finish kernel image transferring ...")

        output = self.pexp.expect_get_output(action="cat /lib/version", prompt="", timeout=3)
        log_debug(output)

        msg(100, "Completed back to T1 process ...")
        self.close_fcd()


def main():
    udm_al524_mfg = UDM_AL524_MFG()
    udm_al524_mfg.run()


if __name__ == "__main__":
    main()
