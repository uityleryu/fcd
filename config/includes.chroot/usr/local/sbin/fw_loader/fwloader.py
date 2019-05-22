#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import threading
import pexpect

from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

try:
        sys.path.remove(str(parent))
except ValueError:
        pass

from ubntlib.Commonlib import *

login_account = "ubnt"
login_passwd = "ubnt"

re_promt = r'UBNT-.+\..+#'

tftpdir = "/tftpboot/"
svip = "192.168.1.19"


class fwloader():
    def __init__(self, boardid, mac, ip, loadcnt):
        # self.configuration = DHCPServerConfiguration()
        # # self.configuration.debug = print
        # # self.configuration.ip_address_lease_time = dhcp_leasetime
        # # self.dhcpsrv = DHCPServer(self.configuration)
        self.boardid = boardid
        self.devmac = mac
        self.devip = ip
        self.loadcnt = int(loadcnt)

    def sshlogin(self, prompt):
        time_wait_ssh = 15
        print("Loging via ssh after %d sec" % time_wait_ssh)
        time.sleep(time_wait_ssh)

        print("Connecting to device => mac={} ip={}".format(self.devmac, self.devip))
        self.conn = ExpttyProcess(0, "sudo ssh -o \"StrictHostKeyChecking=no \" \
                                               -o \"UserKnownHostsFile=/dev/null \" \
                                               {}@{}".format(login_account, self.devip), "\n")

        self.conn.expect2act(30, '{}@{}\'s password:'.format(login_account, self.devip), login_passwd)
        self.conn.expect2act(30, prompt, "")

    def ckburninflag(self, prompt):
        # check burnin flag
        rtbuf = []
        self.conn.expect2actnrd(5, prompt, "cat /tmp/system.cfg | grep burnin.status", rtbuf)
        if len(rtbuf) != 1:
            error_critical("Unfinished factory reset => mac={} ip={}".format(self.devmac, self.devip))

    def xsferfile(self, prompt):
        # fwimg = "images/"+self.boardid+"/fw/"+self.boardid+".bin"
        fwimg = self.boardid+".bin"
        [md5sum, rtc] = xcmd("md5sum " + tftpdir + fwimg + " | " + "awk '{printf($1)}'")
        if (int(rtc) > 0):
            error_critical("Get md5sum of FW img in host failed!!")
        else:
            md5sum = md5sum.decode('utf-8')
            print("md5sum of FW img = {}".format(md5sum))

        # transfer fw img vi tftp
        cmd = ["tftp",
               "-g",
               "-r",
               fwimg,
               svip]
        cmd = ' '.join(cmd)

        self.conn.expect2act(5, prompt, "cd /tmp")
        self.conn.expect2act(5, prompt, cmd)

        # check fw md5sum in device
        rtbuf = []
        self.conn.expect2actnrd(60, prompt, "md5sum " + self.boardid+".bin|awk '{printf(\"%s\\n\",$1)}'", rtbuf)

        if rtbuf[1] != md5sum:
            error_critical("md5sum of FW in device is incorrect")
        else:
            print("md5sum of FW in device is correct")

        self.conn.expect2act(5, prompt, "mv {}.bin fwupdate.bin".format(self.boardid))

    def fwupdate(self, prompt):
        print("Starting fw update =>  mac={} ip={}".format(self.devmac, self.devip))
        self.conn.expect2act(5, prompt, "syswrapper.sh upgrade2 &")

        print("Waiting for updating done => mac={} ip={}".format(self.devmac, self.devip))
        self.conn.expect2act(180, "Done")
        time.sleep(5)

    def showInfo(self, prompt):
        rtbuf = []
        self.conn.expect2actnrd(5, prompt, "info", rtbuf)

    def start(self):

        progval_base = (self.loadcnt-1) * 40
        prompt = re_promt

        if self.loadcnt != 3:
            msg(str(10+progval_base), "Connecting via ssh to devices for the {} time".format(self.loadcnt))
            self.sshlogin(prompt)

            msg(str(20+progval_base), "Transferring fw image for the {} time".format(self.loadcnt))
            self.xsferfile(prompt)

            msg(str(30+progval_base), "Updating fw image for the {} time".format(self.loadcnt))
            self.fwupdate(prompt)

            msg(str(40+progval_base), "Completed FW loading for the {} time".format(self.loadcnt))
        else:
            msg(100, "Connecting via ssh to devices for the {} time".format(self.loadcnt))
            self.sshlogin(prompt)
            self.showInfo(prompt)


def main():
    boardid = sys.argv[1]
    devmac = sys.argv[2]
    devip = sys.argv[3]
    loadcnt = sys.argv[4]
    print("\n\n\nStarting Firmware Loading\n")
    print("The info of devices is bid = {} mac = {} "
          "ip = {} loadcnt = {}".format(boardid, devmac, devip, loadcnt))

    fwldr = fwloader(boardid, devmac, devip, loadcnt)
    fwldr.start()

    if fwldr.loadcnt < 3:
        exit(3)
    else:
        exit(0)

if __name__ == "__main__":
    main()
