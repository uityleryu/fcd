#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
import re
import stat
import filecmp
import argparse
import json
import PAlib
import datetime
import tarfile
import shutil
import subprocess
import data.constant as CONST

from PAlib.Framework.fcd.common import Tee, Common
from PAlib.Framework.fcd.helper import FCDHelper
from PAlib.Framework.fcd.logger import log_debug, log_info, log_error, msg, error_critical
from PAlib.Framework.fcd.singleton import errorcollecter
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.devices.usp_pdu_pro_ed12 import USP_PDU_PRO
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread
from uuid import getnode as get_mac


class ScriptBase(object):
    __version__ = "1.0.54"
    __authors__ = "PA team"
    __contact__ = "fcd@ui.com"

    def __init__(self):
        self.power_supply = None
        self.cnapi = Common()
        self.input_args = self._init_parse_inputs()
        self._init_share_var()
        self.fcd = FCDHelper()
        self._init_log()
        # must be set by set_pexpect_helper()
        # example usuage - self.pexp.{function}(...)
        self.__pexpect_obj = None
        self.__serial_obj = None
        self.__ssh_client_obj = None
        self.log_upload_failed_alert_en = False

        self.version_scriptbase = self.__version__
        self.version_PAlib = PAlib.__version__
        with open(self.fcd_version_info_file_path, 'r') as f:
            self.version_iso = f.read().rstrip('\n')

        self.cnapi.print_current_fcd_version(file=self.fcd_version_info_file_path)
        print("framework version: " + self.__version__)
        print("PAlib version: " + PAlib.__version__)
        self._encrpyt_passphrase_for_log()
        log_debug(str(self.input_args))

    @property
    def pexp(self):
        if self.__pexpect_obj is not None:
            return self.__pexpect_obj
        else:
            error_critical("No pexpect obj exists!")

    @property
    def ser(self):
        if self.__serial_obj is not None:
            return self.__serial_obj
        else:
            error_critical("No serial obj exists!")

    @property
    def session(self):
        if self.__ssh_client_obj is not None:
            return self.__ssh_client_obj
        else:
            error_critical("No ssh client obj exists!")

    def set_ps_port_relay_on(self, ps_ssid="ed12"):
        if self.power_supply is None:
            if ps_ssid == "ed12":
                self.power_supply = USP_PDU_PRO(ip=self.ps_ipaddr)
                if self.power_supply.connect() is False:
                    rmsg = "Can't make SSH connection with the {}, FAIL!!!".format(ps_ssid)
                    error_critical(rmsg)
                else:
                    rmsg = "SSH connection with the {}".format(ps_ssid)
                    log_debug(rmsg)
            else:
                error_critical("GU:{}, Power supply doesn't support, FAIL!!!".format(self.ps_ssid))
        else:
            log_debug("Power supply instance is existed")

        self.power_supply.set_port_relay_on(port=int(self.power_supply_port))
        time.sleep(2)

    def set_ps_port_relay_off(self, ps_ssid="ed12"):
        if self.power_supply is None:
            if ps_ssid == "ed12":
                self.power_supply = USP_PDU_PRO(ip=self.ps_ipaddr)
                if self.power_supply.connect() is False:
                    rmsg = "Can't make SSH connection with the {}, FAIL!!!".format(ps_ssid)
                    error_critical(rmsg)
                else:
                    rmsg = "SSH connection with the {}".format(ps_ssid)
                    log_debug(rmsg)
            else:
                error_critical("GU:{}, Power supply doesn't support, FAIL!!!".format(self.ps_ssid))
        else:
            log_debug("Power supply instance is existed")

        self.power_supply.set_port_relay_off(port=int(self.power_supply_port))
        time.sleep(4)

    def set_sshclient_helper(self, ssh_client):
        self.__ssh_client_obj = ssh_client

    def set_pexpect_helper(self, pexpect_obj):
        self.__pexpect_obj = pexpect_obj
        self.fcd.set_pexpect_obj(pexpect_obj)

    def set_serial_helper(self, serial_obj):
        self.__serial_obj = serial_obj
        self.fcd.set_serial_obj(serial_obj)

    def _init_log(self, log_file_path=None):
        if log_file_path is None:
            log_file_path = os.path.join("/tftpboot/", "log_slot" + self.row_id + ".log")
        if os.path.isfile(log_file_path):
            os.remove(log_file_path)
        Tee(log_file_path, 'w')

    def _init_share_var(self):
        # feature flags
        self.FCD_TLV_data = True

        # prompt related
        self.bootloader_prompt = "u-boot>"
        self.linux_prompt = "#"
        self.cmd_prefix = r"go $ubntaddr "

        # DUT log-in info
        self.user = "ubnt"
        self.password = "ubnt"

        # fcd related
        self.fcd_version_info_file = "version.txt"

        cmd = "who | awk 'NR==1 { print $1 }'"
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("Executing linux command failed!!")
        else:
            sto = sto.strip()
            self.fcd_user = sto

        cmd = "uname -a"
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("Get linux information failed!!")
        else:
            log_debug("Get linux information successfully")
            match = re.findall("armv7l", sto)
            if match:
                self.fcd_version_info_file_path = os.path.join("/home/ubnt", self.fcd_version_info_file)
                self.fcd_user = "ubnt"
                self.fcd_passw = "ubnt"
            else:
                self.fcd_version_info_file_path = os.path.join("/home", self.fcd_user, "Desktop", self.fcd_version_info_file)
                self.fcd_user = "user"
                self.fcd_passw = "live"

        # images is saved at /tftpboot/images, tftp server searches files start from /tftpboot
        self.tftpdir = "/tftpboot"
        self.dut_tmpdir = "/tmp"
        self.image = "images"
        self.tools = "tools"
        self.helper_path = ""
        self.fwdir = os.path.join(self.tftpdir, self.image)
        self.fcd_toolsdir = os.path.join(self.tftpdir, self.tools)
        self.fcd_commondir = os.path.join(self.tftpdir, self.tools, "common")
        self.fcd_scripts_dir = os.path.join('/usr', 'local', 'sbin')
        self.PAlib_dir = os.path.join(self.fcd_scripts_dir, 'PAlib')

        cmd = "uname -a"
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("Get linux information failed!!")
        else:
            log_debug("Get linux information successfully")
            match = re.findall("armv7l", sto)
            if match:
                self.eepmexe   = "aarch64-rpi4-64k-ee"
                self.eepmexe4k = "aarch64-rpi4-4k-ee"
            else:
                self.eepmexe   = "x86-64k-ee"
                self.eepmexe4k = "x86-4k-ee"

        '''
           Will be defined by the specifi model script
           Ex: /tmp/uvp
        '''
        self.devregpart = ""
        '''
            This is the host name of the devreg server, if there is any change,
            please approach Mike.Tyler
        '''
        self.devreg_hostname = "prod.udrs.io"
        self.helperexe = ""
        self.product_class = "basic"

        # EEPROM file in binary format generated by flash editor
        self.eegenbin = "e.gen.{}".format(self.row_id)

        # EEPROM file in binary format generated by helper utility
        self.eebin = "e.b.{}".format(self.row_id)

        # EEPROM file in text format generated by helper utility
        self.eetxt = "e.t.{}".format(self.row_id)

        # compress EEPROM files
        self.eetgz = "e.{}.tgz".format(self.row_id)

        # Get the signed EEPROM from security server
        self.eesign = "e.s.{}".format(self.row_id)

        # After adding date code on signed 64KB
        self.eesigndate = "e.sd.{}".format(self.row_id)

        # retrieve the content from EEPROM partition of DUT
        self.eechk = "e.c.{}".format(self.row_id)

        # extract the FCD information from the EEPROM partition offset 0xd000
        self.eeorg = "e.org.{}".format(self.row_id)

        # RSA key file
        self.rsakey = "dropbear_key.rsa.{}".format(self.row_id)

        # DSS key file
        self.dsskey = "dropbear_key.dss.{}".format(self.row_id)

        # EEPROM related files path on FCD
        # EX: /tftpboot/e.gen.0
        self.eegenbin_path = os.path.join(self.tftpdir, self.eegenbin)

        # EX: /tftpboot/e.b.0
        self.eebin_path = os.path.join(self.tftpdir, self.eebin)

        # EX: /tftpboot/e.t.0
        self.eetxt_path = os.path.join(self.tftpdir, self.eetxt)

        # EX: /tftpboot/e.0.tgz
        self.eetgz_path = os.path.join(self.tftpdir, self.eetgz)

        # EX: /tftpboot/e.s.0
        self.eesign_path = os.path.join(self.tftpdir, self.eesign)

        # EX: /tftpboot/e.sd.0
        self.eesigndate_path = os.path.join(self.tftpdir, self.eesigndate)

        # EX: /tftpboot/e.c.0
        self.eechk_path = os.path.join(self.tftpdir, self.eechk)

        # EX: /tftpboot/e.org.0
        self.eeorg_path = os.path.join(self.tftpdir, self.eeorg)

        # EX: /tftpboot/dropbear_key.rsa.0
        self.rsakey_path = os.path.join(self.tftpdir, self.rsakey)
        self.dsskey_path = os.path.join(self.tftpdir, self.dsskey)

        # DUT IP
        baseip = 31
        self.dutip = "192.168.1." + str((int(self.row_id) + baseip))

        self.fcd_id = ""
        self.sem_ver = ""
        self.sw_id = ""
        self.fw_ver = ""

        self.qrhex = ""
        # The HEX of the QR code
        if self.qrcode is not None:
            self.qrhex = self.qrcode.encode('utf-8').hex()

        self.activate_code_hex = ""
        # The HEX of the QR code
        if self.activate_code is not None:
            self.activate_code_hex = self.activate_code.encode('utf-8').hex()

        # HTTP server
        baseport = 8000
        self.http_port = int(self.row_id) + baseport
        self.http_srv = ""

        # Test result Field
        self.test_result = 'Fail'
        self.test_starttime_datetime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        self.test_endtime_datetime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        self.test_duration = ''
        self.error_code = ''
        self.error_function = ''
        self.progress = 0
        self.pass_devreg_client = False
        try:
            self.teststation_mac = ':'.join(("%012X" % get_mac())[i:i + 2] for i in range(0, 12, 2))
        except Exception as e:
            self.teststation_mac = str(e)

    def _init_parse_inputs(self):
        parse = argparse.ArgumentParser(description="FCD tool args Parser")
        parse.add_argument('--prdline', '-pline', dest='product_line', help='Active Product Line', default=None)
        parse.add_argument('--prdname', '-pname', dest='product_name', help='Active Product Name', default=None)
        parse.add_argument('--slot', '-s', dest='row_id', help='Slot id', default=None)
        parse.add_argument('--dev', '-d', dest='dev', help='UART device number. ex:ttyUSB0, ttyUSB1', default=None)
        parse.add_argument('--tftp_server', '-ts', dest='tftp_server', help='FCD host IP', default=None)
        parse.add_argument('--board_id', '-b', dest='board_id', help='System ID, ex:eb23, eb21', default=None)
        parse.add_argument('--erasecal', '-e', dest='erasecal', help='Erase calibration data selection', default=None)
        parse.add_argument('--erase_devreg', '-ed', dest='erase_devreg', help='Erase devreg data selection',
                           default=None)

        parse.add_argument('--mac', '-m', dest='mac', help='MAC address', default=None)
        parse.add_argument('--pass_phrase', '-p', dest='pass_phrase', help='Passphrase', default=None)
        parse.add_argument('--key_dir', '-k', dest='key_dir', help='Directory of key files', default=None)
        parse.add_argument('--bom_rev', '-bom', dest='bom_rev', help='BOM revision', default=None)
        parse.add_argument('--qrcode', '-q', dest='qrcode', help='QR code', default=None)
        parse.add_argument('--activate_code', '-ac', dest='activate_code', help='Activate Code', default=None)
        parse.add_argument('--region', '-r', dest='region', help='Region Code', default=None)
        parse.add_argument('--ps_ipaddr', '-psaddr', dest='ps_ipaddr', help='Power supply state', default=None)
        parse.add_argument('--ps_state', '-pss', dest='ps_state', help='Power supply state', default=None)
        parse.add_argument('--ps_port', '-pspr', dest='ps_port', help='Power supply port', default=None)
        parse.add_argument('--toplevelbom', '-tlb', dest='toplevelbom', help='Top level BOM', default=None)
        parse.add_argument('--mebom', '-meb', dest='mebom', help='ME BOM', default=None)
        parse.add_argument('--no-upload', dest='upload', help='Disable uploadlog to cloud', action='store_false')
        parse.set_defaults(upload=True)

        args, _ = parse.parse_known_args()
        self.product_line = args.product_line
        self.product_name = args.product_name
        self.row_id = args.row_id if args.row_id is not None else "0"
        self.dev = args.dev
        self.tftp_server = args.tftp_server
        self.board_id = args.board_id if args.board_id is not None else "na"
        self.erasecal = args.erasecal
        self.erase_devreg = args.erase_devreg
        self.mac = args.mac.lower() if args.mac is not None else args.mac
        self.premac = "fc:ec:da:00:00:1" + self.row_id
        self.pass_phrase = args.pass_phrase
        self.key_dir = args.key_dir
        self.ps_ipaddr = args.ps_ipaddr
        if args.ps_state == "True":
            self.ps_state = True
        else:
            self.ps_state = False

        self.power_supply_port = args.ps_port
        self.tlb_rev = args.toplevelbom
        self.meb_rev = args.mebom
        self.bom_rev = args.bom_rev
        self.qrcode = args.qrcode
        self.activate_code = args.activate_code
        self.region = args.region
        self.region_name = CONST.region_names[CONST.region_codes.index(self.region)] if self.region is not None else None
        self.fwimg = "{}.bin".format(self.board_id)
        self.fwimg = "{}-mfg.bin".format(self.board_id)
        self.upload = args.upload
        return args

    def _encrpyt_passphrase_for_log(self):
        if self.input_args.pass_phrase is not None:
            k = []
            for c in self.input_args.pass_phrase:
                k.append('{:02x}'.format(ord(c)))
            self.input_args.pass_phrase = ''.join(k)
        else:
            log_debug("No passphrase input!")

    def login(self, username="ubnt", password="ubnt", timeout=10, press_enter=False, retry=3, log_level_emerg=False):
        '''
            should be called at login console
        '''
        if press_enter is True:
            self.pexp.expect_action(timeout, "Please press Enter to activate this console", "")

        for i in range(0, retry + 1):
            post = [
                "login:",
                "Error-A12 login"
            ]
            ridx = self.pexp.expect_get_index(timeout, post)
            if ridx >= 0:
                '''
                    To give twice in order to make sure of that the username has been keyed in
                '''
                if username != "":
                    self.pexp.expect_action(10, "", username)

                if password != "":
                    self.pexp.expect_action(30, "Password:", password)

                break
            else:
                self.pexp.expect_action(timeout, "", "\003")
                print("Retry login {}/{}".format(i + 1, retry))
                timeout = 10
        else:
            raise Exception("Login exceeded maximum retry times {}".format(retry))

        if log_level_emerg is True:
            self.pexp.expect_action(10, self.linux_prompt, "dmesg -n1")

        return ridx

    def set_bootloader_prompt(self, prompt=None):
        if prompt is not None:
            self.bootloader_prompt = prompt
        else:
            print("Nothing changed. Please assign prompt!")

    def is_dutfile_exist(self, filename):
        """check if file exist on dut by shell script"""
        # ls "<filename>"; echo "RV="$?
        cmd = "ls {0}".format(filename)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

        return True

    def erase_eefiles(self):
        log_debug("Erase existed eeprom information files ...")
        files = [self.eebin, self.eetxt, self.eechk, self.eetgz, self.rsakey, self.dsskey, self.eegenbin, self.eesign,
                 self.eesigndate]

        for f in files:
            destf = os.path.join(self.tftpdir, f)
            rtf = os.path.isfile(destf)
            if rtf is True:
                log_debug("Erasing File - " + f + " ...")
                os.chmod(destf, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.remove(destf)
            else:
                log_debug("File - " + f + " doesn't exist ...")

    def ver_extract(self):
        self.sem_dotver = ""
        self.fw_dotver = ""
        fh = open(self.fcd_version_info_file_path, "r")
        complete_ver = fh.readline()
        fh.close()
        ver_re = "\d+\.\d+\.\d+"
        match = re.findall(ver_re, complete_ver)
        if match:
            print("Found matched version info " + str(match))
            if len(match) >= 2:
                self.sem_dotver = match[0]
                self.fw_dotver = match[1]
        else:
            print("No semantic version and fw version found in version.txt")

        # version mapping

        fh = open('/usr/local/sbin/Products-info.json')
        self.fsiw = json.load(fh)
        fh.close()

        # SW_ID (this name is called by Mike) like product model
        if self.product_line is not None:
            self.sw_id = self.fsiw[self.product_line][self.product_name]['SW_ID']

        # Semantic version (this name is called by Mike) like FCD version
        spt = self.sem_dotver.split(".")
        self.sem_ver = '{:04x}{:02x}{:02x}'.format(int(spt[0]), int(spt[1]), int(spt[2]))
        print("sem_ver: " + self.sem_ver)

        # Firmware version
        spt = self.fw_dotver.split(".")
        self.fw_ver = '{:04x}{:02x}{:02x}'.format(int(spt[0]), int(spt[1]), int(spt[2]))
        print("fw_ver: " + self.fw_ver)

    def access_chips_id(self):
        cmd = [
            "cat " + self.eetxt_path,
            "|",
            'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
            "|",
            'grep -v \"eeprom\"',
            "|",
            "tr '\\n' ' '"
        ]
        cmdj = ' '.join(cmd)
        [sto, rtc] = self.cnapi.xcmd(cmdj)
        if int(rtc) > 0:
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")
            return sto

    def registration(self, regsubparams = None):
        log_debug("Starting to do registration ...")
        if regsubparams is None:
            regsubparams = self.access_chips_id()

        # To decide which client executed file
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

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        if self.sem_ver == "" or self.sw_id == "" or self.fw_ver == "":
            regparam = [
                "-h {}".format(self.devreg_hostname),
                "-k {}".format(self.pass_phrase),
                regsubparams,
                reg_qr_field,
                "-i field=flash_eeprom,format=binary,pathname={}".format(self.eebin_path),
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
            print("WARNING: should plan to add SW_ID ... won't block this time")
        else:
            regparam = [
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

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Security Service Device Registration Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        self.pass_devreg_client = True

        log_debug("Excuting client registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()

    def add_FCD_TLV_info(self):
        log_debug("Gen FCD TLV data into " + self.eesign_path)
        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

        nowtime = time.strftime("%Y%m%d", time.gmtime())
        # /tftpboot/tools/common/x86-64k-ee
        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe)
        cmd = "{0} -B {1} -d {2} -r 113-{3}".format(flasheditor, self.eesign_path, nowtime, self.bom_rev)
        log_debug("cmd: " + cmd)
        sto, rtc = self.cnapi.xcmd(cmd)
        log_debug(sto)

        rtf = os.path.isfile("{0}.FCD".format(self.eesign_path))
        if rtf is False:
            rtmsg = "Can't find the file {0}.FCD".format(self.eesign_path)
            error_critical(rtmsg)
        else:
            cmd = "mv {0}.FCD {1}".format(self.eesign_path, self.eesigndate_path)
            log_debug("cmd: " + cmd)
            self.cnapi.xcmd(cmd)

    def check_devreg_data(self, dut_tmp_subdir=None, mtd_count=None, post_en=True, zmodem=False, timeout=10):
        """check devreg data
        in default we assume the datas under /tmp on dut
        but if there is sub dir in your tools.tar, you should set dut_subdir

        you MUST make sure there is eesign file under /tftpboot

        Keyword Arguments:
            dut_subdir {[str]} -- like udm, unas, afi_aln...etc, take refer to structure of fcd-script-tools repo
        """
        log_debug("Send signed eeprom file adding date code from host to DUT ...")
        post_txt = None

        # Determine what eeprom should be written into DUT finally
        if self.FCD_TLV_data is True:
            eewrite = self.eesigndate
        else:
            eewrite = self.eesign

        eewrite_path = os.path.join(self.tftpdir, eewrite)
        eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)

        if post_en is True:
            post_txt = self.linux_prompt

        if dut_tmp_subdir is not None:
            eewrite_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, eewrite)
        else:
            eewrite_dut_path = os.path.join(self.dut_tmpdir, eewrite)

        if zmodem is False:
            self.tftp_get(remote=eewrite, local=eewrite_dut_path, timeout=timeout, post_en=post_en)
        else:
            self.zmodem_send_to_dut(file=eewrite_path, dest_path=self.dut_tmpdir)

        log_debug("Change file permission - {0} ...".format(eewrite))
        cmd = "chmod 777 {0}".format(eewrite_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Starting to write signed info to SPI flash ...")
        cmd = "dd if={0} of={1} bs=1k count=64".format(eewrite_dut_path, self.devregpart)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        cmd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Send " + self.eechk + " from DUT to host ...")

        if zmodem is False:
            self.tftp_put(remote=self.eechk_path, local=eechk_dut_path, timeout=timeout, post_en=post_en)
        else:
            self.zmodem_recv_from_dut(file=eechk_dut_path, dest_path=self.tftpdir)

        otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, eewrite)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.eechk_path, eewrite_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")

    def gen_and_load_key_to_dut(self):
        src = os.path.join(self.tftpdir, "dropbear_key.rsa")
        cmd = "dropbearkey -t rsa -f {0}".format(src)
        self.cnapi.xcmd(cmd)

        cmd = "chmod 777 {0}".format(src)
        self.cnapi.xcmd(cmd)

        srcp = "dropbear_key.rsa"
        dstp = os.path.join(self.dut_tmpdir, "dropbear_key.rsa")
        self.tftp_get(remote=srcp, local=dstp, timeout=15)

    def copy_and_unzipping_tools_to_dut(self, timeout=15, post_exp=True):
        log_debug("Send tools.tar from host to DUT ...")
        post_txt = self.linux_prompt if post_exp is True else None
        source = os.path.join(self.tools, "tools.tar")
        target = os.path.join(self.dut_tmpdir, "tools.tar")
        self.tftp_get(remote=source, local=target, timeout=timeout, post_en=post_exp)

        cmd = "tar -xzvf {0} -C {1}".format(target, self.dut_tmpdir)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt,
                                valid_chk=True)

        src = os.path.join(self.dut_tmpdir, "*")
        cmd = "chmod -R 777 {0}".format(src)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt,
                                valid_chk=True)

    def set_ub_net(self, premac=None, dutaddr=None, srvaddr=None, ethact=None):
        if premac is not None:
            cmd = "setenv ethaddr {0}; saveenv".format(premac)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        if dutaddr is None:
            dutaddr = self.dutip

        cmd = "setenv ipaddr {0}".format(dutaddr)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        if srvaddr is None:
            srvaddr = self.tftp_server
        cmd = "setenv serverip {0}".format(srvaddr)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        if ethact is not None:
            cmd = "setenv ethact {0}".format(ethact)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

    def set_lnx_net(self, intf, setmac=False, retry=5):
        log_debug("Starting to configure the networking ... ")
        ct = 0
        while ct < retry:
            cmd = "ifconfig {}".format(intf)
            cmd_reply = self.pexp.expect_get_output(cmd, self.linux_prompt)
            if "Link encap:Ethernet" in cmd_reply:
                rmsg = "Network interface: {} is active".format(intf)
                log_debug(rmsg)
                break

            time.sleep(5)
            ct += 1

        if setmac is True:
            comma_mac = self.mac_format_str2comma(self.mac)
            cmd = "ifconfig br0 hw ether {}".format(comma_mac)
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                    valid_chk=True)

        cmd = "ifconfig {0} {1}".format(intf, self.dutip)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

    def display_arp_table(self):
        log_debug("The current ARP table of the FCD host:")
        cmd = "arp -a"
        self.cnapi.xcmd(cmd)

    def del_arp_table(self, ipaddr):
        cmd = "arp -d {}".format(ipaddr)
        self.cnapi.xcmd(cmd)

        log_debug("After deleting the DUT IP in the ARP table:")
        cmd = "arp -a"
        self.cnapi.xcmd(cmd)

    def is_network_alive_in_uboot(self, ipaddr=None, retry=10, timeout=3, arp_logging_en=False, del_dutip_en=False):
        is_alive = False
        if ipaddr is None:
            ipaddr = self.tftp_server

        if del_dutip_en is True:
            self.del_arp_table(self.dutip)

        cmd = "ping {0}".format(ipaddr)
        exp = "host {0} is alive".format(ipaddr)
        self.pexp.expect_ubcmd(timeout=timeout, exptxt="", action=cmd, post_exp=exp, retry=retry)

        if arp_logging_en:
            self.display_arp_table()

    def is_network_alive_in_linux(self, ipaddr=None, retry=3, arp_logging_en=False, del_dutip_en=False):
        if ipaddr is None:
            ipaddr = self.tftp_server

        if del_dutip_en is True:
            self.del_arp_table(self.dutip)

        cmd = "ifconfig; ping -c 3 {0}".format(ipaddr)
        exp = r"64 bytes from {0}".format(ipaddr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=exp, retry=retry)

        if arp_logging_en:
            self.display_arp_table()

    def disable_inittab_process(self, process):
        self.pexp.expect_lnxcmd(60, self.linux_prompt, "while ! grep -q \"{}\" /etc/inittab; "\
                                "do echo 'Wait {}...'; sleep 1; done".format(process, process), self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, 'sed -i "/{}/d" /etc/inittab'.format(process), 
                                self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", self.linux_prompt)

    def disable_udhcpc(self):
        self.disable_inittab_process("udhcpc")

    def disable_wpa_supplicant(self):
        self.disable_inittab_process("wpa_supplicant")

    def disable_hostapd(self):
        self.disable_inittab_process("hostapd")

    def gen_rsa_key(self):
        if os.path.isfile(self.rsakey_path):
            os.remove(self.rsakey_path)

        cmd = "dropbearkey -t rsa -f {0}".format(self.rsakey_path)
        log_debug(cmd)
        self.cnapi.xcmd(cmd)
        '''
            The dropbearkey command will be executed in the FCD host.
            So, it won't cost too much time
        '''
        time.sleep(1)

        cmd = "chmod 777 {0}".format(self.rsakey_path)
        self.cnapi.xcmd(cmd)

        rt = os.path.isfile(self.rsakey_path)
        if rt is not True:
            otmsg = "Can't find the RSA key file"
            error_critical(otmsg)

    def gen_dss_key(self):
        if os.path.isfile(self.dsskey_path):
            os.remove(self.dsskey_path)
        cmd = "dropbearkey -t dss -f {0}".format(self.dsskey_path)
        self.cnapi.xcmd(cmd)
        '''
            The dropbearkey command will be executed in the FCD host.
            So, it won't cost too much time
        '''
        time.sleep(1)

        cmd = "chmod 777 {0}".format(self.dsskey_path)
        self.cnapi.xcmd(cmd)

        rt = os.path.isfile(self.dsskey_path)
        if rt is not True:
            otmsg = "Can't find the DSS key file"
            error_critical(otmsg)

    def data_provision_4k(self, netmeta):
        self.FCD_TLV_data = False
        otmsg = "Starting to do {0} ...".format(self.eepmexe4k)
        log_debug(otmsg)
        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe4k)
        sstr = [
            flasheditor,
            "-F",
            "-f {}".format(self.eegenbin_path),
            "-r 113-{}".format(self.bom_rev),
            "-s 0x{}".format(self.board_id),
            "-m {}".format(self.mac),
            "-c 0x{}".format(self.region),
            "-e {}".format(netmeta['ethnum'][self.board_id]),
            "-w {}".format(netmeta['wifinum'][self.board_id]),
            "-b {}".format(netmeta['btnum'][self.board_id])
        ]
        log_debug("Top level BOM:" + self.tlb_rev)
        if self.tlb_rev != "":
            sstr.append("-t 002-{}".format(self.tlb_rev))

        log_debug("ME BOM:" + self.meb_rev)
        if self.meb_rev != "":
            sstr.append("-M 300-{}".format(self.meb_rev))

        sstr = ' '.join(sstr)
        log_debug("flash editor cmd: " + sstr)
        [output, rv] = self.cnapi.xcmd(sstr)
        time.sleep(0.5)
        if int(rv) > 0 or output:
            otmsg = "Flash editor filling out {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Flash editor filling out {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        cmd = "mv {} {}".format(self.eegenbin_path, self.eebin_path)
        log_debug("cmd: " + cmd)
        self.cnapi.xcmd(cmd)

    def data_provision_64k(self, netmeta, post_en=True, rsa_en=True):
        if rsa_en is True:
            self.gen_rsa_key()

        post_exp = None
        if post_en is True:
            post_exp = self.linux_prompt

        otmsg = "Starting to do {0} ...".format(self.eepmexe)
        log_debug(otmsg)
        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe)
        sstr = [
            flasheditor,
            "-F",
            "-f {}".format(self.eegenbin_path),
            "-r 113-{}".format(self.bom_rev),
            "-s 0x{}".format(self.board_id),
            "-m {}".format(self.mac),
            "-c 0x{}".format(self.region),
            "-e {}".format(netmeta['ethnum'][self.board_id]),
            "-w {}".format(netmeta['wifinum'][self.board_id]),
            "-b {}".format(netmeta['btnum'][self.board_id])
        ]
        log_debug("Top level BOM:" + self.tlb_rev)
        if self.tlb_rev != "":
            sstr.append("-t 002-{}".format(self.tlb_rev))

        log_debug("ME BOM:" + self.meb_rev)
        if self.meb_rev != "":
            sstr.append("-M 300-{}".format(self.meb_rev))

        if rsa_en is True:
            cmd_option = "-k {}".format(self.rsakey_path)
            sstr.append(cmd_option)

        sstr = ' '.join(sstr)
        log_debug("flash editor cmd: " + sstr)
        [sto, rtc] = self.cnapi.xcmd(sstr)
        time.sleep(0.5)
        if int(rtc) > 0:
            otmsg = "Flash editor filling out {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Flash editor filling out {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        # Ex: dd if=/dev/mtdblock2 of=/tmp/e.org.0 bs=1k count=64
        cmd = "dd if={0} of={1}/{2} bs=1k count=64".format(self.devregpart, self.dut_tmpdir, self.eeorg)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(0.1)

        # Ex: /tmp/e.org.0
        dstp = "{0}/{1}".format(self.dut_tmpdir, self.eeorg)
        self.tftp_put(remote=self.eeorg_path, local=dstp, timeout=20)

        log_debug("Writing the information from e.gen.{} to e.org.{}".format(self.row_id, self.row_id))
        '''
            Trying to access the initial information from the EEPROM of DUT and save to e.org.0
        '''
        f1 = open(self.eeorg_path, "rb")
        org_tres = list(f1.read())
        f1.close()

        '''
            Creating by the FCD host with the utiltiy eetool
        '''
        f2 = open(self.eegenbin_path, "rb")
        gen_tres = list(f2.read())
        f2.close()

        '''
            Writing the information from e.gen.0 to e.org.0
        '''
        f3 = open(self.eeorg_path, "wb")

        # Write 40K content to the first 40K section
        # 40 * 1024 = 40960 = 0xA000, 40K
        # the for loop will automatically count it from 0 ~ (content_sz - 1)
        # example:  0 ~ 40K = 0 ~ 40959
        content_sz = 40 * 1024
        for idx in range(0, content_sz):
            org_tres[idx] = gen_tres[idx]

        # Write 4K content start from 0xC000
        # 49152 = 0xC000 = 48K
        content_sz = 4 * 1024
        offset = 48 * 1024
        for idx in range(0, content_sz):
            org_tres[idx + offset] = gen_tres[idx + offset]

        # Write 8K content start from 0xE000
        # 57344 = 0xE000 = 56K
        content_sz = 8 * 1024
        offset = 56 * 1024
        for idx in range(0, content_sz):
            org_tres[idx + offset] = gen_tres[idx + offset]

        arr = bytearray(org_tres)
        f3.write(arr)
        f3.close()

        eeorg_dut_path = os.path.join(self.dut_tmpdir, self.eeorg)
        self.tftp_get(remote=self.eeorg, local=eeorg_dut_path, timeout=15)

        # Ex: dd if=/tmp/e.org.0 of=/dev/mtdblock2 bs=1k count=64
        cmd = "dd if={0}/{1} of={2} bs=1k count=64".format(self.dut_tmpdir, self.eeorg, self.devregpart)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=post_exp)
        time.sleep(0.1)

    def prepare_server_need_files(self, method="tftp", helper_args_type="default"):
        log_debug("Starting to do " + self.helperexe + "...")
        # Ex: tools/uvp/helper_DVF99_release_ata_max
        srcp = os.path.join(self.tools, self.helper_path, self.helperexe)

        # Ex: /tmp/helper_DVF99_release_ata_max
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)

        if method == "tftp":
            self.tftp_get(remote=srcp, local=helperexe_path, timeout=60)
        elif method == "wget":
            self.dut_wget(srcp, helperexe_path, timeout=100)
        else:
            error_critical("Transferring interface not support !!!!")

        cmd = "chmod 777 {0}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)

        HELPER_PROD_CLASS_ARG = {
            'default': "-c",
            'new': "--output-product-class-fields",
        }

        prod_class_arg = HELPER_PROD_CLASS_ARG.get(helper_args_type, HELPER_PROD_CLASS_ARG['default'])

        sstr = [
            helperexe_path,
            "-q",
            "{} product_class={}".format(prod_class_arg, self.product_class),
            "-o field=flash_eeprom,format=binary,pathname=" + eebin_dut_path,
            ">",
            eetxt_dut_path
        ]
        sstr = ' '.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)
        time.sleep(1)

        files = [self.eetxt, self.eebin]
        for fh in files:
            # Ex: /tftpboot/e.t.0
            srcp = os.path.join(self.tftpdir, fh)

            # Ex: /tmp/e.t.0
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send helper output files from DUT to host ...")

    def prepare_server_need_files_bspnode(self, nodes=None):
        log_debug("Starting to extract cpuid, flash_jedecid and flash_uuid from bsp node ...")
        # The sequencial has to be cpu id -> flash jedecid -> flash uuid
        if nodes is None:
            nodes = ["/proc/bsp_helper/cpu_rev_id",
                     "/proc/bsp_helper/flash_jedec_id",
                     "/proc/bsp_helper/flash_uid"]

        if self.product_class == 'basic':
            product_class_hexval = "0014"
        elif self.product_class == 'radio':
            product_class_hexval = "0001"
        else:
            error_critical("product class is '{}', FCD doesn't support \"{}\" class now".format(self.product_class))

        # Gen "e.t" from the nodes which were provided in BSP image
        for i in range(0, len(nodes)):
            sstr = [
                "fcd_reg_val{}=`".format(i+1),
                "cat ",
                nodes[i],
                " | awk -F \"x\" '{print $2}'",
                "`"
            ]
            sstr = ''.join(sstr)
            log_debug(sstr)
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)
       
        sstr = [
            "echo -e \"field=product_class_id,format=hex,value={}\n".format(product_class_hexval),
            "field=cpu_rev_id,format=hex,value=$fcd_reg_val1\n",
            "field=flash_jedec_id,format=hex,value=$fcd_reg_val2\n",
            "field=flash_uid,format=hex,value=$fcd_reg_val3",
            "\" > /tmp/{}".format(self.eetxt)
        ]
        sstr = ''.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)
        
        # copy "e.org" as "e.b", cp -a /tmp/e.org.0 /tmp/e.b.0
        cmd = "cp -a {0}/{1} {0}/{2}".format(self.dut_tmpdir, self.eeorg, self.eebin)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        files = [self.eetxt, self.eebin]
        for fh in files:
            # Ex: /tftpboot/e.t.0
            srcp = os.path.join(self.tftpdir, fh)

            # Ex: /tmp/e.t.0
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send bspnode output files from DUT to host ...")

    '''
        DUT view point
        To get the file from the host by tftp command
        input parameters:
            remote: absolute path of the source file
            local: absolute path of the destination file
            timeout: timeout for expect_lnxcmd API
    '''

    def tftp_get(self, remote, local, timeout=300, retry=3, post_en=True):
        post_exp = None
        if post_en is True:
            post_exp = self.linux_prompt

        __func_name = "tftp_get: "
        if remote == "" or local == "":
            log_debug(__func_name + "source file and destination file can't be empty")
            return False

        cmd = "tftp -g -r {0} -l {1} {2}".format(remote, local, self.tftp_server)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd,
                                post_exp=post_exp, valid_chk=True, retry=retry)

        time.sleep(2)
        self.is_dutfile_exist(local)
        '''
            In order to avoid escaping this API too earlier, adding a delay here.
            Somehow this should be the property of the Python script
        '''
        time.sleep(1)
        return True

    '''
        DUT view point
        To put the file from the host by tftp command
        input parameters:
            remote: absolute path of the source file
            local: absolute path of the destination file
            timeout: timeout for expect_lnxcmd API
    '''

    def tftp_put(self, remote, local, timeout=300, retry=3, post_en=True):
        __func_name = "tftp_put: "
        post_exp = None
        if post_en is True:
            post_exp = self.linux_prompt

        if remote == "" or local == "":
            log_debug(__func_name + "source file and destination file can't be empty")
            return False

        if os.path.isfile(remote) is False:
            os.mknod(remote)
        else:
            log_debug(remote + " is existed")

        os.chmod(remote, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        time.sleep(2)

        cmd = "tftp -p -r {0} -l {1} {2}".format(os.path.basename(remote), local, self.tftp_server)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd,
                                post_exp=post_exp, valid_chk=True, retry=retry)

        '''
            To give a few delays to let the file transfer to the FCD host.
        '''
        time.sleep(3)
        rtc = os.path.isfile(remote)
        if rtc is True:
            '''
                In order to avoid escaping this API too earlier, adding a delay here.
                Somehow this should be the property of the Python script
            '''
            time.sleep(1)
            return rtc
        else:
            raise Exception(__func_name + "can't find the file")

    def zmodem_send_to_dut(self, file, dest_path, timeout=60, retry=3):
        while retry != 0:
            # exe receive cmd on dut
            cmd = "cd {0}; lrz -v -b".format(dest_path)
            self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd)

            # exe send cmd on host
            cmd = "sz -e -v -b {0} < /dev/{1} > /dev/{1}".format(file, self.dev)
            log_debug("host cmd: " + cmd)
            [sto, rtc] = self.cnapi.xcmd(cmd)
            if int(rtc) != 0:
                retry -= 1
                log_debug("Send {} to DUT incomplete, remaining retry {}".format(file, retry))
                time.sleep(2)
            else:
                break

        if retry == 0:
            error_critical("Failed to send {} to DUT".format(file))

    def zmodem_recv_from_dut(self, file, dest_path, timeout=60, retry=3):
        while retry != 0:
            # exe send cmd on dut
            cmd = "lsz -e -v -b {0}".format(file)
            self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd)

            # chdif to dest path on host
            os.chdir(dest_path)

            # exe receive cmd on host
            cmd = "rz -y -v -b < /dev/{0} > /dev/{0}".format(self.dev)
            [sto, rtc] = self.cnapi.xcmd(cmd)
            if int(rtc) != 0:
                retry -= 1
                log_debug("Receive {} from DUT incomplete, remaining retry {}".format(file, retry))
                time.sleep(2)
            else:
                break

        if retry == 0:
            error_critical("Failed to receive {} from DUT".format(file))

    def set_ntptime_to_dut(self, rtc_tool="hwclock", timeout=10):
        [ntp_strf, ntp_ctime] = Common.RequestTimefromNtp("0.cn.pool.ntp.org")
        if ntp_strf is False or ntp_ctime is False:
            error_critical("Timeout waiting for NTP packet")

        cmd = "date -s \"{}\"; {} -w".format(ntp_strf, rtc_tool)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd)

        output = self.pexp.expect_get_output(rtc_tool, self.linux_prompt)
        log_debug("output: {}".format(output))
        match = re.findall(ntp_ctime, output, re.S)

        '''
            url: https://en.wikipedia.org/wiki/C_date_and_time_functions
            strftime: converts a struct tm object to custom textual representation
            ctime: converts a time_t value to a textual representation
        '''

        if match:
            otmsg = match[0]
            log_debug("Time written in DUT: " + otmsg)
        else:
            error_critical("Can't set the initial time to system clock!!!")

    '''
        DUT view point
        To get the file from the host by scp command
            dut_user: DUT username
            dut_pass: DUT password
            dut_ip  : DUT IP address
            src_file: Source filename. It has to be absolutely path
            dst_file: Destination filename. It has to be absolutely path
    '''

    def scp_get(self, dut_user, dut_pass, dut_ip, src_file, dst_file):
        cmd = [
            'sshpass -p {}'.format(dut_pass),
            'scp',
            '-o StrictHostKeyChecking=no',
            '-o UserKnownHostsFile=/dev/null',
            src_file,
            "{}@{}:{}".format(dut_user, dut_ip, dst_file)
        ]
        cmdj = ' '.join(cmd)
        log_debug('Exec "{}"'.format(cmdj))
        [stout, rv] = self.cnapi.xcmd(cmdj)
        if int(rv) != 0:
            error_critical('Exec "{}" failed'.format(cmdj))
        else:
            log_debug('scp successfully')

    '''
        DUT view point, wget files from RPi4 server
        The default url is "http://192.168.1.19" and default link to "tftpboot"
        src_path: please give a whole path
        dst_path: please give the directory where the file will be stored
    '''
    def dut_wget(self, src_path, dst_path, timeout=10):
        url = "http://{}".format(self.tftp_server)
        cmd = "wget -O {0} {1}/{2}".format(dst_path, url, src_path)
        log_info("cmd: " + cmd)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

    def copy_file(self, source, dest):
        if os.path.isfile(dest) and filecmp.cmp(source, dest):
            log_debug("{} and {} are the same, skip copying".format(source, dest))
            return

        sstr = [
            "cp",
            "-p",
            source,
            dest
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Copy file from {} to {} failed".format(source, dest))
        else:
            log_debug('Copy {} to {} successfully'.format(source, dest))

    def check_eeprom_mac(self):
        cmd = "hexdump -C -s 0 -n 6 {}".format(self.eesigndate_path)
        [sto, rtc] = self.cnapi.xcmd(cmd)
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

    def check_eeprom_bomrev(self):
        cmd = "hexdump -C -s 0x10 -n 4 {}".format(self.eesigndate_path)
        [sto, rtc] = self.cnapi.xcmd(cmd)
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

    def stop_http_server(self):
        self.http_srv.shutdown()

    def create_http_server(self):
        self.http_srv = HTTPServer(('', self.http_port), SimpleHTTPRequestHandler)
        t = Thread(target=self.http_srv.serve_forever)
        t.setDaemon(True)
        t.start()
        log_debug('http server running on port {}'.format(self.http_srv.server_port))

    def chk_lnxcmd_valid(self):
        cmd = "echo \"RV\"=$?"
        self.pexp.expect_lnxcmd(timeout=3, pre_exp=self.linux_prompt, action=cmd, post_exp="RV=0", retry=0)

    def mac_format_str2comma(self, strmac):
        mac_comma = ':'.join([strmac[i: i + 2] for i in range(0, len(strmac), 2)])
        return mac_comma

    def mac_format_str2dash(self, strmac):
        mac_dash = '-'.join([strmac[i: i + 2] for i in range(0, len(strmac), 2)])
        return mac_dash

    def mac_format_str2list(self, strmac):
        mac_list = self.mac_format_str2comma(strmac).split(':')
        return mac_list

    def update_eebin_regdmn(self, eebin = None, regdmn = None):
        if eebin is None:
            eebin = self.eebin_path
        if regdmn is None:
            regdmn = self.region

        regdmn_ofst = 0x8020
        regdmn_len  = 0x10
        regdmn_bin  = os.path.join(self.tftpdir, "regdmn.bin")
        file = open(regdmn_bin, "wb")

        # Gen a 16 bytes updated regdmn.bin
        for i in range(0, regdmn_len * 2, 2):
            if i < len(regdmn):
                file.write(bytes((int(regdmn[i:i+2], 16),)))
            else:
                file.write(bytes((0,)))
        file.close()

        # Gen a 64K bianry file {eebin}.regdmn with new region domain
        cmds = [ "dd if={} of={}.part1 bs=1 count=$(({}))".format(eebin, eebin, regdmn_ofst),
                 "dd if={} of={}.part2 bs=1 skip=$(({}))".format(eebin, eebin, regdmn_ofst+regdmn_len),
                 "cat {}.part1 {} {}.part2 > {}.regdmn".format(eebin, regdmn_bin, eebin, eebin)]
        for cmd in cmds:
            [sto, rtc] = self.cnapi.xcmd(cmd)
            if int(rtc) > 0:
                error_critical('Executing linux command "{}" failed!!'.format(cmd))

        self.eebin_path = "{}.regdmn".format(eebin)

    def close_fcd(self):
        # If do back to T1, self.key_dir should be None and do not check blacklist
        if self.key_dir:
            self.check_blacklist()

        self.test_result = 'Pass'
        time.sleep(2)
        exit(0)

    def check_blacklist(self):
        try :
            blacklist_path = '/usr/local/sbin/blacklist/blacklist.json'
            if not os.path.exists(blacklist_path): return

            # Read Log file
            logpath = os.path.join("/tftpboot/", "log_slot" + str(self.row_id) + ".log")
            with open(logpath, 'r') as logfile:
                logcontent = logfile.read().rsplit('Ubiquiti Device Security Client')[-1]

            # Read BlackList Dict
            with open(blacklist_path) as fh:
                self.blacklist_json = json.load(fh)

            if 'BLACK_LIST' in self.blacklist_json[self.product_line][self.product_name]:
                self.blacklist_dict = self.blacklist_json[self.product_line][self.product_name]['BLACK_LIST']

                # Check Reg
                for failure, subdict in self.blacklist_dict.items():
                    matchresult, reg= '', ''

                    if 'reg' in self.blacklist_dict[failure] :
                        reg = self.blacklist_dict[failure]['reg']
                        matchresult = ''.join(re.findall(reg, logcontent))
                    else :
                        continue

                    if matchresult:
                        error_critical_str = ''.join(['{}: {}\n'.format(k, v) for k, v in self.blacklist_dict[failure].items()])
                        error_critical('BlackList Error, please find Engineer for checking\nFailure: {}\n'.format(failure) + error_critical_str  )
                    else :
                        log_debug('Checked BlackList-{}'.format(failure) )

        except KeyError:
            pass

        except Exception as e:
            log_debug(str(e))

    def __del__(self):
        if self.upload:
            self._upload_log()

    def _upload_log(self) -> bool:
        try:
            # Compute test_time/duration
            self.test_endtime_datetime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
            self.test_duration = (self.test_endtime_datetime - self.test_starttime_datetime).seconds
            self.test_starttime = self.test_starttime_datetime.strftime('%Y-%m-%d_%H:%M:%S')
            self.test_endtime = self.test_endtime_datetime.strftime('%Y-%m-%d_%H:%M:')

            # Store error function
            self.__store_error_function()

            # Dump all var
            self.__dump_JSON()
            self._upload_prepare()

        except Exception as e:
            print("***** upload_log exception msg *****")
            print(e)
            return False
        else:
            return True

    def __store_error_function(self):
        PAlib_errorcollecter = errorcollecter()

        self.progress = PAlib_errorcollecter.msgno

        if self.test_result != 'Pass':
            self.error_function = PAlib_errorcollecter.error_function
            # Can implement original error_code
            self.error_code = self.error_function

    def __dump_JSON(self):
        dumpfile = os.path.join("/tftpboot/", "log_slot" + self.row_id + ".json")
        with open(dumpfile, 'w') as f:
            self.__dict__.pop('fsiw', None)
            f.write(str(json.dumps(self.__dict__, default=lambda o: '<not serializable>', sort_keys=True, indent=4)))

    def _upload_prepare(self):
        # Ex: /tftpboot/log_slot0.log
        sfile = os.path.join("/tftpboot/", "log_slot" + str(self.row_id) + ".log")

        # Ex: /tftpboot/log_slot0.json
        jfile = os.path.join("/tftpboot/", "log_slot" + str(self.row_id) + ".json")

        # Ex: /tftpboot/e.sd.0
        eefile = os.path.join("/tftpboot/", "e.sd." + str(self.row_id))

        # Ex: 2020-09-04_02_16_46_856204
        timestamp = self.test_starttime_datetime.strftime('%Y-%m-%d_%H_%M_%S_%f')

        upload_root_folder = "/media/usbdisk/upload"

        # Ex: /media/usbdisk/upload/2020-09-04_02_16_46_856204_e063da46a99b
        upload_dut_folder = os.path.join(upload_root_folder, timestamp + '_' + str(self.mac))

        # Ex: /media/usbdisk/upload/2020-09-04_02_16_46_856204_e063da46a99b_Pass
        upload_dut_filename = '_'.join([timestamp, str(self.mac), str(self.test_result)])

        # Ex: /media/usbdisk/upload/2020-09-04_02_16_46_856204_e063da46a99b_Pass.log
        upload_dut_logpath = os.path.join(upload_dut_folder, upload_dut_filename + ".log")

        # Ex: /media/usbdisk/upload/2020-09-04_02_16_46_856204_e063da46a99b_Pass.json
        upload_dut_jsonpath = os.path.join(upload_dut_folder, upload_dut_filename + ".json")

        # Ex: /media/usbdisk/upload/2020-09-04_02_16_46_856204_e063da46a99b_Pass.bin
        upload_dut_eepath = os.path.join(upload_dut_folder, upload_dut_filename + ".bin")

        if not os.path.isdir(upload_dut_folder):
            os.makedirs(upload_dut_folder)

        # We can extend more file into the upload_dict for uploading
        upload_file_dict = {
            sfile: upload_dut_logpath,
            jfile: upload_dut_jsonpath,
        }
        if self.test_result == 'Pass':
            upload_file_dict[eefile] = upload_dut_eepath

        for ori_file, copy_file in upload_file_dict.items():
            if os.path.isfile(ori_file):
                shutil.copy2(ori_file, copy_file)
                time.sleep(1)

        self._upload_ui_taipei(uploadfolder=upload_dut_folder, mac=self.mac, bom=self.bom_rev)
        # self._upload_ui_taipei_fargate(uploadfolder=upload_dut_folder, mac=self.mac, bom=self.bom_rev)

    def _upload_ui_taipei(self, uploadfolder, mac, bom):
        """
            command parameter description for trigger /api/v1/uploadlog WebAPI in Cloud
            command: python3
            --path:   uploadfolder or uploadpath
            --mac:   mac address with lowercase
            --bom:   BOM Rev version
            --stage:   FCD or FTU
        """
        logupload_client_path = os.path.join(self.PAlib_dir, 'Framework', 'fcd', 'logupload_client.py')

        if bom is None:
            bom = '99999-99'  # Workaround For BackToArt , GUI won't assign BOM version.
            FCDtype = 'BackToArt'
        else:
            FCDtype = 'FCD'

        cmd = [
            "sudo", "/usr/bin/python3",
            logupload_client_path,
            '--path', uploadfolder,
            '--mac', mac,
            '--bom', bom,
            '--srv ecs',
            '--stage', FCDtype]
        execcmd = ' '.join(cmd)

        try:
            uploadproc = subprocess.check_output(execcmd, shell=True)
            if "success" in str(uploadproc.decode('utf-8')):
                log_debug('[Upload_ui_taipei Success]')
            else:
                raise subprocess.CalledProcessError
        except subprocess.CalledProcessError as e:
            if self.log_upload_failed_alert_en is True:
                error_critical('\n{}\n{}\n[Upload_ui_taipei Fail]'.format(e.output.decode('utf-8'), e.returncode))
            else:
                log_debug('\n{}\n{}\n[Upload_ui_taipei Fail]'.format(e.output.decode('utf-8'), e.returncode))
        except:
            if self.log_upload_failed_alert_en is True:
                error_critical("[Upload_ui_taipei Unexpected error: {}]".format(sys.exc_info()[0]))
            else:
                log_debug("[Upload_ui_taipei Unexpected error: {}]".format(sys.exc_info()[0]))

    def _upload_ui_taipei_fargate(self, uploadfolder, mac, bom):
        """
            command parameter description for trigger /api/v1/uploadlog WebAPI in Cloud
            command: python3
            --path:  uploadfolder or uploadpath
            --mac:   mac address with lowercase
            --bom:   BOM Rev version
            --srv:   UI-cloud
            --stage: FCD or FTU
        """
        logupload_client_path = os.path.join(self.PAlib_dir, 'fcd', 'logupload_client.py')

        if bom is None:
            bom = '99999-99'  # Workaround For BackToArt , GUI won't assign BOM version.
            FCDtype = 'BackToArt'
        else:
            FCDtype = 'FCD'

        cmd = [
            "sudo", "/usr/bin/python3",
            logupload_client_path,
            '--path', uploadfolder,
            '--mac', mac,
            '--bom', bom,
            '--srv farget',
            '--stage', FCDtype]

        execcmd = ' '.join(cmd)
        log_debug("cmd: " + execcmd)

        try:
            uploadproc = subprocess.check_output(execcmd, shell=True)
            if "success" in str(uploadproc.decode('utf-8')):
                log_debug('[Upload_ui_taipei farget Success]')
            else:
                raise subprocess.CalledProcessError

        except subprocess.CalledProcessError as e:
            log_debug('\n{}\n{}\n[Upload_ui_taipei farget Fail]'.format(e.output.decode('utf-8'), e.returncode))
        except:
            log_debug("[Upload_ui_taipei farget Unexpected error: {}]".format(sys.exc_info()[0]))
