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

WR_DUMMY_EN = True
DOHELPER_EN = True
REGISTER_EN = True
ADDKEYS_EN = True
WRSIGN_EN = True
DEFAULTCONFIG_EN = True
DATAVERIFY_EN = True


class AFIPQ40XXFactory(ScriptBase):
    def __init__(self):
        super(AFIPQ40XXFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        '''
        AirMax:
            dc99: GBE
            dc9a: GBE-LR
        UAP:
            dc98: UAP-UBB
            dc9c: UAP-UBB 831
        AirFiber:
            dc9b: AF60
            dc9e: AF60-LR
        '''
        # U-boot prompt
        self.ubpmt = {
            'dc99': ".*IPQ40xx.* # ",
            'dc9a': ".*IPQ40xx.* # ",
            'dc98': "\(IPQ40xx\) # ",
            'dc9c': "\(IPQ40xx\) # ",
            'dc9b': "\(IPQ40xx\) # ",
            'dc9e': "\(IPQ40xx\) # "
        }

        # linux console prompt
        self.lnxpmt = {
            'dc99': "GBE#",
            'dc9a': "GBE#",
            'dc98': "UBB#",
            'dc9c': "UBB#",
            'dc9b': "GP#",
            'dc9e': "GP#"
        }

        self.bootloader = {
            'dc99': "dc99-bootloader.bin",
            'dc9a': "dc99-bootloader.bin",
            'dc98': "dc98-bootloader.bin",
            'dc9c': "dc98-bootloader.bin",
            'dc9b': "dc9b-bootloader.bin",
            'dc9e': "dc9e-bootloader.bin"
        }

        self.ubaddr = {
            'dc99': "0xf0000",
            'dc9a': "0xf0000",
            'dc98': "0xf0000",
            'dc9c': "0xf0000",
            'dc9b': "0xf0000",
            'dc9e': "0xf0000"
        }

        self.ubsz = {
            'dc99': "0x80000",
            'dc9a': "0x80000",
            'dc98': "0x80000",
            'dc9c': "0x80000",
            'dc9b': "0x80000",
            'dc9e': "0x80000"
        }

        self.cfgaddr = {
            'dc99': "0x1fc0000",
            'dc9a': "0x1fc0000",
            'dc98': "0x1fc0000",
            'dc9c': "0x1fc0000",
            'dc9b': "0x1fc0000",
            'dc9e': "0x1fc0000"
        }

        self.cfgsz = {
            'dc99': "0x40000",
            'dc9a': "0x40000",
            'dc98': "0x40000",
            'dc9c': "0x40000",
            'dc9b': "0x40000",
            'dc9e': "0x40000"
        }

        self.epromaddr = {
            'dc99': "0x170000",
            'dc9a': "0x170000",
            'dc98': "0x170000",
            'dc9c': "0x170000",
            'dc9b': "0x170000",
            'dc9e': "0x170000"
        }

        self.epromsz = {
            'dc99': "0x10000",
            'dc9a': "0x10000",
            'dc98': "0x10000",
            'dc9c': "0x10000",
            'dc9b': "0x10000",
            'dc9e': "0x10000"
        }

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
        self.af_dir = os.path.join(self.fcd_toolsdir, "af_af60")

        # EX: /tftpboot/tools/af_af60/id_rsa
        self.id_rsa = os.path.join(self.af_dir, "id_rsa")
        self.bomrev = "13-{0}".format(self.bom_rev)

        # EX: helper in FCD host: /tftpboot/tools/af_af60/helper_IPQ40xx
        self.helperexe = "helper_IPQ40xx"
        self.helper_path = "af_af60"

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

    def run(self):
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

        self.uboot_update()
        msg(10, "Finishing update U-Boot")

        if (WR_DUMMY_EN is True) and (self.board_id == "dc9e"):
            self.set_uboot_network()
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "tftpboot 0x84000000 tools/af_af60/af60_dummy_cal.bin")
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

        msg(20, "Do ubntw - data provision")
        int_reg_code = 0
        int_reg_code = int(self.region, 16)
        cmd = "ubntw all {0} {1} {2} {3}".format(self.mac, self.board_id, self.bomrev, int_reg_code)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ubntw dump")

        msg(25, "Flash a temporary config")
        self.set_uboot_network()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "tftpboot 0x84000000 tools/af_af60/cfg_part.bin")
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
        self.pexp.expect_only(30, "Copying partition 'kernel' to flash memory:")
        log_debug("urescue: uboot updated")
        self.pexp.expect_only(30, "Copying partition 'rootfs' to flash memory:")
        log_debug("urescue: kernel updated")
        self.pexp.expect_only(180, "Firmware update complete.")
        msg(35, "urescue: complete")

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

        msg(100, "Formal firmware completed...")
        self.close_fcd()


def main():
    af_ipq840xx_factory = AFIPQ40XXFactory()
    af_ipq840xx_factory.run()

if __name__ == "__main__":
    main()
