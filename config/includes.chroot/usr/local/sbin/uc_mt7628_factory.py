#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class UCMT7628Factory(ScriptBase):
    def __init__(self):
        super(UCMT7628Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        
        self.fwimg = "images/" + self.board_id + "-fw.bin"
        self.initramfs = "images/" + self.board_id + "-initramfs.bin"
        self.ubootimg = "images/" + self.board_id + "-uboot.bin"
        
        self.devregpart = "/dev/mtdblock3"
        self.helperexe = "helper_MT7628_release"
        self.bootloader_prompt = ">"
        self.helper_path = "uc_ups"

        # number of mac
        self.macnum =  {'ed14': "0"}
        # number of WiFi
        self.wifinum = {'ed14': "1"}
        # number of Bluetooth
        self.btnum =   {'ed14': "1"}
        # flash size map
        self.flash_size = {'ed14':  "33554432"}
        # firmware image
        self.fwimg = self.board_id + "-fw.bin"
        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
        }

        self.UPDATE_UBOOT_ENABLE    = True
        self.BOOT_RAMFS_IMAGE       = True 
        self.PROVISION_ENABLE       = True 
        self.DOHELPER_ENABLE        = True 
        self.REGISTER_ENABLE        = True 
        self.FWUPDATE_ENABLE        = True
        self.DATAVERIFY_ENABLE      = True 
        self.LCM_FW_CHECK_ENABLE    = False 
        self.MCU_FW_CHECK_ENABLE    = False 

    def enter_uboot(self):
        self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
        self.set_boot_net()
        
    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv loadaddr 0x81000000")
        self.is_network_alive_in_uboot()
        
    def update_uboot_image(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot ${{loadaddr}} {}".format(self.ubootimg))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf probe; sf erase 0x0 0x60000; sf write ${loadaddr} 0x0 ${filesize}")
        self.pexp.expect_only(120, "Erased: OK")
        self.pexp.expect_only(120, "Written: OK")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def init_ramfs_image(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot ${{loadaddr}} {}".format(self.initramfs))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm")
        
        self.pexp.expect_only(30, "Loading kernel")
        self.login(press_enter=True, log_level_emerg=True, timeout=60)
        self.disable_udhcpc()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", self.linux_prompt)
        # time.sleep(45)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig wlan0 down", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "swconfig dev switch0 set reset", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ps", self.linux_prompt)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "ifconfig eth0 "+self.dutip, self.linux_prompt)
        
        
        self.is_network_alive_in_linux()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo \"EEPROM,388caeadd99840d391301bec20531fcef05400f4\" > " +
                                                       "/sys/module/mtd/parameters/write_perm", self.linux_prompt)

    def fwupdate(self, image, reboot_en):
        if reboot_en is True:
            self.pexp.expect_action(30, self.linux_prompt, "reboot -f")
        self.enter_uboot()
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearcfg TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearenv TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv do_urescue TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
        self.pexp.expect_action(30, "Listening for TFTP transfer on", "")

        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir+"/"+image,
               self.dutip]
        cmdj = ' '.join(cmd)

        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
        self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(120, "done")

    def check_info(self):
        self.pexp.expect_action(30, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(30, "flashSize="+self.flash_size[self.board_id])
        self.pexp.expect_only(30, "systemid="+self.board_id)
        self.pexp.expect_only(30, "serialno="+self.mac.lower())
        self.pexp.expect_only(30, "qrid="+self.qrcode)
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/build.properties")
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/version")

    def lcm_fw_check(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, 'lcm-ctrl -t dump', 'version', retry=48)

    def mcu_fw_check(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, 'ubus call power.outlet.meter_mcu info', 'version', retry=48)

    def run(self):
        self.fcd.common.config_stty(self.dev)
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE is True:
            # self.fwupdate(self.fwimg, reboot_en=False)
            self.enter_uboot()
            self.update_uboot_image()
            msg(10, "Update Uboot image successfully ...")

        if self.BOOT_RAMFS_IMAGE is True:
            msg(15, "Boot into initRamfs image for registration ...")
            self.enter_uboot()
            self.init_ramfs_image()

        if self.PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(30, "Do helper to get the output file to devreg server ...")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
            # import pdb; pdb.set_trace()

        if self.FWUPDATE_ENABLE is True:
            msg(60, "Updating released firmware ...")
            self.fwupdate(self.fwimg, reboot_en=True)
            msg(70, "Updating released firmware done...")
        else:
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "reboot", self.linux_prompt)

        if self.DATAVERIFY_ENABLE is True:
            self.login(press_enter=True, log_level_emerg=True, timeout=60)
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.LCM_FW_CHECK_ENABLE is True:
            self.lcm_fw_check()
            msg(85, "Succeeding in checking the LCM FW information ...")

        if self.MCU_FW_CHECK_ENABLE is True:
            self.mcu_fw_check()
            msg(90, "Succeeding in checking the MCU FW information ...")

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    uc_mt7628_factory = UCMT7628Factory()
    uc_mt7628_factory.run()

if __name__ == "__main__":
    main()
