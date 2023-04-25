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
            dcb0: Radar
            ec46: Gate
            ec3b: Elevator
            ec42: Hub
        '''

        self.ubpmt = {
            'ec42': "MT7621 #"
        }

        # linux console prompt
        self.lnxpmt = {
            'ec42': "root@LEDE:/#"
        }

        self.lnxpmt_fcdfw = {
            'ec42': "#"
        }

        self.bootloader = {
            'ec42': "ec42-t1.bin"
        }

        self.cacheaddr = {
            'ec42': "0x83000000"
        }

        self.ubaddr = {
            'ec42': "0x00000"
        }

        self.ubsz = {
            'ec42': "0x2000000"
        }

        self.cfgaddr = {
            'ec42': "0x1fc0000"
        }

        self.cfgsz = {
            'ec42': "0x40000"
        }

        self.epromaddr = {
            'ec42': "0x170000"
        }

        self.epromsz = {
            'ec42': "0x10000"
        }

        self.product_class_table = {
            'ec42': "basic"
        }

        self.devregmtd = {
            'ec42': "/dev/mtdblock3"
        }

        self.helpername = {
            'ec42': ""
        }

        self.pd_dir_table = {
            'ec42': "ua_hub_4p"
        }

        self.ethnum = {
            'ec42': "1"
        }

        self.wifinum = {
            'ec42': "2"
        }

        self.btnum = {
            'ec42': "0"
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

    def stop_uboot(self, timeout=30):
        self.pexp.expect_ubcmd(timeout, "Hit any key to stop autoboot", "\033")
       
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
        log_debug(cmd)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "usetprotect spm off")

        cmd = "sf probe;sf erase {0} {1};sf write {2} {0} {1}".format(self.uboot_address, self.uboot_size, self.cache_address)
        log_debug(cmd)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(1)

        self.pexp.expect_ubcmd(200, self.bootloader_prompt, "re")
        self.stop_uboot()
        
    def boot_to_T1(self):
        self.set_uboot_network()

        cmd = "sf probe; sf read 0x83000000 0x1a0000 0xE00000; bootm 0x83000000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "\n\n")
        time.sleep(3)
        self.pexp.expect_ubcmd(5, self.linux_prompt, "\n", retry=10)
        self.is_network_alive_in_linux()

    def update_fcdfw(self):
        self.stop_uboot()
        time.sleep(1)
        self.set_uboot_network()

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "set do_urescue TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootubnt")
        self.pexp.expect_ubcmd(30, "Listening for TFTP transfer on", "")

        cmd = "atftp -p -l {0}/{1} {2}".format(self.fwdir, "{}-fw.bin".format(self.board_id), self.dutip)
        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

    def lnx_netcheck(self, netifen=False):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()

    def check_info(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        cmd = 'cat /proc/bsp_helper/cpu_rev_id'
        self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd)

    def check_info2(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")

        if self.board_id == 'ec42':
            self.pexp.expect_ubcmd(30, "kmodloader: done loading kernel modules", "")
            time.sleep(3)

        cmd = "cat /etc/board.info | grep sysid"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "board.sysid=0x" + self.board_id)

        cmd = "cat /etc/board.info | grep hwaddr"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "board.hwaddr=" + self.mac.upper())

    def turn_on_console(self):
        self.stop_uboot(240)
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs console=ttyS0,115200")
        time.sleep(3)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv", "OK")
        time.sleep(3)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def turn_on_ssh(self):
        cmd = "echo -n yes > /etc/dat1/persistent/.ctlrsh ; cfgmtd -t 1 -w -o dat1 -p /etc/dat1/"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        time.sleep(5)
        cmd = "mkdir -p /tmp/dat1/persistent ; cfgmtd -t 1 -r -o dat1 -p /tmp/dat1/"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        time.sleep(5)
        cmd = "cat /tmp/dat1/persistent/.ctlrsh"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "yes")

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
            msg(5, "Update U-Boot ...")
            self.uboot_update()
            msg(10, "Booting the T1 image ...")
            self.boot_to_T1()

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
            self.update_fcdfw()
            msg(75, "turn on console...")
            self.turn_on_console()

        if DATAVERIFY_EN is True:
            self.check_info2()
            msg(80, "Succeeding in checking the devreg information ...")

            msg(90, "turn on ssh...")
            self.turn_on_ssh()

        msg(100, "Complete FCD process ...")
        self.close_fcd()
        
def main():
    ua_mt7621_factory = UAMT7621Factory()
    ua_mt7621_factory.run()

if __name__ == "__main__":
    main()
