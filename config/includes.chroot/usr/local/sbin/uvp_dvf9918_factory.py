#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

NEED_DROPBEAR = True
PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
CHECK_UBOOT_ENABLE = True
FWUPDATE_ENABLE = False
DATAVERIFY_ENABLE = False

# U-boot prompt
ubpmt = ""

# linux console prompt
lnxpmt = ""

username = "root"
password = "ubnt"

tmpdir = "/tmp/"
tftpdir = ""
toolsdir = "tools/"
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
        global lnxpmt
        global ubpmt
        global devregpart

        tftpdir = self.tftpdir + "/"
        bomrev = "113-" + self.bom_rev
        self.devregpart = "/dev/mtdblock2"
        self.bootloader_prompt = "DVF99 #"
        self.linux_prompt = "root@dvf9918:~#"
        lnxpmt = self.linux_prompt
        ubpmt = self.bootloader_prompt

    def dutisfile(self, dir_filename):
        sstr = [
            "ls -la",
            dir_filename
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        idx = self.pexp.expect_get_index(10, "No such file")
        if idx == 0:
            log_debug("Can't find the " + dir_filename)
            exit(1)
        else:
            return True

    def copytool2dut(self):
        global toolsdir
        global tmpdir
        sstr = [
            "tftp",
            "-g",
            "-r " + toolsdir + "uvp/dropbearkey",
            "-l " + tmpdir + "dropbearkey",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        sstr = [
            "tftp",
            "-g",
            "-r " + toolsdir + "uvp/helper_DVF99_release",
            "-l " + tmpdir + "helper_DVF99_release",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        sstr = [
            "tftp",
            "-g",
            "-r " + toolsdir + "uvp/dvf9918-arm64-ee",
            "-l " + tmpdir + "dvf9918-arm64-ee",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        self.dutisfile(tmpdir + "dropbearkey")
        self.dutisfile(tmpdir + "helper_DVF99_release")
        self.dutisfile(tmpdir + "dvf9918-arm64-ee")

    def data_provision(self):
        log_debug("Change file permission - " + helperexe + " ...")
        sstr = [
            "chmod 777",
            tmpdir + helperexe
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Change file permission - " + eepmexe + " ...")
        sstr = [
            "chmod 777",
            tmpdir + eepmexe
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        if NEED_DROPBEAR is True:
            log_debug("Copying the dropbearkey to /usr/bin ...")
            sstr = [
                "chmod 777",
                tmpdir + "dropbearkey"
            ]
            sstrj = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
            sstr = [
                "cp",
                tmpdir + "dropbearkey",
                "/usr/bin/dropbearkey"
            ]
            sstrj = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Starting to do " + eepmexe + "...")
        sstr = [
            tmpdir + eepmexe,
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
        sstrj = ' '.join(sstr)

        postexp = [
            "ssh-dss",
            "ssh-rsa",
            lnxpmt
        ]
        self.pexp.expect_lnxcmd(60, lnxpmt, sstrj, post_exp=postexp)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + helperexe + "...")
        sstr = [
            tmpdir + helperexe,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin,
            ">",
            self.eetxt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
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
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
        time.sleep(2)

        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetxt,
            "-l " + self.eetxt,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
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
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(tftpdir + self.eesign)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

    def fwupdate(self):
        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-fw.bin",
            "-l " + tmpdir + "upgrade.bin",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(300, lnxpmt, sstrj, lnxpmt)

        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-recovery",
            "-l " + tmpdir + "uImage.r",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(90, lnxpmt, sstrj, lnxpmt)

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "sh",
            "/usr/bin/ubnt-upgrade",
            "-d",
            "/tmp/upgrade.bin"
        ]
        sstrj = ' '.join(sstr)

        postexp = [
            "Firmware version",
            "Writing recovery"
        ]
        self.pexp.expect_lnxcmd(300, lnxpmt, sstrj, postexp)

    def check_devreg_data(self):
        log_debug("Send signed eeprom file from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + tmpdir + self.eesign,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            tmpdir + helperexe,
            "-q",
            "-i field=flash_eeprom,format=binary,pathname=" + tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + self.devregpart,
            "of=" + tmpdir + self.eechk,
            "bs=1k count=64"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        os.mknod(tftpdir + self.eechk)
        os.chmod(tftpdir + self.eechk, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + self.eechk + " from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eechk,
            "-l " + tmpdir + self.eechk,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, sstrj)
        self.pexp.expect_only(10, lnxpmt)
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

    def check_info(self):
        ct = 0
        index = -1
        while ct < 5 and index == 0:
            self.pexp.expect_cmd(10, lnxpmt, "info")
            index = self.pexp.expect_get_index(5, infover[self.board_id])
            ct += 1

        self.pexp.expect_lnxcmd(10, lnxpmt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())

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
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Boot to linux console ...")
        self.pexp.expect_only(10, "U-Boot")
        self.pexp.expect_action(60, "login:", username)

        self.pexp.expect_lnxcmd(10, lnxpmt, "dmesg -n 1", lnxpmt)
        time.sleep(5)
        self.pexp.expect_lnxcmd(10, lnxpmt, netif[self.board_id] + self.dutip, lnxpmt)
        postexp = [
            "64 bytes from",
            lnxpmt
        ]
        self.pexp.expect_lnxcmd(10, lnxpmt, "ping -c 1 " + self.tftp_server, postexp)
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
            self.pexp.expect_lnxcmd(90, lnxpmt, sstr, lnxpmt)

        if CHECK_UBOOT_ENABLE is True:
            mcf = self.mac_colon_format(self.mac)
            self.pexp.expect_lnxcmd(10, lnxpmt, "reboot", "")
            self.pexp.expect_action(60, "stop autoboot", "\033")
            self.pexp.expect_ubcmd(30, ubpmt, "printenv")
            self.pexp.expect_only(30, "ethaddr=" + mcf)

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

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
