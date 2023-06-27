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


class USPMT7628Factory(ScriptBase):
    def __init__(self):
        super(USPMT7628Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.devregpart = "/dev/mtdblock3"
        self.helperexe = "helper_MT7628_release"
        self.bootloader_prompt = ">"
        self.helper_path = "pdu_pro"

        # number of mac
        self.macnum =  {
            'ed12': "2"
            }
        # number of WiFi
        self.wifinum = {
            'ed12': "0",
            }
        # number of Bluetooth
        self.btnum =   {
            'ed12': "0",
            }
        # flash size map
        self.flash_size = {'ed12': "16777216"}
        # firmware image
        self.fwimg = self.board_id + "-fw.bin"
        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
        }

        self.UPDATE_RECOVERY_ENABLE = True
        self.BOOT_RECOVERY_IMAGE    = True 
        self.PROVISION_ENABLE       = True 
        self.DOHELPER_ENABLE        = True 
        self.REGISTER_ENABLE        = True 
        self.FWUPDATE_ENABLE        = False
        self.DATAVERIFY_ENABLE      = True 
        self.LCM_FW_CHECK_ENABLE    = True 
        self.MCU_FW_CHECK_ENABLE    = True 

    def enter_uboot(self):
        self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
        self.set_boot_net()
        
    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def init_recovery_image(self):
        self.pexp.expect_only(30, "reading kernel")
        self.login(press_enter=True, log_level_emerg=True, timeout=60)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", self.linux_prompt)
        time.sleep(45)
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
        self.pexp.expect_lnxcmd(5, self.linux_prompt, 'ubus call power.outlet.meter_mcu.1 info', 'version', retry=48)

    def run(self):
        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        self.fcd.common.config_stty(self.dev)
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")

        msg(5, "Open serial port successfully ...")

        if self.UPDATE_RECOVERY_ENABLE is True:
            self.fwupdate(self.fwimg, reboot_en=False)
            msg(10, "Update factory successfully ...")

        if self.BOOT_RECOVERY_IMAGE is True:
            msg(15, "Boot into recovery image for registration ...")
            self.init_recovery_image()

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

        if self.ps_state is True:
            time.sleep(2)
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    usp_mt7628_factory = USPMT7628Factory()
    usp_mt7628_factory.run()

if __name__ == "__main__":
    main()
