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


class IPQ40XXFactory(ScriptBase):
    def __init__(self):
        super(IPQ40XXFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        '''
        AirMax:
            dc99: GBE
            dc9a: GBE-LR
            dca0: GBE-AP
        UAP:
            dc98: UAP-UBB
            dc9c: UAP-UBB 831
        AirFiber:
            dc9b: AF60
            dc9e: AF60-LR
        '''
        # U-boot prompt
        self.ubpmt = {
            '0000': ".*IPQ40xx.* # ",
            'dc99': ".*IPQ40xx.* # ",
            'dc9a': ".*IPQ40xx.* # ",
            'dc98': "\(IPQ40xx\) # ",
            'dc9c': "\(IPQ40xx\) # ",
            'dc9b': "\(IPQ40xx\) # ",
            'dc9e': "\(IPQ40xx\) # ",
            'dca0': "\(IPQ40xx\) # ",
            'dcb0': "\(IPQ40xx\) # "
        }

        # linux console prompt
        self.lnxpmt = {
            '0000': "GBE#",
            'dc99': "GBE#",
            'dc9a': "GBE#",
            'dc98': "UBB#",
            'dc9c': "UBB#",
            'dc9b': "GP#",
            'dc9e': "GP#",
            'dca0': "GBE#",
            'dcb0': "UBB#",
        }

        self.bootloader = {
            '0000': "dc99-bootloader.bin",
            'dc99': "dc99-bootloader.bin",
            'dc9a': "dc99-bootloader.bin",
            'dc98': "dc98-bootloader.bin",
            'dc9c': "dc98-bootloader.bin",
            'dc9b': "dc9b-bootloader.bin",
            'dc9e': "dc9e-bootloader.bin",
            'dca0': "dca0-bootloader.bin",
            'dcb0': "dca0-bootloader.bin"
        }

        self.ubaddr = {
            '0000': "0xf0000",
            'dc99': "0xf0000",
            'dc9a': "0xf0000",
            'dc98': "0xf0000",
            'dc9c': "0xf0000",
            'dc9b': "0xf0000",
            'dc9e': "0xf0000",
            'dca0': "0xf0000",
            'dcb0': "0xf0000"
        }

        self.ubsz = {
            '0000': "0x80000",
            'dc99': "0x80000",
            'dc9a': "0x80000",
            'dc98': "0x80000",
            'dc9c': "0x80000",
            'dc9b': "0x80000",
            'dc9e': "0x80000",
            'dca0': "0x80000",
            'dcb0': "0x80000"
        }

        self.cfgaddr = {
            '0000': "0x1fc0000",
            'dc99': "0x1fc0000",
            'dc9a': "0x1fc0000",
            'dc98': "0x1fc0000",
            'dc9c': "0x1fc0000",
            'dc9b': "0x1fc0000",
            'dc9e': "0x1fc0000",
            'dca0': "0x1fc0000",
            'dcb0': "0x1fc0000"
        }

        self.cfgsz = {
            '0000': "0x40000",
            'dc99': "0x40000",
            'dc9a': "0x40000",
            'dc98': "0x40000",
            'dc9c': "0x40000",
            'dc9b': "0x40000",
            'dc9e': "0x40000",
            'dca0': "0x40000",
            'dcb0': "0x40000"
        }

        self.epromaddr = {
            '0000': "0x170000",
            'dc99': "0x170000",
            'dc9a': "0x170000",
            'dc98': "0x170000",
            'dc9c': "0x170000",
            'dc9b': "0x170000",
            'dc9e': "0x170000",
            'dca0': "0x170000",
            'dcb0': "0x170000"
        }

        self.epromsz = {
            '0000': "0x10000",
            'dc99': "0x10000",
            'dc9a': "0x10000",
            'dc98': "0x10000",
            'dc9c': "0x10000",
            'dc9b': "0x10000",
            'dc9e': "0x10000",
            'dca0': "0x10000",
            'dcb0': "0x10000"
        }

        self.product_class_table = {
            '0000': "radio",
            'dc99': "radio",
            'dc9a': "radio",
            'dc98': "radio",
            'dc9c': "radio",
            'dc9b': "radio",
            'dc9e': "basic",
            'dca0': "basic",
            'dcb0': "basic"
        }

        self.pd_dir_table = {
            '0000': "am",
            'dc99': "am",
            'dc9a': "am",
            'dc98': "uap",
            'dc9c': "uap",
            'dc9b': "af_af60",
            'dc9e': "af_af60",
            'dca0': "am",
            'dcb0': "uap",
        }

        self.product_class = self.product_class_table[self.board_id]

        self.linux_prompt = self.lnxpmt[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]

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
        self.helperexe = "helper_IPQ40xx"
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
        cmd = "tftpboot 84000000 images/{}".format(self.bootloader[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "usetprotect spm off")

        cmd = "sf probe; sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.uboot_address, self.uboot_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")
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

    def airos_run(self):
        WR_DUMMY_EN = False
        DOHELPER_EN = True
        REGISTER_EN = False
        ADDKEYS_EN = False
        WRSIGN_EN = False
        DEFAULTCONFIG_EN = False
        DATAVERIFY_EN = False

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

        #------------------------------
        #self.uboot_update()
        #------------------------------


        '''
        msg(10, "Finishing update U-Boot")

        if (WR_DUMMY_EN is True) and (self.board_id == "dc9e" or self.board_id == "dca0" ):
            self.set_uboot_network()
            cmd = "tftpboot 0x84000000 tools/{0}/{0}_dummy_cal.bin".format(self.pd_dir)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            self.pexp.expect_ubcmd(10, "Bytes transferred", "usetprotect spm off")
            cmd = "sf probe; sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.eeprom_address, self.eeprom_size)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            time.sleep(2)

            cmd = "sf probe; sf read 0x84000000 {0} {1}".format(self.eeprom_address, self.eeprom_size)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            output = self.pexp.expect_get_output("md.b 0x84005000 2", self.ubpmt[self.board_id])
            if ("84005000: 20 2f" in output):
                log_debug("Board is callibrated")
            else:
                error_critical("Board is not callibrated")

            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")
            self.stop_uboot()
        '''


        '''
        msg(20, "Do ubntw - data provision")
        int_reg_code = 0
        int_reg_code = int(self.region, 16)
        cmd = "ubntw all {0} {1} {2} {3}".format(self.mac, self.board_id, self.bomrev, int_reg_code)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ubntw dump")
        '''




        '''
        msg(25, "Flash a temporary config")
        self.set_uboot_network()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
        cmd = "tftpboot 0x84000000 tools/{0}/cfg_part.bin".format(self.pd_dir)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(10, "Bytes transferred", "usetprotect spm off")
        cmd = "sf probe; sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.cfg_address, self.cfg_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        msg(30, "Doing urescue")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue -e -f")
        cmd = "atftp --option \"mode octet\" -p -l {0}/{1} {2}".format(self.fwdir, self.fwimg, self.dutip)
        log_debug("Run cmd on host:" + cmd)
        self.fcd.common.xcmd(cmd=cmd)
        self.pexp.expect_only(30, "Firmware Version:")
        log_debug("urescue: FW loaded")
        self.pexp.expect_only(30, "Image Signature Verfied, Success.")
        log_debug("urescue: FW verified")
        self.pexp.expect_only(300, "Copying partition 'kernel' to flash memory:")
        log_debug("urescue: uboot updated")
        self.pexp.expect_only(300, "Copying partition 'rootfs' to flash memory:")
        log_debug("urescue: kernel updated")
        self.pexp.expect_only(180, "Firmware update complete.")
        msg(35, "urescue: complete")
        '''

        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "fcd")
        self.pexp.expect_ubcmd(10, "Password:", "fcduser")
        cmd = "ifconfig eth0 {0} up".format(self.dutip)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.chk_lnxcmd_valid()
        self.lnx_netcheck()
        

        if DOHELPER_EN is True:
            self.erase_eefiles()
            msg(40, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.registration()
            msg(50, "Finish do registration ...")

        '''
        cmd = "reboot -f"
        self.pexp.expect_lnxcmd(180, self.linux_prompt, cmd)
        self.stop_uboot()
        time.sleep(3)
        self.set_uboot_network()

        if ADDKEYS_EN is True:
            msg(60, "Add RSA Key")

            cmd = "rm {0}; dropbearkey -t rsa -f {0}".format(self.dropbear_key)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                error_critical("Generate RSA key failed!!")
            else:
                log_debug("Generate RSA key successfully")

            cmd = "{0} -f {1} -K {2}".format(self.eetool, self.eesign_path, self.dropbear_key)
            log_debug("cmd: " + cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                error_critical("Append RSA key failed!!")
            else:
                log_debug("Addend RSA key successfully")

        if WRSIGN_EN is True:
            msg(70, "Write signed EEPROM")
            cmd = "tftpboot 84000000 {0}".format(self.eesign)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_ubcmd(30, "Bytes transferred", "usetprotect spm off")
            log_debug("File sent. Writing eeprom")
            cmd = "sf probe; sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.eeprom_address, self.eeprom_size)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            time.sleep(5)

        if DEFAULTCONFIG_EN is True:
            log_debug("Erase tempoarary config")
            cmd = "sf probe; sf erase {0} {1}".format(self.cfg_address, self.cfg_size)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            time.sleep(5)

            msg(80, "Write default setting")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv NORESET")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip 192.168.1.254")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr 192.168.1.20")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs root=/dev/mtdblock5 init=/init")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
            time.sleep(3)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ubntw dump")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

        if DATAVERIFY_EN is True:
            self.check_info()
            msg(90, "Succeeding in checking the devreg information ...")

        '''
        msg(100, "Formal firmware completed...")
        self.close_fcd()


class IPQ40XXMFG(ScriptBase):
    def __init__(self):
        super(IPQ40XXMFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        '''
        AirMax: AME
            dc99: GBE
            dc9a: GBE-LR
            dca0: GBE-AP
        UAP:
            dc98: UAP-UBB
            dc9c: UAP-UBB 831
        AirFiber:
            dc9b: AF60
            dc9e: AF60-LR
        '''
        # U-boot prompt
        self.ubpmt = {
            '0000': "\(IPQ40xx\) # ",
            'dc99': "\(IPQ40xx\) # ",
            'dc9a': "\(IPQ40xx\) # ",
            'dc98': "\(IPQ40xx\) # ",
            'dc9c': "\(IPQ40xx\) # ",
            'dc9b': "\(IPQ40xx\) # ",
            'dc9e': "\(IPQ40xx\) # ",
            'dca0': "\(IPQ40xx\) # "
        }

        # linux console prompt
        self.lnxpmt = {
            '0000': "root@OpenWrt",
            'dc99': "root@OpenWrt",
            'dc9a': "root@OpenWrt",
            'dc98': "root@OpenWrt",
            'dc9c': "root@OpenWrt",
            'dc9b': "root@OpenWrt",
            'dc9e': "root@OpenWrt",
            'dca0': "root@OpenWrt"
        }

        self.artimg = {
            '0000': "dc99-mfg.bin",
            'dc99': "dc99-mfg.bin",
            'dc9a': "dc9a-mfg.bin",
            'dc98': "dc98-mfg.bin",
            'dc9c': "dc9c-mfg.bin",
            'dc9b': "dc9b-mfg.bin",
            'dc9e': "dc9b-mfg.bin",
            'dca0': "dc9b-mfg.bin"
        }

        self.knladdr = {
            '0000': "0x0",
            'dc99': "0x0",
            'dc9a': "0x0",
            'dc98': "0x0",
            'dc9c': "0x0",
            'dc9b': "0x0",
            'dc9e': "0x0",
            'dca0': "0x0"
        }

        self.knlsz = {
            '0000': "0x170000",
            'dc99': "0x170000",
            'dc9a': "0x170000",
            'dc98': "0x170000",
            'dc9c': "0x170000",
            'dc9b': "0x170000",
            'dc9e': "0x170000",
            'dca0': "0x170000"
        }

        self.rfaddr = {
            '0000': "0x180000",
            'dc99': "0x180000",
            'dc9a': "0x180000",
            'dc98': "0x180000",
            'dc9c': "0x180000",
            'dc9b': "0x180000",
            'dc9e': "0x180000",
            'dca0': "0x180000"
        }

        self.rfsz = {
            '0000': "0x1a00000",
            'dc99': "0x1a00000",
            'dc9a': "0x1a00000",
            'dc98': "0x1d00000",
            'dc9c': "0x1d00000",
            'dc9b': "0x1d00000",
            'dc9e': "0x1d00000",
            'dca0': "0x1a00000"
        }

        self.linux_prompt = self.lnxpmt[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]

        self.kernel_address =  self.knladdr[self.board_id]
        self.kernel_size =  self.knlsz[self.board_id]
        self.rootfs_address = self.rfaddr[self.board_id]
        self.rootfs_size = self.rfsz[self.board_id]

    def stop_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "")

    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)

    def run(self):
        """
        Main procedure of factory
        """
        msg(1, "Start Procedure")
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Stop U-boot")
        self.stop_uboot()
        time.sleep(3)
        self.set_uboot_network()

        msg(10, "Get ART Image")
        cmd = "tftpboot 84000000 images/{}".format(self.artimg[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "usetprotect spm off")

        msg(30, "Starting erasing Kernel")
        cmd = "sf probe; sf erase {0} {1}".format(self.kernel_address, self.kernel_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        msg(40, "Starting writing Kernel")
        cmd = "sf probe; sf write 0x84000000 {0} {1}".format(self.kernel_address, self.kernel_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(5)

        if self.erasecal == "True":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf erase 0x170000 0x10000")
            time.sleep(5)

        msg(50, "Clean RootFS")
        cmd = "sf probe; sf erase {0} {1}".format(self.rootfs_address, self.rootfs_size)
        self.pexp.expect_ubcmd(300, self.bootloader_prompt, cmd)
        time.sleep(5)

        msg(60, "Write RootFS")
        cmd = "sf prob; sf write 0x84180000 {0} {1}".format(self.rootfs_address, self.rootfs_size)
        self.pexp.expect_ubcmd(180, self.bootloader_prompt, cmd)
        time.sleep(5)

        self.pexp.expect_ubcmd(600, self.bootloader_prompt, "printenv")

        msg(70, "Cleanup CountryCode")
        cmd = "sf read 0x84000000 0x170000 0x10000 && mw 0x8400100c 00200000 && mw 0x8400500c 00200000 && sf write 0x84000000 0x170000 0x10000"
        self.pexp.expect_action(180, self.ubpmt[self.board_id], cmd)
        time.sleep(5)

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")
        time.sleep(60)

        msg(90, "Reboot")
        self.pexp.expect_only(120, "Linux version 4.4.60")

        msg(100, "Back to ART has completed")
        self.close_fcd()