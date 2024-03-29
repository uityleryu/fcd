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

class IPQ80XXFactory(ScriptBase):
    def __init__(self):
        super(IPQ80XXFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        '''
        AirFiber:
            ac11: AF60-XR
            ac14: Wave-AP
            ac15: Wave-Mesh
            ac16: Wave-AP-Micro
            ac17: Wave-AP-HD
            ac1a: Wave-AP-01206(2.5G)
            ac18: Wave-Pro-01149
            ac1b: Wave-AP-HD
            ac19: Wave-Pro-01205
        '''
        # U-boot prompt
        self.ubpmt = {
            '0000': "IPQ807x# ",
            'ac11': "IPQ807x# ",
            'ac14': "IPQ807x# ",
            'ac15': "IPQ807x# ",
            'ac16': "IPQ807x# ",
            'ac17': "IPQ807x# ",
            'ac1a': "IPQ807x# ",
            'ac18': "IPQ807x# ",
            'ac1b': "IPQ807x# ",
            'ac19': "IPQ807x# "
        }

        # linux console prompt
        self.lnxpmt = {
            '0000': "GBE#",
            'ac11': "#",
            'ac14': "#",
            'ac15': "#",
            'ac16': "#",
            'ac17': "#",
            'ac1a': "#",
            'ac18': "#",
            'ac1b': "#",
            'ac19': "#"
        }

        self.bootloader = {
            '0000': "dc99-bootloader.bin",
            'ac11': "ac11-bootloader.bin",
            'ac14': "ac14-bootloader.bin",
            'ac15': "ac15-bootloader.bin",
            'ac16': "ac16-bootloader.bin",
            'ac17': "ac17-bootloader.bin",
            'ac1a': "ac1a-bootloader.bin",
            'ac18': "ac18-bootloader.bin",
            'ac1b': "ac1b-bootloader.bin",
            'ac19': "ac19-bootloader.bin"
        }

        self.ubaddr = {
            '0000': "0xd80000",
            'ac11': "0xd80000",
            'ac14': "0xd80000",
            'ac15': "0xd80000",
            'ac16': "0xd80000",
            'ac17': "0xd80000",
            'ac1a': "0xd80000",
            'ac18': "0xd80000",
            'ac1b': "0xd80000",
            'ac19': "0xd80000"
        }

        self.ubsz = {
            '0000': "0x100000",
            'ac11': "0x100000",
            'ac14': "0x100000",
            'ac15': "0x100000",
            'ac16': "0x100000",
            'ac17': "0x100000",
            'ac1a': "0x100000",
            'ac18': "0x100000",
            'ac1b': "0x100000",
            'ac19': "0x100000"
        }

        self.cfgaddr = {
            '0000': "0xf000000",
            'ac11': "0xf000000",
            'ac14': "0xf000000",
            'ac15': "0xf000000",
            'ac16': "0xf000000",
            'ac17': "0xf000000",
            'ac1a': "0xf000000",
            'ac18': "0xf000000",
            'ac1b': "0xf000000",
            'ac19': "0xf000000"
        }

        self.cfgsz = {
            '0000': "0x1000000",
            'ac11': "0x1000000",
            'ac14': "0x1000000",
            'ac15': "0x1000000",
            'ac16': "0x1000000",
            'ac17': "0x1000000",
            'ac1a': "0x1000000",
            'ac18': "0x1000000",
            'ac1b': "0x1000000",
            'ac19': "0x1000000"
        }

        self.epromaddr = {
            '0000': "0x2a0000",
            'ac11': "0x2a0000",
            'ac14': "0x2a0000",
            'ac15': "0x2a0000",
            'ac16': "0x2a0000",
            'ac17': "0x2a0000",
            'ac1a': "0x2a0000",
            'ac18': "0x2a0000",
            'ac1b': "0x2a0000",
            'ac19': "0x2a0000"
        }

        self.epromsz = {
            '0000': "0x40000",
            'ac11': "0x40000",
            'ac14': "0x40000",
            'ac15': "0x40000",
            'ac16': "0x40000",
            'ac17': "0x40000",
            'ac1a': "0x40000",
            'ac18': "0x40000",
            'ac1b': "0x40000",
            'ac19': "0x40000"
        }

        self.product_class_table = {
            '0000': "radio",
            'ac11': "basic",
            'ac14': "basic",
            'ac15': "basic",
            'ac16': "basic",
            'ac17': "basic",
            'ac1a': "basic",
            'ac18': "basic",
            'ac1b': "basic",
            'ac19': "basic"
        }

        self.pd_dir_table = {
            '0000': "am",
            'ac11': "af_af60",
            'ac14': "af_af60",
            'ac15': "af_af60",
            'ac16': "af_af60",
            'ac17': "af_af60",
            'ac1a': "af_af60",
            'ac18': "af_af60",
            'ac1b': "af_af60",
            'ac19': "af_af60"
        }

        self.ethspeed_table = {
            '0000': "1000Mb/s",
            'ac11': "1000Mb/s",
            'ac14': "1000Mb/s",
            'ac15': "2500Mb/s",
            'ac16': "2500Mb/s",
            'ac17': "1000Mb/s",
            'ac1a': "2500Mb/s",
            'ac18': "2500Mb/s",
            'ac1b': "2500Mb/s",
            'ac19': "2500Mb/s"
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

        self.fwimg = self.board_id + ".bin"

        # EX: /tftpboot/tools/af_af60
        self.pd_dir = self.pd_dir_table[self.board_id]
        self.tools_full_dir = os.path.join(self.fcd_toolsdir, self.pd_dir)

        # EX: /tftpboot/tools/af_af60/id_rsa
        self.id_rsa = os.path.join(self.tools_full_dir, "id_rsa")
        self.bomrev = "13-{0}".format(self.bom_rev)

        # EX: helper in FCD host: /tftpboot/tools/af_af60/helper_IPQ807x
        self.helperexe = "helper_IPQ807x"
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

        retry = 10
        for i in range(0, retry):
            time.sleep(3)
            try:
                self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
                self.pexp.expect_only(15, "is alive")
            except Exception as e:
                print("ping fail..." + str(i))
                continue
            break
        else:
            print("ping retry fail")
            raise NameError('ping retry fail')

    def uboot_update(self):
        self.stop_uboot()
        time.sleep(1)
        self.set_uboot_network()

        log_debug("Starting doing U-Boot update")
        cmd = "tftpboot 44000000 images/{}".format(self.bootloader[self.board_id])
        self.pexp.expect_ubcmd(120, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "sf probe")

        cmd = "nand erase {0} {1}; nand write 44000000 {0} {1}".format(self.uboot_address, self.uboot_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")
        self.stop_uboot()

    def check_calibration(self):
        cmd = "nand read.raw 0x44000000 0xf80000 0x100"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        cmd = "md 0x44001080 0x2"
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)

        exp_list = ["44001080: 04040001 00000000"]
        index = self.pexp.expect_get_index(5, exp_list)
        if index == self.pexp.TIMEOUT:
            error_critical("Unable to check the calibrated data ... ")
        elif not index == 0:
            error_critical("No calibrated data, Board is not callibrated")

    def lnx_netcheck(self, netifen=False):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()

    def ubntw(self):
        int_reg_code = 0
        int_reg_code = int(self.region, 16)
        cmd = "ubntw all {0} {1} {2} {3}".format(self.mac, self.board_id, self.bomrev, int_reg_code)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")
        self.stop_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ubntw dump")

    def temp_cfg(self):
        self.set_uboot_network()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
        cmd = "tftpboot 44000000 tools/{0}/cfg_part.bin".format(self.pd_dir)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(10, "Bytes transferred", "usetprotect spm off")
        cmd = "nand erase {0} {1}; nand write 44000000 {0} {1}".format(self.cfg_address, self.cfg_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

    def urescue(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "uclearcfg;\r")
        self.pexp.expect_only(10, self.bootloader_prompt)

        retry_cnt = 3
        while retry_cnt > 0:
            if retry_cnt == 1:
                error_critical("urescue failed")

            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue -e -f")
            self.pexp.expect_only(10, "Loading")
            #time.sleep(1)
            cmd = "atftp --option \"mode octet\" -p -l {0}/{1} {2}".format(self.fwdir, self.fwimg, self.dutip)
            log_debug("Run cmd on host:" + cmd)
            self.fcd.common.xcmd(cmd=cmd)

            exp_list = ["Firmware Version:"]
            index = self.pexp.expect_get_index(timeout=10, exptxt=exp_list)
            if index == -1:
                log_error("TFTP wait timeout, retry")
                retry_cnt -= 1
                time.sleep(3)
                self.pexp.expect_action(5, "", "\003")
                self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
                self.pexp.expect_only(10, "is alive")
            else:
                log_debug("urescue: FW loaded")
                break

        #self.pexp.expect_only(30, "Firmware Version:")
        #log_debug("urescue: FW loaded")
        self.pexp.expect_only(30, "Image Signature Verfied, Success.")
        log_debug("urescue: FW verified")
        self.pexp.expect_only(300, "Flashing system0 partition")
        log_debug("Flashing system0 partition")
        self.pexp.expect_only(300, "Flashing system1 partition")
        log_debug("Flashing system1 partition")
        self.pexp.expect_only(180, "Firmware update complete.")
        msg(35, "urescue: complete")

        # Detect if unexpect error occured
        exp_list = [
            "Increase PRS flash failure count",
            "Kernel panic",
            "PREINIT: preinit script failed"
        ]
        index = self.pexp.expect_get_index(timeout=120, exptxt=exp_list)
        if index != -1:
            error_critical("Product FW Kernel Error")

        if self.board_id == "ac15":
            self.pexp.expect_ubcmd(120, "Please press Enter to activate this console.", "")
        else:
            self.pexp.expect_ubcmd(120, "running real init", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")
        cmd = "ifconfig br0 {0} up".format(self.dutip)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        #if self.board_id == "ac19":
        #    cmd = "brctl addif br0 eth0"
        #    self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.chk_lnxcmd_valid()
        self.lnx_netcheck()

    def chk_ethernetspeed(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ethtool eth0 | grep Speed")
        self.pexp.expect_only(10, self.ethspeed_table[self.board_id])

    def chk_usbspeed(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "prs_serial status| grep link")
        self.pexp.expect_only(10, "u0")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "prs_serial status| grep speed")
        self.pexp.expect_only(10, "3.0")

    def add_key(self):
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

    def write_sign(self):
        cmd = "tftpboot 44000000 {0}".format(self.eesign)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "sf probe")
        log_debug("File sent. Writing eeprom")
        cmd = "sf erase {0} {1}; sf write 44000000 {0} {1};\r".format(self.eeprom_address, self.eeprom_size)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(5)

    def default_cfg(self):
        if self.board_id == "ac14":
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "uclearcfg;\r")
            self.pexp.expect_only(10, self.bootloader_prompt)
        else:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv NORESET")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip 192.168.1.254")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr 192.168.1.20")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs root=/dev/mtdblock5 init=/init")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        time.sleep(3)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ubntw dump")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def check_info(self):
        if self.board_id == "ac15":
            self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        else:
            self.pexp.expect_ubcmd(240, "running real init", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")

        self.pexp.expect_lnxcmd(5, self.linux_prompt, "cat /usr/lib/version")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "jq .identification /etc/board.json")

    def airos_run(self):
        UPDATE_BOOTIMG_EN = True
        WR_DUMMY_EN = False
        UBNTW_EN = True
        FLASH_TEMP_CFG = False
        if self.board_id == "ac15":
            CHK_CAL_EN = False
        elif self.board_id == "ac11":
            CHK_CAL_EN = False
        else:
            CHK_CAL_EN = True
        URESCUE_EN = True
        if self.board_id == "ac19":
            ETHERSPEED_EN = False
        else:
            ETHERSPEED_EN = True
        USBSPEED_EN = True
        DOHELPER_EN = True
        REGISTER_EN = True
        ADDKEYS_EN = False
        WRSIGN_EN = True
        DEFAULTCONFIG_EN = True
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

        if UPDATE_BOOTIMG_EN:
            self.uboot_update()
            msg(10, "Finishing update U-Boot")

        if CHK_CAL_EN:
            self.check_calibration()
            msg(15, "Got Calibration data")

        if (WR_DUMMY_EN is True) and (self.board_id == "dc9e" or self.board_id == "dca0" ):
            self.set_uboot_network()
            cmd = "tftpboot 44000000 tools/{0}/{0}_dummy_cal.bin".format(self.pd_dir)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            self.pexp.expect_ubcmd(10, "Bytes transferred", "usetprotect spm off")
            cmd = "nand erase {0} {1}; nand write 44000000 {0} {1}".format(self.eeprom_address, self.eeprom_size)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            time.sleep(2)

            cmd = "nand read 0x84000000 {0} {1}".format(self.eeprom_address, self.eeprom_size)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            output = self.pexp.expect_get_output("md.b 0x84005000 2", self.ubpmt[self.board_id])
            if ("84005000: 20 2f" in output):
                log_debug("Board is callibrated")
            else:
                error_critical("Board is not callibrated")

            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")
            self.stop_uboot()

        if UBNTW_EN:
            msg(20, "Do ubntw - data provision")
            self.ubntw()

        if FLASH_TEMP_CFG:
            msg(25, "Flash a temporary config")
            self.temp_cfg()

        self.set_uboot_network()
        time.sleep(3)

        if URESCUE_EN:
            msg(30, "Do urescue")
            self.urescue()

        if ETHERSPEED_EN:
            msg(35, "Check Ethernet Speed")
            self.chk_ethernetspeed()

        if USBSPEED_EN:
            msg(37, "Check USB Speed")
            self.chk_usbspeed()

        if DOHELPER_EN is True:
            self.erase_eefiles()
            msg(40, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_EN:
            msg(50, "Do registration ...")
            self.registration()
        
        cmd = "reboot -f"
        self.pexp.expect_lnxcmd(180, self.linux_prompt, cmd)
        self.stop_uboot()
        time.sleep(3)
        self.set_uboot_network()

        if ADDKEYS_EN:
            msg(60, "Add RSA Key")
            self.add_key()

        if WRSIGN_EN is True:
            msg(70, "Write signed EEPROM")
            self.write_sign()

        if DEFAULTCONFIG_EN is True:
            msg(80, "Write default setting")
            self.default_cfg()
            
        if DATAVERIFY_EN is True:
            self.check_info()
            msg(90, "Succeeding in checking the devreg information ...")

        msg(100, "Formal firmware completed...")
        self.close_fcd()


class IPQ80XXMFG(ScriptBase):
    def __init__(self):
        super(IPQ80XXMFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        '''
        AirFiber:
            ac11: AF60-XR
            ac14: Wave-AP
            ac15: Wave-Mesh
            ac16: Wave-AP-Micro
            ac17: Wave-AP-HD
            ac1a: Wave-AP-01206(2.5G)
            ac18: Wave-Pro-01149
            ac1b: Wave-AP-HD
            ac19: Wave-Pro-01205
        '''
        # U-boot prompt
        self.ubpmt = {
            '0000': "IPQ807x# ",
            'ac11': "IPQ807x# ",
            'ac14': "IPQ807x# ",
            'ac15': "IPQ807x# ",
            'ac16': "IPQ807x# ",
            'ac17': "IPQ807x# ",
            'ac1a': "IPQ807x# ",
            'ac18': "IPQ807x# ",
            'ac1b': "IPQ807x# ",
            'ac19': "IPQ807x# "
        }

        # linux console prompt
        self.lnxpmt = {
            '0000': "root@OpenWrt",
            'ac11': "root@OpenWrt",
            'ac14': "root@OpenWrt",
            'ac15': "root@OpenWrt",
            'ac16': "root@OpenWrt",
            'ac17': "root@OpenWrt",
            'ac1a': "root@OpenWrt",
            'ac18': "root@OpenWrt",
            'ac1b': "root@OpenWrt",
            'ac19': "root@OpenWrt"
        }

        self.artimg = {
            '0000': "dc99-mfg.bin",
            'ac11': "ac11-mfg.bin",
            'ac14': "ac14-mfg.bin",
            'ac15': "ac15-mfg.bin",
            'ac16': "ac16-mfg.bin",
            'ac17': "ac17-mfg.bin",
            'ac1a': "ac1a-mfg.bin",
            'ac18': "ac1a-mfg.bin",
            'ac1b': "ac1a-mfg.bin",
            'ac19': "ac19-mfg.bin"
        }

        self.addr = {
            '0000': "0x0",
            'ac11': "0x0",
            'ac14': "0x0",
            'ac15': "0x0",
            'ac16': "0x0",
            'ac17': "0x0",
            'ac1a': "0x0",
            'ac18': "0x0",
            'ac1b': "0x0",
            'ac19': "0x0"
        }

        self.machid = {
            '0000': "0x0",
            'ac11': "0x0",
            'ac14': "801000f",
            'ac15': "8010010",
            'ac16': "8010010",
            'ac17': "801000f",
            'ac1a': "801000f",
            'ac18': "801000f",
            'ac1b': "801000f",
            'ac19': "801000f"
        }

        self.method= {
            '0000': 0,
            'ac11': 0,
            'ac14': 1,
            'ac15': 1,
            'ac16': 1,
            'ac17': 1,
            'ac1a': 1,
            'ac18': 1,
            'ac1b': 1,
            'ac19': 1
        }


        self.linux_prompt = self.lnxpmt[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]
        self.b2a_method = self.method[self.board_id]

    def stop_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "")

    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

        retry = 10
        for i in range(0, retry):
            time.sleep(3)
            try:
                self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
                self.pexp.expect_only(15, "is alive")
            except Exception as e:
                print("ping fail..." + str(i))
                continue
            break
        else:
            print("ping retry fail")
            raise NameError('ping retry fail')

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
        time.sleep(10)
        self.set_uboot_network()
     
        if self.b2a_method == 0:
            msg(10, "Get ART Image")
            cmd = "tftpboot 0x42000000 images/{}".format(self.artimg[self.board_id])
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_only(120, "Bytes transferred")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "usetprotect spm off")
            
            msg(30, "Starting erasing NAND")
            cmd = "nand erase.chip"
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

            msg(40, "Starting writing Image")
            cmd = "nand write 0x42000000 {0} $filesize".format(self.addr[self.board_id])
            self.pexp.expect_ubcmd(120, self.bootloader_prompt, cmd)
            time.sleep(5)
        elif self.b2a_method == 1:

            msg(10, "Get ART Image")
            cmd = "tftpboot 0x44000000 images/{}".format(self.artimg[self.board_id])
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_only(120, "Bytes transferred")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv machid {}".format(self.machid[self.board_id]))

            msg(40, "Starting writing Image")
            cmd = "imgaddr=0x44000000 && source $imgaddr:script"
            self.pexp.expect_ubcmd(120, self.bootloader_prompt, cmd)
            time.sleep(5)

        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "re")

        self.stop_uboot()

        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "env default -a ; save")

        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "re")

        time.sleep(60)

        msg(90, "Reboot")
        if self.board_id == 'ac19':
            self.pexp.expect_only(120, "Linux version 4.4.60")
        else:
            self.pexp.expect_only(120, "Linux version 4.4.60")

        msg(100, "Back to ART has completed")
        self.close_fcd()
