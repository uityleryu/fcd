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


class UAMT7621Factory(ScriptBase):
    def __init__(self):
        super(UAMT7621Factory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        '''
            ec43: UA-Locker
        '''

        self.ubpmt = {
            'ec43': "MT7621 #|==>|=>"
        }

        # linux console prompt
        self.lnxpmt = {
            'ec43': "root@LEDE:/#"
        }

        self.lnxpmt_fcdfw = {
            'ec43': "#"
        }

        self.bootloader = {
            'ec43': "{}-fwuboot.bin".format(self.board_id)
        }

        self.cacheaddr = {
            'ec43': "0x80010000"
        }

        self.ubaddr = {
            'ec43': "0x00000"
        }

        self.ubsz = {
            'ec43': "0x60000"
        }

        self.cfgaddr = {
            'ec43': ""
        }

        self.cfgsz = {
            'ec43': ""
        }

        self.epromaddr = {
            'ec43': ""
        }

        self.epromsz = {
            'ec43': ""
        }

        self.product_class_table = {
            'ec43': "basic"
        }

        self.devregmtd = {
            'ec43': "/dev/mtdblock3"
        }

        self.helpername = {
            'ec43': ""
        }

        self.pd_dir_table = {
            'ec43': ""
        }

        self.ethnum = {
            'ec43': "1"
        }

        self.wifinum = {
            'ec43': "1"
        }

        self.btnum = {
            'ec43': "0"
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

        self.cache_address = self.cacheaddr[self.board_id]
        self.uboot_address = self.ubaddr[self.board_id]
        self.uboot_size = self.ubsz[self.board_id]

        self.cfg_address = self.cfgaddr[self.board_id]
        self.cfg_size = self.cfgsz[self.board_id]

        self.eeprom_address = self.epromaddr[self.board_id]
        self.eeprom_size = self.epromsz[self.board_id]
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
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot|Autobooting in 2 seconds", "\033\033")

    def uboot_update(self):
        self.stop_uboot()
        time.sleep(1)
        self.set_ub_net()

        log_debug("Starting doing U-Boot update")
        cmd = "tftpboot {0} images/{1}".format(self.cache_address, self.bootloader[self.board_id])
        log_debug(cmd)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "usetprotect spm off")

        cmd = "sf probe;sf erase {0} {1};sf write {2} {0} {1}".format(self.uboot_address, self.uboot_size, self.cache_address)
        log_debug(cmd)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(200, self.bootloader_prompt, "re")

        self.stop_uboot()
        time.sleep(1)
        self.set_ub_net()

    def update_fcdfw(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "set do_urescue TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootubnt")
        self.pexp.expect_ubcmd(30, "Listening for TFTP transfer on", "")
        cmd = "atftp -p -l {0}/{1}.bin {2}".format(self.fwdir, self.board_id, self.dutip)
        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

    def check_info(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        cmd = 'cat /proc/bsp_helper/cpu_rev_id'
        self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd)

    def check_info2(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")

        cmd = "cat /etc/board.info | grep sysid"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "board.sysid=0x" + self.board_id)

        cmd = "cat /etc/board.info | grep hwaddr"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "board.hwaddr=" + self.mac.upper())

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
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        if UPDATE_UBOOT_EN is True:
            self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "\n\n")
            time.sleep(3)
            self.pexp.expect_ubcmd(5, self.linux_prompt, "\n", retry=10)
            self.set_lnx_net("br-lan")
            self.is_network_alive_in_linux(retry=5)

        if PROVISION_EN is True:    
            msg(20, "Sendtools to DUT and data provision ...")
            self.erase_eefiles()
            self.data_provision_64k(self.devnetmeta)
        
        if DOHELPER_EN is True:
            msg(40, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if REGISTER_EN is True:
            self.registration()
            msg(50, "Finish doing registration ...")
            self.check_devreg_data()
            msg(60, "Finish doing signed file and EEPROM checking ...")
            self.pexp.expect_ubcmd(10, self.linux_prompt, "reboot")
        
        if UPDATE_FCDFW_EN is True:
            msg(70, "update firmware...")
            self.uboot_update()
            self.update_fcdfw()

        if DATAVERIFY_EN is True:
            self.check_info2()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Complete FCD process ...")
        self.close_fcd()
        
def main():
    ua_mt7621_factory = UAMT7621Factory()
    ua_mt7621_factory.run()

if __name__ == "__main__":
    main()
