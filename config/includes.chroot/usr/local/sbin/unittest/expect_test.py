import os
import sys
from nose import with_setup 
from nose.tools import *
import pexpect
from ubntlib.fcd.expect_tty import ExpttyProcess

class TestExpttyProcess():

    @classmethod
    def setup_class(cls):
        print("TestExpttyProcess:setup_class()")
        tty = os.getenv('DUT_TTY', '')
        pexpect_cmd = "sudo picocom " + tty + " -b 115200"
        cls.pexpect_obj = ExpttyProcess(0, pexpect_cmd, "\n")

    @classmethod
    def teardown_class(cls):
        print ("TestExpttyProcess:teardown_class()")
        pass

    def test_01_import(cls):
        from ubntlib.fcd.expect_tty import ExpttyProcess

    def test_02_exptty(cls):
        pass

    def test_11_expect_ubcmd(cls):
        assert cls.pexpect_obj != None
        cls.pexpect_obj.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")

    @timed(15)
    @raises(pexpect.ExceptionPexpect)
    def test_11_expect_ubcmd_nofound(cls):
        cls.pexpect_obj.expect_ubcmd(3, "RRRRRRR", "CC")

    def test_12_expect_only(cls):
        cls.pexpect_obj.expect_ubcmd(10, "\(IPQ40xx\) # ", "version")
        cls.pexpect_obj.expect_only(10, "U-Boot")

    @timed(4)
    @raises(pexpect.ExceptionPexpect)
    def test_12_expect_only_nofound(cls):
        cls.pexpect_obj.expect_only(3, "RRRRRRR")

    def test_13_expect_action(cls):
        cls.pexpect_obj.expect_ubcmd(10, "\(IPQ40xx\) # ", "re")
        cls.pexpect_obj.expect_action(120, "Please press Enter to activate this console. ", "\n")
        cls.pexpect_obj.expect_action(60, "GigaBeam login: ", "ubnt")
        cls.pexpect_obj.expect_action(60, "Password: ", "ubnt")

    @raises(pexpect.ExceptionPexpect)
    def test_13_expect_action_nofound(cls):
        cls.pexpect_obj.expect_action(10, "RRRRRRR", "ubnt")

    def test_21_expect_lnxcmd(cls):
        cls.pexpect_obj.expect_lnxcmd(10, "GBE# ", "uname")

    @timed(16)
    @raises(pexpect.ExceptionPexpect)
    def test_21_expect_lnxcmd_nofound(cls):
        cls.pexpect_obj.expect_lnxcmd(3, "RRRRRRR", "uname")

    @timed(8)
    @raises(pexpect.ExceptionPexpect)
    def test_21_expect_lnxcmd_nofound_retry1(cls):
        cls.pexpect_obj.expect_lnxcmd(3, "RRRRRRR", "uname", retry=1)

    def test_21_expect_lnxcmd_valid_chk(cls):
        cls.pexpect_obj.expect_lnxcmd(10, "GBE# ", "ls", valid_chk=True)

    @timed(16)
    @raises(pexpect.ExceptionPexpect)
    def test_21_expect_lnxcmd_valid_chk_failed(cls):
        cls.pexpect_obj.expect_lnxcmd(10, "GBE# ", "NNNNNNN", valid_chk=True)

    @timed(8)
    @raises(pexpect.ExceptionPexpect)
    def test_21_expect_lnxcmd_valid_chk_failed_retry1(cls):
        cls.pexpect_obj.expect_lnxcmd(10, "GBE# ", "NNNNNNN", valid_chk=True, retry=1)


    def test_31_expect_get_output(cls):
        output = cls.pexpect_obj.expect_get_output("uname", "GBE# ")
        assert "Linux" in output

    def test_32_expect_get_index_found(cls):
        cls.pexpect_obj.expect_ubcmd(10, "GBE# ", "cat /proc/meminfo")
        exp_list = [
            "AAAAAAA",
            "BBBBBBB",
            "AnonPages:",
            "Kernel command line"
        ]
        index = cls.pexpect_obj.expect_get_index(timeout=30, exptxt=exp_list)
        assert index == 2

    def test_32_expect_get_index_nofound(cls):
        cls.pexpect_obj.expect_ubcmd(10, "GBE# ", "free")
        exp_list = [
            "AAAAAAA",
            "BBBBBBB",
            "Linux version",
            "Kernel command line"
        ]
        index = cls.pexpect_obj.expect_get_index(timeout=30, exptxt=exp_list)
        assert index == -1


