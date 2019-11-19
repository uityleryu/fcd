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

from ubntlib.fcd.common import Tee
from ubntlib.fcd.helper import FCDHelper
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical
from ubntlib.fcd.expect_tty import ExpttyProcess
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread


class ScriptBase(object):
    __version__ = "1.0.6"
    __authors__ = "FCD team"
    __contact__ = "fcd@ubnt.com"

    def __init__(self):
        self.input_args = self._init_parse_inputs()
        self._init_share_var()
        self.fcd = FCDHelper()
        self._init_log()
        # must be set by set_pexpect_helper()
        # example usuage - self.pexp.{function}(...)
        self.__pexpect_obj = None
        self.__serial_obj = None
        self.__ssh_client_obj = None
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
        # prompt related
        self.bootloader_prompt = "u-boot>"
        self.linux_prompt = "#"
        self.cmd_prefix = r"go $ubntaddr "

        # DU log-in info
        self.user = "ubnt"
        self.password = "ubnt"

        # fcd related
        self.fcd_user = "user"
        self.fcd_version_info_file = "version.txt"
        self.fcd_version_info_file_path = os.path.join("/home", self.fcd_user, "Desktop", self.fcd_version_info_file)

        # images is saved at /tftpboot/images, tftp server searches files start from /tftpboot
        self.tftpdir = "/tftpboot"
        self.dut_tmpdir = "/tmp"
        self.image = "images"
        self.tools = "tools"
        self.helper_path = ""
        self.fwdir = os.path.join(self.tftpdir, self.image)
        self.fcd_toolsdir = os.path.join(self.tftpdir, self.tools)
        self.fcd_commondir = os.path.join(self.tftpdir, self.tools, "common")
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

    def _init_parse_inputs(self):
        parse = argparse.ArgumentParser(description="FCD tool args Parser")
        parse.add_argument('--prdline', '-pline', dest='product_line', help='Active Product Line', default=None)
        parse.add_argument('--prdname', '-pname', dest='product_name', help='Active Product Name', default=None)
        parse.add_argument('--slot', '-s', dest='row_id', help='Slot id', default=None)
        parse.add_argument('--dev', '-d', dest='dev', help='UART device number. ex:ttyUSB0, ttyUSB1', default=None)
        parse.add_argument('--tftp_server', '-ts', dest='tftp_server', help='FCD host IP', default=None)
        parse.add_argument('--board_id', '-b', dest='board_id', help='System ID, ex:eb23, eb21', default=None)
        parse.add_argument('--erasecal', '-e', dest='erasecal', help='Erase calibration data selection', default=None)
        parse.add_argument('--mac', '-m', dest='mac', help='MAC address', default=None)
        parse.add_argument('--pass_phrase', '-p', dest='pass_phrase', help='Passphrase', default=None)
        parse.add_argument('--key_dir', '-k', dest='key_dir', help='Directory of key files', default=None)
        parse.add_argument('--bom_rev', '-bom', dest='bom_rev', help='BOM revision', default=None)
        parse.add_argument('--qrcode', '-q', dest='qrcode', help='QR code', default=None)
        parse.add_argument('--region', '-r', dest='region', help='Region Code', default=None)

        args, _ = parse.parse_known_args()
        self.product_line = args.product_line
        self.product_name = args.product_name
        self.row_id = args.row_id if args.row_id is not None else "0"
        self.dev = args.dev
        self.tftp_server = args.tftp_server
        self.board_id = args.board_id if args.board_id is not None else "na"
        self.erasecal = args.erasecal
        self.mac = args.mac.lower() if args.mac is not None else args.mac
        self.premac = "fc:ec:da:00:00:1" + self.row_id
        self.pass_phrase = args.pass_phrase
        self.key_dir = args.key_dir
        self.bom_rev = args.bom_rev
        self.qrcode = args.qrcode
        self.region = args.region
        self.fwimg = self.board_id + ".bin"
        self.fwimg_mfg = self.board_id + "-mfg.bin"
        return args

    def _encrpyt_passphrase_for_log(self):
        if self.input_args.pass_phrase is not None:
            k = []
            for c in self.input_args.pass_phrase:
                k.append('{:02x}'.format(ord(c)))
            self.input_args.pass_phrase = ''.join(k)
        else:
            log_debug("No passphrase input!")

    def login(self, username="ubnt", password="ubnt", timeout=10):
        """
        should be called at login console
        """
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
            self.pexp.expect_only(10, username)
            time.sleep(1)
            self.pexp.expect_action(10, "Password:", password)
            time.sleep(2)

        return ridx

    def set_bootloader_prompt(self, prompt=None):
        if prompt is not None:
            self.bootloader_prompt = prompt
        else:
            print("Nothing changed. Please assign prompt!")

    def is_dutfile_exist(self, filename):
        """check if file exist on dut by shell script"""
        # ls "<filename>"; echo "RV="$?
        cmd = "ls {0}; echo \"RV\"=$?".format(filename)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp="RV=0")
        return True

    def erase_eefiles(self):
        log_debug("Erase existed eeprom information files ...")
        files = [self.eeorg, self.eebin, self.eetxt, self.eechk, self.eetgz, self.rsakey, self.eegenbin, self.eesign, self.eesigndate]
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

    def registration(self):
        log_debug("Starting to do registration ...")
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
        regsubparams = sto
        if int(rtc) > 0:
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")

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
                "-i field=flash_eeprom,format=binary,pathname=" + self.eegenbin_path,
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
            clientbin = "/usr/local/sbin/client_x86_release_20190507"
            regparam = [
                "-h devreg-prod.ubnt.com",
                "-k " + self.pass_phrase,
                regsubparams,
                reg_qr_field,
                "-i field=flash_eeprom,format=binary,pathname=" + self.eegenbin_path,
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

        log_debug("Excuting client_x86 registration successfully")

    def add_fcd_info(self):
        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

        cmd = "dd if={0} of=/tmp/{1} bs=1 skip=53248 count=4096".format(self.devregpart, self.eeorg)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(1)
        self.chk_lnxcmd_valid()

        dstp = "/tmp/{0}".format(self.eeorg)
        self.tftp_put(remote=self.eeorg_path, local=dstp, timeout=20)

        '''
            Trying to put the FCD information stored in the e.org.0
            to the area of 0xD000 ~ 0xDFFF of the e.s.0
        '''
        f1 = open(self.eeorg_path, "rb")
        content1 = list(f1.read())
        content1_len = len(content1)
        f1.close()

        f2 = open(self.eesign_path, "rb")
        content2 = list(f2.read())
        f2.close()

        f3 = open(self.eesign_path, "wb")
        for idx in range(0, content1_len - 20):
            '''
                FCD information area: 0xD000 ~ 0xDFFF
                The decimal of 0xD000 is 53248
            '''
            content2[idx + 53248] = content1[idx]

        arr = bytearray(content2)
        f3.write(arr)
        f3.close()

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
        if post_en is True:
            post_txt = self.linux_prompt

        if dut_tmp_subdir is not None:
            eechk_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eechk)
        else:
            eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)

        if dut_tmp_subdir is not None:
            eesigndate_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eesigndate)
        else:
            eesigndate_dut_path = os.path.join(self.dut_tmpdir, self.eesigndate)

        if zmodem is False:
            self.tftp_get(remote=self.eesigndate, local=eesigndate_dut_path, timeout=timeout, post_en=post_en)
        else:
            self.zmodem_send_to_dut(file=self.eesigndate_path, dest_path=self.dut_tmpdir)

        log_debug("Change file permission - {0} ...".format(self.eesigndate))
        cmd = "chmod 777 {0}".format(eesigndate_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt)
        self.chk_lnxcmd_valid()

        log_debug("Starting to write signed info to SPI flash ...")
        cmd = "dd if={0} of={1} bs=1k count=64".format(eesigndate_dut_path, self.devregpart)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt)
        self.chk_lnxcmd_valid()

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        cmd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt)
        self.chk_lnxcmd_valid()

        log_debug("Send " + self.eechk + " from DUT to host ...")

        if zmodem is False:
            self.tftp_put(remote=self.eechk_path, local=eechk_dut_path, timeout=timeout, post_en=post_en)
        else:
            self.zmodem_recv_from_dut(file=eechk_dut_path, dest_path=self.tftpdir)

        otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, self.eesigndate)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.eechk_path, self.eesigndate_path)
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
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt)
        self.chk_lnxcmd_valid()

        src = os.path.join(self.dut_tmpdir, "*")
        cmd = "chmod -R 777 {0}".format(src)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt)
        self.chk_lnxcmd_valid()

    def is_network_alive_in_linux(self):
        time.sleep(3)
        self.pexp.expect_action(timeout=10, exptxt="", action="\nifconfig;ping " + self.tftp_server)
        extext_list = ["ping: sendto: Network is unreachable",
                       r"64 bytes from " + self.tftp_server]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == 0 or index == self.pexp.TIMEOUT:
            self.pexp.expect_action(timeout=10, exptxt="", action="\003")
            return False
        elif index == 1:
            self.pexp.expect_action(timeout=10, exptxt="", action="\003")
            return True

    def gen_rsa_key(self):
        cmd = "dropbearkey -t rsa -f {0}".format(self.rsakey_path)
        self.fcd.common.pcmd(cmd)
        time.sleep(4)

        cmd = "chmod 777 {0}".format(self.rsakey_path)
        self.fcd.common.pcmd(cmd)

        rt = os.path.isfile(self.rsakey_path)
        if rt is not True:
            otmsg = "Can't find the RSA key file"
            error_critical(otmsg)

    def gen_dss_key(self):
        cmd = "dropbearkey -t dss -f {0}".format(self.dsskey_path)
        self.fcd.common.pcmd(cmd)
        time.sleep(4)

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
        time.sleep(1)
        if int(rtc) > 0:
            otmsg = "Flash editor filling out {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Flash editor filling out {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")
        srcp = os.path.join(self.tools, self.helper_path, self.helperexe)
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)
        self.tftp_get(remote=srcp, local=helperexe_path, timeout=20)

        cmd = "chmod 777 {}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        self.chk_lnxcmd_valid()

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
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt)
        self.chk_lnxcmd_valid()
        time.sleep(1)

        files = [self.eetxt]
        for fh in files:
            srcp = os.path.join(self.tftpdir, fh)
            dstp = "/tmp/{0}".format(fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send helper output tgz file from DUT to host ...")

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
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_exp, retry=retry)

        self.chk_lnxcmd_valid()
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
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_exp, retry=retry)

        self.chk_lnxcmd_valid()
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

    def zmodem_send_to_dut(self, file, dest_path, timeout=60):
        # chdir to dest path
        self.pexp.expect_action(timeout, "", "")
        self.pexp.expect_action(timeout, self.linux_prompt, "cd {}".format(dest_path))

        # exe receive cmd on dut
        cmd = "lrz -v -b"
        self.pexp.expect_action(timeout, "", "")
        self.pexp.expect_action(timeout, self.linux_prompt, cmd)

        # exe send cmd on host
        cmd = ["sz", "-e -v -b",
               file,
               "< /dev/" + self.dev,
               "> /dev/" + self.dev]
        cmd = ' '.join(cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if int(rtc) != 0:
            error_critical("Failed to send {} to DUT".format(file))

    def zmodem_recv_from_dut(self, file, dest_path, timeout=60):
        # exe send cmd on dut
        cmd = ["lsz", "-e -v -b", file]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(timeout, "", "")
        self.pexp.expect_action(timeout, self.linux_prompt, cmd)

        # chdif to dest path on host
        os.chdir(dest_path)

        # exe receive cmd on host
        cmd = ["rz", "-y -v -b",
               "< /dev/" + self.dev,
               "> /dev/" + self.dev]
        cmd = ' '.join(cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if int(rtc) != 0:
            error_critical("Failed to receive {} from DUT".format(file))

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
        self.pexp.expect_lnxcmd(timeout=3, pre_exp=self.linux_prompt, action=cmd, post_exp="RV=0")

    def close_fcd(self):
        time.sleep(3)
        exit(0)
