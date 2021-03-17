#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


BOOT_BSP_IMAGE    = True
PROVISION_ENABLE  = True
DOHELPER_ENABLE   = True
REGISTER_ENABLE   = True
FWUPDATE_ENABLE   = True
DATAVERIFY_ENABLE = True


class UDMMT7622BspFactory(ScriptBase):
    def __init__(self):
        super(UDMMT7622BspFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fw_img = os.path.join(self.fwdir, self.board_id + "-fw.bin")
        self.fw_uboot = os.path.join(self.fwdir, self.board_id + "-fw.uboot")
        self.fw_recovery = os.path.join(self.fwdir, self.board_id + "-recovery")

        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "MT7622"
        self.linux_prompt = "#"

        self.ethnum = {
            'eccc': "5"
        }

        self.wifinum = {
            'eccc': "2"
        }

        self.btnum = {
            'eccc': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def enter_uboot(self, timeout=60):
        self.pexp.expect_ubcmd(timeout, "Hit any key to stop autoboot", "")

        log_debug("Setting network in uboot ...")
        self.set_ub_net(premac="00:11:22:33:44:5" + str(self.row_id))
        self.is_network_alive_in_uboot()

    def update_uboot(self, uboot_image):
        log_debug("Updating uboot ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpb {}".format(uboot_image), "Bytes transferred")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "nor init; snor erase 0x60000 0x160000;")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "snor write ${loadaddr} 0x60000 ${filesize};")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "invaild_env")

    def boot_bsp_image(self):
        self.enter_uboot()

        # Update uboot
        self.update_uboot(self.fcd_uboot)

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
        self.enter_uboot()

        # Update kernel
        log_debug("Updating FCD image ...")
        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "tftpb {}".format(self.fcd_img), "Bytes transferred")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run boot_wr_img")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "boot")

    def init_bsp_image(self):
        self.pexp.expect_lnxcmd(120, "BusyBox", "dmesg -n1", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.is_network_alive_in_linux()

    def fwupdate(self):
        self.enter_uboot()

        # Update uboot
        self.update_uboot(self.fw_uboot)

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
        self.enter_uboot()

        log_debug("Updating FW image ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargsextra 'factory server={}'".format(self.tftp_server))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootargsemmcdual0")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "nor init")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "mmc init")

        # copy recovery image to tftp server
        self.copy_file(
            source=self.fw_recovery,
            dest=os.path.join(self.tftpdir, "uImage")  # fixed name
        )

        # copy fw image to tftp server
        self.copy_file(
            source=self.fw_img,
            dest=os.path.join(self.tftpdir, "fw-image.bin")  # fixed name
        )

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot uImage")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm")
        self.pexp.expect_only(300, "Upgrading firmware")

    def login(self):
        self.pexp.expect_only(180, "Welcome to UniFi")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if BOOT_BSP_IMAGE is True:
            self.init_bsp_image()
            msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot -f")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Upgrading FW ...")

        if DATAVERIFY_ENABLE is True:
            self.login()
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        self.set_ntptime_to_dut()
        msg(95, "Set NTP time to DUT ...")

        msg(100, "Completed FCD process ...")
        self.close_fcd()


def main():
    udmmt7622_bspfactory = UDMMT7622BspFactory()
    udmmt7622_bspfactory.run()


if __name__ == "__main__":
    main()
