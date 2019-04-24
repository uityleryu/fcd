#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
CHECK_UBOOT_ENABLE = True

dut_util_dir = ""
host_util_dir = ""

bomrev = ""
eepmexe = "dvf9918-arm64-ee"
helperexe = "helper_DVF99_release"

# number of Ethernet
ethnum = {
    'ef0d': "1"
}

wifinum = {
    'ef0d': "0"
}

btnum = {
    'ef0d': "0"
}

netif = {
    'ef0d': "ifconfig eth0 "
}

infover = {
    'ef0d': "Version:"
}


class UVPDVF99FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UVPDVF99FactoryGeneral, self).__init__()
        global tftpdir
        global bomrev
        global devregpart
        global dut_util_dir
        global host_util_dir

        tftpdir = self.tftpdir + "/"
        bomrev = "113-" + self.bom_rev
        dut_util_dir = os.path.join(self.dut_tmpdir, "uvp")
        host_util_dir = os.path.join("tools", "uvp")
        self.devregpart = "/dev/mtdblock2"
        self.user = "root"
        self.bootloader_prompt = "DVF99 #"
        self.linux_prompt = "root@dvf9918:~#"

    def copytool2dut(self):
        # src = tools/uvp/helper_DVF99_release
        src = os.path.join(host_util_dir, "helper_DVF99_release")

        # dest = /tmp/helper_DVF99_release
        dest = os.path.join(self.dut_tmpdir, "helper_DVF99_release")
        sstr = [
            "tftp",
            "-g",
            "-r " + src,
            "-l " + dest,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(1)
        self.is_dutfile_exist(dest)

        # src = tools/uvp/dvf9918-arm64-ee
        src = os.path.join(host_util_dir, "dvf9918-arm64-ee")

        # dest = /tmp/dvf9918-arm64-ee
        dest = os.path.join(self.dut_tmpdir, "dvf9918-arm64-ee")
        sstr = [
            "tftp",
            "-g",
            "-r " + src,
            "-l " + dest,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(1)
        self.is_dutfile_exist(dest)

    def data_provision(self):
        log_debug("Start doing data provision ...")
        self.gen_and_load_key_to_dut()

        # src = /tmp/*
        stuffs = ["helper_DVF99_release", "dvf9918-arm64-ee", "dropbear_key.rsa"]
        for f in stuffs:
            src = os.path.join(self.dut_tmpdir, f)
            sstr = [
                "chmod 777",
                 src
            ]
            sstr = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Starting to do " + eepmexe + "...")
        eepmexe_path = os.path.join(self.dut_tmpdir, eepmexe)
        sstr = [
            eepmexe_path,
            "-F",
            "-q " + self.devregpart,
            "-r " + bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + ethnum[self.board_id],
            "-w " + wifinum[self.board_id],
            "-b " + btnum[self.board_id],
            "-k"
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(60, self.linux_prompt, sstr, self.linux_prompt)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + helperexe + "...")
        helperexe_path = os.path.join(self.dut_tmpdir, helperexe)
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin,
            ">",
            self.eetxt
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(1)

        os.mknod(tftpdir + self.eebin)
        os.chmod(tftpdir + self.eebin, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        os.mknod(tftpdir + self.eetxt)
        os.chmod(tftpdir + self.eetxt, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output files from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eebin,
            "-l " + self.eebin,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(2)

        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetxt,
            "-l " + self.eetxt,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(2)

    def registration(self):
        log_debug("Starting to do registration ...")
        cmd = [
            "cat " + tftpdir + self.eetxt,
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

        regparam = [
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            regsubparams,
            "-i field=qr_code,format=hex,value=" + self.qrhex,
            "-i field=flash_eeprom,format=binary,pathname=" + tftpdir + self.eebin,
            "-o field=flash_eeprom,format=binary,pathname=" + tftpdir + self.eesign,
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

        regparamj = ' '.join(regparam)

        cmd = "sudo /usr/local/sbin/client_x86_release " + regparamj
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(tftpdir + self.eesign)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

    def check_devreg_data(self):
        log_debug("Send signed eeprom file from host to DUT ...")
        dest = os.path.join(self.dut_tmpdir, self.eesign)
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + dest,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Change file permission - " + self.eesign + " ...")
        dest = os.path.join(self.dut_tmpdir, self.eesign)
        sstr = [
            "chmod 777",
            dest
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Starting to write signed info to SPI flash ...")
        src = os.path.join(self.dut_tmpdir, self.eesign)
        sstr = [
            "dd",
            "if=" + src,
            "of=" + self.devregpart
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        dest = os.path.join(self.dut_tmpdir, self.eechk)
        sstr = [
            "dd",
            "if=" + self.devregpart,
            "of=" + dest,
            "bs=1k count=64"
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr)

        os.mknod(tftpdir + self.eechk)
        os.chmod(tftpdir + self.eechk, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + self.eechk + " from DUT to host ...")
        dest = os.path.join(self.dut_tmpdir, self.eechk)
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eechk,
            "-l " + dest,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(1)

        if os.path.isfile(tftpdir + self.eechk):
            log_debug("Starting to compare the " + self.eechk + " and " + self.eesign + " files ...")
            rtc = filecmp.cmp(tftpdir + self.eechk, tftpdir + self.eesign)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            log_debug("Can't find the " + self.eechk + " and " + self.eesign + " files ...")

    def mac_colon_format(self, mac):
        mcf = [
            self.mac[0:2],
            self.mac[2:4],
            self.mac[4:6],
            self.mac[6:8],
            self.mac[8:10],
            self.mac[10:12]
        ]
        mcf = ':'.join(mcf)
        return mcf

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Boot to linux console ...")
        self.pexp.expect_only(10, "U-Boot")
        self.pexp.expect_action(60, "login:", self.user)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)

        self.pexp.expect_lnxcmd(10, self.linux_prompt, netif[self.board_id] + self.dutip, self.linux_prompt)
        time.sleep(3)
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copytool2dut()
            self.data_provision()

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

            mcf = self.mac_colon_format(self.mac)
            sstr = [
                "fw_setenv",
                "ethaddr",
                mcf
            ]
            sstr = ' '.join(sstr)
            self.pexp.expect_lnxcmd(90, self.linux_prompt, sstr, self.linux_prompt)

        if CHECK_UBOOT_ENABLE is True:
            mcf = self.mac_colon_format(self.mac)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
            self.pexp.expect_action(60, "stop autoboot", "\033")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv")
            self.pexp.expect_only(30, "ethaddr=" + mcf)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "securedev")
            postexp = [
                "program OTP values... ok",
                "verify OTP values... ok",
                "device seems to be partially/secured!"
            ]
            index = self.pexp.expect_get_index(30, postexp)
            log_debug("OTP index: " + str(index))
            if index < 0:
                error_critical("OTP program/verify failed")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        uvp_factory_general = UVPDVF99FactoryGeneral()
        uvp_factory_general.run()

if __name__ == "__main__":
    main()
