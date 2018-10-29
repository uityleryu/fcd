#!/usr/bin/python3
from lazy import lazy
from ubntlib.variable.common_variable import CommonVariable
from ubntlib.variable.mfg_broadcom_variable import MFGBroadcomVariable
from ubntlib.variable.reg_broadcom_variable import RegBroadcomVariable

class VariableHelper(object):

    def __init__(self, args):
        self.args = args

    @lazy
    def common_variable(self):
        instance = CommonVariable(self.args)
        return instance

    @lazy
    def mfg_broadcom(self):
        instance =  MFGBroadcomVariable(self.args)
        return instance

    @lazy
    def reg_boradcom(self):
        """Under developing"""
        instance =  RegBroadcomVariable(self.args)
        return instance

