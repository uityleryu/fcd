#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info

import sys
import time
import os
import re
import traceback
import json

FWUPDATE_ENABLE     = True
PROVISION_ENABLE    = True
DOHELPER_ENABLE     = True
REGISTER_ENABLE     = True
FLASH_DEVREG_DATA   = True
DEVREG_CHECK_ENABLE = True


class UAESP32FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UAESP32FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        # script specific vars
        self.esp32_prompt = "esp32>"
        self.product_class = "0015"
        self.secure_boot_key_bin = os.path.join(self.tftpdir, "images", "{}-secure_boot_key.bin".format(self.board_id))
        self.fw_bootloader_digeset = os.path.join(self.tftpdir, "images", "{}-bootloader-digest.bin".format(self.board_id))
        self.fw_bootloader = os.path.join(self.tftpdir, "images", "{}-bootloader.bin".format(self.board_id))
        self.fw_ota_data = os.path.join(self.tftpdir, "images", "{}-ota.bin".format(self.board_id))
        self.fw_ptn_table = os.path.join(self.tftpdir, "images", "{}-ptn-table.bin".format(self.board_id))
        self.fw_mfg = os.path.join(self.tftpdir, "images", "{}-mfg.bin".format(self.board_id))

        # Index 0: flag to control key is existed or flash is encrypted
        #       1: key name
        #       2: burn_key option
        #       3: key binary
        self.dev_flash_cfg = [[True, "Secure boot key", "secure_boot", self.secure_boot_key_bin]]

        self.regsubparams = ""
        # number of Ethernet
        self.ethnum = {
            'ec84': "1",
        }

        # number of WiFi
        self.wifinum = {
            'ec84': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ec84': "0",
        }

        self.flash_size = {
            'ec84': "16MB",
        }

        self.eeprom_offset = {
            'ec84': "0xfff000",
        }

        self.partion_offset = {
            'ec84': {
                'bootloader_digest': '0',
                'bootloader': '0x1000',
                'partition_table': '0xb000',
                'ota': '0xd000',
                'mfg': '0x90000'},
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        #Add method for write ME BOM
        self.write_mebom = {
            'ec84': True
        }

        #Add method for write top level BOM
        self.write_topbom = {
            'ec84': False
        }

    def prepare_server_need_files(self):
        output = self.pexp.expect_get_output("uniqueid", "", timeout=3)
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
        cmd = "sudo espefuse.py -p /dev/ttyUSB{} summary".format(self.row_id)
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
        for i in range(0, len(self.dev_flash_cfg)):
            if self.dev_flash_cfg[i][0] is False:
                cmd = "sudo espefuse.py -p /dev/ttyUSB{} --do-not-confirm burn_key {} {}".format(self.row_id, self.dev_flash_cfg[i][2], self.dev_flash_cfg[i][3])
                log_debug(cmd)
                [output, rv] = self.cnapi.xcmd(cmd)
                if int(rv) > 0:
                    otmsg = 'burn_key "{}" failed!'.format(self.dev_flash_cfg[i][1])
                    error_critical(otmsg)
            else:
                log_info('Skip programming key "{}" because it is existed there'.format(self.dev_flash_cfg[i][1]))

    def program_bootloader(self, offset, file_bin):
        cmd = "esptool.py --chip esp32 -p /dev/ttyUSB{} -b 460800 --before=default_reset "         \
              "--after=no_reset write_flash --flash_mode dio --flash_freq 40m --flash_size {} " \
              "{} {}".format(self.row_id,
                             self.flash_size[self.board_id],
                             offset, file_bin)
        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash FW into DUT failed"
            error_critical(otmsg)

    def program_fw(self):
        cmd = "esptool.py --chip esp32 -p /dev/ttyUSB{} -b 460800 --before=default_reset "         \
              "--after=hard_reset write_flash --flash_mode dio --flash_freq 40m --flash_size {} " \
              "{} {} {} {} {} {}".format(self.row_id,
                                         self.flash_size[self.board_id],
                                         self.partion_offset[self.board_id]['partition_table'], self.fw_ptn_table,
                                         self.partion_offset[self.board_id]['ota'], self.fw_ota_data,
                                         self.partion_offset[self.board_id]['mfg'], self.fw_mfg)
        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash FW into DUT failed"
            error_critical(otmsg)

        # The waiting time
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        self.pexp.expect_only(120, self.esp32_prompt)
        log_debug("Device boots well")

    def fwupdate(self):
        self.check_device_stat()
        self.program_keys()
        self.program_bootloader(offset=self.partion_offset[self.board_id]['bootloader'], file_bin=self.fw_bootloader)
        self.program_bootloader(offset=self.partion_offset[self.board_id]['bootloader_digest'], file_bin=self.fw_bootloader_digeset)
        self.program_fw()

    def put_devreg_data_in_dut(self):
        self.pexp.close()
        time.sleep(1)

        cmd = "esptool.py -p /dev/ttyUSB{} --chip esp32 -b 460800 --before default_reset "\
              "--after hard_reset write_flash --flash_mode dio --flash_freq 40m "         \
              "--flash_size {} {} /tftpboot/e.s.{}".format(
                  self.row_id,
                  self.flash_size[self.board_id],
                  self.eeprom_offset[self.board_id],
                  self.row_id)

        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash e.s.{} into DUT failed".format(self.row_id)
            error_critical(otmsg)

        # The waiting time
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        self.pexp.expect_only(60, self.esp32_prompt)
        log_debug("Device boots well")

    def check_devreg_data(self):
        output = self.pexp.expect_get_output("info", "", timeout=3)
        info = {}

        # value is our expected string
        devreg_data_dict = {'system_id': self.board_id,
                            'mac_addr': self.mac.upper(),
                            'devreg_check': 'PASS'}

        for key in devreg_data_dict:
            regex = re.compile(r'"{}":"((\w+:?)*)"'.format(key))
            data_list = regex.search(output)
            info[key] = data_list.group(1)

        for key in devreg_data_dict:
            if devreg_data_dict[key] != info[key]:
                error_critical("{}: {}, not {}".format(key, info[key], devreg_data_dict[key]))
            else:
                log_debug("{}: {}".format(key, info[key]))

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        # check ME BOM
        if self.write_mebom[self.board_id] is True:
            if not self.meb_rev:
                error_critical("ME BOM is required ...")

        # check Top level BOM
        if self.write_topbom[self.board_id] is True:
            if not self.tlb_rev:
                error_critical("Top level BOM is required ...")

        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        msg(5, "Open serial port successfully ...")

        self.erase_eefiles()
        msg(10, "Finish erasing ee files ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(15, "Finish FW updating ...")

        if PROVISION_ENABLE is True:
            self.data_provision_4k(netmeta=self.devnetmeta)
            msg(20, "Finish 4K binary generating ...")

        if DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration(regsubparams=self.regsubparams)
            msg(40, "Finish doing registration ...")

        if FLASH_DEVREG_DATA is True:
            self.put_devreg_data_in_dut()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if DEVREG_CHECK_ENABLE is True:
            self.check_devreg_data()
            msg(70, "Finish checking MAC in DUT ...")

        msg(100, "Completing registration ...")
        self.close_fcd()


def main():
    factory_general = UAESP32FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()
