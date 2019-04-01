#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
import stat
import filecmp
import argparse

from ubntlib.fcd.common import Tee
from ubntlib.variable.helper import VariableHelper
from ubntlib.fcd.helper import FCDHelper
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class ScriptBase(object):
    def __init__(self):
        self.input_args = self._init_parse_inputs()
        # shared variable object
        # example usuage - self.var.{toolspecific}.{variable}
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
        self.image = "images"
        self.fwdir = os.path.join(self.tftpdir, self.image)
        self.tools = "tools"
        self.fcd_toolsdir = os.path.join(self.tftpdir, self.tools)
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

        # EEPROM related files path on FCD
        self.eebin_path = os.path.join(self.tftpdir, self.eebin)
        self.eetxt_path = os.path.join(self.tftpdir, self.eetxt)
        self.eetgz_path = os.path.join(self.tftpdir, self.eetgz)
        self.eesign_path = os.path.join(self.tftpdir, self.eesign)
        self.eechk_path = os.path.join(self.tftpdir, self.eechk)


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
        self.row_id = args.row_id if args.row_id is not None else "0"
        self.dev = args.dev
        self.tftp_server = args.tftp_server
        self.board_id = args.board_id if args.board_id is not None else "na"
        self.erasecal = args.erasecal
        self.mac = args.mac.lower() if args.mac is not None else args.mac
        self.pass_phrase = args.pass_phrase
        self.key_dir = args.key_dir
        self.bom_rev = args.bom_rev
        self.qrcode = args.qrcode
        self.region = args.region
        self.fwimg = self.board_id + ".bin"
        self.fwimg_mfg = self.board_id + "-mfg.bin"
        return args

    def login(self, username=None, password=None, timeout=None):
        """
        should be called at login console
        """
        if username is None or password is None:
            # No username/password input, using default account
            username = self.user
            password = self.password

        if timeout is not None:
            tout = timeout
        else:
            tout = 15

        self.pexp.expect_action(timeout=tout, exptxt="login:", action=username)
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

    def check_devreg_data(self, dut_tmp_subdir=None):
        """check devreg data
        in default we assume the datas under /tmp on dut
        but if there is sub dir in your tools.tar, you should set dut_subdir

        you MUST make sure there is eesign file under /tftpboot

        Keyword Arguments:
            dut_subdir {[str]} -- like udm, unas, afi_aln...etc, take refer to structure of fcd-script-tools repo
        """
        log_debug("Send signed eeprom file from host to DUT ...")
        eechk_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eechk) if dut_tmp_subdir is not None \
            else os.path.join(self.dut_tmpdir, self.eechk)
        eesign_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eesign) if dut_tmp_subdir is not None \
            else os.path.join(self.dut_tmpdir, self.eesign)
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + eesign_dut_path,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, sstrj, post_exp=self.linux_prompt)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            eesign_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, sstrj, post_exp=self.linux_prompt)

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            "dd",
            "if=" + eesign_dut_path,
            "of=" + self.devregpart
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, sstrj, post_exp=self.linux_prompt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + self.devregpart,
            "of=" + eechk_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, sstrj, post_exp=self.linux_prompt)

        os.mknod(self.eechk_path)
        os.chmod(self.eechk_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + self.eechk + " from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eechk,
            "-l " + eechk_dut_path,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, sstrj, post_exp=self.linux_prompt)
        time.sleep(3)  # in case the e.c.0 is still in transfering
        if os.path.isfile(self.eechk_path):
            log_debug("Starting to compare the " + self.eechk + " and " + self.eesign + " files ...")
            rtc = filecmp.cmp(self.eechk_path, self.eesign_path)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            log_debug("Can't find the " + self.eechk + " and " + self.eesign + " files ...")

    def is_dutfile_exist(self, filename):
        """check if file exist on dut by ls cmd

        Arguments:
            filename {[str]}

        Returns:
            [bool]
        """
        sstr = [
            "ls",
            filename
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj, post_exp=self.linux_prompt)
        idx = self.pexp.expect_get_index(10, "No such file")
        if idx == 0:
            log_debug("Can't find the " + filename)
            return False
        else:
            return True

    def copy_and_unzipping_tools_to_dut(self, timeout=15):
        log_debug("Send tools.tar from host to DUT ...")
        source = os.path.join(self.tools, "tools.tar")
        target = os.path.join(self.dut_tmpdir, "tools.tar")
        sstr = [
            "tftp",
            "-g",
            "-r " + source,
            "-l " + target,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=sstrj, post_exp=self.linux_prompt)
        log_debug("Unzipping the tools.tar in the DUT ...")

        self.is_dutfile_exist(target)
        sstr = [
            "tar",
            "-xzvf",
            target,
            "-C " + self.dut_tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=sstrj, post_exp=self.linux_prompt)

    def is_network_alive_in_linux(self):
        time.sleep(3)
        self.pexp.expect_action(timeout=10, exptxt="", action="\nifconfig;ping " + self.tftp_server)
        extext_list = ["ping: sendto: Network is unreachable",
                       r"64 bytes from " + self.tftp_server]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == 0 or index == self.pexp.TIMEOUT:
            self.pexp.expect_action(timeout=10, exptxt="", action="\003")
            return False
        elif index == 1:
            self.pexp.expect_action(timeout=10, exptxt="", action="\003")
            return True
