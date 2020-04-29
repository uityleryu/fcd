import os
import sys
from nose import with_setup 
from ubntlib.fcd.expect_tty import ExpttyProcess

class TestExpttyProcess():

    @classmethod
    def setup_class(cls):
        print("TestExpttyProcess:setup_class()")
        pexpect_cmd = "sudo picocom /dev/ttyUSB0 -b 115200"
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
        pass

    def test_12_expect_only(cls):
        cls.pexpect_obj.expect_ubcmd(10, "\(IPQ40xx\) # ", "version")
        cls.pexpect_obj.expect_only(10, "U-Boot")
        pass

    def test_13_expect_action(cls):
        cls.pexpect_obj.expect_ubcmd(10, "\(IPQ40xx\) # ", "re")
        cls.pexpect_obj.expect_action(120, "Please press Enter to activate this console. ", "\n")
        cls.pexpect_obj.expect_action(60, "GigaBeam login: ", "ubnt")
        cls.pexpect_obj.expect_action(60, "Password: ", "ubnt")
        
        pass

    def test_21_expect_lnxcmd(cls):
        cls.pexpect_obj.expect_ubcmd(10, "GBE# ", "uname")
        pass

    def test_31_expect_get_index(cls):
        pass

    def test_32_expect_get_output(cls):
        output = cls.pexpect_obj.expect_get_output("uname", "GBE# ")
        assert "Linux" in output
        pass