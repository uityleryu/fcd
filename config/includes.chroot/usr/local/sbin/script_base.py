#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
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
        self.mac = args.mac
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
