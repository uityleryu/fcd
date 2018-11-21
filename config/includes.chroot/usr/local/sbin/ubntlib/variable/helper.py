#!/usr/bin/python3
from lazy import lazy
from ubntlib.variable.common import CommonVariable
from ubntlib.variable.us_mfg_variable import USMFG
from ubntlib.variable.us_factory_variable import USFactory


class VariableHelper(object):
    def __init__(self, args):
        self.args = args

    @lazy
    def common(self):
        instance = CommonVariable()
        return instance

    @lazy
    def us_mfg(self):
        instance = USMFG(self.args)
        return instance

    @lazy
    def us_factory(self):
        instance = USFactory(self.args)
        return instance

