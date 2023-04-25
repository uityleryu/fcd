#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.pserial import SerialExpect
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.ssh_client import SSHClient
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info

import sys
import time
import os
import re
import traceback
import subprocess as sp
import glob
import pexpect

FWUPDATE_ENABLE     = False
PROVISION_ENABLE    = True
DOHELPER_ENABLE     = True
REGISTER_ENABLE     = True
DEVREG_CHECK_ENABLE = True
CERT_INSTALL        = True


class USWPUMA7MfgGeneral(ScriptBase):
    def __init__(self):
        super(USWPUMA7MfgGeneral, self).__init__()

        self.ver_extract()

        # script specific vars
        self.puma7_prompt = "mainMenu>"
        self.puma7_atom_prompt = "debug:~#"
        self.helperexe = "helper_PUMA7_ARM_release"
        self.helper_path = "usw_puma7"
        self.certs = "certs"
        self.devregpart = "/dev/disk/by-partlabel/EEPROM"
        self.dut_ip = "192.168.1.20"
        self.dut_default_ip = "192.168.100.1"
        self.username = "ubnt"
        self.password = "ubnt"
        self.mac_upper = self.mac.upper()
        self.certs_tftp_dir = os.path.join(self.tftpdir, self.certs)
        self.pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"

        self.proc = None
        self.newline = "\n"

        # number of Ethernet
        self.ethnum = {
            'ed60': "1",
        }

        # number of WiFi
        self.wifinum = {
            'ed60': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ed60': "0",
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def send_cmd_by_char(self, cmd):
        for s in cmd:
            self.proc.send(s)
            time.sleep(0.1)
        self.proc.send(self.newline)

    def send_wo_extra_newline(self, pre_exp, cmd, post_exp=None):
        if post_exp is None:
            self.proc.expect([pre_exp, pexpect.EOF, pexpect.TIMEOUT], 3)
            self.send_cmd_by_char(cmd)
        else:
            self.proc.expect([pre_exp, pexpect.EOF, pexpect.TIMEOUT], 3)
            self.send_cmd_by_char(cmd)
            self.proc.expect([post_exp, pexpect.EOF, pexpect.TIMEOUT], 3)

    def cert_erase(self):
        self.pexp.close()
        time.sleep(1)
        self.proc = pexpect.spawn(self.pexpect_cmd, encoding='utf-8', codec_errors='replace', timeout=2000)
        self.proc.logfile_read = sys.stdout
        self.proc.send(self.newline)

        cmd = "/etc/scripts/init/nss stop"
        self.send_wo_extra_newline(self.puma7_atom_prompt, cmd)

        cmd = "umount /nvram"
        self.send_wo_extra_newline(self.puma7_atom_prompt, cmd)

        cmd = "mkfs.ext3 /dev/disk/by-partlabel/APP_CPU_NVRAM"
        self.send_wo_extra_newline(self.puma7_atom_prompt, cmd)
        self.send_wo_extra_newline("(y,N)", "y", "Writing superblocks and filesystem accounting information: done")

        cmd = "mount /dev/disk/by-partlabel/APP_CPU_NVRAM /nvram/"
        self.send_wo_extra_newline(self.puma7_atom_prompt, cmd, "mounted filesystem with ordered data mode")

        cmd = "mkdir /nvram/itstore"
        self.send_wo_extra_newline(self.puma7_atom_prompt, cmd)

        cmd = "echo \"vendorId=0a\" > /nvram/sec_vendorId"
        self.send_wo_extra_newline(self.puma7_atom_prompt, cmd)
        self.proc.close()

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        self.fcd.common.config_stty(self.dev)
        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        msg(5, "Open serial port successfully ...")

        self.pexp.expect_lnxcmd(180, "Dual boot handshake is done", "", self.puma7_atom_prompt)
        # below 2 command lines to disable console message
        self.pexp.expect_lnxcmd(10, self.puma7_atom_prompt, "systemctl stop mcad", self.puma7_atom_prompt)
        self.pexp.expect_lnxcmd(10, self.puma7_atom_prompt, "systemctl stop lcmd", self.puma7_atom_prompt)

        msg(10, "Start to erase certificates ...")
        self.cert_erase()
        msg(100, "Erase complete ...")

        self.close_fcd()


def main():
    factory_general = USWPUMA7MfgGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()