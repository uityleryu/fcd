#!/usr/bin/python3
import sys
import time
import os
import re
import stat
import filecmp
import json
import base64
import zlib
import shutil

from pprint import pformat
from collections import OrderedDict

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

class UPLQCS405FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UPLQCS405FactoryGeneral, self).__init__()

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

        self.homekit_dict = {
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
        log_debug(msg="sleep 50 secs")
        time.sleep(50)

        self.pexp.expect_lnxcmd(timeout=10, pre_exp="login:", action="", post_exp="")

        self.pexp.expect_lnxcmd(10, "", "")
        self.login(username="ui", password="ui", timeout=120)
        self.setup_network()
        msg(20, "Finish setting up network ...")

        if PROVISION_EN is True:
            self.format_backup_partition_ext4()
            msg(25, "Finish formatting backup partition to ext4 ...")
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

            if self.homekit_dict[self.board_id] is True:
                self.homekit_setup_after_registration()
                msg(65, "Finish Homekit setup ...")

            self.check_devreg_data()
            msg(70, "Finish doing signed file and EEPROM checking ...")

        self.setup_mfg_mode()
        msg(80, "Finish setting to mfg mode ...")

        if W_MAC_EN is True:
            self.write_mac_addr()
            msg(85, "Finish writing MAC address ...")

            if self.homekit_dict[self.board_id] is True:
                self.check_tokenid_match_after_reboot()
                msg(90, "Finish checking HK token ID ...")

        if CHECK_MAC_EN is True:
            self.check_mac()
            msg(95, "Finish checking MAC address ...")

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

        # reboot to activate MAC address & re-login
        if self.reboot_dict[self.board_id] is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")
            log_info(msg="reboot to activate MAC address, sleep 50 secs to wait for boot-up")
            time.sleep(50)

            self.login(username="ui", password="ui", timeout=120)
            #self.setup_network()

    def setup_network(self):
        # temporally added to avoid unexpected msg from console
        cmd = 'killall ui-connect-mqttd'
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        cmd = 'killall ui-spotify-connect spotify_connect'
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

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

        cmd = "sync"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt, valid_chk=True)

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
            is_match = mac_dict_dut[connect_type].upper() == mac_dict_exp[connect_type].upper()
            results_dict[connect_type] = "Pass" if is_match else "Fail"
            log_info('{} MAC address check is {}'.format(connect_type, "Pass" if is_match else "Fail"))

        pass_num = list(results_dict.values()).count("Pass")
        result = pass_num == len(results_dict)
        log_info('MAC address check results_dict = {}'.format(results_dict))

        if result:
            log_info('MAC address check successfully')
        else:
            error_critical('MAC address check failed')

    def homekit_setup_after_registration(self):
        if self.is_homekit_done_before is False:
            self.__gen_homkit_token_csv_txt(self.client_x86_rsp)
            self.__write_homkit_token_to_dut()
        else:
            self.__check_tokenid_match(self.client_x86_rsp)

    def __check_tokenid_match(self, client_x86_rsp):
        regex = re.compile(r'token_id,format=string,value=(.*)')
        tokenid_client = regex.findall(client_x86_rsp+'\n')[0]

        log_info('tokenid_client = {}'.format(tokenid_client))
        log_info('tokenid_dut = {}"'.format(self.tokenid_dut))

        is_tokenid_match = tokenid_client == self.tokenid_dut
        log_info('tokenid_dut & tokenid_client are {}match'.format('' if is_tokenid_match else 'NOT '))
        if is_tokenid_match is False:
            log_info('So server treat this DUT as first time HK registration')
            self.__gen_homkit_token_csv_txt(client_x86_rsp)
            self.__write_homkit_token_to_dut()

        return is_tokenid_match

    def __gen_homkit_token_csv_txt(self, client_x86_rsp):
        def _calculate_crc(info_dict):
            byte = b''
            byte += info_dict['product_plan_id'].encode('UTF-8')
            byte += info_dict['token_id'].encode('UTF-8')
            try:
                token_encode = info_dict['token'].encode('UTF-8')
                byte += base64.b64decode(token_encode)
            except Exception as e:
                log_info(e)
                log_info('calculate_crc fail..')
                crc32 = 0
            else:
                crc32 = hex(zlib.crc32(byte) & 0xffffffff).replace('0x', '')
            return crc32

        log_info('__gen_homkit_token_csv_txt..')

        '''Devreg server response example:
            field=flash_eeprom,format=binary,pathname=/tftpboot/e.s.0
            field=registration_id,format=u_int,value=99099685
            field=result,format=u_int,value=1
            field=device_id,format=u_int,value=94429505
            field=homekit_device_token_id,format=string,value=0C00852350D648C68519AE0EF79F0D7F
            field=homekit_device_token,format=string,value=MYGrMFACAQECAQEESDBGAiEAqB6jlfVSXyItOGpYO5Cg3zvznl4PIi6eMZre9N5HmJgCIQC90d2p828W5bNhsAmnD+K9RDQ/9xZGfLJl9lImcnonRDBXAgECAgEBBE8xTTAJAgFmAgEBBAEBMBACAWUCAQEECPFcGs94AQAAMBQCAgDJAgEBBAsyMTcwMDEtMDAwNDAYAgFnAgEBBBAMAIUjUNZIxoUZrg73nw1/
            field=homekit_device_uuid,format=string,value=1f551899-b3d3-4305-aa60-3e64185f7d7a
            field=homekit_product_plan_id,format=string,value=217001-0004
        '''

        # prepare data
        info_dict = OrderedDict()
        info_dict['token_id'] = None
        info_dict['token'] = None
        info_dict['uuid'] = None
        info_dict['product_plan_id'] = None

        log_info('{}'.format([client_x86_rsp]))

        re_tmp = r"{},format=string,value=(.*)\n"
        for k, v in info_dict.items():
            log_info('k = {}'.format(k))
            regex = re.compile(re_tmp.format(k))
            info_dict[k] = regex.findall(client_x86_rsp+'\n')[0]
            log_info('v = {}'.format(info_dict[k]))

        info_dict['crc32'] = _calculate_crc(info_dict)
        log_info('info_dict = \n{}'.format(pformat(info_dict, indent=4)))

        # gen file
        file_dir = os.path.join('/home/ubnt/usbdisk', 'UPL-AMP_hk_output')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        # prepare token.txt to write into dut / backup on usbdisk
        self.token_txt_path = os.path.join(self.tftpdir, 'token.txt')
        self.tokenid_dut = info_dict['token_id']
        with open(self.token_txt_path, 'w') as f:
            f.write('"product_plan_id","{}","device_uuid","{}","security_token_id","{}","security_token","{}"'.format(
                info_dict['product_plan_id'], info_dict['uuid'],
                info_dict['token_id'], info_dict['token']))
        mfi_token_txt_path = os.path.join(file_dir, 'MFi_token_{}.txt'.format(self.mac.upper()))
        shutil.copy2(self.token_txt_path, mfi_token_txt_path)

        # csv
        csv_path = os.path.join(file_dir, 'token_{}.csv'.format(self.mac.upper()))
        with open(csv_path, 'w') as f:
            f.write('{}, {}, {}, {}'.format(
                info_dict['product_plan_id'], info_dict['token_id'],
                info_dict['token'], info_dict['crc32']))
        # txt
        txt_path = os.path.join(file_dir, 'uuid_{}.txt'.format(self.mac.upper()))
        with open(txt_path, 'w') as f:
            f.write('{}'.format(info_dict['uuid']))

        is_file = os.path.isfile(self.token_txt_path) and os.path.isfile(csv_path) and os.path.isfile(txt_path)
        log_info('token_info_path = {}'.format(self.token_txt_path))
        log_info('token_info_path = {}'.format(mfi_token_txt_path))
        log_info('csv_path = {}'.format(csv_path))
        log_info('txt_path = {}'.format(txt_path))
        log_info('token_id = {}'.format(self.tokenid_dut))
        log_info('Token INFO TXT & Token CSV & uuid TXT files generate {}'.format('success' if is_file else 'fail'))

        return is_file

    def __write_homkit_token_to_dut(self):

        log_debug('__write_homkit_token_to_dut')
        token_txt = 'token.txt'
        read_txt = 'read.txt'

        # record token.txt file size
        cmd = 'wc -c {} | cut -d\' \' -f1'.format(self.token_txt_path)
        [file_size, rtc] = self.fcd.common.xcmd(cmd)
        log_debug('token.txt file_size = {}'.format(file_size))

        # transfer token.txt to dut
        token_txt_path_dut = os.path.join('/tmp', token_txt)
        self.tftp_get(remote=token_txt, local=token_txt_path_dut)

        # write into dut
        log_debug("Change file permission - {0} ...".format(token_txt_path_dut))
        cmd = "chmod 777 {0}".format(token_txt_path_dut)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, valid_chk=True)
        cmd = 'dd if={} of={} bs=1 seek=65536 count={}'.format(token_txt_path_dut, self.devregpart, file_size)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, valid_chk=True)

        # read from dut
        read_txt_path_dut = os.path.join('/tmp', read_txt)
        cmd = 'dd if={} of={} bs=1 skip=65536 count={}'.format(self.devregpart, read_txt_path_dut, file_size)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, valid_chk=True)

        # transfer token_read.txt to RPi
        read_txt_path= os.path.join(self.tftpdir, read_txt)
        self.tftp_put(remote=read_txt, local=read_txt_path_dut)

        # compare
        otmsg = "Starting to compare the {0} and {1} files ...".format(self.token_txt_path, read_txt_path)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.token_txt_path, read_txt_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")

    def _check_is_homekit_done_mod_cmd(self, reg_cmd):

        log_debug('_check_is_homekit_done')
        self.tokenid_dut = ''

        cmd = 'test -f /persist/apple/MFi_token ; echo $?'
        rtc = self.pexp.expect_get_output(action=cmd, prompt=self.linux_prompt).split('\n')[-2]
        log_debug('rtc = {}'.format(rtc))
        if int(rtc) == 0:
            cmd = 'cat /persist/apple/MFi_token |awk -F \'","\' \'{print $6}\''
            res = self.pexp.expect_get_output(action=cmd, prompt=self.linux_prompt).split('\n')[-2].strip()
            self.tokenid_dut = res
            log_info('tokenid = {}'.format(self.tokenid_dut))

        self.is_homekit_done_before = self.tokenid_dut != ''

        log_info('DUT has {}done homekit registration before'.format(
            '' if self.is_homekit_done_before else 'NOT '))

        if self.is_homekit_done_before is True:
            reg_cmd.append('-i field=last_homekit_device_token_id,format=string,value={}'.format(self.tokenid_dut))

        return reg_cmd

    def registration(self, regsubparams = None):
        log_debug("Starting to do registration ...")
        if regsubparams is None:
            regsubparams = self.access_chips_id()

        # must use new client to get hk token
        clientbin = "/usr/local/sbin/client_x64_release_20230908"
        cmd = 'chmod 777 {}'.format(clientbin)
        self.fcd.common.xcmd(cmd)

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        cmd = [
#            "-h stage.udrs.io",
           "-h {}".format(self.devreg_hostname),
            "-k {}".format(self.pass_phrase),
            regsubparams,
            reg_qr_field,
            "-i field=flash_eeprom,format=binary,pathname={}".format(self.eebin_path),
            "-i field=fcd_version,format=hex,value={}".format(self.sem_ver),
            "-i field=sw_id,format=hex,value={}".format(self.sw_id),
            "-i field=sw_version,format=hex,value={}".format(self.fw_ver),
            "-o field=flash_eeprom,format=binary,pathname={}".format(self.eesign_path),
            "-o field=registration_id",
            "-o field=result",
            "-o field=device_id",
            "-o field=registration_status_id",
            "-o field=registration_status_msg",
            "-o field=error_message",
            "-x {}ca.pem".format(self.key_dir),
            "-y {}key.pem".format(self.key_dir),
            "-z {}crt.pem".format(self.key_dir)
        ]

        if self.homekit_dict[self.board_id] is True:
            cmd = self._check_is_homekit_done_mod_cmd(cmd)

        cmdj = ' '.join(cmd)

        reg_cmd = "sudo {0} {1}".format(clientbin, cmdj)

        log_debug('cmd = \n{}'.format(pformat(cmd, indent=4)))
        log_debug('cmd = {}'.format(reg_cmd))
        [self.client_x86_rsp, rtc] = self.fcd.common.xcmd(reg_cmd)
        log_debug('client_x86 return code = \n{}'.format(rtc))

        if (int(rtc) > 0):
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

