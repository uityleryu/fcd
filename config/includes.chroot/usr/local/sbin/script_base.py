#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
import stat
import argparse
from ubntlib.fcd.common import Tee
from ubntlib.variable.helper import VariableHelper
from ubntlib.fcd.helper import FCDHelper
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class ScriptBase(object):
    def __init__(self):
        self.input_args = self._init_parse_inputs()
        # shared variable object
        # example usuage - self.variable.{toolspecific}.{variable}
        self.var = VariableHelper(self.input_args)
        self._init_share_var()
        self.fcd = FCDHelper()
        self._init_log()
        # must be set by set_pexpect_helper()
        # example usuage - self.pexp.{function}(...)
        self.__pexpect_obj = None
        self.fcd.common.print_current_fcd_version(file=self.fcd_version_info_file_path)
        log_debug(str(self.input_args))

    @property
    def pexp(self):
        if self.__pexpect_obj is not None:
            return self.__pexpect_obj
        else:
            error_critical("No pexpect obj exists!")

    def set_pexpect_helper(self, pexpect_obj):
        self.__pexpect_obj = pexpect_obj
        self.fcd.set_pexpect_obj(pexpect_obj)

    def _init_log(self, log_file_path=None):
        if log_file_path is None:
            log_file_path = os.path.join("/tftpboot/", "log_slot" + self.row_id + ".log")
        if os.path.isfile(log_file_path):
            os.remove(log_file_path)
        Tee(log_file_path, 'w')

    def _init_share_var(self):
        # prompt related
        self.bootloader_prompt = "u-boot>"
        self.linux_prompt = "#"
        self.cmd_prefix = r"go $ubntaddr "

        # DU log-in info
        self.user = "ubnt"
        self.password = "ubnt"

        # fcd related
        self.fcd_user = "user"
        self.fcd_version_info_file = "version.txt"
        self.fcd_version_info_file_path = os.path.join("/home", self.fcd_user, "Desktop", self.fcd_version_info_file)

        # images is saved at /tftpboot/images, tftp server searches files start from /tftpboot
        self.tftpdir = "/tftpboot"
        self.fwdir = self.tftpdir + "/images"
        self.toolsdir = self.tftpdir + "/tools"
        self.dut_tmpdir = "/tmp"
        self.devregpart = ""

        # EEPROM file in binary format generated by helper utility
        self.eebin = "e.b." + self.row_id

        # EEPROM file in text format generated by helper utility
        self.eetxt = "e.t." + self.row_id

        # compress EEPROM files
        self.eetgz = "e." + self.row_id + ".tgz"

        # Get the signed EEPROM from security server
        self.eesign = "e.s." + self.row_id

        # retrieve the content from EEPROM partition of DUT
        self.eechk = "e.c." + self.row_id

        # DUT IP
        baseip = 31
        self.dutip = "192.168.1." + str((int(self.row_id) + baseip))

        # The HEX of the QR code
        if self.qrcode is not None:
            self.qrhex = self.qrcode.encode('utf-8').hex()

    def _init_parse_inputs(self):
        parse = argparse.ArgumentParser(description="FCD tool args Parser")
        parse.add_argument('--slot', '-s', dest='row_id', help='Slot id', default=None)
        parse.add_argument('--dev', '-d', dest='dev', help='UART device number. ex:ttyUSB0, ttyUSB1', default=None)
        parse.add_argument('--tftp_server', '-ts', dest='tftp_server', help='FCD host IP', default=None)
        parse.add_argument('--board_id', '-b', dest='board_id', help='System ID, ex:eb23, eb21', default=None)
        parse.add_argument('--erasecal', '-e', dest='erasecal', help='Erase calibration data selection', default=None)
        parse.add_argument('--mac', '-m', dest='mac', help='MAC address', default=None)
        parse.add_argument('--pass_phrase', '-p', dest='pass_phrase', help='Passphrase', default=None)
        parse.add_argument('--key_dir', '-k', dest='key_dir', help='Directory of key files', default=None)
        parse.add_argument('--bom_rev', '-bom', dest='bom_rev', help='BOM revision', default=None)
        parse.add_argument('--qrcode', '-q', dest='qrcode', help='QR code', default=None)
        parse.add_argument('--region', '-r', dest='region', help='Region Code', default=None)

        args, _ = parse.parse_known_args()
        self.row_id = args.row_id
        self.dev = args.dev
        self.tftp_server = args.tftp_server
        self.board_id = args.board_id
        self.erasecal = args.erasecal
        self.mac = args.mac.lower()
        self.pass_phrase = args.pass_phrase
        self.key_dir = args.key_dir
        self.bom_rev = args.bom_rev
        self.qrcode = args.qrcode
        self.region = args.region
        self.fwimg = self.board_id + ".bin"
        self.fwimg_mfg = self.board_id + "-mfg.bin"
        return args

    def login(self, username=None, password=None):
        """
        should be called at login console
        """
        if username is None or password is None:
            # No username/password input, using default account
            username = self.user
            password = self.password
        self.pexp.expect_action(timeout=15, exptxt="login:", action=username)
        self.pexp.expect_action(timeout=15, exptxt="Password:", action=password)
        time.sleep(2)

    def set_bootloader_prompt(self, prompt=None):
        if prompt is not None:
            self.bootloader_prompt = prompt
        else:
            print("Nothing changed. Please assign prompt!")

    def erase_eefiles(self):
        tftpdir = self.tftpdir + "/"
        log_debug("Erase existed eeprom information files ...")
        files = [self.eebin, self.eetxt, self.eechk, self.eetgz]
        for f in files:
            rtf = os.path.isfile(tftpdir + f)
            if rtf is True:
                log_debug("Erasing File - " + f + " ...")
                os.chmod(tftpdir + f, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.remove(tftpdir + f)
            else:
                log_debug("File - " + f + " doesn't exist ...")

    def close_fcd(self):
        time.sleep(3)
        exit(0)

    def check_devreg_data(self):
        log_debug("Send signed eeprom file from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + self.dut_tmpdir + self.eesign,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            self.dut_tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            self.dut_tmpdir + helperexe,
            "-q",
            "-i field=flash_eeprom,format=binary,pathname=" + self.dut_tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + self.devregpart,
            "of=" + self.dut_tmpdir + self.eechk
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        os.mknod(tftpdir + self.eechk)
        os.chmod(tftpdir + self.eechk, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + self.eechk + " from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eechk,
            "-l " + self.dut_tmpdir + self.eechk,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
        time.sleep(1)

        if os.path.isfile(tftpdir + self.eechk):
            log_debug("Starting to compare the " + self.eechk + " and " + self.eesign + " files ...")
            rtc = filecmp.cmp(tftpdir + self.eechk, tftpdir + self.eesign)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            log_debug("Can't find the " + self.eechk + " and " + self.eesign + " files ...")
