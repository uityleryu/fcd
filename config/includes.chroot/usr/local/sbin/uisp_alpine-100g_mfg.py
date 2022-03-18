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


class UISPALPINEMFG(ScriptBase):
    def __init__(self):
        super(UISPALPINEMFG, self).__init__()

        self.ver_extract()
        self.devregpart = "/dev/mtd4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = self.board_id
        self.bootloader_prompt = "UBNT_UISP_ALL>"

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
        self.pexp.expect_action(120, "Autobooting in 2 seconds, press", "\x1b\x1b")
        self.set_ub_net()

        cmd = "setenv tftpdir images/"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "run bootupd"
        post_exp_list = [
            "Bytes transferred",
            "bootupd done"
        ]
        self.pexp.expect_ubcmd(480, self.bootloader_prompt, cmd, post_exp=post_exp_list)

        cmd = "run delenv"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "saveenv"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()

def main():
    uisp_apline = UISPALPINEMFG()
    uisp_apline.run()

if __name__ == "__main__":
    main()
