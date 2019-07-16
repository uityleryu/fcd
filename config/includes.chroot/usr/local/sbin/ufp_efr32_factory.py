#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.pserial import SerialExpect
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical
from xmodem import XMODEM

import sys
import time
import os
import re
import stat

NEED_DROPBEAR = True
PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True


class UFPEFR32FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UFPEFR32FactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        # script specific vars
        self.bomrev = "113-" + self.bom_rev
        self.eepmexe = "x86-64k-ee"
        self.linux_prompt = "EH:"
        self.prodclass = "0014"
        self.dut_dhcp_ip = ""
        self.dut_port = ""

        # Base path
        self.toolsdir = "tools/"
        self.dut_dir = os.path.join(self.dut_tmpdir, "tools", "ufp_sense")
        self.host_dir = os.path.join(self.tftpdir, "tools", "ufp_sense")
        self.common_dir = os.path.join(self.tftpdir, "tools", "common")

        self.ncert = "cert_{0}.pem".format(self.row_id)
        self.nkey = "key_{0}.pem".format(self.row_id)
        self.nkeycert = "key_cert_{0}.bin".format(self.row_id)
        self.nkeycertchk = "key_cert_chk_{0}.bin".format(self.row_id)
        self.cert_path = os.path.join(self.tftpdir, self.ncert)
        self.key_path = os.path.join(self.tftpdir, self.nkey)
        self.keycert_path = os.path.join(self.tftpdir, self.nkeycert)
        self.keycertchk_path = os.path.join(self.tftpdir, self.nkeycertchk)
        self.flasheditor = os.path.join(self.common_dir, self.eepmexe)

        # number of Ethernet
        self.ethnum = {
            'a911': "0",
            'a912': "0"
        }

        # number of WiFi
        self.wifinum = {
            'a911': "0",
            'a912': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'a911': "1",
            'a912': "1",
        }

    def prepare_server_need_files(self):
        log_debug("Starting to create a 64KB binary file ...")
        self.gen_rsa_key()

        sstr = [
            self.flasheditor,
            "-F",
            "-f " + self.eebin_path,
            "-r " + self.bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Generating " + self.eebin_path + " file failed!!")
        else:
            log_debug("Generating " + self.eebin_path + " files successfully")

    def registration(self):
        log_debug("Starting to do registration ...")

        uid = self.ser.execmd_getmsg("GETUID")
        res = re.search(r"UNIQUEID:27-(.*)\n", uid, re.S)
        uids = res.group(1)

        cpuid = self.ser.execmd_getmsg("GETCPUID")
        res = re.search(r"CPUID:(.*)\n", cpuid, re.S)
        cpuids = res.group(1)

        jedecid = self.ser.execmd_getmsg("GETJEDEC")
        res = re.search(r"JEDECID:(.*)\n", jedecid, re.S)
        jedecids = res.group(1)

        cmd = [
            "sudo /usr/local/sbin/client_x86_release_20190507",
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            "-i field=product_class_id,format=hex,value=" + self.prodclass,
            "-i field=flash_jedec_id,format=hex,value=" + jedecids,
            "-i field=flash_uid,format=hex,value=" + uids,
            "-i field=cpu_rev_id,format=hex,value=" + cpuids,
            "-i field=qr_code,format=hex,value=" + self.qrhex,
            "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
            "-i field=fcd_id,format=hex,value=" + self.fcd_id,
            "-i field=fcd_version,format=hex,value=" + self.sem_ver,
            "-i field=sw_id,format=hex,value=" + self.sw_id,
            "-i field=sw_version,format=hex,value=" + self.fw_ver,
            "-o field=flash_eeprom,format=binary,pathname=" + self.eesign_path,
            "-o field=registration_id",
            "-o field=result",
            "-o field=device_id",
            "-o field=registration_status_id",
            "-o field=registration_status_msg",
            "-o field=error_message",
            "-x " + self.key_dir + "ca.pem",
            "-y " + self.key_dir + "key.pem",
            "-z " + self.key_dir + "crt.pem"
        ]

        cmdj = ' '.join(cmd)

        clit = ExpttyProcess(self.row_id, cmdj, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        cmd[2] = "-k " + self.input_args.pass_phrase
        poscmd = ' '.join(cmd)
        print("CMD: \n" + poscmd)

        log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign_path)

        log_debug("Add the date code in the devreg binary file")
        sstr = [
            self.flasheditor,
        ]

    def check_devreg_data(self):
        log_debug("DUT request the signed 64KB file ...")
        self.ser.execmd_expect("xstartdevreg", "begin upload")

        log_debug("Starting xmodem file transfer ...")
        modem = XMODEM(self.ser.xmodem_getc, self.ser.xmodem_putc, mode='xmodem1k')
        stream = open(self.eesign_path, 'rb')
        modem.send(stream, retry=64)

    def check_info(self):
        pass

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        serialcomport = "/dev/{0}".format(self.dev)
        serial_obj = SerialExpect(port=serialcomport, baudrate=115200)
        self.set_serial_helper(serial_obj=serial_obj)
        time.sleep(1)

        msg(5, "Open serial port successfully ...")
        self.ser.expect_only("Protect Sensor APP STARTUP", 60)
        self.ser.execmd("")

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        udm_factory_general = UFPEFR32FactoryGeneral()
        udm_factory_general.run()

if __name__ == "__main__":
    main()
