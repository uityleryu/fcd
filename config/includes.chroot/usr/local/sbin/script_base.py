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
import ubntlib
import datetime
import tarfile
import shutil
import subprocess
import data.constant as CONST

from ubntlib.fcd.common import Tee, Common
from ubntlib.fcd.helper import FCDHelper
from ubntlib.fcd.logger import log_debug, log_info, log_error, msg, error_critical
from ubntlib.fcd.singleton import errorcollecter
from ubntlib.fcd.expect_tty import ExpttyProcess
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread
from uuid import getnode as get_mac


class ScriptBase(object):
    __version__ = "1.0.22"
    __authors__ = "FCD team"
    __contact__ = "fcd@ui.com"

    def __init__(self):
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

        self.version_scriptbase = self.__version__
        self.version_ubntlib = ubntlib.__version__
        with open(self.fcd_version_info_file_path, 'r') as f:
            self.version_iso = f.read().rstrip('\n')

        self.fcd.common.print_current_fcd_version(file=self.fcd_version_info_file_path)
        print("framework version: " + self.__version__)
        print("ubntlib version: " + ubntlib.__version__)
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
        self.ubntlib_dir = os.path.join(self.fcd_scripts_dir, 'ubntlib')

        cmd = "uname -a"
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("Get linux information failed!!")
        else:
            log_debug("Get linux information successfully")
            match = re.findall("armv7l", sto)
            if match:
                self.eepmexe = "aarch64-rpi4-64k-ee"
            else:
                self.eepmexe = "x86-64k-ee"

        '''
           Will be defined by the specifi model script
           Ex: /tmp/uvp
        '''
        self.devregpart = ""
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
        parse.add_argument('--region', '-r', dest='region', help='Region Code', default=None)
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
        self.bom_rev = args.bom_rev
        self.qrcode = args.qrcode
        self.region = args.region
        self.region_name = CONST.region_names[CONST.region_codes.index(self.region)] if self.region is not None else None
        self.fwimg = self.board_id + ".bin"
        self.fwimg_mfg = self.board_id + "-mfg.bin"
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

    def login(self, username="ubnt", password="ubnt", timeout=10, press_enter=False, log_level_emerg=False):
        """
        should be called at login console
        """
        if press_enter is True:
            self.pexp.expect_action(timeout, "Please press Enter to activate this console", "")

        post = [
            "login:",
            "Error-A12 login"
        ]
        ridx = self.pexp.expect_get_index(timeout, post)
        if ridx >= 0:
            '''
                To give twice in order to make sure of that the username has been keyed in
            '''
            self.pexp.expect_action(10, "", username)
            self.pexp.expect_action(10, "Password:", password)

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
        files = [self.eebin, self.eetxt, self.eechk, self.eetgz, self.rsakey, self.eegenbin, self.eesign,
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

        # FCD_ID (this name is called by Mike) like product line
        self.fcd_id = self.fsiw[self.product_line][self.product_name]['FCD_ID']

        # SW_ID (this name is called by Mike) like product model
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
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if int(rtc) > 0:
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")
            return sto

    def registration(self):
        log_debug("Starting to do registration ...")
        regsubparams = self.access_chips_id()

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        if self.fcd_id == "" or self.sem_ver == "" or self.sw_id == "" or self.fw_ver == "":
            clientbin = "/usr/local/sbin/client_x86_release"
            regparam = [
                "-h devreg-prod.ubnt.com",
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
            print("WARNING: should plan to add FCD_ID, SW_ID ... won't block this time")
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
                    clientbin = "/usr/local/sbin/client_x86_release_20190507"

            regparam = [
                "-h devreg-prod.ubnt.com",
                "-k " + self.pass_phrase,
                regsubparams,
                reg_qr_field,
                "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
                "-i field=fcd_id,format=hex,value=" + self.fcd_id,
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

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        self.pass_devreg_client = True

        log_debug("Excuting client_x86 registration successfully")
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
        sto, rtc = self.fcd.common.xcmd(cmd)
        log_debug(sto)

        rtf = os.path.isfile("{0}.FCD".format(self.eesign_path))
        if rtf is False:
            rtmsg = "Can't find the file {0}.FCD".format(self.eesign_path)
            error_critical(rtmsg)
        else:
            cmd = "mv {0}.FCD {1}".format(self.eesign_path, self.eesigndate_path)
            log_debug("cmd: " + cmd)
            self.fcd.common.pcmd(cmd)

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
        self.fcd.common.pcmd(cmd)

        cmd = "chmod 777 {0}".format(src)
        self.fcd.common.pcmd(cmd)

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

    def set_ub_net(self, premac=None, dutaddr=None, srvaddr=None):
        if premac is not None:
            cmd = "setenv ethaddr {0}".format(premac)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        if dutaddr is None:
            dutaddr = self.dutip
        cmd = "setenv ipaddr {0}".format(dutaddr)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        if srvaddr is None:
            srvaddr = self.tftp_server
        cmd = "setenv serverip {0}".format(srvaddr)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

    def set_lnx_net(self, intf):
        log_debug("Starting to configure the networking ... ")
        cmd = "ifconfig {0} {1}".format(intf, self.dutip)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

    def is_network_alive_in_uboot(self, ipaddr=None, retry=3):
        is_alive = False
        if ipaddr is None:
            ipaddr = self.tftp_server

        cmd = "ping {0}".format(ipaddr)
        exp = "host {0} is alive".format(ipaddr)
        self.pexp.expect_ubcmd(timeout=10, exptxt="", action=cmd, post_exp=exp, retry=retry)

    def is_network_alive_in_linux(self, ipaddr=None, retry=3):
        if ipaddr is None:
            ipaddr = self.tftp_server

        cmd = "ifconfig; ping -c 3 {0}".format(ipaddr)
        exp = r"64 bytes from {0}".format(ipaddr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=exp, retry=retry)

    def gen_rsa_key(self):
        cmd = "dropbearkey -t rsa -f {0}".format(self.rsakey_path)
        self.fcd.common.pcmd(cmd)
        '''
            The dropbearkey command will be executed in the FCD host.
            So, it won't cost too much time
        '''
        time.sleep(1)

        cmd = "chmod 777 {0}".format(self.rsakey_path)
        self.fcd.common.pcmd(cmd)

        rt = os.path.isfile(self.rsakey_path)
        if rt is not True:
            otmsg = "Can't find the RSA key file"
            error_critical(otmsg)

    def gen_dss_key(self):
        cmd = "dropbearkey -t dss -f {0}".format(self.dsskey_path)
        self.fcd.common.pcmd(cmd)
        '''
            The dropbearkey command will be executed in the FCD host.
            So, it won't cost too much time
        '''
        time.sleep(1)

        cmd = "chmod 777 {0}".format(self.dsskey_path)
        self.fcd.common.pcmd(cmd)

        rt = os.path.isfile(self.dsskey_path)
        if rt is not True:
            otmsg = "Can't find the DSS key file"
            error_critical(otmsg)

    def data_provision_64k(self, netmeta, post_en=True):
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
            "-f " + self.eegenbin_path,
            "-r 113-{0}".format(self.bom_rev),
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + netmeta['ethnum'][self.board_id],
            "-w " + netmeta['wifinum'][self.board_id],
            "-b " + netmeta['btnum'][self.board_id],
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
        log_debug("flash editor cmd: " + sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(0.5)
        if int(rtc) > 0:
            otmsg = "Flash editor filling out {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Flash editor filling out {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        cmd = "dd if={0} of=/tmp/{1} bs=1k count=64".format(self.devregpart, self.eeorg)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(0.1)

        dstp = "/tmp/{0}".format(self.eeorg)
        self.tftp_put(remote=self.eeorg_path, local=dstp, timeout=20)

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

        cmd = "dd if=/tmp/{0} of={1} bs=1k count=64".format(self.eeorg, self.devregpart)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=post_exp)
        time.sleep(0.1)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")
        srcp = os.path.join(self.tools, self.helper_path, self.helperexe)
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)
        self.tftp_get(remote=srcp, local=helperexe_path, timeout=30)

        cmd = "chmod 777 {0}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class=" + self.product_class,
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
            srcp = os.path.join(self.tftpdir, fh)
            dstp = "/tmp/{0}".format(fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send helper output files from DUT to host ...")

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
            [sto, rtc] = self.fcd.common.xcmd(cmd)
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
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if int(rtc) != 0:
                retry -= 1
                log_debug("Receive {} from DUT incomplete, remaining retry {}".format(file, retry))
                time.sleep(2)
            else:
                break

        if retry == 0:
            error_critical("Failed to receive {} from DUT".format(file))

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
            'sshpass -p ' + dut_pass,
            'scp',
            '-o StrictHostKeyChecking=no',
            '-o UserKnownHostsFile=/dev/null',
            src_file,
            dut_user + "@" + dut_ip + ":" + dst_file
        ]
        cmdj = ' '.join(cmd)
        log_debug('Exec "{}"'.format(cmdj))
        [stout, rv] = self.fcd.common.xcmd(cmdj)
        if int(rv) != 0:
            error_critical('Exec "{}" failed'.format(cmdj))
        else:
            log_debug('scp successfully')

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
        mac_comma = ':'.join([self.mac[i: i + 2] for i in range(0, len(self.mac), 2)])
        return mac_comma

    def mac_format_str2dash(self, strmac):
        mac_dash = '-'.join([self.mac[i: i + 2] for i in range(0, len(self.mac), 2)])
        return mac_dash

    def mac_format_str2list(self, strmac):
        mac_list = self.mac_format_str2comma(strmac).split(':')
        return mac_list

    def close_fcd(self):
        self.test_result = 'Pass'
        time.sleep(2)
        exit(0)

    def __del__(self):
        try:
            if self.upload:
                # Compute test_time/duration
                self.test_endtime_datetime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
                self.test_duration = (self.test_endtime_datetime - self.test_starttime_datetime).seconds
                self.test_starttime = self.test_starttime_datetime.strftime('%Y-%m-%d_%H:%M:%S')
                self.test_endtime = self.test_endtime_datetime.strftime('%Y-%m-%d_%H:%M:%S')

                # Store error function
                self.__store_error_function()

                # Dump all var
                self.__dump_JSON()
                self._upload_prepare()

        except Exception as e:
            print (e)

    def __store_error_function(self):
        ubntlib_errorcollecter = errorcollecter()

        self.progress = ubntlib_errorcollecter.msgno

        if self.test_result != 'Pass':
            self.error_function = ubntlib_errorcollecter.error_function
            # Can implement original error_code
            self.error_code = self.error_function

    def __dump_JSON(self):
        dumpfile = os.path.join("/tftpboot/", "log_slot" + self.row_id + ".json")
        with open(dumpfile, 'w') as f:
            self.__dict__.pop('fsiw', None)
            f.write(str(json.dumps(self.__dict__, default=lambda o: '<not serializable>', sort_keys=True, indent=4)))

    def _upload_prepare(self):
        sfile = os.path.join("/tftpboot/", "log_slot" + str(self.row_id) + ".log")
        jfile = os.path.join("/tftpboot/", "log_slot" + str(self.row_id) + ".json")

        timestamp = self.test_starttime_datetime.strftime('%Y-%m-%d_%H_%M_%S_%f')
        upload_root_folder = "/media/usbdisk/upload"
        upload_dut_folder = os.path.join(upload_root_folder, timestamp + '_' + str(self.mac))
        upload_dut_filename = '_'.join([timestamp, str(self.mac), str(self.test_result)])
        upload_dut_logpath = os.path.join(upload_dut_folder, upload_dut_filename + ".log")
        upload_dut_jsonpath = os.path.join(upload_dut_folder, upload_dut_filename + ".json")

        if not os.path.isdir(upload_dut_folder):
            os.makedirs(upload_dut_folder)

        # We can extend more file into the upload_dict for uploading
        upload_file_dict = {
            sfile: upload_dut_logpath,
            jfile: upload_dut_jsonpath
        }

        for ori_file, copy_file in upload_file_dict.items():
            if os.path.isfile(ori_file):
                shutil.copy2(ori_file, copy_file)
                time.sleep(1)

        self._upload_ui_taipei(uploadfolder=upload_dut_folder, mac=self.mac, bom=self.bom_rev)
        self._upload_ui_taipei_farget(uploadfolder=upload_dut_folder, mac=self.mac, bom=self.bom_rev)
        self._upload_ui_usa(uploadfolder=upload_dut_folder, mac=self.mac, bom=self.bom_rev,
                            upload_dut_logpath=upload_dut_logpath)

    def _upload_ui_taipei(self, uploadfolder, mac, bom):
        """
            command parameter description for trigger /api/v1/uploadlog WebAPI in Cloud
            command: python3
            --path:   uploadfolder or uploadpath
            --mac:   mac address with lowercase
            --bom:   BOM Rev version
            --stage:   FCD or FTU
        """
        logupload_client_path = os.path.join(self.ubntlib_dir, 'fcd', 'logupload_client.py')

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
            log_debug('\n{}\n{}\n[Upload_ui_taipei Fail]'.format(e.output.decode('utf-8'), e.returncode))
        except:
            log_debug("[Upload_ui_taipei Unexpected error: {}]".format(sys.exc_info()[0]))

    def _upload_ui_taipei_farget(self, uploadfolder, mac, bom):
        """
            command parameter description for trigger /api/v1/uploadlog WebAPI in Cloud
            command: python3
            --path:  uploadfolder or uploadpath
            --mac:   mac address with lowercase
            --bom:   BOM Rev version
            --srv:   UI-cloud
            --stage: FCD or FTU
        """
        logupload_client_path = os.path.join(self.ubntlib_dir, 'fcd', 'logupload_client.py')

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

    def _upload_ui_usa(self, uploadfolder, mac, bom, upload_dut_logpath):
        """
            Mike Taylor's uploadlog client. If any error , give up uploading
        """
        if not self.pass_phrase:
            log_debug("[Upload_ui_usa Skip - pass_phrase is None]")
            return

        try:
            stage = 'FCD'
            timestampstr = '%Y-%m-%d_%H_%M_%S_%f'
            tpe_tz = datetime.timezone(datetime.timedelta(hours=8))
            start_time = datetime.datetime.now(tpe_tz)
            start_timestr = start_time.strftime(timestampstr)
            uploadpath = os.path.join(uploadfolder, '{}_{}{}'.format(start_timestr, mac, ".tar.gz"))
            with tarfile.open(uploadpath, mode="w|gz") as tf:
                if os.path.isdir(upload_dut_logpath):
                    tar_dir = os.path.join(stage, bom, start_timestr + '_' + mac)
                    tf.add(upload_dut_logpath, tar_dir)
                elif os.path.isfile(upload_dut_logpath):
                    tar_dir = os.path.join(stage, bom, start_timestr + '_' + mac, os.path.basename(upload_dut_logpath))
                    tf.add(upload_dut_logpath, tar_dir)

            cmd = "uname -a"
            [sto, rtc] = self.cnapi.xcmd(cmd)
            if int(rtc) > 0:
                error_critical("Get linux information failed!!")
            else:
                log_debug("Get linux information successfully")
                match = re.findall("armv7l", sto)
                if match:
                    clientbin = "/usr/local/sbin/upload_rpi4_release"
                else:
                    clientbin = "/usr/local/sbin/upload_x86_release"

            regparam = [
                "-h prod.udrs.io",
                "--input field=name,format=binary,value={}".format(os.path.basename(uploadpath)),
                "--input field=content,format=binary,pathname={}".format(uploadpath),
                "--input field=type_id,format=hex,value=00000001",
                "--output field=result",
                "--output field=upload_id",
                "--output field=registration_status_id",
                "--output field=registration_status_msg",
                "--output field=error_message",
                "-k " + self.pass_phrase,
                "-x " + os.path.join(self.key_dir, "ca.pem"),
                "-y " + os.path.join(self.key_dir, "key.pem"),
                "-z " + os.path.join(self.key_dir, "crt.pem")
            ]
            regparam = ' '.join(regparam)
            execcmd = "sudo {0} {1}".format(clientbin, regparam)

            uploadproc = subprocess.check_output(execcmd, shell=True)
            log_debug('\n[Start upload_x86_client Command]\n{}\n'.format(execcmd))
            if "field=result,format=u_int,value=1" in str(uploadproc.decode('utf-8')):
                log_debug('[Upload_ui_usa Success]')
            else:
                raise subprocess.CalledProcessError

        except subprocess.CalledProcessError as e:
            log_debug('\n{}\n{}\n[Upload_ui_usa Fail]'.format(e.output.decode('utf-8'), e.returncode))
        except:
            log_debug("[Upload_ui_usa Unexpected error: {}]".format(sys.exc_info()[0]))
