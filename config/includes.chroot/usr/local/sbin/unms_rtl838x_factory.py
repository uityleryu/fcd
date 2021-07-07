#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
SECCHK_EN = True
BDINFO_EN = True

'''
    eed0: UNMS_S_LITE
    eed1: UISP_S_PRO
    ee50: UISP_S_LITE
    eed3: UISP_O_PRO
    ee6f: UISP_S
'''


class UNMSRTL838XFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UNMSRTL838XFactoryGeneral, self).__init__()

        self.ver_extract()

        # board model
        self.bdmd = {
            'eed0': "UNMS_S_LITE",
            'eed1': "UISP_S_PRO",
            'ee50': "UISP_S_LITE",
            'eed3': "UISP_O_PRO",
            'ee6f': "UISP_S"
        }

        # number of Ethernet
        ethnum = {
            'eed0': "3",
            'eed1': "3",
            'ee50': "3",
            'eed3': "3",
            'ee6f': "3"
        }

        # number of WiFi
        wifinum = {
            'eed0': "0",
            'eed1': "0",
            'ee50': "0",
            'eed3': "0",
            'ee6f': "0"
        }

        # number of Bluetooth
        btnum = {
            'eed0': "0",
            'eed1': "1",
            'ee50': "0",
            'eed3': "1",
            'ee6f': "1"
        }

        btprmt = {
            '0000': "RTL838x#",
            'eed0': "RTL838x#",
            'eed1': "RTL9300#",
            'ee50': "RTL838x#",
            'eed3': "RTL9300#",
            'ee6f': "RTL838x#"
        }

        # helper path
        hpth = {
            '0000': "unms-slite",
            'eed0': "unms-slite",
            'eed1': "unms-spro",
            'ee50': "unms-slite",
            'eed3': "unms-spro",
            'ee6f': "unms-slite"
        }

        # helper executable file
        hpeb = {
            '0000': "helper_RTL838x_release",
            'eed0': "helper_RTL838x_release",
            'eed1': "helper_RTL930x_release",
            'ee50': "helper_RTL838x_release",
            'eed3': "helper_RTL930x_release",
            'ee6f': "helper_RTL838x_release"
        }

        # EEPROM device
        eedev = {
            '0000': "/dev/mtdblock6",
            'eed0': "/dev/mtdblock6",
            'eed1': "/dev/mtdchar12",
            'ee50': "/dev/mtdblock6",
            'eed3': "/dev/mtdchar12",
            'ee6f': "/dev/mtdblock6"
        }

        self.netif = {
            'eed0': "ifconfig eth0 ",
            'eed1': "ifconfig eth0 ",
            'ee50': "ifconfig eth0 ",
            'eed3': "ifconfig eth0 ",
            'ee6f': "ifconfig eth0 "
        }

        self.bootloader_prompt = btprmt[self.board_id]
        self.helper_path = hpth[self.board_id]
        self.helperexe = hpeb[self.board_id]
        self.devregpart = eedev[self.board_id]

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

        self.developed = ["eed1", "eed3"]

    def stop_at_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit Esc key to stop autoboot", "\033\033")

    def uboot_upgrade(self):
        cmd = "upgrade loader {0}/{1}-uboot.img".format(self.image, self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        wmsg = "Upgrade loader image \[{0}/{1}-uboot.img\] success".format(self.image, self.board_id)
        self.pexp.expect_only(60, wmsg)

        cmd = "reset"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        self.stop_at_uboot()


    def uboot_config(self):
        cmdset = [
            "setenv ipaddr {0}".format(self.dutip),
            "setenv serverip {0}".format(self.tftp_server),
            "setenv boardmodel {0}".format(self.bdmd[self.board_id]),
            "setenv burnNum 0",
            "setenv telnet 0",
            "saveenv",
            "reset"
        ]
        for idx in range(len(cmdset)):
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmdset[idx])

        self.stop_at_uboot()

        cmd = "rtk network on".format(self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "ping {0}".format(self.tftp_server)
        postexp = "host {0} is alive".format(self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd, post_exp=postexp)

    def set_ub_net(self):
        cmdset = [
            "setenv ipaddr {0}".format(self.dutip),
            "setenv serverip {0}".format(self.tftp_server)
        ]
        for idx in range(len(cmdset)):
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmdset[idx])

        cmd = "rtk network on".format(self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "ping {0}".format(self.tftp_server)
        postexp = "host {0} is alive".format(self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd, post_exp=postexp)

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

        msg(1, "Stop at U-Boot ...")
        self.stop_at_uboot()
        self.uboot_config()

        # msg(5, "Upgrading U-Boot ...")
        '''
        To remove the U-Boot upgrade temporarily
        20201224
        '''
        if self.board_id in self.developed:
            self.uboot_upgrade()

        self.set_ub_net()

        msg(10, "Upgrading DIAG image ...")
        cmd = "upgrade runtime {0}/{1}-fw.bin".format(self.image, self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        wmsg = "Upgrade runtime image \[{0}/{1}-fw.bin\] success".format(self.image, self.board_id)
        self.pexp.expect_only(520, wmsg)

        msg(15, "Loading cfg and log parts ...")
        cmd = "tftpboot 0x81000000 {0}/{1}/esx_cfg.part".format(self.tools, self.helper_path)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred = 1048576")
        cmd = "flwrite name JFFS2_CFG 0x81000000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "tftpboot 0x81000000 {0}/{1}/esx_log.part".format(self.tools, self.helper_path)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred = 1048576")
        cmd = "flwrite name JFFS2_LOG 0x81000000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "setenv ethaddr 00:E0:4C:00:00:0{}; saveenv".format(self.row_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(1)

        cmd = "boota"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        '''
            In this case, the UNMS-S-LITE will boot up to DIAG image as default.
            And the DIAG image will start running another shell.
            And it only could accept the "\r" as an Enter key in this shell.
        '''
        self.pexp.expect_lnxcmd(60, "UBNT_Diag", "exit\r", self.linux_prompt)
        self.set_lnx_net("eth0")
        self.is_network_alive_in_linux()

        if self.board_id == "eed1" or self.board_id == "eed3":
            flerase_host_path = os.path.join(self.tools, self.helper_path, "flash_eraseall")
            flerase_dut_path = os.path.join(self.dut_tmpdir, "flash_eraseall")
            self.tftp_get(remote=flerase_host_path, local=flerase_dut_path, timeout=15)
            cmd = "chmod 777 {}".format(flerase_dut_path)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            self.erase_eefiles()
            msg(20, "Send tools to DUT and data provision ...")
            if self.board_id == "eed1" or self.board_id == "eed3":
                cmd = "/tmp/flash_eraseall {}".format(self.devregpart)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            if self.board_id == "eed1" or self.board_id == "eed3":
                cmd = "/tmp/flash_eraseall {}".format(self.devregpart)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
            ============ Registration End ============
        '''

        if SECCHK_EN is True:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
            self.pexp.expect_lnxcmd(10, "UBNT_Diag", "sectest\r", "security test pass")

        if BDINFO_EN is True:
            self.pexp.expect_lnxcmd(30, "UBNT_Diag", "exit\r", self.linux_prompt)
            self.set_lnx_net("eth0")
            self.is_network_alive_in_linux()

            epm = "eeprom_{}.bin".format(self.row_id)
            dstf = os.path.join(self.tftpdir, epm)
            rtf = os.path.isfile(dstf)
            if rtf is True:
                rmsg = "Erasing File - {} ...".format(rtf)
                log_debug(rmsg)
                os.chmod(dstf, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.remove(dstf)
            else:
                rmsg = "File - {} doesn't exist ...".format(dstf)
                log_debug(rmsg)

            cmd = "dd if={} of=/tmp/{}".format(self.devregpart, epm)
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)

            srcf = os.path.join(self.tftpdir, epm)
            dstf = os.path.join("/tmp", epm)
            rmsg = "Remote path(Host): {}".format(srcf)
            log_debug(rmsg)
            rmsg = "Local path(DUT): {}".format(dstf)
            log_debug(rmsg)
            self.tftp_put(remote=srcf, local=dstf, timeout=10)

            cmd = "hexdump -C -s 0 -n 6 {}".format(srcf)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if rtc >= 0:
                m_mac = re.findall("00000000  (.*) (.*) (.*) (.*) (.*) (.*)", sto)
                if m_mac:
                    t_mac = m_mac[0][0].replace(" ", "")
                    if t_mac in self.mac:
                        rmsg = "MAC: {}, check PASS".format(t_mac)
                        log_debug(rmsg)
                    else:
                        rmsg = "Read MAC: {}, expected: {}, check Failed".format(t_mac, self.mac)
                        error_critical(rmsg)
                else:
                    error_critical("Can't get MAC from EEPROM")

            cmd = "hexdump -C -s 0x10 -n 4 {}".format(srcf)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if rtc >= 0:
                m_bomrev = re.findall("00000010  (.*) (.*) (.*) (.*)", sto)
                if m_bomrev:
                    bom_2nd = int(m_bomrev[0][0][3:8].replace(" ", ""), 16)
                    bom_3rd = int(m_bomrev[0][0][9:11], 16)
                    bom_all = "113-{:05d}-{:02d}".format(bom_2nd, bom_3rd)
                    if self.bom_rev in bom_all:
                        rmsg = "BOM revision: {}, check PASS".format(bom_all)
                        log_debug(rmsg)
                    else:
                        rmsg = "Read BOM revision: {}, expected: {}, check Failed".format(bom_all, self.bom_rev)
                        error_critical(rmsg)
                else:
                    error_critical("Can't get BOM revision from EEPROM")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
        self.stop_at_uboot()

        cmdset = [
            "setenv telnet 1",
            "saveenv",
        ]
        for idx in range(len(cmdset)):
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmdset[idx])

        msg(100, "Completing ...")
        self.close_fcd()

def main():
    unms_factory_general = UNMSRTL838XFactoryGeneral()
    unms_factory_general.run()

if __name__ == "__main__":
    main()
