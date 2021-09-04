#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

SIM_PCYL_LNX_EN = False
SIM_PCYL_UB_EN = False
UB_WR_DUMMY_EN = True
PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
SETBOARDNAME_EN = True
FWUPDATE_EN = True
DATAVERIFY_EN = True
VTSYCHECK_EN = False
AUTODIAG_EN = False

'''
    eed4: UISP-SPINE-100G
    eed5: UISP-LEAF-100G
'''


class UISPALPINE(ScriptBase):
    def __init__(self):
        super(UISPALPINE, self).__init__()

        self.ver_extract()
        self.devregpart = "/dev/mtd4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = self.board_id

        # number of Ethernet
        ethnum = {
            'eed4': "130",
            'eed5': "65",
        }

        # number of WiFi
        wifinum = {
            'eed4': "0",
            'eed5': "0",
        }

        # number of Bluetooth
        btnum = {
            'eed4': "1",
            'eed5': "1",
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

    def login(self, username="ubnt", password="ubnt", timeout=10, press_enter=False, retry=3, log_level_emerg=False):
        """
        should be called at login console
        """
        for i in range(0, retry + 1):
            post = [
                "login:",
                "Error-A12 login"
            ]
            ridx = self.pexp.expect_get_index(timeout, post)
            if ridx >= 0:
                '''
                    To give twice in order to make sure of that the username has been keyed in
                '''
                self.pexp.expect_action(10, "", username)
                self.pexp.expect_action(10, "Password:", password)
                break
            else:
                self.pexp.expect_action(timeout, "", "\003")
                print("Retry login {}/{}".format(i + 1, retry))
                timeout = 10
                self.pexp.expect_action(10, "", "\n")
        else:
            raise Exception("Login exceeded maximum retry times {}".format(retry))

        if log_level_emerg is True:
            self.pexp.expect_action(10, self.linux_prompt, "dmesg -n1")

        return ridx

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

        msg(5, "Boot from SPI recovery image ...")
        self.login(retry=100)
        self.set_lnx_net("eth1")
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

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()

def main():
    uisp_apline = UISPALPINE()
    uisp_apline.run()

if __name__ == "__main__":
    main()
