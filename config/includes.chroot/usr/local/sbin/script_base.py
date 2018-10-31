#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
from ubntlib.variable.helper import VariableHelper 
from ubntlib.fcd.helper import FCDHelper
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

class ScriptBase(object):
    def __init__(self):
        self.args = sys.argv
        log_debug(msg="Initial script with args: " + str(self.args[1:]))

        #shared variable object
        #example usuage - self.variable.common.xxx / self.variable.{toolspecific}.{variable}
        self.variable = VariableHelper(self.args[1:])
        self.fcd = FCDHelper()

        #shared pexpect object, instanced from class ExpttyProcess
        #must be set by set_pexpect_helper()
        #example usuage - self.pexpect.proc.send(...) / .sendline(...)
        self.__pexpect_obj = None
      

    @property
    def pexpect(self):
        if self.__pexpect_obj != None:
            return self.__pexpect_obj
        else:
            error_critical("No pexpect obj exists!")

    def set_pexpect_helper(self, pexpect_obj):
        self.__pexpect_obj = pexpect_obj
        self.fcd.set_pexpect_obj(pexpect_obj)

    def stop_uboot(self, timeout=30):
        if self.pexpect == None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexpect.expect2actu1(timeout=timeout, exptxt="Hit any key to stop autoboot", action="\r")
            self.pexpect.expect2actu1(timeout=timeout, exptxt=self.variable.common.bootloader_prompt, action="\r")

    def is_mdk_exist_in_uboot(self):
        is_exist = False
        log_debug(msg="Checking if MDK available in U-boot.")
        self.pexpect.proc.send('\r')
        self.pexpect.expect2actu1(timeout=30, exptxt=self.variable.common.bootloader_prompt, action="")
        time.sleep(1)
        self.pexpect.proc.sendline('mdk_drv')
        extext_list = ["Found MDK device", 
                       "Unknown command"]
        (index, _) = self.pexpect.expect_base(timeout=30, exptxt=extext_list, action="", get_result_index=True)
        if index == 0 :
            is_exist = True
        elif index == 1:
            is_exist = False
            self.pexpect.expect2actu1(timeout=30, exptxt=self.variable.common.bootloader_prompt, action="")
        return is_exist

    def sf_erase(self, address, erase_size):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string} 
        """
        log_debug(msg="Initializing sf => sf probe")
        self.pexpect_helper.proc.sendline('sf probe')
        self.pexpect_helper.expect2actu1(timeout=20, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")

        earse_cmd = "sf erase " + address + " " +erase_size
        log_debug(msg="run cmd " + earse_cmd)
        self.pexpect_helper.proc.sendline(earse_cmd)
        self.pexpect_helper.expect2actu1(timeout=20, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")

    def uclearcal(self, args="-f -e"):
        """
        run cmd in uboot: uclearcal {args}
        for wifi usage only
        """
        self.pexpect_helper.proc.sendline(self.variable_helper.common_variable.cmd_prefix + "uclearcal " + args)
        self.pexpect_helper.expect2actu1(timeout=20, exptxt="Done.", action="")
        self.pexpect_helper.expect2actu1(timeout=20, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
        log_debug(msg="Calibration Data erased")

    def login(self, username=None, password=None):
        """
        should be called at login console
        """
        if username == None or password == None:
            #No username/password input, using default account
            username = self.variable.common.user
            password = self.variable.common.password
        self.pexpect.proc.sendline(username)
        self.pexpect.expect2actu1(timeout=20, exptxt="Password:", action="")
        self.pexpect.proc.sendline(password)
        time.sleep(2)
