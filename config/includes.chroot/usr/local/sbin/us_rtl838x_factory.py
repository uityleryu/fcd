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
FWUPGRADE_ENABLE = True
DATAVERIFY_ENABLE = True

# U-boot prompt
ubpmt = "UBNT"

# linux console prompt
lnxpmt = "#"

tmpdir = "/tmp/"
tftpdir = ""
toolsdir = "tools/"
bomrev = ""
eepmexe = "rtl838x-ee"
helperexe = "helper_rtl838x"
mtdpart = "/dev/mtdblock6"
dutuser = "ubnt"
dutpwd = "ubnt"

# number of Ethernet
ethnum = {
    'ed20': "17",
    'ed21': "25",
    'ed22': "49"
}

# number of WiFi
wifinum = {
    'ed20': "0",
    'ed21': "0",
    'ed22': "0"
}

# number of Bluetooth
btnum = {
    'ed20': "0",
    'ed21': "0",
    'ed22': "0"
}


class USWLITEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USWLITEFactoryGeneral, self).__init__()
        global tftpdir
        global bomrev
        tftpdir = self.tftpdir + "/"
        bomrev = "113-" + self.bom_rev

    def dutisfile(self, dir_filename):
        sstr = [
            "ls",
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
        log_debug("Send tools.tar from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + toolsdir + "tools.tar",
            "-l " + tmpdir + "tools.tar",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Unzipping the tools.tar in the DUT ...")
        self.dutisfile(tmpdir + "tools.tar")
        sstr = [
            "tar",
            "-xvzf",
            tmpdir + "tools.tar",
            "-C " + tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

    def data_provision(self):
        log_debug("Change file permission - " + helperexe + " ...")
        self.dutisfile(tmpdir + helperexe)
        self.dutisfile(tmpdir + eepmexe)
        sstr = [
            "chmod 777",
            tmpdir + helperexe
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)

        log_debug("Change file permission - " + eepmexe + " ...")
        sstr = [
            "chmod 777",
            tmpdir + eepmexe
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Starting to do " + eepmexe + "...")
        sstr = [
            tmpdir + eepmexe,
            "-F",
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
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(60, "ssh-dss")
        self.pexp.expect_only(60, "ssh-rsa")
        self.pexp.expect_only(30, lnxpmt)

    def prepare_sever_need_files(self):
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
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        sstr = [
            "tar",
            "cf",
            self.eetgz,
            self.eebin,
            self.eetxt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        os.mknod(tftpdir + self.eetgz)
        os.chmod(tftpdir + self.eetgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetgz,
            "-l " + self.eetgz,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        sstr = [
            "tar",
            "xvf " + tftpdir + self.eetgz,
            "-C " + tftpdir
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz + " files successfully")

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
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(6)
        if int(rtc) > 0:
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(tftpdir + self.eesign)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

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
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            "dd",
            "if=" + tmpdir + self.eesign,
            "of=" + mtdpart
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_only(10, lnxpmt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + mtdpart,
            "of=" + tmpdir + self.eechk
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, sstrj)
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
        self.pexp.expect_only(10, lnxpmt)

        if os.path.isfile(tftpdir + self.eechk):
            log_debug("Starting to compare the " + self.eechk + " and " + self.eesign + " files ...")
            rtc = filecmp.cmp(tftpdir + self.eechk, tftpdir + self.eesign)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            log_debug("Can't find the " + self.eechk + " and " + self.eesign + " files ...")

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
        msg(5, "Open serial port successfully ...")

        self.pexp.expect_action(150, "Please press Enter to activate this console", "")
        self.pexp.expect_action(30, "login:", dutuser)
        self.pexp.expect_action(10, "Password:", dutpwd)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, "dmesg -n 1")
        self.pexp.expect_action(10, lnxpmt, "ping " + self.tftp_server)
        self.pexp.expect_action(10, "64 bytes from", '\003')
        self.pexp.expect_only(10, lnxpmt)
        msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copytool2dut()
            self.data_provision()

        if DOHELPER_ENABLE is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_sever_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPGRADE_ENABLE is True:
            pass

        if DATAVERIFY_ENABLE is True:
            pass
        exit(0)


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        us_factory_general = USWLITEFactoryGeneral()
        us_factory_general.run()

if __name__ == "__main__":
    main()
