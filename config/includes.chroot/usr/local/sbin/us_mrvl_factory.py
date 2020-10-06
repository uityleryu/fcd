#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp


class USW_MARVELL_FactoryGeneral(ScriptBase):
    CMD_PREFIX = "go $ubntaddr"

    def __init__(self):
        super(USW_MARVELL_FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ver_extract()
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "Marvell>>"
        self.fwimg = self.board_id + "-fw.bin"

        # customize variable for different products
        self.wait_LCM_upgrade_en = {}

        # number of Ethernet
        self.macnum = {
            'ed40': "3",  # usw-flex-xg
            'ed41': "3",  # u6-s8
        }

        # number of WiFi
        self.wifinum = {
            'ed40': "0",
            'ed41': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ed40': "0",
            'ed41': "0",
        }

        self.netif = {
            'ed40': "ifconfig tap0 ",
            'ed41': "ifconfig tap0 ",
        }

        devregpart = {
            'ed40': "/dev/mtdblock6",
            'ed41': "/dev/mtdblock6"
        }

        helper_path = {
            'ed40': "usw_flex_xg",
            'ed41': "u6_s8",

        }

        helperexe = {
            'ed40': "helper_MRVL_XCAT3_release",
            'ed41': "helper_MRVL_XCAT3_release",
        }

        self.devregpart = devregpart[self.board_id]
        self.helper_path = helper_path[self.board_id]
        self.helperexe = helperexe[self.board_id]

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        self.UPDATE_UBOOT_ENABLE    = False
        self.BOOT_RECOVERY_IMAGE    = False
        self.PROVISION_ENABLE       = True
        self.DOHELPER_ENABLE        = True
        self.REGISTER_ENABLE        = True
        self.FWUPDATE_ENABLE        = True
        self.DATAVERIFY_ENABLE      = True
        self.CONF_ZEROIP_ENABLE     = False
        self.WAIT_LCMUPGRADE_ENABLE = True

    def stop_uboot(self, uappinit_en=False):
        log_debug("Stopping U-boot")
        self.pexp.expect_action(90, "Hit any key to stop autoboot", "\x1b")
        if uappinit_en is True:
            cmd = ' '.join([self.CMD_PREFIX,
                            "uappinit"])
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, post_exp="UBNT application initialized")


    def set_data_in_uboot(self):

        self.stop_uboot(uappinit_en=True)

        cmd = [
            self.CMD_PREFIX,
            "usetbid",
            self.board_id
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, post_exp="Done")
        log_debug("Board setting succeded")


    def fwupdate(self):
        self.stop_uboot()

        msg(65, "Reboot into Uboot again for urescue")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "mini_xcat3")
        self.pexp.expect_action(30, self.bootloader_prompt, "urescue -u")
        self.pexp.expect_only(60, "Listening for TFTP transfer on")

        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir + "/" + self.fwimg,
               self.dutip]
        cmdj = ' '.join(cmd)
        time.sleep(3)
        msg(65, "Uploading released firmware...")
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "go $ubntaddr uappinit")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "go $ubntaddr uwrite")

        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Signature Verfied, Success.")

        msg(70, "Updating released firmware...")
        self.pexp.expect_only(120, "Copying to 'kernel0' partition")
        self.pexp.expect_only(180, "done")
        self.pexp.expect_only(120, "Copying to 'kernel1' partition")
        self.pexp.expect_only(180, "done")


    def check_info(self):
        """under developing
        """
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno(mac) error")

    def wait_lcm_upgrade(self):
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "lcm-ctrl -t dump", post_exp="version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "", post_exp=self.linux_prompt)

    def login_kernel(self):
        self.login(timeout=240, press_enter=True)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /lib/build.properties", post_exp=self.linux_prompt)

    def SetNetEnv(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i \"/\/sbin\/lcmd/d\" /etc/inittab", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i \"/\/sbin\/udhcpc/d\" /etc/inittab", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "initd", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, post_exp=self.linux_prompt)
        if self.board_id == "ed2d":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "/usr/share/librtk/diag -c \"port set 10g-media port all fiber10g\"", post_exp=self.linux_prompt)
        self.is_network_alive_in_linux()


    def clear_eeprom_in_uboot(self, timeout=30):
        # Ensure sysid is empty when FW is T1 img.
        # Some T1 image will boot so slow if get non-empty sysid
        self.pexp.expect_action(timeout, "Hit Esc key to stop autoboot", "\x1b")
        self.pexp.expect_action(10, self.bootloader_prompt, "bootubnt ucleareeprom")
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")

    def run(self):  
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE == True:
            pass
        if self.BOOT_RECOVERY_IMAGE == True:
            pass

        msg(5, "Set data in uboot")
        self.set_data_in_uboot()
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "reset")

        msg(15, "Login kernel")
        self.login_kernel()
        #self.SetNetEnv()
        self.is_network_alive_in_linux()

        msg(15, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        # reboot anyway
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot -f")

        if self.FWUPDATE_ENABLE is True:
            msg(55, "Starting firmware upgrade process...")
            self.fwupdate()
            msg(75, "Completing firmware upgrading ...")

        self.login_kernel()

        if self.DATAVERIFY_ENABLE is True:
            # self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id in self.wait_LCM_upgrade_en:
                msg(90, "Waiting LCM upgrading ...")
                self.wait_lcm_upgrade()

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    us_factory_general = USW_MARVELL_FactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
