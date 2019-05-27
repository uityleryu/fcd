#!/usr/bin/python3
"""
Base script class
"""
import sys
import time
import os
import stat
import filecmp
import argparse
import json

from ubntlib.fcd.common import Tee
from ubntlib.variable.helper import VariableHelper
from ubntlib.fcd.helper import FCDHelper
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical
from ubntlib.fcd.expect_tty import ExpttyProcess


class ScriptBase(object):
    def __init__(self):
        self.input_args = self._init_parse_inputs()
        # shared variable object
        # example usuage - self.var.{toolspecific}.{variable}
        self.var = VariableHelper(self.input_args)
        self._init_share_var()
        self.fcd = FCDHelper()
        self._init_log()
        # must be set by set_pexpect_helper()
        # example usuage - self.pexp.{function}(...)
        self.__pexpect_obj = None
        self.fcd.common.print_current_fcd_version(file=self.fcd_version_info_file_path)

        self._encrpyt_passphrase_for_log()
        log_debug(str(self.input_args))

    @property
    def pexp(self):
        if self.__pexpect_obj is not None:
            return self.__pexpect_obj
        else:
            error_critical("No pexpect obj exists!")

    def set_pexpect_helper(self, pexpect_obj):
        self.__pexpect_obj = pexpect_obj
        self.fcd.set_pexpect_obj(pexpect_obj)

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
        self.prodl = ""
        self.fwdir = os.path.join(self.tftpdir, self.image)
        self.fcd_toolsdir = os.path.join(self.tftpdir, self.tools)
        self.eepmexe = "x86-64k-ee"

        '''
           Will be defined by the specifi model script
           Ex: /tmp/uvp
        '''
        self.devregpart = ""
        self.helperexe = ""

        # EEPROM file in binary format generated by flash editor
        self.eegenbin = "e.gen." + self.row_id

        # EEPROM file in binary format generated by helper utility
        self.eebin = "e.b." + self.row_id

        # EEPROM file in text format generated by helper utility
        self.eetxt = "e.t." + self.row_id

        # compress EEPROM files
        self.eetgz = "e." + self.row_id + ".tgz"

        # Get the signed EEPROM from security server
        self.eesign = "e.s." + self.row_id

        # retrieve the content from EEPROM partition of DUT
        self.eechk = "e.c." + self.row_id

        # RSA key file
        self.rsakey = "dropbear_key.rsa." + self.row_id

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

        # EX: /tftpboot/e.c.0
        self.eechk_path = os.path.join(self.tftpdir, self.eechk)

        # EX: /tftpboot/dropbear_key.rsa.0
        self.rsakey_path = os.path.join(self.tftpdir, self.rsakey)

        # DUT IP
        baseip = 31
        self.dutip = "192.168.1." + str((int(self.row_id) + baseip))

        self.fcd_id = ""
        self.sem_ver = ""
        self.sw_id = ""
        self.fw_ver = ""

        # The HEX of the QR code
        if self.qrcode is not None:
            self.qrhex = self.qrcode.encode('utf-8').hex()

    def _init_parse_inputs(self):
        parse = argparse.ArgumentParser(description="FCD tool args Parser")
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
        self.row_id = args.row_id if args.row_id is not None else "0"
        self.dev = args.dev
        self.tftp_server = args.tftp_server
        self.board_id = args.board_id if args.board_id is not None else "na"
        self.erasecal = args.erasecal
        self.mac = args.mac.lower() if args.mac is not None else args.mac
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
        self.pexp.expect_action(timeout, "login:", username)
        self.pexp.expect_only(10, username)
        self.pexp.expect_action(10, "Password:", password)
        time.sleep(2)

    def set_bootloader_prompt(self, prompt=None):
        if prompt is not None:
            self.bootloader_prompt = prompt
        else:
            print("Nothing changed. Please assign prompt!")

    def is_dutfile_exist(self, filename):
        """check if file exist on dut by shell script"""
        # ls "<filename>"; echo "RV="$?
        sstrj = 'ls "' + filename + '"; echo "RV="$?'
        self.pexp.expect_lnxcmd_retry(10, self.linux_prompt, sstrj, post_exp="RV=0")

    def erase_eefiles(self):
        log_debug("Erase existed eeprom information files ...")
        files = [self.eebin, self.eetxt, self.eechk, self.eetgz, self.rsakey, self.eegenbin]
        for f in files:
            destf = os.path.join(self.tftpdir, f)
            rtf = os.path.isfile(destf)
            if rtf is True:
                log_debug("Erasing File - " + f + " ...")
                os.chmod(destf, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.remove(destf)
            else:
                log_debug("File - " + f + " doesn't exist ...")

    def ver_extract(self, productline, productname):
        fh = open(self.fcd_version_info_file_path, "r")
        complete_ver = fh.readline()
        msg(no="", out="FCD version: " + complete_ver)
        fh.close()
        complete_ver_s = complete_ver.split("-")
        self.sem_dotver = complete_ver_s[3]
        self.fw_dotver = complete_ver_s[4]

        # version mapping
        fh = open('/usr/local/sbin/Products-info.json')
        self.fsiw = json.load(fh)
        fh.close()

        # FCD_ID (this name is called by Mike) like product line
        self.fcd_id = self.fsiw[productline][productname]['FCD_ID']

        # SW_ID (this name is called by Mike) like product model
        self.sw_id = self.fsiw[productline][productname]['SW_ID']

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
        regsubparams = sto.decode('UTF-8')
        if int(rtc) > 0:
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")

        if self.fcd_id == "" or self.sem_ver == "" or self.sw_id == "" or self.fw_ver == "":
            clientbin = "/usr/local/sbin/client_x86_release"
            regparam = [
                "-h devreg-prod.ubnt.com",
                "-k " + self.pass_phrase,
                regsubparams,
                "-i field=qr_code,format=hex,value=" + self.qrhex,
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
            clientbin = "/usr/local/sbin/client_x86_release_20190507"
            regparam = [
                "-h devreg-prod.ubnt.com",
                "-k " + self.pass_phrase,
                regsubparams,
                "-i field=qr_code,format=hex,value=" + self.qrhex,
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

        log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

    def check_devreg_data(self, dut_tmp_subdir=None, mtd_count=None, post_exp=True, timeout=10):
        """check devreg data
        in default we assume the datas under /tmp on dut
        but if there is sub dir in your tools.tar, you should set dut_subdir

        you MUST make sure there is eesign file under /tftpboot

        Keyword Arguments:
            dut_subdir {[str]} -- like udm, unas, afi_aln...etc, take refer to structure of fcd-script-tools repo
        """
        log_debug("Send signed eeprom file from host to DUT ...")
        post_txt = self.linux_prompt if post_exp is True else None
        eechk_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eechk) if dut_tmp_subdir is not None \
            else os.path.join(self.dut_tmpdir, self.eechk)
        eesign_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eesign) if dut_tmp_subdir is not None \
            else os.path.join(self.dut_tmpdir, self.eesign)

        cmd = "tftp -g -r {0} -l {1} {2}".format(self.eesign, eesign_dut_path, self.tftp_server)
        self.pexp.expect_lnxcmd_retry(timeout, self.linux_prompt, cmd, post_exp=post_txt)

        log_debug("Change file permission - " + self.eesign + " ...")
        cmd = "chmod 777 {0}".format(eesign_dut_path)
        self.pexp.expect_lnxcmd_retry(timeout, self.linux_prompt, cmd, post_exp=post_txt)

        log_debug("Starting to write signed info to SPI flash ...")
        cmd = "dd if={0} of={1} bs=1k count=64".format(eesign_dut_path, self.devregpart)
        self.pexp.expect_lnxcmd_retry(timeout, self.linux_prompt, cmd, post_exp=post_txt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        cmd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
        self.pexp.expect_lnxcmd_retry(timeout, self.linux_prompt, cmd, post_exp=post_txt)

        os.mknod(self.eechk_path)
        os.chmod(self.eechk_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + self.eechk + " from DUT to host ...")
        cmd = "tftp -p -r {0} -l {1} {2}".format(self.eechk, eechk_dut_path, self.tftp_server)
        self.pexp.expect_lnxcmd_retry(timeout, self.linux_prompt, cmd, post_exp=post_txt)
        time.sleep(3)  # in case the e.c.0 is still in transfering
        if os.path.isfile(self.eechk_path):
            otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, self.eesign)
            log_debug(otmsg)
            rtc = filecmp.cmp(self.eechk_path, self.eesign_path)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            otmsg = "Can't find the {0} and {1} files ...".format(self.eechk, self.eesign)
            log_debug(otmsg)

    def gen_and_load_key_to_dut(self):
        src = os.path.join(self.tftpdir, "dropbear_key.rsa")
        sstr = [
            "dropbearkey",
            "-t rsa",
            "-f",
            src
        ]
        sstr = ' '.join(sstr)
        self.fcd.common.pcmd(sstr)

        sstr = [
            "chmod 777",
            src
        ]
        sstr = ' '.join(sstr)
        self.fcd.common.pcmd(sstr)

        dest = os.path.join(self.dut_tmpdir, "dropbear_key.rsa")
        sstr = [
            "tftp",
            "-g",
            "-r dropbear_key.rsa",
            "-l " + dest,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd_retry(timeout=15, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt)
        self.is_dutfile_exist(dest)

    def copy_and_unzipping_tools_to_dut(self, timeout=15, post_exp=True):
        log_debug("Send tools.tar from host to DUT ...")
        post_txt = self.linux_prompt if post_exp is True else None
        source = os.path.join(self.tools, "tools.tar")
        target = os.path.join(self.dut_tmpdir, "tools.tar")

        cmd = "tftp -g -r {0} -l {1} {2}".format(source, target, self.tftp_server)
        self.pexp.expect_lnxcmd_retry(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt)
        time.sleep(1)

        self.is_dutfile_exist(target)

        cmd = "tar -xzvf {0} -C {1}".format(target, self.dut_tmpdir)
        self.pexp.expect_lnxcmd_retry(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt)

        src = os.path.join(self.dut_tmpdir, "*")
        cmd = "chmod -R 777 {0}".format(src)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt)

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

    def data_provision_64k(self, netmeta):
        self.gen_rsa_key()

        otmsg = "Starting to do {0} ...".format(self.eepmexe)
        log_debug(otmsg)
        flasheditor = os.path.join(netmeta['flashed_dir'], self.eepmexe)
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
            otmsg = "Generating {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Generating {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        cmd = "tftp -g -r {0} -l /tmp/{0} {1}".format(self.eegenbin, self.tftp_server)
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)

        cmd = "dd if=/tmp/{0} of={1} bs=1k count=64".format(self.eegenbin, self.devregpart)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")

        src = os.path.join(self.tools, self.prodl, self.helperexe)
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)

        cmd = "tftp -g -r {0} -l {1} {2}".format(src, helperexe_path, self.tftp_server)
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)

        cmd = "chmod 777 {}".format(helperexe_path)
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)        
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + eebin_dut_path,
            ">",
            eetxt_dut_path
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        files = [self.eebin, self.eetxt]
        for fh in files:
            fh_path = os.path.join(self.tftpdir, fh)
            os.mknod(fh_path)
            os.chmod(fh_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            cmd = "tftp -p -r {0} -l /tmp/{0} {1}".format(fh, self.tftp_server)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
            time.sleep(1)

        log_debug("Send helper output tgz file from DUT to host ...")

        rtc = filecmp.cmp(self.eebin_path, self.eegenbin_path)
        if rtc is True:
            otmsg = "Comparing files {0} and {1} are the same".format(self.eebin, self.eegenbin)
            log_debug(otmsg)
        else:
            otmsg = "Comparing files failed!! {0}, {1} are not the same".format(self.eebin, self.eegenbin)
            error_critical(otmsg)

    def close_fcd(self):
        time.sleep(3)
        exit(0)
