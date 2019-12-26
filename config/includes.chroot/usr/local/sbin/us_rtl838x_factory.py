#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp


class USW_RTL838X_FactoryGeneral(ScriptBase):
    def __init__(self):
        super(USW_RTL838X_FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ver_extract()
        self.ubpmt = "UBNT"
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.helperexe = "helper_rtl838x"
        self.helper_path = "usw_rtl838x"
        self.bootloader_prompt = "uboot>"
        self.fwimg = self.board_id + "-fw.bin"

        # customize variable for different products
        self.wait_LCM_upgrade_en = {'ed20','ed21', 'ed22', 'ed23', 'ed24'}

        # number of Ethernet
        self.macnum = {
            'ed20': "3",  # usw-16-poe
            'ed21': "3",  # usw-24-poe
            'ed22': "3",  # usw-48-poe
            'ed23': "3",  # usw-16
            'ed24': "3",  # usw-24
            'ed25': "3",  # usw-48
            'ed26': "3",  # usw-lite-16-poe
            'ed2a': "3"   # usw-lite-8-poe
        }

        # number of WiFi
        self.wifinum = {
            'ed20': "0",
            'ed21': "0",
            'ed22': "0",
            'ed23': "0",
            'ed24': "0",
            'ed25': "0",
            'ed26': "0",
            'ed2a': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ed20': "0",
            'ed21': "0",
            'ed22': "0",
            'ed23': "0",
            'ed24': "0",
            'ed25': "0",
            'ed26': "0",
            'ed2a': "0"
        }

        self.netif = {
            'ed20': "ifconfig eth0 ",
            'ed21': "ifconfig eth0 ",
            'ed22': "ifconfig eth0 ",
            'ed23': "ifconfig eth0 ",
            'ed24': "ifconfig eth0 ",
            'ed25': "ifconfig eth0 ",
            'ed26': "ifconfig eth0 ",
            'ed2a': "ifconfig eth0 "
        }

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

    def fwupdate(self):
        self.pexp.expect_action(10, "Hit Esc key to stop autoboot", "\x1b")
        msg(60, "Reboot into Uboot for resetting to default environment")
        self.pexp.expect_action(15, self.bootloader_prompt, "env set boardmodel unknown")
        self.pexp.expect_action(20, self.bootloader_prompt, "bootubnt")
        self.pexp.expect_only(60, "Resetting to default environment")
        self.pexp.expect_only(60, "done")
        self.pexp.expect_action(120, "Hit Esc key to stop autoboot", "\x1b")
        msg(63, "Reboot into Uboot again for urescue")
        self.pexp.expect_action(15, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(15, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_action(15, self.bootloader_prompt, "bootubnt ubntrescue")
        self.pexp.expect_action(15, self.bootloader_prompt, "bootubnt")
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
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Signature Verfied, Success.")

        msg(70, "Updating released firmware...")
        self.pexp.expect_only(120, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(120, "done")

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
        self.pexp.expect_lnxcmd(300, "Please press Enter to activate this console", "")
        self.login()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /lib/build.properties", post_exp=self.linux_prompt)

    def SetNetEnv(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i \"/\/sbin\/lcmd/d\" /etc/inittab", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i \"/\/sbin\/udhcpc/d\" /etc/inittab", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "initd", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, post_exp=self.linux_prompt)
        self.CheckNet()

    def CheckNet(self):
        for _ in range(3):
            is_network_alive = self.is_network_alive_in_linux()
            if is_network_alive is True:
                break
            time.sleep(5)
        if is_network_alive is not True:
            error_critical("Network is not good")

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

        self.login_kernel()
        self.SetNetEnv()
        msg(10, "Boot up to linux console and network is good ...")

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
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id in self.wait_LCM_upgrade_en:
                msg(90, "Waiting LCM upgrading ...")
                self.wait_lcm_upgrade()

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    us_factory_general = USW_RTL838X_FactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
