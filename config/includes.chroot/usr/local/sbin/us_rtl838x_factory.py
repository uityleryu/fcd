#!/usr/bin/python3
import re

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

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
        self.boot_prompt = "uboot> #"

        # TODO: FW have issue now. It should be fixed.
        # self.devregpart = "/dev/mtdblock6"
        self.devregpart = "/dev/mtd6"

        self.bomrev = "113-" + self.bom_rev

        self.helpername = {
            'ed20': "helper_RTL838x",
            'ed21': "helper_RTL838x",
            'ed22': "helper_RTL838x",
            'ed23': "helper_RTL838x",
            'ed24': "helper_RTL838x",
            'ed25': "helper_RTL838x",
            'ed26': "helper_RTL838x",
            'ed2a': "helper_RTL838x",
            'ed2c': "helper_RTL838x",
            'ed2d': "helper_RTL838x",
            'ed2e': "helper_RTL838x",  # usw-16-poe 32MB
            'ed50': "helper_RTL838x",  # usw-24-poe 32MB
            'ed51': "helper_RTL838x",  # usw-24 32MB
            'ed52': "helper_RTL838x",  # usw-48-pe 32MB
            'ed53': "helper_RTL838x",  # usw-48 32MB
            'ed54': "helper_RTL838x",  # usw-lite-16-poe 32MB
            'ed55': "helper_RTL838x",  # usw-lite-8-poe 32MB
            'ed56': "helper_RTL838x",  # usw-pro-24-poe (RTK)
            'ed58': "helper_RTL838x",  # usw-pro-48-poe (RTK)
            'ed5a': "helper_RTL838x",  # usw-pro-8-poe (RTK)
            'ed5b': "helper_RTL838x_UNIFI_release",  # usw-pro-max-24-poe (RTK)
            'ed5c': "helper_RTL838x_UNIFI_release",  # usw-pro-max-24 (RTK)
            'ed5d': "helper_RTL838x_UNIFI_release",  # usw-pro-max-48-poe (RTK)
            'ed5e': "helper_RTL838x_UNIFI_release",  # usw-pro-max-48 (RTK)
        }

        self.helperexe = self.helpername[self.board_id]
        self.helper_path = "usw_rtl838x"
        self.bootloader_prompt = "uboot>"
        self.fwimg = self.board_id + "-fw.bin"

        # customize variable for different products
        self.skip_FW_upgrade = {}

        # customize variable for different products
        self.wait_LCM_upgrade_en = {
            'ed20', 'ed21', 'ed22', 'ed23', 'ed24', 'ed25', 'ed2c', 'ed2d',
            'ed2e', 'ed50', 'ed51', 'ed52', 'ed53', 'ed56', 'ed58', 'ed5a',
            'ed5b', 'ed5c', 'ed5d', 'ed5e'
        }
        # TODO: Add ed5b & ed5d later when available

        self.check_led_mcu_fw_en = {
            'ed5b', 'ed5c', 'ed5d', 'ed5e'
        }

        self.led_board_id = {
            'ed5b': "2",
            'ed5c': "2",
            'ed5d': "1",
            'ed5e': "1",
        }

        self.disable_powerd_list = ['ed2c']
        self.disable_battery = {'ed2c'}

        # number of Ethernet
        self.macnum = {
            'ed20': "3",  # usw-16-poe
            'ed21': "3",  # usw-24-poe
            'ed22': "3",  # usw-48-poe
            'ed23': "3",  # usw-16
            'ed24': "3",  # usw-24
            'ed25': "3",  # usw-48
            'ed26': "3",  # usw-lite-16-poe
            'ed2a': "3",  # usw-lite-8-poe
            'ed2c': "2",  # usw-missioon-critical. Total 3 (eth:2 + bt:1). Mike taylor could not increase so workaround it  # noqa: E501
            'ed2d': "3",  # usw-aggregation
            'ed2e': "3",  # usw-16-poe 32MB
            'ed50': "3",  # usw-24-poe 32MB
            'ed51': "3",  # usw-24 32MB
            'ed52': "3",  # usw-48-pe 32MB
            'ed53': "3",  # usw-48 32MB
            'ed54': "3",  # usw-lite-16-poe 32MB
            'ed55': "3",  # usw-lite-8-poe 32MB
            'ed56': "3",  # usw-pro-24-poe (RTK)
            'ed58': "3",  # usw-pro-48-poe (RTK)
            'ed5a': "3",  # usw-pro-8-poe (RTK)
            'ed5b': "3",  # usw-pro-max-24-poe (RTK)
            'ed5c': "3",  # usw-pro-max-24 (RTK)
            'ed5d': "3",  # usw-pro-max-48-poe (RTK)
            'ed5e': "3",  # usw-pro-max-48 (RTK)
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
            'ed2a': "0",
            'ed2c': "0",
            'ed2d': "0",
            'ed2e': "0",  # usw-16-poe 32MB
            'ed50': "0",  # usw-24-poe 32MB
            'ed51': "0",  # usw-24 32MB
            'ed52': "0",  # usw-48-pe 32MB
            'ed53': "0",  # usw-48 32MB
            'ed54': "0",  # usw-lite-16-poe 32MB
            'ed55': "0",  # usw-lite-8-poe 32MB
            'ed56': "0",  # usw-pro-24-poe (RTK)
            'ed58': "0",  # usw-pro-48-poe (RTK)
            'ed5a': "0",  # usw-pro-8-poe (RTK)
            'ed5b': "0",  # usw-pro-max-24-poe (RTK)
            'ed5c': "0",  # usw-pro-max-24 (RTK)
            'ed5d': "0",  # usw-pro-max-48-poe (RTK)
            'ed5e': "0",  # usw-pro-max-48 (RTK)
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
            'ed2a': "0",
            'ed2c': "1",
            'ed2d': "0",
            'ed2e': "0",  # usw-16-poe 32MB
            'ed50': "0",  # usw-24-poe 32MB
            'ed51': "0",  # usw-24 32MB
            'ed52': "0",  # usw-48-pe 32MB
            'ed53': "0",  # usw-48 32MB
            'ed54': "0",  # usw-lite-16-poe 32MB
            'ed55': "0",  # usw-lite-8-poe 32MB
            'ed56': "0",  # usw-pro-24-poe (RTK)
            'ed58': "0",  # usw-pro-48-poe (RTK)
            'ed5a': "0",  # usw-pro-8-poe (RTK)
            'ed5b': "0",  # usw-pro-max-24-poe (RTK)
            'ed5c': "0",  # usw-pro-max-24 (RTK)
            'ed5d': "0",  # usw-pro-max-48-poe (RTK)
            'ed5e': "0",  # usw-pro-max-48 (RTK)
        }

        self.netif = {
            'ed20': "ifconfig eth0 ",
            'ed21': "ifconfig eth0 ",
            'ed22': "ifconfig eth0 ",
            'ed23': "ifconfig eth0 ",
            'ed24': "ifconfig eth0 ",
            'ed25': "ifconfig eth0 ",
            'ed26': "ifconfig eth0 ",
            'ed2a': "ifconfig eth0 ",
            'ed2c': "ifconfig eth0 ",
            'ed2d': "ifconfig eth0 ",
            'ed2e': "ifconfig eth0 ",  # usw-16-poe 32MB
            'ed50': "ifconfig eth0 ",  # usw-24-poe 32MB
            'ed51': "ifconfig eth0 ",  # usw-24 32MB
            'ed52': "ifconfig eth0 ",  # usw-48-pe 32MB
            'ed53': "ifconfig eth0 ",  # usw-48 32MB
            'ed54': "ifconfig eth0 ",  # usw-lite-16-poe 32MB
            'ed55': "ifconfig eth0 ",  # usw-lite-8-poe 32MB
            'ed56': "ifconfig eth0 ",  # usw-pro-24-poe (RTK)
            'ed58': "ifconfig eth0 ",  # usw-pro-48-poe (RTK)
            'ed5a': "ifconfig eth0 ",  # usw-pro-8-poe (RTK)
            'ed5b': "ifconfig eth0 ",  # usw-pro-max-24-poe (RTK)
            'ed5c': "ifconfig eth0 ",  # usw-pro-max-24 (RTK)
            'ed5d': "ifconfig eth0 ",  # usw-pro-max-48-poe (RTK)
            'ed5e': "ifconfig eth0 ",  # usw-pro-max-48 (RTK)
        }

        self.set_boardmodel_uboot = ['ed5b', 'ed5c']
        self.longtime_login = ['ed5b', 'ed5d']

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
        self.pexp.expect_action(60, "Hit Esc key to stop autoboot", "\x1b")
        msg(60, "Reboot into Uboot for resetting to default environment")
        # FIXME: need to add sysid condition?
        self.pexp.expect_action(15, self.bootloader_prompt, "env set boardmodel unknown")
        self.pexp.expect_action(20, self.bootloader_prompt, "bootubnt")
        self.pexp.expect_only(60, "Resetting to default environment")
        self.pexp.expect_only(60, "done")
        self.pexp.expect_action(120, "Hit Esc key to stop autoboot", "\x1b")

        msg(63, "Reboot into Uboot again for urescue")

        def set_ip_and_urescue():
            self.pexp.expect_action(15, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
            self.pexp.expect_action(15, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
            self.pexp.expect_action(15, self.bootloader_prompt, "bootubnt ubntrescue")
            self.pexp.expect_action(15, self.bootloader_prompt, "bootubnt")

        set_ip_and_urescue()

        wrong_boardmodel = 'Wrong boardmodel'
        listening_tftp = 'Listening for TFTP transfer on'
        expect_list = [wrong_boardmodel, listening_tftp]
        index = self.pexp.expect_get_index(timeout=60, exptxt=expect_list)

        if index == self.pexp.TIMEOUT:
            error_critical(msg='Can not detect "Wrong boardmodel" or "TFTP transfer on", failed to start urescue.')
        elif index == 0:
            log_debug('Detected "Wrong boardmodel", reboot into Uboot again for urescue.')

            self.pexp.expect_action(120, "Hit Esc key to stop autoboot", "\x1b")
            set_ip_and_urescue()
            self.pexp.expect_only(60, "Listening for TFTP transfer on.")
        elif index == 1:
            log_debug('No "Wrong boardmodel" error, continue to FW upload.')
            pass

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
        self.pexp.expect_only(240, "done")

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
        if self.board_id in self.longtime_login:
            self.pexp.expect_lnxcmd(600, "Please press Enter to activate this console", "")  # Color LED models
        else:
            self.pexp.expect_lnxcmd(300, "Please press Enter to activate this console", "")

        self.login()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /lib/build.properties", post_exp=self.linux_prompt)

    def SetNetEnv(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i \"/\/sbin\/lcmd/d\" /etc/inittab", post_exp=self.linux_prompt)  # noqa: E501
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i \"/\/sbin\/udhcpc/d\" /etc/inittab", post_exp=self.linux_prompt)  # noqa: E501
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "initd", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, post_exp=self.linux_prompt)  # noqa: E501
        if self.board_id == "ed2d":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "/usr/share/librtk/diag -c \"port set 10g-media port all fiber10g\"", post_exp=self.linux_prompt)  # noqa: E501
        self.is_network_alive_in_linux()

    def disable_powerd(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i '/powerd/ s,^,#,g' /etc/inittab && init -q", post_exp=self.linux_prompt)  # noqa: E501
        time.sleep(5)

    def clear_eeprom_in_uboot(self, timeout=30):
        # Ensure sysid is empty when FW is T1 img.
        # Some T1 image will boot so slow if get non-empty sysid
        self.pexp.expect_action(timeout, "Hit Esc key to stop autoboot", "\x1b")
        self.pexp.expect_action(10, self.boot_prompt, "bootubnt ucleareeprom")
        self.pexp.expect_action(10, self.boot_prompt, "reset")

    def set_boardmodel_in_uboot(self):
        self.pexp.expect_action(30, "Hit Esc key to stop autoboot", "\x1b")
        self.pexp.expect_ubcmd(5, self.boot_prompt, 'setenv boardmodel UBNT_USPM24')
        self.pexp.expect_ubcmd(5, self.boot_prompt, 'saveenv')
        self.pexp.expect_action(5, self.boot_prompt, "bootubnt")

    def check_led_mcu_fw_version(self):

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "", post_exp=self.linux_prompt)
        output = self.pexp.expect_get_output(action="ls -l /usr/share/firmware/port_led_fw.bin", prompt=self.linux_prompt, timeout=10)  # noqa: E501
        regex_pattern = r'\d+(?:\.\d+)+'
        match = re.search(regex_pattern, output.split("->")[1])

        if not match:
            error_critical("LED MCU FW not found.")
        else:
            led_mcu_fw_version = match.group()
            log_debug("LED MCU FW Expect Version: {0}".format(led_mcu_fw_version))
            try:
                self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/led/led_version", post_exp=led_mcu_fw_version, retry=18)  # noqa: E501
                log_debug("LED MCU FW version matched!")
            except Exception as e:
                log_error(e)
                error_critical("LED MCU FW version mismatch, expect version is {0}!".format(led_mcu_fw_version))

    def set_boardid_for_mcu_fw(self):
        led_board_id = self.led_board_id[self.board_id]
        log_debug("LED board ID for [{0}] is {1}".format(self.board_id, led_board_id))

        # unlock MCU
        cmd = 'echo "unlock_board_id 1" > /proc/led/led_test_cmd'
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp=self.linux_prompt)

        time.sleep(0.2)
        cmd = "echo {0} > /proc/led/led_board_id".format(led_board_id)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp=self.linux_prompt)

        time.sleep(0.2)
        # lock MCU
        cmd = 'echo "unlock_board_id 0" > /proc/led/led_test_cmd'
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp=self.linux_prompt)

    def check_boardid_for_mcu_fw(self):
        cmd = "cat /proc/led/led_board_id"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp=self.led_board_id[self.board_id])

    def disable_li_battery(self):
        self.pexp.expect_action(10, self.linux_prompt, "syswrapper.sh shutdown")

    def check_rtk_network(self):
        self.pexp.expect_action(30, "Hit Esc key to stop autoboot", "")
        expects = [
            'Starting kernel ...',
            "Hit Esc key to stop autoboot",
        ]
        ans = self.pexp.expect_get_index(300, expects)
        if ans == 1:
            self.pexp.expect_ubcmd(5, '', '\x1b')
            print_env = 'printenv'
            res = self.pexp.expect_get_output(print_env, self.boot_prompt)
            key = 'UBNT_USL48_8218D'
            if key in res:
                rtk_network_on = 'rtk network on'
                self.pexp.expect_ubcmd(5, self.boot_prompt, rtk_network_on)

            if self.board_id == "ed5d":
                self.pexp.expect_ubcmd(5, self.boot_prompt, 'setenv boardmodel UBNT_USPM48')
                self.pexp.expect_ubcmd(5, self.boot_prompt, 'saveenv')
            self.pexp.expect_ubcmd(5, self.boot_prompt, 'bootubnt')

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE is True:
            pass
        if self.BOOT_RECOVERY_IMAGE is True:
            pass

        self.clear_eeprom_in_uboot()
        msg(10, "Clear EEPROM in uboot")

        # TODO: ed5b got error in uboot
        if self.board_id in self.set_boardmodel_uboot:
            self.set_boardmodel_in_uboot()
            msg(13, "Set boardmodel in uboot")

        else:
            msg(13, "Check RTK Network")
            self.check_rtk_network()

        self.login_kernel()
        self.SetNetEnv()
        msg(15, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files(helper_args_type="new")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        # reboot anyway
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot -f")
        if self.FWUPDATE_ENABLE is True:
            if self.board_id not in self.skip_FW_upgrade:
                msg(55, "Starting firmware upgrade process...")
                self.fwupdate()
                msg(80, "Completing firmware upgrading ...")

        self.login_kernel()

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(82, "Succeeding in checking the devreg information ...")

        if self.board_id in self.disable_powerd_list:
            msg(83, "Disable powerd")
            self.disable_powerd()

        if self.WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id in self.wait_LCM_upgrade_en:
                msg(85, "Waiting LCM upgrading ...")
                self.wait_lcm_upgrade()

        if self.board_id in self.check_led_mcu_fw_en:
            msg(90, "Check LED MCU FW version and board ID...")
            self.check_led_mcu_fw_version()
            self.set_boardid_for_mcu_fw()
            self.check_boardid_for_mcu_fw()

        if self.board_id in self.disable_battery:
            msg(95, "Disable battery")
            self.disable_li_battery()

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    us_factory_general = USW_RTL838X_FactoryGeneral()
    us_factory_general.run()


if __name__ == "__main__":
    main()
