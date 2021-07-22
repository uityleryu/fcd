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

FWUPDATE_ENABLE     = True 
PROVISION_ENABLE    = True 
DOHELPER_ENABLE     = True 
REGISTER_ENABLE     = True 
FLASH_DEVREG_DATA   = True
DEVREG_CHECK_ENABLE = True
SPIFF_FORMAT_CHECK  = True

class UFPESP32FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UFPESP32FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        # script specific vars
        self.esp32_prompt = "esp32>"
        self.product_class = "0015"
        self.flash_encrypt_key_bin = os.path.join(self.tftpdir, "images", "{}-flash_encryption_key.bin".format(self.board_id))
        self.secure_boot_key_bin   = os.path.join(self.tftpdir, "images", "{}-secure_bootloader_key.bin".format(self.board_id))
        self.regsubparams = ""

        # Index 0: flag to control key is existed or flash is encrypted
        #       1: key name
        #       2: burn_key option
        #       3: key binary
        self.dev_flash_cfg = [[True, "Flash encryption key"         , "flash_encryption", self.flash_encrypt_key_bin], 
                              [True, "Secure boot key"              , " secure_boot"     , self.secure_boot_key_bin  ],
                              [True, "Flash encryption mode counter", None              , None                      ]]
        # number of Ethernet
        self.ethnum = {
            'ec47': "0",
        }

        # number of WiFi
        self.wifinum = {
            'ec47': "1",
        }

        # number of Bluetooth
        self.btnum = {
            'ec47': "1",
        }

        self.devnetmeta = {                                                                                                  
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def prepare_server_need_files(self):
        output = self.pexp.expect_get_output("uniqueid", self.esp32_prompt, timeout=10)
        log_debug(output)
        id_list = re.findall(r'id: 0x(\w+)', output)
        cpu_id = id_list[0]
        flash_jedec_id = id_list[1]
        flash_uuid = id_list[2]
        
        log_debug("cpu_id={}, flash_jedec_id={}, flash_uuid{}".format(cpu_id, flash_jedec_id, flash_uuid))
        self.regsubparams = " -i field=product_class_id,format=hex,value={}".format(self.product_class) + \
                            " -i field=cpu_rev_id,format=hex,value={}".format(cpu_id)                   + \
                            " -i field=flash_jedec_id,format=hex,value={}".format(flash_jedec_id)       + \
                            " -i field=flash_uid,format=hex,value={}".format(flash_uuid) 

    ### To check if keys are exist and device is first programmed or not
    def check_device_stat(self):
        cmd = "sudo espefuse.py -p /dev/ttyUSB1 summary"
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Get efuse summary failed"
            error_critical(otmsg)

        for key in self.dev_flash_cfg:
            match = re.search(r'{}\W+= (.*) .\/.'.format(key[1]), output)
            if match:
                key_val = match.group(1)
                log_info('{} = "{}"'.format(key[1], key_val))
                if key_val == "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00" or \
                   key_val == "0":
                    key[0] = False
            else:
                error_critical("Can't parse key {}".format(key[0]))

    def program_keys(self):
        for i in range(0, 2):
            if self.dev_flash_cfg[i][0] is False:
                cmd = "sudo espefuse.py -p /dev/ttyUSB{} --do-not-confirm burn_key {} {}".format(self.row_id, self.dev_flash_cfg[i][2], self.dev_flash_cfg[i][3])
                log_debug(cmd)
                [output, rv] = self.cnapi.xcmd(cmd)
                if int(rv) > 0:
                    otmsg = 'burn_key "{}" failed!'.format(self.dev_flash_cfg[i][1])
                    error_critical(otmsg)
            else:
                log_info('Skip programming key "{}" because it is existed there'.format(self.dev_flash_cfg[i][1]))

        cmd = "sudo espefuse.py -p /dev/ttyUSB{} --do-not-confirm burn_efuse FLASH_CRYPT_CONFIG 0xF".format(self.row_id)
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = 'burn_key "{}" failed!'.format("FLASH_CRYPT_CONFIG")
            #error_critical(otmsg)

        cmd = "sudo espefuse.py -p /dev/ttyUSB{} --do-not-confirm burn_efuse  FLASH_CRYPT_CNT 127".format(self.row_id)
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = 'burn_key "{}" failed!'.format("FLASH_CRYPT_CNT")
            #error_critical(otmsg)

        cmd = "sudo espefuse.py -p /dev/ttyUSB{} --do-not-confirm burn_efuse DISABLE_DL_ENCRYPT".format(self.row_id)
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = 'burn_key "{}" failed!'.format("DISABLE_DL_ENCRYPT")
            #error_critical(otmsg)

    def program_flash(self):
        encrypt_postfix = "encrypted"
        fw_bootloader = os.path.join(self.tftpdir, "images", "{}-bootloader-reflash-digest.{}.bin".format(self.board_id, encrypt_postfix))
        fw_ptn_table  = os.path.join(self.tftpdir, "images", "{}-partition-table.{}.bin".format(self.board_id, encrypt_postfix))
        fw_ota_data   = os.path.join(self.tftpdir, "images", "{}-ota_data_initial.{}.bin".format(self.board_id, encrypt_postfix))
        fw_app        = os.path.join(self.tftpdir, "images", "{}-uc_thermostat_bsp.{}.bin".format(self.board_id, encrypt_postfix))
        fw_nvs_key    = os.path.join(self.tftpdir, "images", "{}-nvs_key.{}.bin".format(self.board_id, encrypt_postfix))


        cmd = "esptool.py --chip esp32 -p /dev/ttyUSB{} -b 460800 --before=default_reset "         \
              "--after=hard_reset write_flash --flash_mode dio --flash_freq 40m " \
              "{} {} {} {} {} {} {} {} {} {}".format(self.row_id,
                                                     "0x0"     , fw_bootloader,
                                                     "0xb000"  , fw_ptn_table ,
                                                     "0xe000"  , fw_ota_data  ,
                                                     "0x10000" , fw_app       ,
                                                     "0xd000", fw_nvs_key   )
        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash FW into DUT failed"
            error_critical(otmsg)

        # The waiting time         
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        self.pexp.expect_only(180, self.esp32_prompt)
        log_debug("Device boots well")

    def fwupdate(self):
        self.check_device_stat()
        self.program_keys()
        self.program_flash()

    def put_devreg_data_in_dut(self):
        self.pexp.close()
        cmd = "esptool.py -p /dev/ttyUSB{} --chip esp32 -b 460800 --before default_reset "\
              "--after hard_reset write_flash --flash_mode dio --flash_freq 40m "         \
              "--flash_size 4MB 0x3ff000 /tftpboot/e.s.{}".format(self.row_id, self.row_id)
        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash e.s.{} into DUT failed".format(self.row_id)
            error_critical(otmsg)
        
        ## The waiting time
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)
        self.pexp.expect_only(60, "DEVREG:") # The security check will fail if littlefs isn't mounted

    def check_devreg_data(self):
        output = self.pexp.expect_get_output("info", self.esp32_prompt, timeout=10)
        log_debug("output:".format(output))
        info = {}
        # value is our expected string
        devreg_data_dict = {'System ID'   : self.board_id              ,
                            'Bom Revision': self.bom_rev.split('-')[0] ,
                            'Mac Address' : self.mac                   ,
                            'DEVREG check': 'PASS'                     }

        for key in devreg_data_dict:
            regex = re.compile(r"{}: (\w+)".format(key))
            data_list = regex.findall(output)
            info[key] = data_list[0]

        for key in devreg_data_dict:
            if devreg_data_dict[key] != info[key]:
                error_critical("{}: {}, not {}".format(key, info[key], devreg_data_dict[key]))
            else:
                log_debug("{}: {}".format(key, info[key]))

    def check_littlefs_mount(self):
        time.sleep(90)
        self.pexp.expect_lnxcmd(timeout=3, pre_exp=self.esp32_prompt, action="littlefs_get_info", 
                                post_exp="littlefs_cmd: mount", retry=80)

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        msg(5, "Open serial port successfully ...")
    
        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(10, "Finish FW updating ...")

        if PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(15, "Finish erasing ee files ...")
            self.data_provision_4k(netmeta=self.devnetmeta)
            msg(20, "Finish 4K binary generating ...")

        if DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration(regsubparams = self.regsubparams)
            msg(40, "Finish doing registration ...")

        if FLASH_DEVREG_DATA is True:
            self.put_devreg_data_in_dut()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if DEVREG_CHECK_ENABLE is True:
            self.check_devreg_data()
            msg(70, "Finish checking MAC in DUT ...")

        if SPIFF_FORMAT_CHECK is True:
            self.check_littlefs_mount()
            msg(90, "Littlefs mounted")

        msg(100, "Completing registration ...")
        self.close_fcd()

def main():
    factory_general = UFPESP32FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()