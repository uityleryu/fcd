#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

import sys
import time
import os


class USM487_MFG(ScriptBase):
    def __init__(self):
        super(USM487_MFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.linux_prompt = "/>"

    def set_ipaddr(self):
        self.pexp.expect_action(10, self.linux_prompt, "ip down")
        self.pexp.expect_only(20, "Service Stopped")
        self.pexp.expect_action(10, self.linux_prompt, "setenv ipaddr {}".format(self.dutip), send_action_delay=True)
        self.pexp.expect_action(10, self.linux_prompt, "setenv dhcp_enable 0", send_action_delay=True)
        self.pexp.expect_action(10, self.linux_prompt, "ip up")
        self.pexp.expect_only(20, "Service Started")
        time.sleep(5)

    def check_info(self):
        self.pexp.expect_only(80, "Send normal inform to")  # ensure devreg thread is started
        self.pexp.expect_action(10, "", "")
        out = self.pexp.expect_get_output("version", self.linux_prompt, 20)
        log_debug("FW version: "+out)

    def reset_env(self):
        self.pexp.expect_action(10, self.linux_prompt, "resetenv")
        self.pexp.expect_action(10, self.linux_prompt, "saveenv")
        time.sleep(2)
        env = self.pexp.expect_get_output("printenv", self.linux_prompt, 10)
        if "fw_url" in env:
            error_critical("Reset environment FAILED!!!")
        else:
            log_debug("Reset environment check PASS")

    def stop_HTTP_Server(self):
        self.http_srv.shutdown()

    def create_HTTP_Server(self, port):
        self.http_srv = HTTPServer(('', port), SimpleHTTPRequestHandler)
        t = Thread(target=self.http_srv.serve_forever)
        t.setDaemon(True)
        t.start()
        log_debug('http server running on port {}'.format(self.http_srv.server_port))

    def fwupdate(self):
        os.chdir(self.fwdir)

        port = "800"+self.row_id
        self.create_HTTP_Server(int(port))

        fw_url = "http://{}:{}/{}-mfg.bin".format(self.tftp_server, port, self.board_id)
        log_debug("fw_url:\n" + fw_url)

        # Reset for clear FCD enable which make fwupdate fail
        self.pexp.expect_action(10, self.linux_prompt, "reset")
        self.pexp.expect_only(60, "Service Started")
        self.pexp.expect_action(10, "", "")
        self.set_ipaddr()
        self.pexp.expect_action(10, self.linux_prompt, "setenv do_fwupgrade 1", send_action_delay=True)
        self.pexp.expect_action(10, self.linux_prompt, "setenv fw_url "+fw_url, send_action_delay=True)
        self.pexp.expect_action(10, self.linux_prompt, "saveenv")
        self.pexp.expect_action(10, self.linux_prompt, "reset")

        self.pexp.expect_only(200, "Run application from")
        self.stop_HTTP_Server()

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Open serial port successfully ...")
        self.pexp.expect_only(60, "Service Started")
        self.pexp.expect_action(10, "", "")


        msg(40, "Updating MFG img ...")
        self.fwupdate()
        msg(80, "Checking info ...")
        self.check_info()
        msg(90, "Resetting environment ...")
        self.reset_env()
        msg(100, "Completed back to MFG ...")
        self.close_fcd()


def main():
    us_m487_mfg = USM487_MFG()
    us_m487_mfg.run()

if __name__ == "__main__":
    main()
