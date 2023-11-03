#!/usr/bin/python3
import re
import time

from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import error_critical, log_debug, log_error, msg
from script_base import ScriptBase

"""
    a6a0: UC-EV-Station-Ultra
"""


class EVIPQ5018BspFactory(ScriptBase):
    def __init__(self):
        super(EVIPQ5018BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.devregpart = "/dev/mtdblock9"
        self.bomrev = "113-{}".format(self.bom_rev)
        self.bootloader_prompt = "IPQ5018#"
        self.linux_prompt = "root@OpenWrt:/#"

        self.ethnum = {
            "a6a0": "1",
        }

        self.wifinum = {
            "a6a0": "1",
        }

        self.btnum = {
            "a6a0": "1",
        }

        self.bootm_addr = {
            "a6a0": "",
        }

        self.bootm_cmd = {
            "a6a0": "?",
        }

        self.linux_prompt_select = {
            "a6a0": "#",
        }

        self.uboot_eth_port = {
            "a6a0": "eth0",
        }

        self.lnx_eth_port = {
            "a6a0": "br-lan",
        }

        self.devnetmeta = {
            "ethnum": self.ethnum,
            "wifinum": self.wifinum,
            "btnum": self.btnum,
        }

        self.BOOT_INITRAM_IMAGE = False
        self.BOOT_BSP_IMAGE = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.FWUPDATE_ENABLE = True
        self.DATAVERIFY_ENABLE = True

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(
            180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0
        )
        self.set_lnx_net(self.lnx_eth_port[self.board_id])
        self.is_network_alive_in_linux()

    def run_initram_bootup(self):
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.set_ub_net(self.premac, ethact=self.uboot_eth_port[self.board_id])
        self.is_network_alive_in_uboot()
        cmd = "tftpboot 0x50000000 images/{}.itb".format(self.board_id)
        self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)
        cmd = self.bootm_cmd[self.board_id]
        self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)

        self.linux_prompt = "#"
        self.login(
            self.user,
            self.password,
            timeout=300,
            log_level_emerg=True,
            press_enter=True,
            retry=3,
        )
        cmd = "ifconfig br0"
        self.pexp.expect_lnxcmd(
            20, self.linux_prompt, cmd, "Link encap:Ethernet", retry=10
        )

        self.set_lnx_net("br0")
        self.is_network_alive_in_linux()
        cmd = "echo 5edfacbf > /proc/ubnthal/.uf"
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd)

    def setup_uboot_env_tftp_server(self):
        log_debug("Start setup the uboot env (tftp server)")
        cmds = [
            "setenv machid 8040104;",
            "setenv ipaddr {};".format(self.dutip),
            "setenv serverip {};".format(self.tftp_server),
        ]
        for i in cmds:
            self.pexp.expect_ubcmd(60, self.bootloader_prompt, i)
        self.is_network_alive_in_uboot()

    def flash_fw(self):
        log_debug("Start flash fw-evs-ultra_nor.bin ...")
        fw_nor_bin = "images/a6a0-fw-nor.bin"
        cmds = [
            "tftpboot 0x44000000 {};".format(fw_nor_bin),
            "sf probe; sf erase 0x0 0x1C0000;",
            "sf write 0x44000000 0x0 0x1c0000;",
        ]
        for i in cmds:
            self.pexp.expect_ubcmd(60, self.bootloader_prompt, i)

    def flash_fw_bootconfig(self):
        log_debug("Start flash fw-evs-ultra_nor_bootconfig_1.bin ...")
        fw_nor_bootconfig_bin = "images/a6a0-fw-nor-bootconfig.bin"
        cmds = [
            "tftpboot 0x44000000 {};".format(fw_nor_bootconfig_bin),
            "sf probe; sf erase 0x240000 0x10000;",
            "sf write 0x44000000 0x240000 0x10000;",
        ]
        for i in cmds:
            self.pexp.expect_ubcmd(60, self.bootloader_prompt, i)

    def flash_fw_emmc(self):
        log_debug("Start flash fw-evs-ultra_emmc.bin ...")
        fw_emmc_bin = "images/a6a0-fw-emmc.bin"
        cmds = [
            "tftpboot 0x44000000 {};".format(fw_emmc_bin),
            "mmc erase 0x0 2A422; mmc write 0x44000000 0x0 2A422;",
        ]

        for i in cmds:
            self.pexp.expect_ubcmd(100, self.bootloader_prompt, i)

    def expect_erase_written(self):
        expecteds = [
            "blocks erased: OK",
            "written: OK",
        ]
        for i in expecteds:
            self.pexp.expect_only(60, i)

    def reboot_from_kernel(self):
        log_debug("Reboot from kernel ...")
        cmds = ["reboot -f"]
        for i in cmds:
            self.pexp.expect_lnxcmd(60, self.linux_prompt, i)

    def reboot_from_uboot(self):
        log_debug("Reboot from uboot ...")
        cmds = ["reset"]
        for i in cmds:
            self.pexp.expect_ubcmd(60, self.bootloader_prompt, i)

    def stop_uboot(self):
        log_debug("Stop uboot ...")
        self.pexp.expect_action(20, "to stop", "\033\033")

    def expect_login(self):
        self.pexp.expect_action(300, "Starting QDSS for Integrated", "")
        self.linux_prompt = "#"
        username = password = "ui"
        self.login(
            username,
            password,
            timeout=300,
            log_level_emerg=True,
            press_enter=False,
            retry=3,
        )

    def fw_update(self):
        log_debug("Start upgrade mfg images ...")
        self.reboot_from_kernel()
        self.stop_uboot()
        self.setup_uboot_env_tftp_server()
        self.flash_fw()
        self.flash_fw_bootconfig()
        self.flash_fw_emmc()
        log_debug("Ugrade mfg done ...")
        self.reboot_from_uboot()
        self.expect_login()

    def disable_fcd_tlv_check():
        log_debug("Disable FCD TLV data checking as a temporary workaround")
        self.FCD_TLV_data = False
                
    def registration(self):
        if self.BOOT_BSP_IMAGE is True:
            self.init_bsp_image()
        if self.BOOT_INITRAM_IMAGE is True:
            self.run_initram_bootup()

        msg(10, "Boot up to linux console by initram and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if self.REGISTER_ENABLE is True:
            super().registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

    def set_up_console(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

    def check_info(self):
        self.linux_prompt = "#"
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")

        self.pexp.expect_only(
            10, "flashSize=", err_msg="No flashSize, factory sign failed."
        )
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        self.set_up_console()
        self.registration()

        if self.FWUPDATE_ENABLE is True:
            self.fw_update()
            msg(70, "Succeeding in firmware update ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    ev_ipq5018_bspfactory = EVIPQ5018BspFactory()
    ev_ipq5018_bspfactory.run()


if __name__ == "__main__":
    main()
