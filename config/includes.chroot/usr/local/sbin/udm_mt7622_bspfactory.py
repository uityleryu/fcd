#!/usr/bin/python3
import time
import os
import stat
from udm_alpine_factory import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

BOOT_BSP_IMAGE    = True
PROVISION_ENABLE  = True
DOHELPER_ENABLE   = True
REGISTER_ENABLE   = True
FWUPDATE_ENABLE   = False
DATAVERIFY_ENABLE = False


class UDMMT7622BspFactory(ScriptBase):
    def __init__(self):
        super(UDMMT7622BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = "images/" + self.board_id + "-fw.bin"
        self.fcdimg = "images/" + self.board_id + "-fcd.bin"
        self.uboot_img = "images/" + self.board_id + "-uboot.bin"
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "MT7622"
        self.linux_prompt = "root@LEDE:/#"

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

    def boot_bsp_image(self):
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "")
        self.set_ub_net()
        self.is_network_alive_in_uboot()
        # Update uboot
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "tftp {}".format(self.uboot_img))
        self.pexp.expect_only(120, "Bytes transferred")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "nor init; snor erase 0x60000 0x70000;")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "snor write ${loadaddr} 0x60000 ${filesize};")
        # Update kernel
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "tftp {}".format(self.fcdimg))
        self.pexp.expect_only(120, "Bytes transferred")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run boot_wr_img")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "boot")

    def init_bsp_image(self):
        self.pexp.expect_lnxcmd(120, "BusyBox", "dmesg -n1", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.is_network_alive_in_linux()

    def fwupdate(self):
        pass

    def check_info(self):
        pass

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if BOOT_BSP_IMAGE is True:
            self.boot_bsp_image()
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

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    udmmt7622_bspfactory = UDMMT7622BspFactory()
    udmmt7622_bspfactory.run()

if __name__ == "__main__":
    main()
