
#!/usr/bin/python3

import sys
import time
import os
import re
import traceback
import base64
import zlib

from script_base import ScriptBase
from PAlib.Framework.fcd.pserial_v2 import SerialExpect
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info
from xmodem import XMODEM
from pprint import pformat
from collections import OrderedDict


DOHELPER_ENABLE = True
REGISTER_ENABLE = True


class UTMOVEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UTMOVEFactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        # script specific vars
        self.linux_prompt = "&"

        # The product class is Basic-4K, value = 21(decimal), 0x15(hex), defined by Mike.Taylor
        self.prodclass = "0015"

        self.baudrate = 921600
        self._reseted_flag = False

        # number of Ethernet
        self.ethnum = {
            'ec1f': "0"
        }

        # number of WiFi
        self.wifinum = {
            'ec1f': "1"
        }

        # number of Bluetooth
        self.btnum = {
            'ec1f': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def prepare_server_need_files(self):
        log_debug("Starting to get CPUID, flash_JEDECID, Flash_UID ...")
        dutinfo_path = os.path.join(self.tftpdir, "dut_info.txt")
        cmd = "cat {}".format(dutinfo_path)
        [rtmsg, rtc] = self.cnapi.xcmd(cmd)

        m_flashuid = re.findall(r"FLASHUID: ([a-fA-F0-9]{16})", rtmsg)
        if m_flashuid:
            self.uid = m_flashuid[0]
        else:
            error_critical("Can't read the flash UID message")

        m_cpuid = re.findall(r"CPUID: ([0-9]{8})", rtmsg)
        if m_cpuid:
            self.cpuid = m_cpuid[0]
        else:
            error_critical("Can't read the CPUID message")

        m_jedecid = re.findall(r"JEDEC: ([a-fA-F0-9]{8})", rtmsg)
        if m_jedecid:
            self.jedecid = m_jedecid[0]
        else:
            error_critical("Can't read the flash JEDECID message")

    def registration(self):
        log_debug("Starting to do registration ...")
        clientbin = "/usr/local/sbin/client_rpi4_release"
        devreg_server = "prod.udrs.io"

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value={}".format(self.qrhex)

        cmd = [
            "sudo {}".format(clientbin),
            "-h {}".format(devreg_server),
            "-k {}".format(self.pass_phrase),
            reg_qr_field,
            "-i field=product_class_id,format=hex,value={}".format(self.prodclass),
            "-i field=flash_jedec_id,format=hex,value={}".format(self.jedecid),
            "-i field=flash_uid,format=hex,value={}".format(self.uid),
            "-i field=cpu_rev_id,format=hex,value={}".format(self.cpuid),
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
            "-x {}{}".format(self.key_dir, "ca.pem"),
            "-y {}{}".format(self.key_dir,"key.pem"),
            "-z {}{}".format(self.key_dir,"crt.pem")
        ]
        cmd = ' '.join(cmd)
        log_debug('cmd: \n{}'.format(cmd))

        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Security Service Device Registration Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            rmsg = "Can't find {}".foramt(self.eesign_path)
            error_critical(rmsg)

        log_debug("Add the date code in the devreg binary file")

    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.print_current_fcd_version()

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Finish erasing ee files ...")
            self.data_provision_4k(self.devnetmeta)
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")

        msg(100, "Completing registration ...")
        self.close_fcd()

def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        factory = UTMOVEFactoryGeneral()
        factory.run()


if __name__ == "__main__":

    try:
        main()
    except Exception:
        error_critical(traceback.format_exc())

