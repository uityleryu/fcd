#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os
import re

'''
    a678: UDR-Pro
   
'''


class UDM_IPQ53XX_BSPFACTORY(ScriptBase):
    def __init__(self):
        super(UDM_IPQ53XX_BSPFACTORY, self).__init__()
        self.is_ddr_4g = True
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.bootloader_prompt = "#"
        self.linux_prompt = "#"
        self.bsp_fw_prompt = "#"
        self.nor_2g_img = self.board_id + "-bsp-2g_nor.bin"
        self.nor_4g_img = self.board_id + "-bsp-4g_nor.bin"
        self.bsp_2g_single_img = self.board_id + "-bsp-2g.img"
        self.bsp_4g_single_img = self.board_id + "-bsp-4g.img"
        # active port
        self.activeport = {
            'a678': "al_eth3",
        }
        # ethernet interface
        self.netif = {
            'a678': "eth0",
        }
        self.UPDATE_UBOOT = True
        self.UPDAE_Single = True

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)
        out_msg = self.pexp.expect_get_output(action="bdinfo", prompt=self.bootloader_prompt, timeout=3)
        if "size     = 0xC0000000" in out_msg:
            self.is_ddr_4g = True
        elif "size     = 0x80000000" in out_msg:
            self.is_ddr_4g = False
        else:
            raise Exception("DDR Size is unknown")
        if self.is_ddr_4g:
            self.copy_file(
                source=os.path.join(self.fwdir, self.nor_4g_img),
                dest=os.path.join(self.tftpdir, "nor.bin")
            )
        else:
            self.copy_file(
                source=os.path.join(self.fwdir, self.nor_2g_img),
                dest=os.path.join(self.tftpdir, "nor.bin")
            )
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpb 0x44000000 nor.bin")  # tranfer img and update
        self.pexp.expect_only(60, "Bytes transferred =")
        self.pexp.expect_action(150, self.bootloader_prompt,
                                "sf probe; sf erase 0x0 +0x300000; sf write 0x44000000 0x0 0x300000")
        self.pexp.expect_only(120, "Erased: OK")
        self.pexp.expect_only(120, "Written: OK")

    def update_single(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)
        self.is_network_alive_in_uboot(retry=9, timeout=10)
        out_msg = self.pexp.expect_get_output(action="bdinfo", prompt=self.bootloader_prompt, timeout=3)
        if "size     = 0xC0000000" in out_msg:
            self.is_ddr_4g = True
        elif "size     = 0x80000000" in out_msg:
            self.is_ddr_4g = False
        else:
            raise Exception("DDR Size is unknown")
        if self.is_ddr_4g:
            self.copy_file(
                source=os.path.join(self.fwdir, self.bsp_4g_single_img),
                dest=os.path.join(self.tftpdir, "single.img")
            )
        else:
            self.copy_file(
                source=os.path.join(self.fwdir, self.bsp_2g_single_img),
                dest=os.path.join(self.tftpdir, "single.img")
            )
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpb 0x44000000 single.img")  # tranfer img and update
        self.pexp.expect_only(60, "Bytes transferred =")
        self.pexp.expect_action(10, self.bootloader_prompt, "imgaddr=$fileaddr && source $imgaddr:script")  # tranfer img and update
        self.pexp.expect_only(120, "Either NAND or eMMC already initialized")
        self.pexp.expect_only(120, "Flashing gptbackup:")
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")  # tranfer img and update
    def t1_image_check(self):
        self.pexp.expect_only(50, "Starting kernel")
        self.pexp.expect_lnxcmd(150, "UBNT BSP INIT", "dmesg -n1", "#", retry=0)
    def set_boot_net(self):
        # import pdb; pdb.set_trace()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)


    def run(self):
        """
                Main procedure of factory
                """
        # Connect into DUT and set pexpect helper for class using picocom
        if self.ps_state is True:
            self.set_ps_port_relay_off()
            time.sleep(2)
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        if self.ps_state is True:
            self.set_ps_port_relay_on()
        msg(5, "Open serial port successfully ...")
        if self.UPDATE_UBOOT is True:
            self.update_uboot()
            self.pexp.expect_action(10, self.bootloader_prompt, "reset")
            msg(20, "Finish boot updating")

        if self.UPDAE_Single is True:
            msg(60, "Updating Single Image")
            self.update_single()
            msg(70, "Finish Single updating")
            self.t1_image_check()
            msg(90, 'Check T1 image done ...')

        output = self.pexp.expect_get_output(action="cat /proc/sys/kernel/version", prompt=self.bsp_fw_prompt,
                                             timeout=3)
        log_debug(output)
        msg(100, "Completing Back2T1 process ...")
        self.close_fcd()


def main():
    udm_ipq53xx_bspfactory = UDM_IPQ53XX_BSPFACTORY()
    udm_ipq53xx_bspfactory.run()


if __name__ == "__main__":
    main()