#        clit = ExpttyProcess(self.row_id, cmd, "\n")
#        clit.expect_only(30, "Security Service Device Registration Client")
#        clit.expect_only(30, "Hostname")
#        clit.expect_only(30, "field=result,format=u_int,value=1")

        self.pass_devreg_client = True

        log_debug("Excuting client registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()

    def format_backup_partition_ext4(self):
        log_debug("erasing devregpart")
        cmd = "/etc/mkfs_backup.sh "
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd)

        log_debug("dump devregpart")
        cmd = "hexdump -C {} 2>&1".format(self.devregpart)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd)

    def check_tokenid_match_after_reboot(self):
        cmd = 'cat /persist/apple/MFi_token |awk -F \'","\' \'{print $6}\''
        res = self.pexp.expect_get_output(action=cmd, prompt=self.linux_prompt).split('\n')[-2].strip()
        self.tokenid_dut_after_reboot = res
        log_info('tokenid_after_reboot = {}'.format(self.tokenid_dut_after_reboot))
        log_info('tokenid_dut = {}'.format(self.tokenid_dut))

        is_tokenid_match = self.tokenid_dut_after_reboot == self.tokenid_dut
        log_info('tokenid_after_reboot & tokenid_dut are {}match'.format('' if is_tokenid_match else 'NOT '))

        if is_tokenid_match:
            log_info('HK Token ID check successfully')
        else:
            error_critical('HK Token ID check failed')

def main():
    uc_factory_general = UPLQCS405FactoryGeneral()
    uc_factory_general.run()


if __name__ == "__main__":
    main()
