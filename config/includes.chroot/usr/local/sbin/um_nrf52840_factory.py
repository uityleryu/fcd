#!/usr/bin/python3
import time
import os
import re

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FLASH_DEVREG_DATA = False
DEVREG_CHECK_ENABLE = False
RECORD_MODEM_IMEI = True


class UMNRF52840FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UMNRF52840FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.nrf52840_prompt = "umt:~"
        self.product_class = "0015"  # for basic 4k product, please refer https://docs.google.com/spreadsheets/d/18hqzWQowU-3KRXN-N3BlWYDUyQ7WKnELLQrevznXOKA/edit#gid=1
        self.regsubparams = ""

        if self.board_id in ["0121", "0122"]:
            self.log_upload_failed_alert_en = True

        # number of Ethernet
        self.ethnum = {
            '0121': "0",
            '0122': "0"
        }

        # number of WiFi
        self.wifinum = {
            '0121': "0",
            '0122': "0"
        }

        # number of Bluetooth
        self.btnum = {
            '0121': "1",
            '0122': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def prepare_server_need_files(self):
        self.pexp.expect_lnxcmd(15, self.nrf52840_prompt, 'shell colors off')
        output = self.pexp.expect_get_output("uart_debug uniqueid", self.nrf52840_prompt, timeout=3)
        # log_debug(output)
        id_list = re.findall(r'id: 0x(\w+)', output)
        cpu_id = id_list[0]
        flash_jedec_id = id_list[1]
        flash_uuid = id_list[2]

        log_debug("cpu_id={}, flash_jedec_id={}, flash_uuid={}".format(cpu_id, flash_jedec_id, flash_uuid))
        self.regsubparams = " -i field=product_class_id,format=hex,value={}".format(self.product_class) + \
                            " -i field=cpu_rev_id,format=hex,value={}".format(cpu_id) + \
                            " -i field=flash_jedec_id,format=hex,value={}".format(flash_jedec_id) + \
                            " -i field=flash_uid,format=hex,value={}".format(flash_uuid)

    def registration(self, regsubparams=None):
        log_debug("Starting to do registration ...")

        # To decide which client executed file
        cmd = "uname -a"
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("Get linux information failed!!")
        else:
            log_debug("Get linux information successfully")
            match = re.findall("armv7l", sto)
            if match:
                clientbin = "/usr/local/sbin/client_rpi4_release"
            else:
                clientbin = "/usr/local/sbin/client_x86_release"

        self.devreg_hostname = "stage.udrs.io"  # for activation code

        if regsubparams is None:
            regsubparams = self.access_chips_id()

        code_type = "01"  # for activation code

        # The HEX of the activate code
        if self.activate_code is None or not self.activate_code:
            reg_activate_code = ""
        else:
            reg_activate_code = "-i field=code,format=hex,value={}".format(self.activate_code_hex)

        regparam = [
            "-h {}".format(self.devreg_hostname),
            "-k {}".format(self.pass_phrase),
            regsubparams,
            "-i field=code_type,format=hex,value={}".format(code_type),
            reg_activate_code,
            "-i field=flash_eeprom,format=binary,pathname={}".format(self.eebin_path),
            "-i field=fcd_version,format=hex,value={}".format(self.sem_ver),
            "-i field=sw_id,format=hex,value={}".format(self.sw_id),
            "-i field=sw_version,format=hex,value={}".format(self.fw_ver),
            "-o field=flash_eeprom,format=binary,pathname={}".format(self.eesign_path),
            "-o field=registration_id",
            "-o field=result",
            "-o field=device_id",
            "-o field=registration_status_id",
            "-o field=registration_status_msg",
            "-o field=error_message",
            "-x {}ca.pem".format(self.key_dir),
            "-y {}key.pem".format(self.key_dir),
            "-z {}crt.pem".format(self.key_dir)
        ]

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Security Service Device Registration Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        self.pass_devreg_client = True

        log_debug("Excuting client registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()

    def put_devreg_data_in_dut(self):
        self.pexp.expect_only(60, "DEVREG:")  # The security check will fail if littlefs isn't mounted

    def check_devreg_data(self):
        output = self.pexp.expect_get_output2("info", "ubnt", self.nrf52840_prompt, timeout=10)

    def record_modem_imei(self):
        output = self.pexp.expect_get_output("uishell_mdm imei", self.nrf52840_prompt, timeout=3)
        log_debug("rsp={}".format(output))
        match = re.search(r'([0-9]{15,})', output)
        imei = match.group(1)
        log_debug("imei={}".format(imei))
        self.imei = imei

    def run(self):
        """
            Main procedure of factory
        """
        # log_debug(msg="The HEX of the QR code=" + self.qrhex)
        log_debug(msg="The HEX of the Activation code=" + self.activate_code_hex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
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

        if RECORD_MODEM_IMEI is True:
            self.record_modem_imei()
            msg(90, "Finish recording modem IMEI ...")

        msg(100, "Completing registration ...")
        self.close_fcd()


def main():
    factory_general = UMNRF52840FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()
