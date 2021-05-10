#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

class UNMSALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UNMSALPINEFactoryGeneral, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = "UBNT"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.bomrev = "113-" + self.bom_rev
        self.username = "ubnt"
        self.password = "ubnt"
        self.linux_prompt = "#"

        # Base path
        self.tftpdir = self.tftpdir + "/"
        self.toolsdir = "tools/"

        # helper path
        helppth = {
            'ee6a': "uisp-console",
        }

        self.helper_path = helppth[self.board_id]

        # switch chip
        self.swchip = {
            'ee6a': "rtl83xx",
        }

        # sub-system ID
        self.wsysid = {
            'ee6a': "77076aee",
        }

        # number of Ethernet
        self.ethnum = {
            'ee6a': "11",
        }

        # number of WiFi
        self.wifinum = {
            'ee6a': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ee6a': "1",
        }

        # ethernet interface
        self.netif = {
            'ee6a': "ifconfig eth0 ",
        }

        self.infover = {
            'ee6a': "Version:",
        }

        self.devnetmeta = {
            'ethnum'          : self.ethnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.SET_FAKE_EEPROM       = True
        self.UPDATE_UBOOT          = True
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
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + self.wsysid[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000004 01d30200")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000008 ffdaecfc")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.w 0x0800000c 000"+str(self.row_id))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf erase 0x410000 0x1000")
        self.pexp.expect_only(30, "Erased: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 0x41000c 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000004 0x410010 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000008 0x410000 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x0800000c 0x410004 0x2")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000008 0x410006 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x0800000c 0x41000a 0x2")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def update_uboot(self):
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv tftpdir images/" + self.board_id + "_signed_")
        self.set_ub_net()
        time.sleep(2)
        self.is_network_alive_in_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_only(10, "bootupd done")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def reset_uboot_env(self):
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "env default -a -f")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")  # for second partition
        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def boot_recovery_image(self):
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.set_ub_net()
        time.sleep(2)
        self.is_network_alive_in_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs ubnt-flash-factory pci=pcie_bus_perf console=ttyS0,115200")
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 0x08000004 images/" + self.board_id + "-recovery")
        self.pexp.expect_only(90, "Bytes transferred")
        self.pexp.expect_action(11, self.bootloader_prompt, "bootm $fitbootconf")

    def init_recovery_image(self):
        self.login(self.username, self.password, timeout=180, log_level_emerg=True)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "info", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
        time.sleep(2)
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo 5edfacbf > /proc/ubnthal/.uf", self.linux_prompt)

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

        postexp = ["U-Boot"]
        self.pexp.expect_lnxcmd(300, self.linux_prompt, sstr, postexp)

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
        cmd = 'ubios-udapi-client put -r /services "$(ubios-udapi-client get -r /services | jq \'.sshServer.enabled = true\')"'
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True, retry=5)

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.SET_FAKE_EEPROM is True:
            self.set_fake_EEPROM()

        if self.UPDATE_UBOOT is True:
            self.update_uboot()
            self.reset_uboot_env()

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
            msg(70, "Firmware upgrade done ...")
            self.reset_uboot_env()
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
    unms_alpine_factory_general = UNMSALPINEFactoryGeneral()
    unms_alpine_factory_general.run()

if __name__ == "__main__":
    main()
