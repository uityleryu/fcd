#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.pserial import SerialExpect
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info

import sys
import time
import os
import re
import traceback

DUT_STATUS = True
FLASH_DUT_DATA = True

FWUPDATE_ENABLE     = True 
PROVISION_ENABLE    = True 
DOHELPER_ENABLE     = True 
REGISTER_ENABLE     = True 
FLASH_DEVREG_DATA   = True
DEVREG_CHECK_ENABLE = True
SPIFF_FORMAT_CHECK  = True

class PSoC6FactoryGeneral(ScriptBase):
    def __init__(self):
        super(PSoC6FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        # script specific vars
        self.esp32_prompt = "esp32>"
        self.product_class = "0015"
        self.flash_encrypt_key_bin = os.path.join(self.tftpdir, "images", "{}-flash_encrypt_key.bin".format(self.board_id))
        self.secure_boot_key_bin   = os.path.join(self.tftpdir, "images", "{}-secure_boot_key.bin".format(self.board_id))
        self.regsubparams = ""
        self.allflash_uuid = ""
        # Index 0: flag to control key is existed or flash is encrypted
        #       1: key name
        #       2: burn_key option
        #       3: key binary
        self.dev_flash_cfg = [[True, "Flash encryption key"         , "flash_encryption", self.flash_encrypt_key_bin], 
                              [True, "Secure boot key"              , "secure_boot"     , self.secure_boot_key_bin  ],
                              [True, "Flash encryption mode counter", None              , None                      ]]
        # number of Ethernet
        self.ethnum = {
            'ec40': "0",
        }

        # number of WiFi
        self.wifinum = {
            'ec40': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ec40': "1",
        }

        self.devnetmeta = {                                                                                                  
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def dutbootup_check(self):
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)

        self.pexp.expect_lnxcmd(5, "", "route2command", "Not allow sleep")
        self.pexp.expect_lnxcmd(5, "", "mfglogoff", "Not allow sleep")
        self.pexp.expect_lnxcmd(5, "", "mfg?", "devreg passed?")
    
    def flashdutdata(self):
        bom_id = self.bom_rev.split('-')[0]
        board_rev = self.bom_rev.split('-')[1]
        self.pexp.expect_action(1, "", "mfgbdid={}".format(self.board_id))
        self.pexp.expect_action(1, "", "mfgbdmac={}".format(self.mac))
        self.pexp.expect_action(1, "", "mfgqrcode={}".format(self.qrcode))
        self.pexp.expect_action(1, "", "mfgcountry={}".format(self.region))
        self.pexp.expect_action(1, "", "mfgbomrev={}".format(bom_id))
        self.pexp.expect_action(1, "", "mfgbdrev={}".format(board_rev))
        output = self.pexp.expect_get_output("mfglist", "contry:", timeout=3)
        try:
            sysinfo_list = re.findall(r'\w+:\s+(\w+) !', output)
            dut_board_id = sysinfo_list[0].replace("0x", "")
            dut_board_rev = sysinfo_list[1].replace("0x", "")
            dut_bom_id = sysinfo_list[2].replace("0x", "")
            dut_mac = sysinfo_list[3].replace("0x", "")
            dut_qrcode = sysinfo_list[4]
            dut_region = sysinfo_list[5]
            itemlist = ["board_id", "board_rev", "bom_id", "mac", "qrcode", "region"]
            expectlist = [self.board_id, board_rev, bom_id, self.mac, self.qrcode, self.region]
            dutlist = [dut_board_id, dut_board_rev, dut_bom_id, dut_mac, dut_qrcode, dut_region]
            for idx in range(len(itemlist)):
                if expectlist[idx] == dutlist[idx]:
                    msg = "DUT {}: {} match with expect info: {}".format(itemlist[idx], expectlist[idx], expectlist[idx])
                    log_debug(msg)
                else:
                    msg = "DUT {}: {} doesn't match with expect info: {}".format(itemlist[idx], expectlist[idx], expectlist[idx])
                    log_debug(msg)
                    error_critical(msg)
        except Exception as e:
            log_debug("{}".format(e))

    def prepare_server_need_files(self):
        cmd = "sudo rm /tftpboot/hash_file.{}; sync; sleep 1".format(self.row_id)
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Remove hash_file failed"
            error_critical(otmsg)
        cmd = "sudo rm /tftpboot/md5sum_file.{}; sync; sleep 1".format(self.row_id)
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Remove md5sum_file failed"
            error_critical(otmsg)

        output = self.pexp.expect_get_output("mfginfo", "device CPU:", timeout=10)
        cpu_id = re.search(r'device CPU: (\w+-\w+)', output).group(1)
        flash_jedec_id = "00"+re.search(r'flash jedec id: (\w+)', output).group(1)
        flash_uuid = re.search(r'SPI Flash UUID: (\w+)', output).group(1)[:26]
        self.allflash_uuid = re.search(r'SPI Flash UUID: (\w+)', output).group(1)
        if cpu_id == 'CY8C6137BZI-F54':
            cpu_id = "0000E217"
        else:
            otmsg = "Get CPU ID failed"
            error_critical(otmsg)

        log_debug("cpu_id={}, flash_jedec_id={}, flash_uuid:{}".format(cpu_id, flash_jedec_id, flash_uuid))
        self.regsubparams = " -i field=product_class_id,format=hex,value={}".format(self.product_class) + \
                            " -i field=cpu_rev_id,format=hex,value={}".format(cpu_id)                   + \
                            " -i field=flash_jedec_id,format=hex,value={}".format(flash_jedec_id)       + \
                            " -i field=flash_uid,format=hex,value={}".format(flash_uuid)

    def put_devreg_data(self):
        try:
            cmd = "sudo chmod 777 /tftpboot/tools/ua_hotel/hash32-arm-rpi"
            log_debug(cmd)
            [output, rv] = self.cnapi.xcmd(cmd)
            if int(rv) > 0:
                otmsg = "Create hash_file failed"
                error_critical(otmsg)

            cmd = "sudo md5sum /tftpboot/e.s.{} | cut -c -32 > /tftpboot/md5sum_file.{}".format(self.row_id, self.row_id)
            log_debug(cmd)
            [output, rv] = self.cnapi.xcmd(cmd)
            if int(rv) > 0:
                otmsg = "Create md5_file failed"
                error_critical(otmsg)

            cmd = "/tftpboot/tools/ua_hotel/hash32-arm-rpi {} {} > /tftpboot/hash_file.{}".format(self.qrcode, self.allflash_uuid, self.row_id)
            log_debug(cmd)
            [output, rv] = self.cnapi.xcmd(cmd)
            if int(rv) > 0:
                otmsg = "Create hash_file failed"
                error_critical(otmsg)

            cmd = "cat /tftpboot/md5sum_file.{}".format(self.row_id)
            log_debug(cmd)
            [md5sum, rv] = self.cnapi.xcmd(cmd)
            if int(rv) > 0:
                otmsg = "get md5_file failed"
                error_critical(otmsg)
            log_debug("MD5: {}".format(md5sum))

            cmd = "cat  /tftpboot/hash_file.{}".format(self.row_id)
            log_debug(cmd)
            [hash, rv] = self.cnapi.xcmd(cmd)
            if int(rv) > 0:
                otmsg = "get Hash_file failed"
                error_critical(otmsg)
            log_debug("Hash: {}".format(hash))
            self.pexp.expect_lnxcmd(15, "", "mfgcalc", "x3=")
            self.pexp.expect_lnxcmd(15, "", "mfgkey={}".format(hash).format(self.board_id), "")
            self.pexp.expect_lnxcmd(15, "", "mfgupdate", "update key:")
            self.pexp.expect_lnxcmd(15, "", "mfgblock={}".format(md5sum), "waiting for block of hash:")

        except Exception as e:
            log_debug(e)
            error_critical(otmsg)

    def send_signed_data(self):
        cmd = "cat /tftpboot/md5sum_file.{}".format(self.row_id)
        log_debug(cmd)
        [md5sum, rv] = self.cnapi.xcmd(cmd)

        cmd = "sudo chmod 777 /dev/ttyUSB{}".format(self.row_id, self.row_id)
        log_debug(cmd)
        self.cnapi.xcmd(cmd)

        cmd = "cat /tftpboot/e.s.{} > /dev/ttyUSB{}".format(self.row_id, self.row_id)
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "send signed data failed"
            error_critical(otmsg)

        self.pexp.expect_only(10, "done. hash:{}".format(md5sum))

        output = self.pexp.expect_get_output("mfgblock", "md5hash(4096):{}".format(md5sum), timeout=3)
        if "md5hash(4096):{}".format(md5sum) not in output:
            otmsg = "check md5hash data failed"
            error_critical(otmsg)
        output = self.pexp.expect_get_output("mfgsave", "saved in flash!", timeout=3)
        if "saved in flash!" not in output:
            otmsg = "mfg save failed"
            error_critical(otmsg)
        output = self.pexp.expect_get_output("mfg?", "devreg passed?", timeout=3)
        if "DEVREG Security check result: Pass." not in output:
            otmsg = "check devreg failed"
            error_critical(otmsg)
    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        msg(5, "Open serial port successfully ...")

        if DUT_STATUS is True:
            self.dutbootup_check()
            msg(10, "Cehck DUT boot up ...")

        if PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Finish erasing ee files ...")
            self.data_provision_4k(netmeta=self.devnetmeta)
            msg(30, "Finish 4K binary generating ...")
            
        if DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(50, "Finish preparing the devreg file ...")
        
        if FLASH_DUT_DATA is True:
            self.flashdutdata()
            msg(60, "Finish flash dut information ...")

        if REGISTER_ENABLE is True:
            self.registration(regsubparams=self.regsubparams)
            msg(70, "Finish doing registration ...")

        if FLASH_DEVREG_DATA is True:
            self.put_devreg_data()
            msg(80, "Finish doing drvreg file updateing ...")
            self.send_signed_data()
            msg(90, "Finish mfg block and checking ...")

        msg(100, "Completing registration ...")
        return
        self.close_fcd()


def main():
    factory_general = PSoC6FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()
