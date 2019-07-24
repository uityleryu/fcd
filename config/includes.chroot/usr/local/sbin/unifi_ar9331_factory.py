#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

class UNIFIAR9331FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UNIFIAR9331FactoryGeneral, self).__init__()

        self.ver_extract()
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = "ar7240>"
        self.devregpart = "/dev/mtdblock5"
        self.helperexe = "helper_mips32"
        self.helper_path = "usp"
        self.product_class = "radio"
        self.force_update_eeprom = False
        self.cal_data_beg_ofs = 4096 * 1
        self.cal_data_size = 4096 * 8
        self.cal_data_end_ofs = self.cal_data_beg_ofs + self.cal_data_size

        # number of Ethernet
        ethnum = {
            'e643': "1",
            'e648': "1",
        }

        # number of WiFi
        wifinum = {
            'e643': "1",
            'e648': "1",
        }

        # number of Bluetooth
        btnum = {
            'e643': "1",
            'e648': "1",
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

        self.netif = {
            'e643': "ifconfig eth1 ",
            'e648': "ifconfig br0 ",
        }

        self.UPDATE_UBOOT_ENABLE    = False
        self.PROGRAM_FW_ENABLE      = True
        self.INIT_FW_ENABLE         = True
        self.PROVISION_ENABLE       = True
        self.GET_CAL_DATA_ENABLE    = True
        self.DOHELPER_ENABLE        = True
        self.REGISTER_ENABLE        = True
        self.FWUPDATE_ENABLE        = False
        self.DATAVERIFY_ENABLE      = True

    def program_fw(self):
        self.pexp.expect_action(30, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        time.sleep(3)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "urescue")
        self.pexp.expect_only(15, "Waiting for connection")

        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir + "/" + self.fwimg,
               self.dutip]
        cmdj = ' '.join(cmd)
        time.sleep(3)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(15, "Receiving file from")
        self.pexp.expect_only(15, "Copying partition")
        self.pexp.expect_only(120, "Firmware update complete")


    def init_fw(self):
        self.pexp.expect_lnxcmd(60, "Please press Enter to activate this console.", "")
        self.login(self.user, self.password, 10)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n1")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.PROGRAM_FW_ENABLE is True:
            msg(10, "Program FW ...")
            self.program_fw()

        if self.INIT_FW_ENABLE is True:
            msg(15, "Init FW ...")
            self.init_fw()
 
        if self.PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.GET_CAL_DATA_ENABLE is True:
            msg(25, "Put calibration data into eeprom")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if=" + self.devregpart + " bs=1 skip=" + str(self.cal_data_beg_ofs) + " count=" + str(self.cal_data_size) + " > /tmp/EEPROM_CAL")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if=/tmp/e.gen." + self.row_id + " bs=1 skip=0 count=" + str(self.cal_data_beg_ofs) + " > /tmp/e.gen." + self.row_id + ".PartA")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if=/tmp/e.gen." + self.row_id + " bs=1 skip=" + str(self.cal_data_end_ofs) + " > /tmp/e.gen." + self.row_id + ".PartB")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /tmp/e.gen." + self.row_id + ".PartA /tmp/EEPROM_CAL /tmp/e.gen." + self.row_id + ".PartB > /tmp/e.gen." + self.row_id + "_update")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "mv /tmp/e.gen." + self.row_id + "_update /tmp/e.gen." + self.row_id + "")

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
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()

def main():
    unifi_ar9331_factory_general = UNIFIAR9331FactoryGeneral()
    unifi_ar9331_factory_general.run()

if __name__ == "__main__":
    main()
