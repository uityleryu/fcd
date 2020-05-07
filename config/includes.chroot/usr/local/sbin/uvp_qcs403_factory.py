#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

sys.path.append("/tftpboot/tools")

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True


class UVPQCS403FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UVPQCS403FactoryGeneral, self).__init__()

        self.ver_extract()
        self.devregpart = "/dev/mtdblock22"
        self.helperexe = "helper_QCS403_debug"
        self.helper_path = "uvp"

        # number of Ethernet
        ethnum = {
            'ef11': "1"
        }

        # number of WiFi
        wifinum = {
            'ef11': "1"
        }

        # number of Bluetooth
        btnum = {
            'ef11': "1"
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        self.login(username="root", password="ubnt", timeout=120)
        cmd = "dmesg -n1"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        self.chk_lnxcmd_valid()

        cmd = "ifconfig eth0 down"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        self.chk_lnxcmd_valid()
        time.sleep(2)

        self.set_lnx_net("eth0")
        self.is_network_alive_in_linux()

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

        msg(100, "Completing registration ...")
        self.close_fcd()


def main():
    uvp_factory_general = UVPQCS403FactoryGeneral()
    uvp_factory_general.run()

if __name__ == "__main__":
    main()
