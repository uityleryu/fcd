#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp
import json

sys.path.append("/tftpboot/tools")

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical, log_info

PROVISION_EN = True
DOHELPER_EN = True
W_MAC_EN = True
REGISTER_EN = True
CHECK_MAC_EN = True

'''
    aa03:  UniFiPlay-AMP
'''

class UCQCS403FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UCQCS403FactoryGeneral, self).__init__()

        self.ver_extract()
        devreg_mtd = {
            'aa03': "/dev/block/bootdevice/by-name/factory"
        }
        self.devregpart = devreg_mtd[self.board_id]

        self.mac_check_dict = {
            'aa03': True
        }

        self.reboot_dict = {
            'aa03': True
        }

        # number of Ethernet
        ethnum = {
            'aa03': "1"
        }

        # number of WiFi
        wifinum = {
            'aa03': "1"
        }

        # number of Bluetooth
        btnum = {
            'aa03': "1"
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

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        msg(10, "TTY initialization successfully ...")

        self.pexp.expect_lnxcmd(timeout=10, pre_exp="login:", action="", post_exp="")

        self.pexp.expect_lnxcmd(10, "", "")
        self.login(username="ui", password="ui", timeout=120)
        self.setup_network()
        msg(20, "Finish setting up network ...")

        if PROVISION_EN is True:
            self.erase_eefiles()
            msg(30, "Finish erasing ee files ...")
            self.data_provision_64k(self.devnetmeta)
            msg(40, "Finish preparing the devreg file ...")

        if DOHELPER_EN is True:
            self.prepare_server_need_files()
            msg(50, "Finish do helper to get the output file to devreg server ...")

        if REGISTER_EN is True:
            self.registration()
            msg(60, "Finish doing registration ...")
            self.check_devreg_data()
            msg(70, "Finish doing signed file and EEPROM checking ...")

        if W_MAC_EN is True:
            self.write_mac_addr()
            msg(80, "Finish writing MAC address ...")

        if CHECK_MAC_EN is True:
            self.check_mac()
            msg(90, "Finish checking MAC address ...")

        self.setup_mfg_mode()
        msg(95, "Finish setting to mfg mode ...")

        msg(100, "Completing registration ...")
        self.close_fcd()

    def prepare_server_need_files(self, method="tftp"):
        log_info('prepare_server_need_files_ssh()')

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

        log_info("Send helper output files from DUT to host ...")

    def get_cpu_id(self):
        res = self.pexp.expect_get_output('cat /tmp/bsp_helper/cpuid', self.linux_prompt).split('\n')[-2]
        res = res.replace('\r', '')
        id = res
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
        log_info("provided {} successfully".format(output_path))

    def helper_generate_e_b(self, output_path='/tmp/e.b'):
        log_debug('helper_generate_e_b to {}'.format(output_path))

        cmd_dd = "dd if={} of={} bs=1k count=64".format(self.devregpart, output_path)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd_dd, post_exp=self.linux_prompt,
                                valid_chk=True)
        # self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action='mv /tmp/e.org.0 /tmp/e.b.0', post_exp=self.linux_prompt, valid_chk=True)
        log_info("provided {} successfully".format(output_path))

    def write_mac_addr(self):
        # write
        cmd = 'ubus call main hal_write_mac_addrs'
        res = self.pexp.expect_get_output(action=cmd, prompt=self.linux_prompt)
        match = re.search(r'"result":\s+"ok"', res)

        if not match:
            error_critical('write MAC address failed')

        log_info('write MAC address successfully')

        # sync data to flash
        cmd = "sync"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt, valid_chk=True)

        # reboot to activate MAC address & re-login
        if self.reboot_dict[self.board_id] is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")
            log_info(msg="sleep 50 secs to wait for boot-up")
            time.sleep(50)

            self.login(username="ui", password="ui", timeout=120)
            self.setup_network()

    def setup_network(self):
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

    def setup_mfg_mode(self):
        cmd = "echo 1 > /data/mfg_mode"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd)

        cmd = "cat /data/mfg_mode"
        flag = "1"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=flag)

    def check_mac(self):
        log_info("Starting to check MAC")
        log_info("self.mac_check_dict = {}".format(self.mac_check_dict))

        if self.mac_check_dict[self.board_id] is False:
            log_info("skip check the MAC in DUT ...")
            return

        # expected mac
        int_mac = int(self.mac, 16)
        mac_hex_wifi = hex(int_mac + 1).replace("0x", "").zfill(12)
        mac_hex_bt = hex(int_mac + 2).replace("0x", "").zfill(12)

        mac_dict_exp = {}
        mac_dict_exp['eth0'] = self.mac_format_str2comma(self.mac)
        mac_dict_exp['wlan0'] = self.mac_format_str2comma(mac_hex_wifi)
        mac_dict_exp['BT'] = self.mac_format_str2comma(mac_hex_bt)

        log_info('[exp] mac_dict = {}'.format(mac_dict_exp))

        # read mac
        cmd = 'ubus call main hal_read_mac_addrs'
        res = self.pexp.expect_get_output(action=cmd, prompt=self.linux_prompt)
        json_data = re.search(r'{[^}]+}', res).group()
        mac_dict_dut = json.loads(json_data)
        log_info('[dut] mac_dict = {}'.format(mac_dict_dut))

        results_dict = {}
        for connect_type, mac in mac_dict_exp.items():
            is_match = mac_dict_dut[connect_type] == mac_dict_exp[connect_type]
            results_dict[connect_type] = "Pass" if is_match else "Fail"
            log_info('{} MAC check is {}'.format(connect_type, "Pass" if is_match else "Fail"))

        pass_num = list(results_dict.values()).count("Pass")
        result = pass_num == len(results_dict)
        log_info('MAC check results_dict = {}'.format(results_dict))

        if result:
            log_info('MAC check successfully')
        else:
            error_critical('MAC check failed')

def main():
    uc_factory_general = UCQCS403FactoryGeneral()
    uc_factory_general.run()


if __name__ == "__main__":
    main()
