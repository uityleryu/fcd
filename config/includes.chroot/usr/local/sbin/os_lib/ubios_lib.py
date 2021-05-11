#!/usr/bin/python3

import time, os
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class UbiOSLib(object):
    def __init__(self, ubios_obj):
        self.ubios_obj = ubios_obj
        self.username = "root"
        self.password = "ubnt"

    def fwupdate(self):
        log_debug("Transfer fw image ... ")
        self.ubios_obj.scp_get(dut_user=self.username, dut_pass=self.password, dut_ip=self.ubios_obj.dutip, 
                               src_file=os.path.join(self.ubios_obj.fwdir, self.ubios_obj.fwimg),
                               dst_file=self.ubios_obj.dut_tmpdir + "/upgrade.bin")

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "sh",
            "/usr/bin/ubnt-upgrade",
            "-d",
            self.ubios_obj.dut_tmpdir + "/upgrade.bin"
        ]
        sstr = ' '.join(sstr)

        postexp = [ "Starting kernel" ]

        self.ubios_obj.pexp.expect_lnxcmd(300, self.ubios_obj.linux_prompt, sstr, postexp, retry=0)

    def check_info(self):
        self.ubios_obj.pexp.expect_lnxcmd(5, self.ubios_obj.linux_prompt, "info", 
                                          self.ubios_obj.infover[self.ubios_obj.board_id], retry=12)
        self.ubios_obj.pexp.expect_lnxcmd(10, self.ubios_obj.linux_prompt, "cat /proc/ubnthal/system.info")
        self.ubios_obj.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.ubios_obj.pexp.expect_only(10, "systemid=" + self.ubios_obj.board_id)
        self.ubios_obj.pexp.expect_only(10, "serialno=" + self.ubios_obj.mac.lower())
        self.ubios_obj.pexp.expect_only(10, self.ubios_obj.linux_prompt)  
