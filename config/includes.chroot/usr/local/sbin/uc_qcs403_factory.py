#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

sys.path.append("/tftpboot/tools")

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

PROVISION_EN = True
DOHELPER_EN = True
W_MAC_EN = True
REGISTER_EN = True

'''
    ec80:  UC-SPK-MINI
    aa01:  Amplifi-Cinema-Bridge
    aa02:  Amplifi-AMP
'''


class UCQCS403FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UCQCS403FactoryGeneral, self).__init__()

        self.ver_extract()
        #self.devregpart = "/dev/mtdblock23"
        devreg_mtd = {
            'ec80': "/dev/mtdblock23",
            'aa01': "/dev/mmcblk0p1",
            'aa02': "/dev/mtdblock23"
        }
        self.devregpart = devreg_mtd[self.board_id]

        # number of Ethernet
        ethnum = {
            'ec80': "1",
            'aa01': "1",
            'aa02': "1"
        }

        # number of WiFi
        wifinum = {
            'ec80': "0",
            'aa01': "1",
            'aa02': "1"
        }

        # number of Bluetooth
        btnum = {
            'ec80': "0",
            'aa01': "2",
            'aa02': "1"
        }

        self.devnetmeta = {
            'ethnum': ethnum,
            'wifinum': wifinum,
            'btnum': btnum,
        }

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

        msg(10, "TTY initialization successfully ...")
        log_debug(msg="sleep 70 secs")
        time.sleep(70)

        self.pexp.expect_lnxcmd(10, "", "")
        if self.board_id == 'aa01':
            self.login(username="root", password="ubnt", timeout=120)
        else:
            self.login(username="root", password="ubnt", timeout=120)
        cmd = "dmesg -n1"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        self.chk_lnxcmd_valid()

        cmd = "ifconfig eth0 down"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        self.chk_lnxcmd_valid()
        time.sleep(10)

        self.set_lnx_net("eth0")
        self.set_lnx_net("eth0")
        time.sleep(10)
        self.is_network_alive_in_linux()


        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            self.erase_eefiles()
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            if self.board_id == 'aa01':
                cmd = "dump-uid"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
            self.prepare_server_need_files()

        if W_MAC_EN is True:
            # Write MAC
            int_mac = int(self.mac, 16)
            if int(self.devnetmeta['wifinum'][self.board_id]) > 0:
                hex_wifi_mac = hex(int_mac + 1).replace("0x", "").zfill(12)
            if int(self.devnetmeta['btnum'][self.board_id]) > 0:
                hex_bt_mac = hex(int_mac + 2).replace("0x", "").zfill(12)
            comma_mac = self.mac_format_str2comma(self.mac)

            # Write Eth MAC
            cmd = "echo {} > /persist/emac_config.ini".format(comma_mac)
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

            # Write WiFi MAC
            if int(self.devnetmeta['wifinum'][self.board_id]) > 0:
                cmdset = [
                    "mkdir -p /persist/factory/wlan/",
                    "echo \"Intf0MacAddress={}\" > /persist/factory/wlan/wlan_mac.bin".format(hex_wifi_mac),
                    "echo \"END\" >> /persist/factory/wlan/wlan_mac.bin"
                ]
                for cmd in cmdset:
                    self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

            # Write BT MAC
            if int(self.devnetmeta['btnum'][self.board_id]) > 0:
                comma_bt_mac = self.mac_format_str2comma(hex_bt_mac)
                cmd = "btnvtool -b {}".format(comma_bt_mac)
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

            # sync data to flash
            cmd = "sync"
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

            # Check MAC
            cmd = "cat /persist/emac_config.ini"
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=comma_mac)


            # for AMP, it needs reboot to have MAC address take effect
            if self.board_id == 'aa01' or self.board_id == 'aa02':
                self.pexp.expect_action(10, self.linux_prompt, "reboot -f")
                log_debug(msg="sleep 50 secs")
                time.sleep(50)

                self.login(username="root", password="ubnt", timeout=120)

                cmd = "dmesg -n1"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
                self.chk_lnxcmd_valid()

                cmd = "ifconfig eth0 down"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
                self.chk_lnxcmd_valid()
                time.sleep(10)

                self.set_lnx_net("eth0")
                self.set_lnx_net("eth0")
                time.sleep(10)
                self.is_network_alive_in_linux()

            # Check WiFi MAC
            if int(self.devnetmeta['wifinum'][self.board_id]) > 0:
                cmd = "/sbin/insmod /usr/lib/modules/4.14.117-perf/extra/wlan.ko"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
                time.sleep(5)
                cmd = "ifconfig wlan0 up"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

                cmd = "ifconfig wlan0 | grep HWaddr"
                comma_wifi_mac = self.mac_format_str2comma(hex_wifi_mac)
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=comma_wifi_mac.upper())
                # postexp = "Link encap:Ethernet  HWaddr {}".format(comma_wifi_mac.upper())
                # self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=postexp)

            # Check BT MAC
            if int(self.devnetmeta['btnum'][self.board_id]) > 0:
                cmd = "cat /persist/factory/bluetooth/bdaddr.txt"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=comma_bt_mac)


        if REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
            if self.board_id == 'aa02' or self.board_id == 'aa01':
                cmd = "echo 1 > /data/mfg_mode"
            else:
                cmd = "echo enable > /data/keymfg_mode"

            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd)

            if self.board_id == 'aa02' or self.board_id == 'aa01':
                cmd = "cat /data/mfg_mode"
                flag = "1"
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=flag)
        '''
            ============ Registration End ============
        '''

        msg(100, "Completing registration ...")
        self.close_fcd()

    def prepare_server_need_files(self, method="tftp"):
        log_debug('prepare_server_need_files_ssh()')
        # log_debug("Starting to do " + self.helperexe + "...")
        # # Ex: tools/uvp/helper_DVF99_release_ata_max
        # srcp = os.path.join(self.tools, self.helper_path, self.helperexe)
        #
        # # Ex: /tmp/helper_DVF99_release_ata_max
        # helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)
        #
        # if method == "tftp":
        #     self.tftp_get(remote=srcp, local=helperexe_path, timeout=60)
        # elif method == "wget":
        #     self.dut_wget(srcp, helperexe_path, timeout=100)
        # else:
        #     error_critical("Transferring interface not support !!!!")
        #
        # cmd = "chmod 777 {0}".format(helperexe_path)
        # self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
        #                         valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        self.helper_generate_e_t(eetxt_dut_path)
        self.helper_generate_e_b(eebin_dut_path)

        files = [self.eetxt, self.eebin]
        for fh in files:
            # Ex: /tftpboot/e.t.0
            srcp = os.path.join(self.tftpdir, fh)

            # Ex: /tmp/e.t.0
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send helper output files from DUT to host ...")

    def get_cpu_id(self):
        res = self.pexp.expect_get_output('cat /tmp/bsp_helper/cpuid', self.linux_prompt).split('\n')[-2]
        res = res.replace('\r', '')
        id = res
        if self.board_id == 'aa01':
            id = id.replace('0x00000000', '')
        log_debug(id)
        return id

    def get_jedec_id(self):
        res = self.pexp.expect_get_output('cat /tmp/bsp_helper/jedec_id', self.linux_prompt).split('\n')[-2]
        res = res.replace('\r', '')
        id = res.zfill(8)
        log_debug(id)
        return id

    def get_flash_uid(self):
        res = self.pexp.expect_get_output('cat /tmp/bsp_helper/otp', self.linux_prompt).split('\n')[-2]
        res = res.replace('\r', '')
        id = res
        log_debug(id)
        return id

    def helper_generate_e_t(self, output_path='/tmp/e.t'):
        log_debug('helper_generate_e_t to {}'.format(output_path))
        cpu_rev_id = self.get_cpu_id()
        jedec_id = self.get_jedec_id()
        flash_uid = self.get_flash_uid()

        sstr = [
            'field=product_class_id,format=hex,value=0014',
            'field=cpu_rev_id,format=hex,value={}'.format(cpu_rev_id),
            'field=flash_jedec_id,format=hex,value={}'.format(jedec_id),
            'field=flash_uid,format=hex,value={}'.format(flash_uid)
        ]
        sstr = '\n'.join(sstr)
        log_debug(sstr)

        cmd = 'echo "{}" > {}'.format(sstr, output_path)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)
        log_debug("provided {} successfully".format(output_path))

    def helper_generate_e_b(self, output_path='/tmp/e.b'):
        log_debug('helper_generate_e_b to {}'.format(output_path))

        cmd_dd = "dd if={} of={} bs=1k count=64".format(self.devregpart, output_path)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd_dd, post_exp=self.linux_prompt,
                                valid_chk=True)
        # self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action='mv /tmp/e.org.0 /tmp/e.b.0', post_exp=self.linux_prompt, valid_chk=True)
        log_debug("provided {} successfully".format(output_path))


def main():
    uc_factory_general = UCQCS403FactoryGeneral()
    uc_factory_general.run()


if __name__ == "__main__":
    main()
