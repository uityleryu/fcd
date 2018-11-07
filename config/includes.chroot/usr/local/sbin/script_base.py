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
        #example usuage - self.pexpect.proc.{function}(...)
        self.__pexpect_obj = None
      

    @property
    def pexp(self):
        if self.__pexpect_obj != None:
            return self.__pexpect_obj
        else:
            error_critical("No pexpect obj exists!")

    def set_pexpect_helper(self, pexpect_obj):
        self.__pexpect_obj = pexpect_obj
        self.fcd.set_pexpect_obj(pexpect_obj)

    def login(self, username=None, password=None):
        """
        should be called at login console
        """
        if username == None or password == None:
            #No username/password input, using default account
            username = self.variable.common.user
            password = self.variable.common.password
        self.pexp.expect_action(timeout=15, exptxt="login:", action=username)
        self.pexp.expect_action(timeout=15, exptxt="Password:", action=password)
        time.sleep(2)
