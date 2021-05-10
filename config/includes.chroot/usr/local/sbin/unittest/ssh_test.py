import os
import sys
import hashlib
from nose import with_setup 
from nose.tools import *
import pexpect
from PAlib.FrameWork.fcd.ssh_client import SSHClient
import paramiko
import socket

ssh = None

class TestSSHClient():

    @classmethod
    def setup_class(cls):
        print("TestSSHClient:setup_class()")
        
        cls.host = os.getenv('DUT_IP', '')

    @classmethod
    def teardown_class(cls):
        print ("TestSSHClient:teardown_class()")
        pass

    def test_01_import(cls):
        from PAlib.FrameWork.fcd.ssh_client import SSHClient

    def test_02_construct(cls):
        global ssh
        ssh = SSHClient(host=cls.host, username="ubnt", password="ubnt")
        assert ssh != None

    @raises(paramiko.ssh_exception.AuthenticationException)
    def test_02_construct_fail(cls):
        global ssh
        ssh = SSHClient(host=cls.host, username="aaaa", password="ubnt")
        assert ssh != None


    def test_11_execmd(cls):
        ret = ssh.execmd("uptime")
        assert ret == 0

    def test_11_execmd_get_exit_val_err(cls):
        ret = ssh.execmd("babalalalalba")
        assert ret == 127

    def test_11_execmd_get_exit_val_false(cls):
        ret = ssh.execmd("babalalalalba", get_exit_val=False)
        assert ret == None

    @timed(4)
    @raises(paramiko.ssh_exception.SSHException)
    def test_11_execmd_timeout(cls):
        ret = ssh.execmd("sleep 10", timeout=3)

    def test_12_execmd_getmsg(cls):
        ret = ssh.execmd_getmsg("uname")
        assert "Linux" in ret

    @timed(4)
    @raises(socket.timeout)
    def test_12_execmd_getmsg_timeout(cls):
        ret = ssh.execmd_getmsg("sleep 10", timeout=3)

    def test_12_execmd_getmsg_stderr(cls):
        ret = ssh.execmd_getmsg("babalalalalba", stderr=True)
        assert len(ret) == 2
        assert "not found" in ret[1]
        
        ret = ssh.execmd_getmsg("babalalalalba", stderr=False)
        assert ret == ''

    def test_12_execmd_getmsg_get_all(cls):
        ret = ssh.execmd_getmsg("babalalalalba", get_all=True)
        assert len(ret) == 3
        assert "not found" in ret[2]


    def test_13_execmd_expect(cls):
        ret = ssh.execmd_expect("cat /proc/meminfo", "MemTotal:")
        assert ret == True

        ret = ssh.execmd_expect("cat /proc/meminfo", "RRRRRRRRR:")
        assert ret == False

    def test_14_execmd_expect_get_index(cls):
        exp_list = [
            "AAAAAAA",
            "BBBBBBB",
            "AnonPages:",
            "Kernel command line"
        ]
        ret = ssh.execmd_expect_get_index("cat /proc/meminfo", exp_list)
        assert ret == 2

        exp_list = [
            "AAAAAAA",
            "BBBBBBB",
            "Kernel command line"
        ]
        ret = ssh.execmd_expect_get_index("cat /proc/meminfo", exp_list)
        assert ret == -1

    def test_15_execmd_interact(cls):
        pass

    def test_21_put_file(cls):
        ssh.put_file("/usr/local/sbin/client_x86_release" , "/tmp/client")
        md5sum = hashlib.md5(open("/usr/local/sbin/client_x86_release", 'rb').read()).hexdigest()
        ret = ssh.execmd_getmsg("md5sum /tmp/client")
        assert md5sum in ret

    def test_22_get_file(cls):
        ssh.get_file("/tmp/client" , "/tmp/AAAAA")
        md5sum = hashlib.md5(open("/tmp/AAAAA", 'rb').read()).hexdigest()
        ret = ssh.execmd_getmsg("md5sum /tmp/client")
        assert md5sum in ret
