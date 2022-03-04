#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.pserial import SerialExpect
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info
from pprint import pformat

import sys
import time
import os
import re
import traceback

FWUPDATE_ENABLE     = True
PROVISION_ENABLE    = True
DOHELPER_ENABLE     = True 
REGISTER_ENABLE     = True 
FLASH_DEVREG_DATA   = True
DEVREG_CHECK_ENABLE = True
SPIFF_FORMAT_CHECK  = False

class UFPESP32FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UFPESP32FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        # script specific vars
        self.esp32_prompt = "esp32>"
        self.product_class = "0015"

        # Index 0: flag to control key is existed or flash is encrypted
        #       1: key name
        #       2: burn_key option
        #       3: key binary
        self.secure_boot_key_bin = os.path.join(self.tftpdir, "images", "secure-bootloader-key-256.bin")
        self.flash_encrypt_key_bin = os.path.join(self.tftpdir, "images", "flash_encryption_key.bin")
        self.regsubparams = ""
        self.dev_flash_cfg = [[True, "Secure boot key"              , " secure_boot"     , self.secure_boot_key_bin  ],
                              [True, "Flash encryption key"         , None              , None                      ],
                              [False, "Flash encryption mode counter", None              , None                      ]]

        # number of Ethernet
        self.ethnum = {
            'ec4c': "0",
            "ec4a": "0",
        }

        # number of WiFi
        self.wifinum = {
            'ec4c': "1",
            "ec4a": "1",
        }

        # number of Bluetooth
        self.btnum = {
            'ec4c': "1",
            'ec4a': "1",
        }

        self.devnetmeta = {                                                                                                  
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.homekit_dict = {
            'ec4c': False,
            'ec4a': False
        }

    def prepare_server_need_files(self):
        output = self.pexp.expect_get_output("uniqueid", self.esp32_prompt, timeout=10)
        log_debug(output)
        id_list = re.findall(r'id: 0x(\w+)', output)
        cpu_id = id_list[0]
        flash_jedec_id = id_list[1]
        flash_uuid = id_list[2]
        
        log_debug("cpu_id={}, flash_jedec_id={}, flash_uuid{}".format(cpu_id, flash_jedec_id, flash_uuid))
        self.regsubparams = " -i field=product_class_id,format=hex,value={}".format(self.product_class) + \
                            " -i field=cpu_rev_id,format=hex,value={}".format(cpu_id)                   + \
                            " -i field=flash_jedec_id,format=hex,value={}".format(flash_jedec_id)       + \
                            " -i field=flash_uid,format=hex,value={}".format(flash_uuid) 

    ### To check if keys are exist and device is first programmed or not
    def check_device_stat(self):
        cmd = "sudo espefuse.py -p /dev/ttyUSB1 summary"
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Get efuse summary failed"
            error_critical(otmsg)

        for key in self.dev_flash_cfg:
            match = re.search(r'{}\W+= (.*) .\/.'.format(key[1]), output)
            if match:
                key_val = match.group(1)
                log_info('{} = "{}"'.format(key[1], key_val))
                if key_val == "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00" or \
                   key_val == "0":
                    key[0] = False
            else:
                error_critical("Can't parse key {}".format(key[0]))

    def program_keys(self):
        for i in range(0, 1):
            if self.dev_flash_cfg[i][0] is False:
                cmd = "sudo espefuse.py -p /dev/ttyUSB{} --do-not-confirm burn_key {} {}".format(self.row_id, self.dev_flash_cfg[i][2], self.dev_flash_cfg[i][3])
                log_debug(cmd)
                [output, rv] = self.cnapi.xcmd(cmd)
                if int(rv) > 0:
                    otmsg = 'burn_key "{}" failed!'.format(self.dev_flash_cfg[i][1])
                    error_critical(otmsg)
            else:
                log_info('Skip programming key "{}" because it is existed there'.format(self.dev_flash_cfg[i][1]))


    def program_flash(self):
        fw_bootloader = os.path.join(self.tftpdir, "images", "bootloader.bin")
        fw_ptn_table  = os.path.join(self.tftpdir, "images", "partition-table.bin")
        fw_ota_data   = os.path.join(self.tftpdir, "images", "ota_data_initial.bin")
        if self.product_name == 'ULED-INSTANT':
            fw_app        = os.path.join(self.tftpdir, "images", "uled-inst_mfg.bin")
        elif self.product_name == 'ULED-BULB':
            fw_app        = os.path.join(self.tftpdir, "images", "wifibulb_mfg.bin")

        fw_nvs_key    = os.path.join(self.tftpdir, "images", "bootloader-reflash-digest.bin")

        cmd = "esptool.py --chip esp32 -p /dev/ttyUSB{} -b 460800 --before=default_reset " \
              "--after=no_reset write_flash --flash_mode dio --flash_freq 40m --flash_size 16MB " \
              "{} {}".format(self.row_id, "0x1000", fw_bootloader)
        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash FW into DUT failed"
            error_critical(otmsg)

        cmd = "esptool.py --chip esp32 -p /dev/ttyUSB{} -b 460800 --before=default_reset "         \
              "--after=hard_reset write_flash --flash_mode dio --flash_freq 40m --flash_size 16MB " \
              "{} {} {} {} {} {} {} {}".format(self.row_id,
                                                     "0x00000" , fw_nvs_key,
                                                     "0xb000"  , fw_ptn_table ,
                                                     "0xd000"  , fw_ota_data  ,
                                                     "0x90000" , fw_app)
        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash FW into DUT failed"
            error_critical(otmsg)

        # The waiting time         
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        self.pexp.expect_only(180, self.esp32_prompt)
        log_debug("Device boots well")

    def fwupdate(self):
        self.check_device_stat()
        self.program_keys()
        self.program_flash()

    def put_devreg_data_in_dut(self):
        self.pexp.close()
        cmd = "esptool.py -p /dev/ttyUSB{} --chip esp32 -b 460800 --before default_reset "\
              "--after hard_reset write_flash --flash_mode dio --flash_freq 40m "         \
              "--flash_size 16MB 0xfff000  /tftpboot/e.s.{}".format(self.row_id, self.row_id)
        log_debug(cmd)

        [output, rv] = self.cnapi.xcmd(cmd)
        if int(rv) > 0:
            otmsg = "Flash e.s.{} into DUT failed".format(self.row_id)
            error_critical(otmsg)
        
        ## The waiting time
        pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)
        self.pexp.expect_only(60, "DEVREG:") # The security check will fail if littlefs isn't mounted

    def check_devreg_data(self):
        output = self.pexp.expect_get_output("info", self.esp32_prompt, timeout=5)
        info = {}
        mac_format = self.mac.upper()
        # value is our expected string
        devreg_data_dict = {'"system_id"'   : self.board_id,
                            '"bom_rev"': "{}{}".format((hex(int(self.bom_rev.split('-')[0])).replace('0x','')).zfill(6), hex(int(self.bom_rev.split('-')[1])).replace('0x', '').zfill(2)),
                            '"mac_addr"' : mac_format,
                            '"devreg_check"': 'PASS'}

        for key in devreg_data_dict:
            regex = re.compile(r"{}:\"(\w+)\"".format(key))
            data_list = regex.findall(output)
            info[key] = data_list[0]

        for key in devreg_data_dict:
            if devreg_data_dict[key] != info[key]:
                error_critical("{}: {}, not {}".format(key, info[key], devreg_data_dict[key]))
            else:
                log_debug("{}: {}".format(key, info[key]))

    def check_littlefs_mount(self):
        time.sleep(90)
        self.pexp.expect_lnxcmd(timeout=3, pre_exp=self.esp32_prompt, action="littlefs_get_info", 
                                post_exp="littlefs_cmd: mount", retry=80)

    def _check_is_homekit_done_mod_cmd(self, cmd):

        log_debug('_check_is_homekit_done')
        rsp = self.pexp.expect_get_output("hk -l", self.esp32_prompt, timeout=5)
        rsp = rsp.split(',')
        rsp = rsp[0]
        log_debug(rsp)
        res = re.search(r"\"tokenid\":\"(.*)\"", rsp, re.S)
        self.tokenid_dut = res.group(1).upper()
        log_info('tokenid = {}'.format(self.tokenid_dut))
        if self.tokenid_dut == "":
            self.is_homekit_done_before = False
        else:
            self.is_homekit_done_before = True

        if self.is_homekit_done_before is True:
            cmd.append('-i field=last_homekit_device_token_id,format=string,value={}'.format(
                self.tokenid_dut))

        return cmd

    def registration(self, regsubparams = None):
        log_debug("Starting to do registration ...")
        if regsubparams is None:
            regsubparams = self.access_chips_id()

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        if self.sem_ver == "" or self.sw_id == "" or self.fw_ver == "":
            clientbin = "/usr/local/sbin/client_x86_release"
            regparam = [
                "-h prod.udrs.io",
                "-k " + self.pass_phrase,
                regsubparams,
                reg_qr_field,
                "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
                "-o field=flash_eeprom,format=binary,pathname=" + self.eesign_path,
                "-o field=registration_id",
                "-o field=result",
                "-o field=device_id",
                "-o field=registration_status_id",
                "-o field=registration_status_msg",
                "-o field=error_message",
                "-x " + self.key_dir + "ca.pem",
                "-y " + self.key_dir + "key.pem",
                "-z " + self.key_dir + "crt.pem"
            ]
            print("WARNING: should plan to add SW_ID ... won't block this time")
        else:
            cmd = "uname -a"
            [sto, rtc] = self.cnapi.xcmd(cmd)
            if int(rtc) > 0:
                error_critical("Get linux information failed!!")
            else:
                log_debug("Get linux information successfully")
                match = re.findall("armv7l", sto)
                if match:
                    clientbin = "/usr/local/sbin/client_rpi4_release"
                else:
                    clientbin = "/usr/local/sbin/client_x86_release"

            regparam = [
                "-h stage.udrs.io",
                "-k " + self.pass_phrase,
                regsubparams,
                reg_qr_field,
                "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
                "-i field=fcd_version,format=hex,value=" + self.sem_ver,
                "-i field=sw_id,format=hex,value=" + self.sw_id,
                "-i field=sw_version,format=hex,value=" + self.fw_ver,
                "-o field=flash_eeprom,format=binary,pathname=" + self.eesign_path,
                "-o field=registration_id",
                "-o field=result",
                "-o field=device_id",
                "-o field=registration_status_id",
                "-o field=registration_status_msg",
                "-o field=error_message",
                "-x " + self.key_dir + "ca.pem",
                "-y " + self.key_dir + "key.pem",
                "-z " + self.key_dir + "crt.pem"
            ]

        if self.homekit_dict[self.board_id] is True:
            regparam = self._check_is_homekit_done_mod_cmd(regparam)
        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        log_debug('cmd = \n{}'.format(cmd))

        # clit = ExpttyProcess(self.row_id, cmd, "\n")
        # clit.expect_only(30, "Security Service Device Registration Client")
        # clit.expect_only(30, "Hostname")
        # clit.expect_only(30, "field=result,format=u_int,value=1")

        [self.client_x86_rsp, rtc] = self.cnapi.xcmd(cmd)
        log_debug('client_x86 return code = \n{}'.format(rtc))

        if (int(rtc) > 0):
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

        self.pass_devreg_client = True

        log_debug("Excuting client registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()

    def homekit_setup_after_registration(self):
        if self.is_homekit_done_before is False:
            self.__gen_homkit_token_csv_txt(self.client_x86_rsp)

        else:
            self.__check_tokenid_match(self.client_x86_rsp)

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
        file_dir = os.path.join('/home/ubnt/usbdisk', 'LOCK-R_hk_output')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

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

        is_file = os.path.isfile(csv_path) and os.path.isfile(txt_path)
        log_info('csv_path = {}'.format(csv_path))
        log_info('txt_path = {}'.format(txt_path))
        log_info('Token CSV & uuid TXT files generate {}'.format('success' if is_file else 'fail'))
        if is_file:
            log_info('Write Homekit token_id/token/plan_id/uuid in Device...')
            rsp = self.pexp.expect_get_output("hk -k tokenid -v {}".format(info_dict['tokenid']), self.esp32_prompt,
                                              timeout=5)
            rsp = self.pexp.expect_get_output("hk -k token -v {}".format(info_dict['token']), self.esp32_prompt,
                                              timeout=5)
            rsp = self.pexp.expect_get_output("hk -k plainid -v {}".format(info_dict['product_plan_id']),
                                              self.esp32_prompt, timeout=5)
            rsp = self.pexp.expect_get_output("hk -k uuid -v {}".format(info_dict['uuid']), self.esp32_prompt,
                                              timeout=5)
            log_info('Check Homekit token_id/token/plan_id/uuid in Device...')
            rsp = self.pexp.expect_get_output("hk -l", self.esp32_prompt, timeout=5)
            for idx in info_dict:
                if info_dict[idx] in rsp:
                    log_info('{} check PASS'.format(idx))
                else:
                    log_info('{} check FAIL'.format(idx))
                    is_file = False
                    break
        return is_file

    def __check_tokenid_match(self, client_x86_rsp):
        regex = re.compile(r'token_id,format=string,value=(.*)')
        tokenid_client = regex.findall(client_x86_rsp+'\n')[0]

        log_info('tokenid_client = {}'.format(tokenid_client))
        log_info('tokenid_dut = {}'.format(self.tokenid_dut))

        is_tokenid_match = tokenid_client == self.tokenid_dut
        log_info('tokenid_dut & tokenid_client are {}match'.format('' if is_tokenid_match else 'NOT '))
        if is_tokenid_match is False:
            log_info('So server treat this DUT as first time HK registration')
            self.__gen_homkit_token_csv_txt(client_x86_rsp)

        return is_tokenid_match

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        msg(5, "Open serial port successfully ...")
    
        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(10, "Finish FW updating ...")

        if PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(15, "Finish erasing ee files ...")
            self.data_provision_4k(netmeta=self.devnetmeta)
            msg(20, "Finish 4K binary generating ...")

        if DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration(regsubparams=self.regsubparams)
            msg(40, "Finish doing registration ...")

            if self.homekit_dict[self.board_id] is True:
                self.homekit_setup_after_registration()
                msg(45, "Finish Homekit setup ...")

        if FLASH_DEVREG_DATA is True:
            self.put_devreg_data_in_dut()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if DEVREG_CHECK_ENABLE is True:
            self.check_devreg_data()
            msg(70, "Finish checking MAC in DUT ...")

        if SPIFF_FORMAT_CHECK is True:
            self.check_littlefs_mount()
            msg(90, "Littlefs mounted")

        msg(100, "Completing registration ...")
        self.close_fcd()

def main():
    factory_general = UFPESP32FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()
