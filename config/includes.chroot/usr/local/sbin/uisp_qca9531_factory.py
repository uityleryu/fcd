#!/usr/bin/python3

from binascii import unhexlify
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil

class UISPQCA9531Factory(ScriptBase):
    def __init__(self):
        super(UISPQCA9531Factory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        self.ubpmt = {
            'ee5a': "#",
            'ee5b': "#",
        }

        self.lnxpmt = {
            'ee5a': "#",
            'ee5b': "#",
        }

        self.lnxpmt_fcdfw = {
            'ee5a': "#",
            'ee5b': "#",
        }

        self.product_class_table = {
            'ee5a': "basic",
            'ee5b': "basic", 
        }

        self.devregmtd = {
            'ee5a': "/dev/mtdblock5",
            'ee5b': "/dev/mtdblock5",
        }

        self.helpername = {
            'ee5a': "helper_ARxxxx_release",
            'ee5b': "helper_ARxxxx_release",
        }

        self.pd_dir_table = {
            'ee5a': "uisp_p",
            'ee5b': "uisp_p_pro",
        }

        self.ethnum = {
            'ee5a': "1",
            'ee5b': "1",
        }

        self.wifinum = {
            'ee5a': "0",
            'ee5b': "0",
        }

        self.btnum = {
            'ee5a': "1",
            'ee5b': "1",
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.devregpart = self.devregmtd[self.board_id]
        self.product_class = self.product_class_table[self.board_id]

        self.linux_prompt = self.lnxpmt[self.board_id]
        self.linux_prompt_fcdfw = self.lnxpmt_fcdfw[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]

        self.tftpdir = self.tftpdir + "/"

        # EX: /tftpboot/tools/af_af60
        self.pd_dir = self.pd_dir_table[self.board_id]
        self.tools_full_dir = os.path.join(self.fcd_toolsdir, self.pd_dir)

        # EX: /tftpboot/tools/af_af60/id_rsa
        self.id_rsa = os.path.join(self.tools_full_dir, "id_rsa")
        self.bomrev = "13-{0}".format(self.bom_rev)

        # EX: helper in FCD host: /tftpboot/tools/af_af60/helper_IPQ40xx
        self.helperexe = self.helpername[self.board_id]
        self.helper_path = self.pd_dir

        # EX: /tftpboot/tools/commmon/x86-64k-ee
        self.eetool = os.path.join(self.fcd_commondir, self.eepmexe)
        self.dropbear_key = "/tmp/dropbear_key.rsa.{0}".format(self.row_id)

    def stop_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
       
    def set_up_kernel(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "\n\n")
        time.sleep(3)
        self.pexp.expect_ubcmd(5, self.linux_prompt, "\n", retry=10)
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, 'ifconfig eth0 ' + self.dutip)
        self.is_network_alive_in_linux()

    def set_up_uboot(self):
        self.stop_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'ubnt all 68d79a1f4454 uisp-p-pro 822 1')
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'run bootcmd')

    def run(self):
        UPDATE_UBOOT_EN = True
        PROVISION_EN = True
        DOHELPER_EN = True
        REGISTER_EN = True
        UPDATE_FCDFW_EN = True
        DATAVERIFY_EN = True

        """
        Main procedure of factory
        """
        msg(1, "Start Procedure")
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        if UPDATE_UBOOT_EN is True:
            msg(5, "Set up U-Boot ...")
            self.set_up_uboot()
            msg(10, "Completed set up U-Boot...")

        self.set_up_kernel()

        if PROVISION_EN is True:    
            msg(20, "Sendtools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
            msg(40, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.registration()
            msg(50, "Finish doing registration ...")
            self.check_devreg_data()
            msg(60, "Finish doing signed file and EEPROM checking ...")

        msg(100, "Complete FCD process ...")
        self.close_fcd()
        
def main():
    uisp_qca9531_factory = UISPQCA9531Factory()
    uisp_qca9531_factory.run()

if __name__ == "__main__":
    main()
