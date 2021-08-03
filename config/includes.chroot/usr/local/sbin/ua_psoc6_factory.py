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
        starttime = time.time()
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)

        while True:
            self.pexp.expect_get_output("route2command", "Not allow sleep", timeout=5)
            self.pexp.expect_get_output("mfglogoff", "Not allow sleep", timeout=5)
            output = self.pexp.expect_get_output("mfg?", "devreg passed?", timeout=10)

            if "devreg passed?" in output:
                msg = "Detect DUT boot up"
                log_debug(msg)
                break
            else:
                if time.time() - starttime > 20:
                    msg = "Can't detect DUT boot up"
                    log_debug(msg)
                    error_critical(msg)

        if "devreg passed? yes !" not in output:
            msg = "Already does devreg, please reprogram it"
            log_debug(msg)
            error_critical(msg)
    
    def flashdutdata(self):
        bom_id = self.bom_rev.split('-')[0]
        board_rev = self.bom_rev.split('-')[1]
        self.pexp.expect_action(1, "", "mfgbdid={}".format(self.board_id))
        self.pexp.expect_action(1, "", "mfgbdmac={}".format(self.mac))
        self.pexp.expect_action(1, "", "mfgqrcode={}".format(self.qrcode))
        self.pexp.expect_action(1, "", "mfgcountry={}".format(self.region))
        self.pexp.expect_action(1, "", "mfgbomrev={}".format(bom_id))
        self.pexp.expect_action(1, "", "mfgbdrev={}".format(board_rev))
        output = self.pexp.expect_get_output("mfglist", "contry:", timeout=10)

        sysinfo_list = re.findall(r'\w+:\s*(\w+) !', output)
        dut_board_id = sysinfo_list[0].replace("0x", "")
        dut_board_rev = sysinfo_list[1].replace("0x", "")
        dut_bom_id = sysinfo_list[2].replace("0x", "")
        dut_mac = sysinfo_list[3].replace("0x", "")
        dut_qrcode = sysinfo_list[5]
        dut_region = sysinfo_list[6]

        itemlist = ["board_id", "board_rev", "bom_id", "mac", "qrcode", "region"]
        expectlist = [self.board_id, self.board_rev, self.bom_id, self.mac, self.qrcode, self.region]
        dutlist = [dut_board_id, dut_board_rev, dut_bom_id, dut_mac, dut_qrcode, dut_region]
        for idx in range(len(itemlist)):
            if expectlist[idx] == dutlist[idx]:
                msg = "DUT {}: {} match with expect info: {}".format(itemlist[idx], expectlist[idx], expectlist[idx])
                log_debug(msg)
            else:
                msg = "DUT {}: {} doesn't match with expect info: {}".format(itemlist[idx], expectlist[idx], expectlist[idx])
                log_debug(msg)
                error_critical(msg)

    def prepare_server_need_files(self):
        output = self.pexp.expect_get_output("mfginfo", "device CPU:", timeout=10)
        cpu_id = re.search(r'device CPU: (\w+-\w+)', output).group(1)
        flash_jedec_id = "00"+re.search(r'flash jedec id: (\w+)', output).group(1)
        flash_uuid = re.search(r'SPI Flash UUID: (\w+)', output).group(1)[:26]
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

    def program_flash(self):
        encrypt_postfix = "-encrypt" if self.dev_flash_cfg[2][0] is True else ""
        fw_bootloader = os.path.join(self.tftpdir, "images", "{}-bootloader{}.bin".format(self.board_id, encrypt_postfix))
        fw_ptn_table  = os.path.join(self.tftpdir, "images", "{}-ptn-table{}.bin".format(self.board_id, encrypt_postfix))
        fw_ota_data   = os.path.join(self.tftpdir, "images", "{}-ota{}.bin".format(self.board_id, encrypt_postfix))
        fw_app        = os.path.join(self.tftpdir, "images", "{}-app{}.bin".format(self.board_id, encrypt_postfix))
        fw_nvs_key    = os.path.join(self.tftpdir, "images", "{}-nvs-key{}.bin".format(self.board_id, encrypt_postfix))


        cmd = "esptool.py --chip esp32 -p /dev/ttyUSB{} -b 460800 --before=default_reset "         \
              "--after=hard_reset write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB " \
              "{} {} {} {} {} {} {} {} {} {}".format(self.row_id,
                                                     "0x0"     , fw_bootloader,
                                                     "0xb000"  , fw_ptn_table ,
                                                     "0xd000"  , fw_ota_data  ,
                                                     "0x10000" , fw_app       ,
                                                     "0x3fc000", fw_nvs_key   )
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
        
        if DUT_STATUS is True:
            self.dutbootup_check()
            msg(10, "Cehck DUT boot up ...")

        if PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(15, "Finish erasing ee files ...")
            self.data_provision_4k(netmeta=self.devnetmeta)
            msg(20, "Finish 4K binary generating ...")
            
        if DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")
        
        if FLASH_DUT_DATA is True:
            self.flashdutdata()
            msg(40, "Finish flash dut information ...")
        return

        ######old######    
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
    factory_general = PSoC6FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()
