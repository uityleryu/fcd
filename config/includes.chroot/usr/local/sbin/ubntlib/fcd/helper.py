#!/usr/bin/python3
from lazy import lazy
from ubntlib.fcd.common import Common
from ubntlib.fcd.uboot import Uboot

class FCDHelper(object):
    def __init__(self):
        self.__pexpect_obj = None

    def set_pexpect_obj(self, pexpect_obj):
        self.__pexpect_obj = pexpect_obj

    @lazy
    def common(self):
        instance = Common()
        return instance

    @lazy
    def uboot(self):
        instance =  Uboot(self.__pexpect_obj)
        return instance


