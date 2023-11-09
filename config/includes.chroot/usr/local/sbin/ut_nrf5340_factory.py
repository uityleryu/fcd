#!/usr/bin/python3
import logging
import time
import os
import re

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FLASH_DEVREG_DATA = True
DEVREG_CHECK_ENABLE = True


class UMNRF52840FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UMNRF52840FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.nrf5340_prompt = "uart:~$"
        self.product_class = "0015"  # for basic 4k product, please refer https://docs.google.com/spreadsheets/d/18hqzWQowU-3KRXN-N3BlWYDUyQ7WKnELLQrevznXOKA/edit#gid=1
        self.regsubparams = ""

        # number of Ethernet
        self.ethnum = {
            'efbe': "0"
        }

        # number of WiFi
        self.wifinum = {
            'efbe': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'efbe': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.pd_dir = {
            'efbe': "ut-g3-handset"
        }
        self.tools_full_dir = os.path.join(self.fcd_toolsdir, self.pd_dir[self.board_id])

    def prepare_server_need_files(self):
        output = self.pexp.expect_get_output("extflash uniqueid", self.nrf5340_prompt, timeout=3)
        output = output.replace('[1;32muart:~$ [m[8D[J', '')
        id_list = re.findall(r'id: 0x(\w+)', output)
        cpu_id = id_list[0]
        flash_jedec_id = id_list[1]
        flash_uuid = re.findall(r'flash_uid:(\w+)', output)[0]

        log_debug("cpu_id={}, flash_jedec_id={}, flash_uuid={}".format(cpu_id, flash_jedec_id, flash_uuid))
        self.regsubparams = " -i field=product_class_id,format=hex,value={}".format(self.product_class) + \
                            " -i field=cpu_rev_id,format=hex,value={}".format(cpu_id) + \
                            " -i field=flash_jedec_id,format=hex,value={}".format(flash_jedec_id) + \
                            " -i field=flash_uid,format=hex,value={}".format(flash_uuid)

    def put_devreg_data_in_dut(self):
        self.disconnect_uart()
        cmd = "bash {}/program.sh {} /dev/{}".format(self.tools_full_dir, self.eesign_path, self.dev)
        log_debug("cmd={}".format(cmd))
        [output, rv] = self.cnapi.xcmd(cmd)
        self.connect_uart()
        time.sleep(2)

    def check_qspi_flash(self):
        timeout = 300
        log_info("Start checking QSPI flash, maximum {} seconds ...".format(timeout))
        cmd = "ui_flash verify_range w25q64jv@0 0x0 0x7ff000"
        self.pexp.expect_action(2, "", cmd)
        self.pexp.expect_only(timeout, "err=0")
        log_info("QSPI Flash check pass!!!")

    def check_devreg_data(self):
        pattern = r"[a-f0-9]{64}"
        for i in range(3):
            cmd = "ui_flash sha256 w25q64jv@0 0x7ff000 0x1000"
            output = self.pexp.expect_get_output2(cmd, self.nrf5340_prompt, self.nrf5340_prompt, timeout=3)
            sha256_eeprom = re.findall(pattern, output)
            if sha256_eeprom:
                log_info("eeprom sha256 is {}".format(sha256_eeprom[0]))
            else:
                log_info("Parsing sha256sum fail!")
                continue
            cmd = "sha256sum {}".format(self.eesign_path)
            [output, rv] = self.cnapi.xcmd(cmd)
            sha256_signed = re.findall(pattern, output)
            if sha256_signed:
                log_info("signed sha256 is {}".format(sha256_signed[0]))
            else:
                log_info("Parsing sha256sum fail!")
                continue
            if sha256_eeprom[0] != sha256_signed[0]:
                log_info("{} != {}".format(sha256_eeprom, sha256_signed))
                log_info("eeprom check fail!!!")
                log_info("Try to write again ... {}".format(i+1))
                self.put_devreg_data_in_dut()
            else:
                log_info("{} = {}".format(sha256_eeprom, sha256_signed))
                log_info("eeprom check OK!!!")
                break
        else:
            error_critical("eeprom check fail!!!")


    def connect_uart(self):
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)

    def disconnect_uart(self):
        pexpect_obj = None
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)

    def run(self):
        """
            Main procedure of factory
        """
        # log_debug(msg="The HEX of the QR code=" + self.qrhex)
        log_debug(msg="The HEX of the Activation code=" + self.activate_code_hex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()

        self.connect_uart()
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(15, "Finish erasing ee files ...")
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

        if self.board_id in ['efbe']:
            self.check_qspi_flash()
            msg(90, "Finish checking QSPI flash  ...")

        msg(100, "Completing registration ...")
        self.close_fcd()


def main():
    factory_general = UMNRF52840FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()
