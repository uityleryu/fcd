#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.pserial import SerialExpect
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info
from xmodem import XMODEM

import sys
import time
import os
import re
import traceback
import base64
import zlib

from pprint import pformat
from collections import OrderedDict


DOHELPER_ENABLE = True
REGISTER_ENABLE = True
SET_SKU_ENABLE = True
CHECK_MAC_ENABLE = True
CHECK_BOMID_CORRECT = True

class UFPEFR32FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UFPEFR32FactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        # script specific vars
        self.linux_prompt = "EH:"
        self.prodclass = "0014"

        self.baudrate = 921600
        self._reseted_flag = False

        # check MAC
        self.cmd_version = "VERSION"
        self.cmd_reset = "RESET"
        self.cmd_erase_devreg = "ERASEDEVREG"

        self.mac_check_dict = {
            'a911': True,
            'a941': True,
            'a912': False,
            'a915': True,
            'a918': True,
            'a919': True,
            'ee76': True,
            'a922': True,
            'ec51': True,
        }

        self.bom_check_dict = {
            'a911': False,
            'a941': False,
            'a912': False,
            'a915': False,
            'a918': False,
            'a919': False,
            'ee76': False,
            'a922': False,
            'ec51': True,
        }

        self.qrcode_dict = {
            'a911': False,
            'a941': False,
            'a912': False,
            'a915': False,
            'a918': False,
            'a919': True,
            'ee76': True,
            'a922': True,
            'ec51': False,
        }

        self.sku_dict = {
            'a911': True,
            'a941': False,  # doorlock homekit set sku in FTU
            'a912': False,
            'a915': False,
            'a918': False,
            'a919': True,
            'ee76': False,
            'a922': True,
            'ec51': False,
        }

        self.homekit_dict = {
            'a911': False,
            'a941': True,
            'a912': False,
            'a915': False,
            'a918': False,
            'a919': False,
            'ee76': False,
            'a922': False,
            'ec51': False,
        }

        # number of Ethernet
        self.ethnum = {
            'a911': "0",
            'a941': "0",
            'a912': "0",
            'a915': "0",
            'a918': "0",
            'a919': "0",
            'ee76': "0",
            'a922': "0",
            'ec51': "0",
        }

        # number of WiFi
        self.wifinum = {
            'a911': "0",
            'a941': "0",
            'a912': "0",
            'a915': "0",
            'a918': "0",
            'a919': "0",
            'ee76': "0",
            'a922': "1",
            'ec51': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'a911': "1",
            'a941': "1",
            'a912': "1",
            'a915': "1",
            'a918': "1",
            'a919': "1",
            'ee76': "1",
            'a922': "1",
            'ec51': "1",
        }

    def prepare_server_need_files(self):
        log_debug("Starting to create a 64KB binary file ...")
        self.gen_rsa_key()

        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe)

        sstr = [
            flasheditor,
            "-F",
            "-f " + self.eebin_path,
            "-r 113-{0}".format(self.bom_rev),
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
        log_debug('sstr = {}'.format(sstr))

        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Generating " + self.eebin_path + " file failed!!")
        else:
            log_debug("Generating " + self.eebin_path + " files successfully")

        # check if device connect
        if self.board_id == "a912":
            self._sense_cmd_before_registration()

        # get uid
        try:
            uid_rtv = self.ser.execmd_getmsg("GETUID", waitperiod=3, ignore=True)
            log_info('uid_rtv = {}'.format([uid_rtv]))
            if uid_rtv == "":
                error_critical("Can't read the UID message")

            if self.board_id == "a919" or self.board_id == "a922":
                res = re.search(r"UNIQUEID:8-([a-fA-Z0-9]{16})\n", uid_rtv, re.S)
            elif self.board_id == "ec51":
                res = re.search(r"UNIQUEID:27-(.*)\r\n", uid_rtv, re.S)
            else:
                res = re.search(r"UNIQUEID:27-(.*)\n", uid_rtv, re.S)

            self.uid = res.group(1)

            cpuid_rtv = self.ser.execmd_getmsg("GETCPUID", ignore=True)
            if self.board_id == "ec51":
                res = re.search(r"CPUID:([a-zA-Z0-9]{8})\r", cpuid_rtv, re.S)
            else:
                res = re.search(r"CPUID:([a-zA-Z0-9]{8})\n", cpuid_rtv, re.S)
            self.cpuid = res.group(1)

            jedecid_rtv = self.ser.execmd_getmsg("GETJEDEC", ignore=True)
            if self.board_id == "ec51":
                res = re.search(r"JEDECID:([a-fA-F0-9]{8})\r", jedecid_rtv, re.S)
            else:
                res = re.search(r"JEDECID:([a-fA-F0-9]{8})\n", jedecid_rtv, re.S)
            self.jedecid = res.group(1)
        except Exception as e:
            log_debug("Extract UID, CPUID and JEDEC failed")
            log_debug("{}".format(traceback.format_exc()))
            error_critical("{}\n{}".format(sys.exc_info()[0], e))

        def trim_information_for_ee76():
            """
            Trim redundant error code output.
            """
            if self.board_id == 'ee76':
                self.uid = self.uid[0:54]
                self.cpuid = self.cpuid[0:8]
                self.jedecid = self.jedecid[0:8]
        trim_information_for_ee76()

        log_info('uid = {}'.format(self.uid))
        log_info('cpuid = {}'.format(self.cpuid))
        log_info('jedecid = {}'.format(self.jedecid))
        log_info("Extract UID, CPUID and JEDEC successfully")

    def _sense_cmd_before_registration(self):

        log_debug("check dut connection".center(60, "="))
        rtv = self.ser.execmd_getmsg(cmd="app 20", waitperiod=0, sleep_time=0.5)
        log_debug('command "app 20" rtv = {}'.format([rtv]))
        if rtv == "" or rtv == "app 20\n":
            error_critical("DUT is not connected, please check the connection")
        log_debug("DUT is connected")

        log_debug("disable all sensors".center(60, "="))
        cmd_clr_all_disable = "app 43 02 05 00 00 32 00 00 96 00 00 05 20 03 23 05 0F 15 04 05 07 00 00 0F 0A 3C"
        log_debug(cmd_clr_all_disable+"\n")
        self.ser.execmd(cmd=cmd_clr_all_disable)
        time.sleep(2)

    def _check_is_homekit_done_mod_cmd(self, cmd):

        log_debug('_check_is_homekit_done')

        rsp = self.ser.execmd_getmsg("FCDMFGDATAHKTOKENIDGET", ignore=True)
        res = re.search(r"TOKENID:(.*)\n", rsp, re.S)
        self.tokenid_dut = res.group(1).upper()
        log_info('tokenid = {}'.format(self.tokenid_dut))

        rsp = self.ser.execmd_getmsg("FCDMFGDATAHKSETUPCODEGET", ignore=True)
        res = re.search(r"SETUPCODE:(.*)\n", rsp, re.S)
        setupcode = res.group(1)
        log_info('setupcode = {}'.format(setupcode))

        self.is_homekit_done_before = self.tokenid_dut != 'UNKNOWN'

        log_info('DUT has {}done homekit registration before'.format(
            '' if self.is_homekit_done_before else 'NOT '))

        if self.is_homekit_done_before is True:
            cmd.append('-i field=last_homekit_device_token_id,format=string,value={}'.format(
                self.tokenid_dut))

        return cmd

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

    def homekit_setup_after_registration(self):
        if self.is_homekit_done_before is False:
            self.__gen_homkit_token_csv_txt(self.client_x86_rsp)
        else:
            self.__check_tokenid_match(self.client_x86_rsp)

    def registration(self):
        log_debug("Starting to do registration ...")

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
                clientbin = "/usr/local/sbin/client_x86_release_20190507"

        cmd = [
            "sudo {0}".format(clientbin),
            '-h prod.udrs.io',
            "-k " + self.pass_phrase,
            "-i field=product_class_id,format=hex,value=" + self.prodclass,
            "-i field=flash_jedec_id,format=hex,value=" + self.jedecid,
            "-i field=flash_uid,format=hex,value=" + self.uid,
            "-i field=cpu_rev_id,format=hex,value=" + self.cpuid,
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

        if self.qrcode_dict[self.board_id]:
            cmd.append("-i field=qr_code,format=hex,value=" + self.qrhex)

        if self.homekit_dict[self.board_id] is True:
            cmd = self._check_is_homekit_done_mod_cmd(cmd)

        cmdj = ' '.join(cmd)
        log_debug('cmd = \n{}'.format(pformat(cmd, indent=4)))
        log_debug('cmdj = \n{}'.format(cmdj))

        [self.client_x86_rsp, rtc] = self.fcd.common.xcmd(cmdj)
        log_debug('client_x86 return code = \n{}'.format(rtc))

        if (int(rtc) > 0):
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

        cmd[2] = "-k " + self.input_args.pass_phrase
        poscmd = ' '.join(cmd)
        print("CMD: \n" + poscmd)

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign_path)

        log_debug("Add the date code in the devreg binary file")

    def put_devreg_data_in_dut(self):
        log_debug("DUT request the signed 64KB file ...")

        if self.board_id in ["a912", "a918", "a919", "ee76", "a922"]:
            self.ser.execmd_expect("xstartdevreg", "begin upload")
        elif self.board_id in ["a911", "a941", "a915", "a920", "ec51"]:
            self.ser.execmd("xstartdevreg")
            time.sleep(0.5)

        log_debug("Starting xmodem file transfer ...")
        if self.board_id in ["a919", "ee76", "a922"]:
            modem = XMODEM(self.ser.xmodem_getc, self.ser.xmodem_putc)
        else:
            modem = XMODEM(self.ser.xmodem_getc, self.ser.xmodem_putc, mode='xmodem1k')

        stream = open(self.eesign_path, 'rb')
        modem.send(stream, retry=64)

    def _read_version(self, msg):
        # only for LOCK-R(a911) and 60G-LAS(a918)
        log_info('Version information = {}'.format(msg))
        msg_versw = msg.split("VER-SW:")[-1].split("\r")[0].split(";")
        msg_verhw = msg.split("VER-HW:")[-1].split("\r")[0].split(";")
        msg_verswhw = msg_versw + msg_verhw
        version = {}
        for ii in msg_verswhw:
            version[ii.split("-", 1)[0]] = ii.split("-", 1)[1]
        return version

    def _reset(self):
        # it needs to reset for updating the MAC, otherwise the MAC would be like "VER-HW:MAC-ff.ff.ff.ff.ff.ff"
        log_info('Sending the reset command')
        try:
            rtv_reset = self.ser.execmd_getmsg(self.cmd_reset, ignore=True)
            log_info('rtv_reset = {}'.format(rtv_reset))
        except Exception as e:
            log_info('')
            log_info("{}".format(traceback.format_exc()))
            log_info("{}".format(sys.exc_info()[0]))
            log_info("{}".format(e))
            log_info('')
            log_info('This might be the garbled code of the return value in LOCK_R (a911)')

        self._reseted_flag = True
        time.sleep(3)

        if self.board_id == "a919":
            self.ser.execmd("FCDSTOP")
            time.sleep(1)
            self.ser.execmd_expect_retry("FCDSTART", "Hold", pre_n=True)

    def set_sku(self):
        if self.sku_dict[self.board_id] is False:
            log_debug("Skip setting SKU ...")
            return

        # parameters
        cmd_set_sku = 'FCDSKUSET:{sku}' if self.board_id != 'a941' else 'FCDMFGDATASKUSET:{sku}'
        cmd_get_sku = 'FCDSKUGET' if self.board_id != 'a941' else 'FCDMFGDATASKUGET'
        expected_rsp = 'SKU: {sku}'

        '''
            The value stored in the FW are as the following
            Unknown: 0
            US: 1
            EU: 2
            Scandi: 3
        '''
        region_name_dict = {
            "World": 'EU',
            "USA/Canada": 'US',
            'EU': 'EU',
            "Scandi": 'SCANDI'}

        # set_sku
        log_debug("Starting to set SKU")
        log_info("self.sku_dict = {}".format(self.sku_dict))
        log_info('self.region_name = {}'.format(self.region_name))

        if self.region_name not in list(region_name_dict.keys()):
            msg = 'self.region_name ({}) is not in region_name_dict {}, Skip setting SKU ...'
            error_critical(msg.format(self.region_name, region_name_dict))
            return

        sku_code = region_name_dict[self.region_name]
        cmd_set_sku = cmd_set_sku.format(sku=sku_code)
        log_info("cmd_set_sku = {}".format(cmd_set_sku))
        rsp = self.ser.execmd_getmsg(cmd_set_sku)
        log_info("rsp = {}".format(rsp))

        time.sleep(0.5)

        self._reset()

        # check SKU
        log_info("cmd_get_sku = {}".format(cmd_get_sku))
        rtv_get_sku = self.ser.execmd_getmsg(cmd_get_sku)
        log_info("rtv_get_sku = {}".format(rtv_get_sku))

        expected_rsp = expected_rsp.format(sku=sku_code)
        if expected_rsp not in rtv_get_sku:
            error_critical('expected_rsp ({}) not in rtv_get_sku, set SKU fail..'.format(expected_rsp))
        else:
            log_debug('expected_rsp ({}) in rtv_get_sku, set SKU success..'.format(expected_rsp))

    def check_mac(self):
        log_debug("Starting to check MAC")
        log_info("self.mac_check_dict = {}".format(self.mac_check_dict))

        if self.mac_check_dict[self.board_id] is False:
            log_debug("skip check the MAC in DUT ...")
            return

        if self._reseted_flag is not True:
            self._reset()
        else:
            log_info('Have reseted before, skip this time')

        rtv_verison = self.ser.execmd_getmsg(self.cmd_version, ignore=True)

        version = self._read_version(rtv_verison)
        for key, value in version.items():
            log_info("{} = {}".format(key, value))

        dut_mac = version["MAC"].replace(".", "").upper()
        expect_mac = self.mac.upper()
        log_info("MAC_DUT    = {}".format(dut_mac))
        log_info("MAC_expect = {}".format(expect_mac))
        log_info("FW version in DUT = {}".format(version["SWv"]))

        if dut_mac == expect_mac:
            log_debug('MAC_DUT and MAC_expect are match')
        else:
            error_critical("MAC_DUT and MAC_expect are NOT match")

    def check_bom(self):
         log_debug("Starting to check BOM ID")
         log_info("self.bom_check_dict = {}".format(self.bom_check_dict))

         if self.bom_check_dict[self.board_id] is False:
             log_debug("skip check the BOM ID in DUT ...")
             return

         rtv_verison = self.ser.execmd_getmsg(self.cmd_version, ignore=True)

         version = self._read_version(rtv_verison)
         for key, value in version.items():
             log_info("{} = {}".format(key, value))

         dut_bom = version["BOMPCB"]
         expect_bom = '113-' + self.bom_rev
         log_info("BOM_REV_DUT    = {}".format(dut_bom))
         log_info("BOM_REV_expect = {}".format(expect_bom))
         log_info("FW version in DUT = {}".format(version["SWv"]))

         if dut_bom == expect_bom:
             log_debug('BOM_REV_DUT and BOM_REV_expect are match')
         else:
             error_critical("BOM_REV_DUT and BOM_REV_expect are NOT match")
   
    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        serialcomport = "/dev/{0}".format(self.dev)
        serial_obj = serialExpect(port=serialcomport, baudrate=self.baudrate)
        self.set_serial_helper(serial_obj=serial_obj)
        time.sleep(1)

        msg(5, "Open serial port successfully ...")
        time.sleep(1)
        self.ser.execmd("")
        if self.board_id == "a919":
            self.ser.execmd("FCDSTOP")
            time.sleep(1)
            self.ser.execmd_expect_retry("FCDSTART", "Hold", pre_n=True)

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Finish erasing ee files ...")
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")

            if self.homekit_dict[self.board_id] is True:
                self.homekit_setup_after_registration()
                msg(50, "Finish Homekit setup ...")

            self.put_devreg_data_in_dut()
            msg(60, "Finish doing signed file and EEPROM checking ...")

        if SET_SKU_ENABLE is True:
            self.set_sku()
            msg(70, "Finish setting SKU ...")

        if CHECK_MAC_ENABLE is True:
            self.check_mac()
            msg(80, "Finish checking MAC in DUT ...")

        if CHECK_BOMID_CORRECT is True:
            self.check_bom()
            msg(90, "Finish checking BOM ...")  

        if self.board_id == "a919":
            self.ser.execmd(cmd="BOOTFW:1")
            self.ser.expect_only("erase", timeout=10)
            self.ser.expect_only("write", timeout=20)
            self.ser.expect_only("Hello Mediatek", timeout=60)
            self.ser.execmd("")
            self.ser.execmd("")
            rsp = self.ser.execmd_getmsg("ver")
            if "SDK Ver" not in rsp:
                error_critical("Can't find SDK version, maybe not in the FTU image ... !!!")

        msg(100, "Completing registration ...")
        self.close_fcd()

class serialExpect(SerialExpect):
    def execmd_getmsg(self, cmd="", waitperiod=2, sleep_time=0.5, pre_n=True, print_en=True, ignore=False):
        if pre_n is True:
            self._enter()

        if cmd != "":
            cmd = "{0}\n".format(cmd)
            self.ser.write(cmd.encode())
            self.ser.flush()
            time.sleep(sleep_time)

        outstream = []
        stoptm = time.time() + waitperiod
        while True:
            if self.ser.inWaiting() > 0:
                out = self.ser.read(self.ser.in_waiting)
                if ignore:
                    dout = out.decode("utf-8", "ignore")
                else:
                    dout = out.decode()
                outstream.append(dout)
            if time.time() > stoptm:
                break

            time.sleep(0.1)

        jotsm = "".join(outstream)

        if print_en is True:
            print(jotsm)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return jotsm

def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        udm_factory_general = UFPEFR32FactoryGeneral()
        udm_factory_general.run()


if __name__ == "__main__":

    try:
        main()
    except Exception:
        error_critical(traceback.format_exc())

