#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

class UNMSMT7621Factory(ScriptBase):
    def __init__(self):
        super(UNMSMT7621Factory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = "=>"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_MT7621_release"
        self.helper_path = "unms-rlite"
        self.bomrev = "113-" + self.bom_rev
        self.username = "ubnt"
        self.password = "ubnt"
        self.linux_prompt = "#"

        # Base path
        self.tftpdir = self.tftpdir + "/"
        self.toolsdir = "tools/"

        # number of Ethernet
        self.ethnum = {
            'ee6b': "13"
        }

        # number of WiFi
        self.wifinum = {
            'ee6b': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ee6b': "1"
        }

        # ethernet interface
        self.netif = {
            'ee6b': "ifconfig eth0 "
        }

        self.devnetmeta = {
            'ethnum'          : self.ethnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.SET_FAKE_EEPROM       = True
        self.UPDATE_UBOOT          = False
        self.BOOT_RECOVERY_IMAGE   = True
        self.INIT_RECOVERY_IMAGE   = True
        self.NEED_DROPBEAR         = True
        self.PROVISION_ENABLE      = True
        self.DOHELPER_ENABLE       = True
        self.REGISTER_ENABLE       = True
        self.FWUPDATE_ENABLE       = True
        self.DATAVERIFY_ENABLE     = True
        self.SSH_ENABLE            = True

    def set_fake_EEPROM(self):
        # Only 0 second to stop uboot so need to expect it early
        self.pexp.expect_action(30, "MediaTek MT7621AT", "\033\033")

        fake_mac = "7483c29fc33"+str(self.row_id)
        fake_bom = "814"
        fake_rev = "1"
        cmd = "ubntw all {0} {0} {1} {2} {3} 0".format(fake_mac, self.board_id, fake_bom, fake_rev)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "complete")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def boot_recovery_image(self):
        # Only 0 second to stop uboot so need to expect it early
        self.pexp.expect_action(30, "MediaTek MT7621AT", "\033\033")
        self.set_ub_net()
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs \"console=ttyS1,57600n8 ro\"")
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 0x88000000 images/" + self.board_id + "-recovery.bin")
        self.pexp.expect_only(60, "Bytes transferred")
        self.pexp.expect_action(11, self.bootloader_prompt, "bootm")

    def init_recovery_image(self):
        self.login(self.username, self.password, timeout=90, log_level_emerg=True)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "info", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
        time.sleep(2)
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)

    def fwupdate(self):
        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-fw.bin",
            "-l " + self.dut_tmpdir + "/upgrade.bin",
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(180, self.linux_prompt, sstr, self.linux_prompt, valid_chk=True)

        msg(60, "Succeeding in downloading the upgrade tar file ...")

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "sh",
            "/usr/bin/ubnt-upgrade",
            "-d",
            self.dut_tmpdir + "/upgrade.bin"
        ]
        sstr = ' '.join(sstr)

        postexp = [ "Upgrade completed" ]
        self.pexp.expect_lnxcmd(180, self.linux_prompt, sstr, postexp)
        msg(70, "Firmware upgrade done ...")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def ssh_enable(self):
        '''
        unms-r-pro default ssh connection is disabled
        need to enable it manually before FTU test
        '''
        cmd = "ubios-udapi-client put /services \'{\"sshServer\": {\"enabled\": true,\"sshPort\":22}}\'"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True, retry=5)

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 57600"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.SET_FAKE_EEPROM is True:
            self.set_fake_EEPROM()

        if self.BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()

        if self.INIT_RECOVERY_IMAGE is True:
            self.init_recovery_image()
            msg(10, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            self.fwupdate()
            self.login(self.username, self.password, timeout=180, log_level_emerg=True)

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.SSH_ENABLE is True:
            msg(85, "Enable SSH connection...")
            self.ssh_enable()

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    unms_mt7621_factory = UNMSMT7621Factory()
    unms_mt7621_factory.run()

if __name__ == "__main__":
    main()
