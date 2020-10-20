#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import filecmp

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.common import Common
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True


class UNIFIBMCFactory(ScriptBase):
    def __init__(self):
        super(UNIFIBMCFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.helperexe = "helper_AST2500_release"
        self.helper_path = "usrv"
        self.devregpart = "/tmp/eeprom0"

        # number of mac
        self.macnum = {
            '1200': "2"
        }

        # number of WiFi
        self.wifinum = {
            '1200': "0"
        }

        # number of Bluetooth
        self.btnum = {
            '1200': "1"
        }

        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.PROVISION_EN       = True
        self.DOHELPER_EN        = True
        self.REGISTER_EN        = True

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        self.login(timeout=300, username="root", password="0penBmc")
        # Workaround: To sleep until network stable, the network intialization is divided into several parts
        #             It's hard to check if network initialization completes or not via ping.
        time.sleep(60)
        cmd = "dmesg -n1"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        cmd = "dd if=/dev/zero bs=1k count=64 | tr '\\000' '\\377' > {0}".format(self.devregpart)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            self.erase_eefiles()
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
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

        cmd = "write_eeprom 6-0050 {0}".format(self.devregpart)
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, "Write EEPROM Done")
        msg(60, "Finish writing EEPROM ...")

        eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)
        cmd = "read_eeprom 6-0050 {0}".format(eechk_dut_path)
        self.pexp.expect_lnxcmd(120, self.linux_prompt, cmd, "Read EEPROM Done")

        self.tftp_put(remote=self.eechk_path, local=eechk_dut_path, timeout=30)
        rtc = filecmp.cmp(self.eechk_path, self.eesigndate_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")
        msg(70, "Finish comparing EEPROM ...")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm -rf /run/initramfs/rw/cow/etc/systemd/network",
                                self.linux_prompt)

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    factory = UNIFIBMCFactory()
    factory.run()

if __name__ == "__main__":
    main()
