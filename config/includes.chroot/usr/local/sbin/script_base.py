#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
from ubntlib.fcd.common import Tee
from ubntlib.variable.helper import VariableHelper
from ubntlib.fcd.helper import FCDHelper
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class ScriptBase(object):
    def __init__(self):
        self.args = sys.argv
        # shared variable object
        # example usuage - self.variable.{toolspecific}.{variable}
        self.variable = VariableHelper(self.args)
        self._init_share_var()
        self.fcd = FCDHelper()
        self._init_log()
        # must be set by set_pexpect_helper()
        # example usuage - self.pexp.{function}(...)
        self.__pexpect_obj = None
        self.fcd.common.print_current_fcd_version(file=self.fcd_version_info_file_path)
        log_debug(msg="Initial script with args: " + str(self.args[1:]))

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
            log_file_path = os.path.join("/tftpboot/", "log_slot" + self.args[1] + ".log")
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
        self.firmware_dir = "images"
        self.tftp_server_dir = "/tftpboot"

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
