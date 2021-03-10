#!/usr/bin/python3

from binascii import unhexlify
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil


class UAUBOOTFactory(ScriptBase):
    def __init__(self):
        super(UAUBOOTFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        '''
        UniFi-Protect:
            dcb0: Radar
            ec46: Gate
        '''
        # U-boot prompt
        self.ubpmt = {
            'dcb0': "\(IPQ40xx\) # ",
            'ec46': "MT7621 #"
        }

        # linux console prompt
        self.lnxpmt = {
            'dcb0': "pre#",
            'ec46': "root@LEDE:/#"
        }

        self.lnxpmt_fcdfw = {
            'dcb0': "#",
            'ec46': "root@LEDE:/#"
        }

        self.bootloader = {
            'dcb0': "dcb0-bootloader.bin",
            'ec46': "ec46-t1.bin"
        }

        self.cacheaddr = {
            'dcb0': "0x84000000",
            'ec46': "0x83000000"
        }

        self.ubaddr = {
            'dcb0': "0x00000",
            'ec46': "0x00000"
        }

        self.ubsz = {
            'dcb0': "0x10a0000",
            'ec46': "0x10a0000"
        }

        self.cfgaddr = {
            'dcb0': "0x1fc0000",
            'ec46': "0x1fc0000"
        }

        self.cfgsz = {
            'dcb0': "0x40000",
            'ec46': "0x40000"
        }

        self.epromaddr = {
            'dcb0': "0x170000",
            'ec46': "0x170000"
        }

        self.epromsz = {
            'dcb0': "0x10000",
            'ec46': "0x10000"
        }

        self.product_class_table = {
            'dcb0': "basic",
            'ec46': "basic"
        }

        self.devregmtd = {
            'dcb0': "/dev/mtdblock3",
            'ec46': "/dev/mtdblock3"
        }

        self.helpername = {
            'dcb0': "helper_IPQ40xx",
            'ec46': ""
        }

        self.pd_dir_table = {
            'dcb0': "ufp_radar",
            'ec46': "ua-gate",
        }

        self.ethnum = {
            'dcb0': "1",
            'ec46': "1"
        }

        self.wifinum = {
            'dcb0': "1",
            'ec46': "1"
        }

        self.btnum = {
            'dcb0': "1",
            'ec46': "1"
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
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "")

    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)

    def uboot_update(self):
        self.stop_uboot()
        time.sleep(1)
        self.set_uboot_network()

        log_debug("Starting doing U-Boot update")
        cmd = "tftpboot {0} images/{1}".format(self.cache_address, self.bootloader[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "usetprotect spm off")

        cmd = "sf probe;sf erase {0} {1};sf write {2} {0} {1}".format(self.uboot_address, self.uboot_size, self.cache_address)
        log_debug(cmd)
        
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(200, self.bootloader_prompt, "re")
        self.stop_uboot()
        
        

    def lnx_netcheck(self, netifen=False):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()


    def check_info(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")

        cmd = "cat /proc/ubnthal/board.info"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)


    def check_info2(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")

        cmd = "cat /proc/ubnthal/system.info"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())


    def run(self):
        DOHELPER_EN = True
        REGISTER_EN = True
        DATAVERIFY_EN = True
        #-----------------------------------------------------------------------------------

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
        #-----------------------------------------------------------------------------------

        msg(5, "update U-Boot")
        self.uboot_update()
        #-----------------------------------------------------------------------------------

        msg(20, "Login new U-Boot")
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")
        cmd = "ifconfig eth0 {0} up".format(self.dutip)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.chk_lnxcmd_valid()
        self.lnx_netcheck()
        cmd = 'echo "5edfacbf" > /proc/ubnthal/.uf'
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        #-----------------------------------------------------------------------------------

        if DOHELPER_EN is True:
            self.erase_eefiles()
            msg(40, "Do helper to get the output file to devreg server ...")
            self.data_provision_64k(self.devnetmeta)
            self.prepare_server_need_files()
        #-----------------------------------------------------------------------------------

        if REGISTER_EN is True:
            self.registration()
            msg(50, "Finish do registration ...")
            self.check_devreg_data()
            msg(55, "Finish doing signed file and EEPROM checking ...")
        #-----------------------------------------------------------------------------------

        cmd = "reboot -f"
        self.pexp.expect_lnxcmd(180, self.linux_prompt, cmd)
        if DATAVERIFY_EN is True:
            self.check_info2()
            msg(90, "Succeeding in checking the devreg information ...")
        #-----------------------------------------------------------------------------------
        
        msg(100, "Formal firmware completed...")
        self.close_fcd()
        #-----------------------------------------------------------------------------------



def main():
    print('hello')
    ua_uboot_factory = UAUBOOTFactory()
    ua_uboot_factory.run()

if __name__ == "__main__":
    main()