#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
from ubntlib.variable.variable_helper import VariableHelper 
from ubntlib.Commonlib import log_debug, log_error, msg, error_critical, pcmd, xcmd


class ScriptBase(object):
    def __init__(self):
        self.args = sys.argv
        print("Initial script with args: " + str(self.args[1:]))

        #shared variable object
        #example usuage - self.variable_helper.common_variable.xxx / self.variable_helper.{toolspecific}_variable.xxx
        self.__variable_obj = VariableHelper(self.args[1:])
        
        #shared pexpect object, instanced from class ExpttyProcess
        #example usuage - self.pexpect_helper.proc.send(...) / .sendline(...)
        self.__pexpect_obj = None

    @property
    def variable_helper(self):
        return self.__variable_obj

    @property
    def pexpect_helper(self):
        if self.__pexpect_obj != None:
            return self.__pexpect_obj
        else:
            error_critical("No pexpect obj exists!")

    def set_variable_helper(self, variable_helper):
        self.__variable_obj = variable_helper

    def set_pexpect_helper(self, pexpect_helper):
        self.__pexpect_obj = pexpect_helper

    def config_stty(self, dev=None):
        """
        config stty to 777 and set output to /dev/{dev}
        """
        if dev is None:
            error_critical(msg="dev is not assigned")
        else:
            cmd = "sudo chmod 777 /dev/" + dev
            [_, returncode] = xcmd(cmd)
            if (int(returncode) > 0):
                error_critical("Can't set tty to 777 failed!!")
            else:
                log_debug("Configure tty to 777 successfully")
        
            time.sleep(0.5)

            cmd = "stty -F /dev/" + dev +" sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
            [_, returncode] = xcmd(cmd)
            if (int(returncode) > 0):
                error_critical("stty configuration failed!!")
            else:
                log_debug("Configure stty successfully")

            time.sleep(0.5)

    def print_current_fcd_version(self, file=None):
        out_log = "Using default file "+ self.variable_helper.common_variable.fcd_version_info_file_path if file is None else \
                "Using file " + file
        file = self.variable_helper.common_variable.fcd_version_info_file_path if file is None else file
        msg(no="", out=out_log)
        f = open(file, "r")
        line = f.readline()
        msg(no="", out="FCD version: " + line) 
        f.close()

    def stop_uboot(self, timeout=30):
        if self.pexpect_helper == None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexpect_helper.expect2actu1(timeout=timeout, exptxt="Hit any key to stop autoboot", action="\r")
            self.pexpect_helper.expect2actu1(timeout=timeout, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="\r")

    def is_mdk_exist_in_uboot(self):
        is_exist = False
        log_debug(msg="Checking if MDK available in U-boot.")
        self.pexpect_helper.proc.send('\r')
        self.pexpect_helper.expect2actu1(timeout=30, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
        time.sleep(1)
        self.pexpect_helper.proc.sendline('mdk_drv')
        extext_list = ["Found MDK device", 
                       "Unknown command"]
        (index, _) = self.pexpect_helper.expect_base(timeout=30, exptxt=extext_list, action="", get_result_index=True)
        if index == 0 :
            is_exist = True
        elif index == 1:
            is_exist = False
            self.pexpect_helper.expect2actu1(timeout=30, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
        return is_exist

    def sf_erase(self, address, erase_size):
        """
        run [sf erase address erase_size]
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

    def login(self, username=None, password=None):
        """
        should be called at login console
        """
        if username == None or password == None:
            #No username/password input, using default account
            username = self.variable_helper.common_variable.user
            password = self.variable_helper.common_variable.password
        self.pexpect_helper.proc.sendline(username)
        self.pexpect_helper.expect2actu1(timeout=20, exptxt="Password:", action="")
        self.pexpect_helper.proc.sendline(password)
        time.sleep(2)
