#!/usr/bin/python3

import re
import sys
import os
import time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    eb10: US-8-150W
    eb18: US-8-60W
    eb20: US-XG
    eb21: US-16-150W
    eb30: US-24
    eb31: US-24-250W
    eb60: US-48
    eb62: US-48-500W
'''


class MT7621LIB(ScriptBase):
    def __init__(self):
        super(MT7621LIB, self).__init__()
        self.init_vars()

    def init_vars(self):
        '''
            dcb0: Radar
            ec46: Gate
            ec3b: Elevator
            ec43: UA-Locker
        '''

        self.ubpmt = {
            'dcb0': "\(IPQ40xx\) # ",
            'ec46': "MT7621 #",
            'ec3b': "MT7621 #",
            'ec43': "=>"
        }

        # linux console prompt
        self.lnxpmt = {
            'dcb0': "pre#",
            'ec46': "root@LEDE:/#",
            'ec3b': "root@LEDE:/#",
            'ec43': "root@LEDE:/#"
        }

        self.lnxpmt_fcdfw = {
            'dcb0': "#",
            'ec46': "#",
            'ec3b': "#",
            'ec43': "#"
        }

        self.bootloader = {
            'dcb0': "{}-bootloader.bin".format(self.board_id),
            'ec46': "{}-t1.bin".format(self.board_id), 
            'ec3b': "{}-t1.bin".format(self.board_id),
            'ec43': "{}-fwuboot.bin".format(self.board_id)
        }

        self.cacheaddr = {
            'dcb0': "0x84000000",
            'ec46': "0x83000000",
            'ec3b': "0x83000000",
            'ec43': "0x80010000"
        }

        self.ubaddr = {
            'dcb0': "0x00000",
            'ec46': "0x00000",
            'ec3b': "0x00000",
            'ec43': "0x00000"
        }

        self.ubsz = {
            'dcb0': "0x10a0000",
            'ec46': "0x2000000", 
            'ec3b': "0x2000000",
            'ec43': "0x60000"
        }

        self.cfgaddr = {
            'dcb0': "0x1fc0000",
            'ec46': "0x1fc0000",
            'ec3b': "0x1fc0000",
            'ec43': ""
        }

        self.cfgsz = {
            'dcb0': "0x40000",
            'ec46': "0x40000",
            'ec3b': "0x40000",
            'ec43': ""
        }

        self.epromaddr = {
            'dcb0': "0x170000",
            'ec46': "0x170000",
            'ec3b': "0x170000",
            'ec43': ""
        }

        self.epromsz = {
            'dcb0': "0x10000",
            'ec46': "0x10000",
            'ec3b': "0x10000",
            'ec43': ""
        }

        self.product_class_table = {
            'dcb0': "basic",
            'ec46': "basic", 
            'ec3b': "basic",
            'ec43': "basic"
        }

        self.devregmtd = {
            'dcb0': "/dev/mtdblock3",
            'ec46': "/dev/mtdblock3",
            'ec3b': "/dev/mtdblock3",
            'ec43': "/dev/mtdblock3"
        }

        self.helpername = {
            'dcb0': "helper_IPQ40xx",
            'ec46': "",
            'ec3b': "",
            'ec43': ""
        }

        self.pd_dir_table = {
            'dcb0': "ufp_radar",
            'ec46': "ua-gate",
            'ec3b': "ua_elevator",
            'ec43': ""
        }

        self.ethnum = {
            'dcb0': "1",
            'ec46': "1",
            'ec3b': "1",
            'ec43': "1"
        }

        self.wifinum = {
            'dcb0': "1",
            'ec46': "1",
            'ec3b': "1",
            'ec43': "1"
        }

        self.btnum = {
            'dcb0': "1",
            'ec46': "1",
            'ec3b': "1",
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
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
       
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

        if self.board_id == "ec43":
            self.bootloader_prompt = self.ubpmt[self.board_id]

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

        if self.board_id == "ec43":
            cmd = "atftp -p -l {0}/{1} {2}".format(self.fwdir, "{}-fw.bin".format(self.board_id), self.dutip)
        else:
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

        cmd = "cat /etc/board.info | grep sysid"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "board.sysid=0x" + self.board_id)

        cmd = "cat /etc/board.info | grep hwaddr"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)
        self.pexp.expect_only(10, "board.hwaddr=" + self.mac.upper())
