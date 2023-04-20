#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import re
import stat
import filecmp

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
SETUBMACID_EN = True
CHECK_UBOOT_EN = True
FWUPDATE_EN = False

'''
    ef0d: UT-PHONE-FLEX
    ef0f: UT-ATA
    ef12: UT-ATA-MAX
    ec0e: ULED-SWITCH
    ef15: UTP-G3-Touch
'''


class UVPDVF99FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UVPDVF99FactoryGeneral, self).__init__()
        self.ver_extract()
        self.devregpart = "/dev/mtdblock2"
        self.user = "root"
        self.bootloader_prompt = "#"
        self.fwversion = r"IMAGE_VER: UVP-FLEX_IMAGE_1.0.13"

        # number of Ethernet
        ethnum = {
            'ef0d': "1",
            'ef0f': "1",
            'ef12': "1",
            'ec0e': "1",
            'ef15': "1"
        }

        # number of WiFi
        wifinum = {
            'ef0d': "0",
            'ef0f': "0",
            'ef12': "1",
            'ec0e': "0",
            'ef15': "0"
        }

        # number of Bluetooth
        btnum = {
            'ef0d': "0",
            'ef0f': "0",
            'ef12': "0",
            'ec0e': "1",
            'ef15': "1"
        }

        # helper
        hlp = {
            '0000': "helper_DVF99_release",
            'ef0d': "helper_DVF99_release",
            'ef0f': "helper_DVF99_release_ata",
            'ef12': "helper_DVF99_release_ata_max",
            'ec0e': "helper_DVF101_release",
            'ef15': "helper_DVF101_release"
        }

        pd_dir = {
            '0000': "uvp",
            'ef0d': "uvp",
            'ef0f': "uvp",
            'ef12': "uvp",
            'ec0e': "ec0e",
            'ef15': "ef15"
        }

        flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
            'flashed_dir'     : flashed_dir
        }

        self.netif = {
            'ef0d': "ifconfig eth0 ",
            'ef0f': "ifconfig eth0 ",
            'ef12': "ifconfig eth0 ",
            'ec0e': "ifconfig eth0 ",
            'ef15': "ifconfig eth0 "
        }

        self.helperexe = hlp[self.board_id]
        self.helper_path = pd_dir[self.board_id]

    def mac_colon_format(self, mac):
        mcf = [
            self.mac[0:2],
            self.mac[2:4],
            self.mac[4:6],
            self.mac[6:8],
            self.mac[8:10],
            self.mac[10:12]
        ]
        mcf = ':'.join(mcf)
        return mcf

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Boot to linux console ...")
        self.pexp.expect_action(60, "stop autoboot", "\033")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "setenv dev_ubntconsole true")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "saveenv")
        self.pexp.expect_only(15, "Writing to NAND... OK")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "reset")
        #ef15
        if self.board_id == "ef15":
            self.login(username="ubnt", password="ubnt", retry=15, log_level_emerg=True)
        else:
            self.login(username="root", password="", retry=15, log_level_emerg=True)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)

        cmd = "{0} {1}".format(self.netif[self.board_id], self.dutip)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        time.sleep(3)
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        cmd = "ping -c 1 {0}".format(self.tftp_server)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, postexp)
        msg(10, "Boot up to linux console and network is good ...")

        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
            ============ Registration End ============
        '''

        if SETUBMACID_EN is True:
            if self.board_id == "ef12":
                cmd = "fw_setenv shield=CA"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt, valid_chk=True)

            mcf = self.mac_colon_format(self.mac)
            cmd = "fw_setenv ethaddr {0}; sync".format(mcf)
            self.pexp.expect_lnxcmd(90, self.linux_prompt, cmd, self.linux_prompt)
            time.sleep(1)
            cmd = "fw_printenv ethaddr"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, mcf)

        if CHECK_UBOOT_EN is True:
            mcf = self.mac_colon_format(self.mac)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
            self.pexp.expect_action(60, "stop autoboot", "\033")
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, "printenv ethaddr")
            self.pexp.expect_only(30, "ethaddr=" + mcf)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "securedev")
            postexp = [
                "program OTP values... ok",
                "verify OTP values... ok",
                "device seems to be partially/secured!",
                self.bootloader_prompt
            ]
            index = self.pexp.expect_get_index(30, postexp)
            log_debug("OTP index: " + str(index))
            if index < 0:
                error_critical("OTP program/verify failed")

            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv mfg_mode 1")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv dev_ubntconsole true")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
            self.pexp.expect_action(60, "stop autoboot", "\033")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv mfg_mode")
            self.pexp.expect_only(10, "mfg_mode=1")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv dev_ubntconsole")
            self.pexp.expect_only(10, "dev_ubntconsole=true")

        if FWUPDATE_EN is True:
            self.set_boot_net()
            cmd = "tftp 0xc8800000 images/ef0d-fw.bin.unsign"
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_only(30, "done")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run dfu_manifest_system")
            self.pexp.expect_only(60, "Copy to Flash... done")
            self.pexp.expect_only(60, "U-Boot")
            self.pexp.expect_action(60, "login:", self.user)
            self.pexp.expect_lnxcmd(10, "", "", "")
            cmd = "cat /etc/fw.version"
            output = self.pexp.expect_get_output(cmd, self.linux_prompt)
            match = re.findall(self.fwversion, output)
            if match:
                log_debug("FW version is correct " + self.fwversion)
            else:
                error_critical("OTP program/verify failed")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        uvp_factory_general = UVPDVF99FactoryGeneral()
        uvp_factory_general.run()

if __name__ == "__main__":
    main()
