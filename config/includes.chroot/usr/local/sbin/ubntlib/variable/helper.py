#!/usr/bin/python3
from lazy import lazy
from ubntlib.variable.us_variable import US


class VariableHelper(object):
    def __init__(self, args):
        self.args = args

    @lazy
    def us(self):
        instance = US(self.args)
        return instance
