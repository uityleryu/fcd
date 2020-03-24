#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

SET_FAKE_EEPROM     = True
UPDATE_UBOOT        = True
BOOT_RECOVERY_IMAGE = True
INIT_RECOVERY_IMAGE = True 
NEED_DROPBEAR       = True  
PROVISION_ENABLE    = True  
DOHELPER_ENABLE     = True  
REGISTER_ENABLE     = True  
FWUPDATE_ENABLE     = True
DATAVERIFY_ENABLE   = True

class UDMALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UDMALPINEFactoryGeneral, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.UNMS_series = ['ee6a']
        self.bootloader_prompt = "UBNT"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = "udm"
        self.helper_path = "unms" if self.board_id in self.UNMS_series else self.helper_path
        self.bomrev = "113-" + self.bom_rev
        self.username = "root"
        self.username = "ubnt" if self.board_id in self.UNMS_series else self.username
        self.password = "ubnt"
        self.linux_prompt = "#"
       
        # Base path 
        self.tftpdir = self.tftpdir + "/"
        self.toolsdir = "tools/"
 
        # switch chip
        self.swchip = {
            'ea11': "qca8k",
            'ea13': "rtl83xx",
            'ea15': "rtl83xx",
            'ea19': "rtl83xx",
            'ee6a': "rtl83xx"
        }
        
        # sub-system ID
        self.wsysid = {
            'ea11': "770711ea",
            'ea13': "770713ea",
            'ea15': "770715ea",
            'ea19': "770719ea",
            'ee6a': "77076aee"
        }
        
        # number of Ethernet
        self.ethnum = {
            'ea11': "5",
            'ea13': "8",
            'ea15': "11",
            'ea19': "4",
            'ee6a': "11"
        }
        
        # number of WiFi
        self.wifinum = {
            'ea11': "2",
            'ea13': "2",
            'ea15': "0",
            'ea19': "0",
            'ee6a': "0"
        }
        
        # number of Bluetooth
        self.btnum = {
            'ea11': "1",
            'ea13': "1",
            'ea15': "1",
            'ea19': "1",
            'ee6a': "1"
        }
       
        # ethernet interface 
        self.netif = {
            'ea11': "ifconfig eth0 ",
            'ea13': "ifconfig eth1 ",
            'ea15': "ifconfig eth0 ",
            'ea19': "ifconfig eth1 ",
            'ee6a': "ifconfig eth0 "
        }
        
        self.infover = {
            'ea11': "Version:",
            'ea13': "Version",
            'ea15': "Version:",
            'ea19': "Version:",
            'ee6a': "Version:"
        }

        self.devnetmeta = {
            'ethnum'          : self.ethnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def set_fake_EEPROM(self):
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + self.wsysid[self.board_id])

        UDM_PRO_ID = 'ea15'
        tmp_list = [UDM_PRO_ID] + self.UNMS_series

        if self.board_id in tmp_list:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000004 01d30200")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")

        if self.board_id in self.UNMS_series:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf erase 0x410000 0x1000")
        else:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf erase 0x1f0000 0x1000")
        self.pexp.expect_only(30, "Erased: OK")

        if self.board_id in self.UNMS_series:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 0x41000c 0x4")
        else:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 0x1f000c 0x4")

        if self.board_id in tmp_list:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000004 0x410010 0x4")
        elif self.board_id == UDM_PRO_ID:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000004 0x1f0010 0x4")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def update_uboot(self):
        self.pexp.expect_action(10, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.set_boot_net()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv tftpdir images/" + self.board_id + "_signed_")
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_only(10, "bootupd done")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def boot_recovery_image(self):
        self.pexp.expect_action(10, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.set_boot_net()
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs ubnt-flash-factory pci=pcie_bus_perf console=ttyS0,115200")
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 0x08000004 images/" + self.board_id + "-recovery")
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_action(11, self.bootloader_prompt, "bootm $fitbootconf")

    def init_recovery_image(self):
        self.login(self.username, self.password, 60)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "info", self.linux_prompt)
        if self.board_id == 'ea19':
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig br0 down")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "brctl delbr br0")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 down")
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
        self.pexp.expect_lnxcmd(300, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "sh",
            "/usr/bin/ubnt-upgrade",
            "-d",
            self.dut_tmpdir + "/upgrade.bin"
        ]
        sstr = ' '.join(sstr)

        if self.board_id not in self.UNMS_series:
            postexp = [
                "Firmware version",
                "Writing recovery"
            ]
        else:
            postexp = [
                "Starting kernel"
            ]

        self.pexp.expect_lnxcmd(300, self.linux_prompt, sstr, postexp)

    def check_info(self):
        if self.board_id not in self.UNMS_series:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "info", self.infover[self.board_id], retry=5)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

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

        if SET_FAKE_EEPROM is True:
            self.set_fake_EEPROM()

        if UPDATE_UBOOT is True:
            self.update_uboot()

        if BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()

        if INIT_RECOVERY_IMAGE is True:
            self.init_recovery_image()
            msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")
            self.login(self.username, self.password, 200)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    udm_alpine_factory_general = UDMALPINEFactoryGeneral()
    udm_alpine_factory_general.run()

if __name__ == "__main__":
    main()     
