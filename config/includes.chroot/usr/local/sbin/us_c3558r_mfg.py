#!/usr/bin/python3

import re
import sys
import os
import time
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical
from PAlib.Framework.fcd.ssh_client import SSHClient
from PAlib.Framework.fcd.common import Common


'''
    f064: HyperSwitch
'''


class HYPERSWITCH_MFG(ScriptBase):
    def __init__(self):
        super(HYPERSWITCH_MFG, self).__init__()
        self.init_vars()
        self.ver_extract()
        self.cn = Common()

    def init_vars(self):
        self.bootloader_prompt = "Shell>"
        self.linux_prompt = "#"

    def login(self, username="ubnt", password="ubnt", timeout=10, press_enter=False, retry=3, log_level_emerg=False):
        '''
            should be called at login console
        '''
        if press_enter is True:
            self.pexp.expect_action(timeout, "Please press Enter to activate this console", "")

        for i in range(0, retry + 1):
            post = [
                "login:",
                "Error-A12 login",
                "Shell"
            ]
            ridx = self.pexp.expect_get_index(timeout, post)
            if ridx == 0 or ridx == 1:
                '''
                    To give twice in order to make sure of that the username has been keyed in
                '''
                if username != "":
                    self.pexp.expect_action(10, "", username)

                if password != "":
                    self.pexp.expect_action(30, "Password:", password)

                break
            elif ridx == 2:
                pass
            else:
                self.pexp.expect_action(timeout, "", "\003")
                print("Retry login {}/{}".format(i + 1, retry))
                timeout = 10
        else:
            raise Exception("Login exceeded maximum retry times {}".format(retry))

        if log_level_emerg is True:
            self.pexp.expect_action(10, self.linux_prompt, "dmesg -n1")

        return ridx

    def run(self):
        """
            Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        preload_gu_ip = "192.168.1.19"
        preload_gu_username = "ubnt"
        preload_gu_password = "ubnt"
        try:
            ssh_DUT = SSHClient(host=preload_gu_ip, username=preload_gu_username, password=preload_gu_password)
        except Exception as e:
            rmsg = "The status of the extra RPi4 for loading FW image:"
            rmsg += "Can't make SSH connection: {}... FAIL!!!".format(preload_gu_ip)
            error_critical(rmsg)

        onie_file = "onie-installer.bin"
        src_file = os.path.join(self.fwdir, onie_file)
        dst_file = "/tftpboot/{}".format(onie_file)
        cmd = "ls -la {}".format(self.fwdir)
        self.cn.xcmd(cmd)

        cmd = "md5sum {} | awk '{{print $1}}'".format(dst_file)
        cmd_reply = ssh_DUT.execmd_getmsg(cmd)
        rmsg = "{}, MD5SUM from GU: {}".format(onie_file, cmd_reply)
        log_debug(rmsg)
        cmd = "md5sum {} | awk '{{print $1}}'".format(src_file)
        [sto, rtc] = self.cn.xcmd(cmd)
        rmsg = "{}, MD5SUM from FCD: {}".format(onie_file, sto)
        log_debug(rmsg)
        if cmd_reply.strip() != sto.strip():
            self.scp_get(preload_gu_username, preload_gu_password, preload_gu_ip, src_file, dst_file)

        bootx_file = "bootx64.efi"
        src_file = os.path.join(self.fwdir, bootx_file)
        dst_file = "/tftpboot/{}".format(bootx_file)

        cmd = "md5sum {} | awk '{{print $1}}'".format(dst_file)
        cmd_reply = ssh_DUT.execmd_getmsg(cmd)
        rmsg = "{}, MD5SUM from GU: {}".format(onie_file, cmd_reply)
        log_debug(rmsg)
        cmd = "md5sum {} | awk '{{print $1}}'".format(src_file)
        [sto, rtc] = self.cn.xcmd(cmd)
        rmsg = "{}, MD5SUM from FCD: {}".format(onie_file, sto)
        log_debug(rmsg)
        if cmd_reply.strip() != sto.strip():
            self.scp_get(preload_gu_username, preload_gu_password, preload_gu_ip, src_file, dst_file)

        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")

        msg(1, "Waiting - PULG in the device...")
        rv = self.login(timeout=120, retry=30)

        if rv == 0 or rv == 1:
            cmd = "efibootmgr --bootnext $(efibootmgr | grep \"UEFI: Built-in EFI Shell\" | tr -d -c 0-9)"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
            self.pexp.expect_lnxcmd(10, "UEFI: Built-in EFI Shell", "reboot")
        else:
            error_critical("Unexpecting login ... FAIL!!!")

        self.pexp.expect_ubcmd(120, "any other key to continue", "\r\r\r\r")
        time.sleep(2)
        self.pexp.expect_ubcmd(80, "Shell", "mm -io E3E8 1\r")
        time.sleep(2)
        self.pexp.expect_ubcmd(80, "", "mm -io E3E8 1\r")
        time.sleep(2)
        self.pexp.expect_ubcmd(20, "", "mm -io B2 BF\r")
        time.sleep(2)
        self.pexp.expect_ubcmd(20, "", "reset\r")

        self.pexp.expect_only(120, "ONIE: Executing installer")
        self.login(timeout=120, retry=30)

        cmd = "cat /usr/lib/version"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.pexp.expect_only(10, "Atom-C3K")

        msg(no=100, out="Load the FW image completed")
        self.close_fcd()


def main():
    factory = HYPERSWITCH_MFG()
    factory.run()


if __name__ == "__main__":
    main()
