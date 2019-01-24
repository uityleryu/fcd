#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

# linux console prompt
lnxpmt = "# $"

class UDMXEONFactory(ScriptBase):
    def __init__(self):
        super(UDMXEONFactory, self).__init__()

    def run(self):
        """
        Main procedure of factory
        """
        tmpdir = "/tmp/"
        tftpdir = self.tftpdir + "/"
        toolsdir = "tools/"
        bomrev = "113-" + self.bom_rev
        tools_pack = "tools.tar"
        eepmexe = "xeon1521-ee"
        helperexe = "helper_XEON1521_release"
        eeupdate = "eeupdate64e"
        mtdpart = "/dev/sda3"

        # switch chip
        swchip = {
            'ea17': "qca8k",
        }

        wsysid = {
            'ea17': "770711ea"
        }

        # number of Ethernet
        ethnum = {
            'ea17': "2"
        }

        # number of WiFi
        wifinum = {
            'ea17': "0"
        }

        # number of Bluetooth
        btnum = {
            'ea17': "0"
        }

        netif = {
            'ea17': "ifconfig eth0 "
        }

        infover = {
            'ea17': "Version:"
        }

        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Login to DUT ...")

        self.pexp.expect_action(300, "Welcome to UbiOS", self.pexp.newline)
        time.sleep(0.5)

        self.pexp.expect_action(300, "login:", "root")
        self.pexp.expect_action(10, "Password:", "ubnt")

        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt, "dmesg -n 1")

        msg(10, "Config DUT IP ...")
        self.pexp.expect_action(10, lnxpmt, netif[self.board_id] + self.dutip)
        time.sleep(2)
        self.pexp.expect_action(10, lnxpmt, "ping " + self.tftp_server)
        self.pexp.expect_action(10, "64 bytes from", '\003')
        self.pexp.expect_action(10, lnxpmt, "")

        msg(20, "Send EEPROM command and set info to EEPROM ...")

        log_debug("Send tools.tar from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + toolsdir + tools_pack,
            "-l " + tmpdir + tools_pack,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        time.sleep(2)
        self.pexp.expect_action(10, ".*" + lnxpmt, "")


        log_debug("Unzipping the tools.tar in the DUT ...")
        sstr = [
            "tar",
            "-xvzf",
            tmpdir + tools_pack,
            "-C " + tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")

        log_debug("Change file permission - " + helperexe + " " + eepmexe + " " + eeupdate + " ...")
        sstr = [
            "chmod 777",
            tmpdir + helperexe,
            tmpdir + eepmexe,
            tmpdir + eeupdate
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")

        log_debug("Copy missing library ...")
        cmd = "cp /tmp/lib/* /lib/"
        self.pexp.expect_action(10, lnxpmt, cmd)
        self.pexp.expect_action(10, lnxpmt, "")

        msg(25, "Run " + eepmexe + " ...")

        # ./xeon1521-ee -F -r 113-02719-11 -s 0xea17 -m 0418d6a0f7f7 -c 0x0000 -e 2 -w 2 -b 0 -k
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
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")
        
        # TODO
        #self.pexp.expect_action(10, "ssh-dss", "")
        #self.pexp.expect_action(10, "ssh-rsa", "")

        msg(30, "Prepeare files for registration ...")
        log_debug("Erase existed eeprom information files ...")

        eefiles = [self.eebin, self.eetxt, self.eesign, self.eechk, self.eetgz]

        for file_del in eefiles:
            rtf = os.path.isfile(tftpdir + file_del)
            if rtf is True:
                log_debug("Erasing File - " + file_del + " ...")
                os.chmod(tftpdir + file_del, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.remove(tftpdir + file_del)
            else:
                log_debug("File - " + file_del + " doesn't exist ...")


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
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")

        sstr = [
            "tar",
            "cf",
            self.eetgz,
            self.eebin,
            self.eetxt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")

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
        self.pexp.expect_action(10, lnxpmt, sstrj)
        time.sleep(2)
        self.pexp.expect_action(10, lnxpmt, "")

        cmd = "tar xvf " + tftpdir + self.eetgz + " -C " + tftpdir
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz + " files successfully")

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

        msg(35, "Sending Request to devreg server ...")
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

        msg(40, "Finish doing registration ...")
        log_debug("Send signed eeprom file from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + tmpdir + self.eesign,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")
        time.sleep(2)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            "dd",
            "if=" + tmpdir + self.eesign,
            "of=" + mtdpart
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + mtdpart,
            "of=" + tmpdir + self.eechk,
            "count=128"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")
        time.sleep(1)

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
        self.pexp.expect_action(10, lnxpmt, sstrj)
        self.pexp.expect_action(10, lnxpmt, "")
        time.sleep(2)

        if os.path.isfile(tftpdir + self.eechk):
            log_debug("Starting to compare the " + self.eechk + " and " + self.eesign + " files ...")
            rtc = filecmp.cmp(tftpdir + self.eechk, tftpdir + self.eesign)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            log_debug("Can't find the " + self.eechk + " and " + self.eesign + " files ...")

        msg(50, "Finish doing signed file and EEPROM checking ...")

        log_debug("Write Intel 82599 MAC address ...")
        base_mac = self.mac
        mac_1 = base_mac[0:6]+str(hex(int(base_mac[6:12],16)+1))[2:8].upper()
        mac_2 = base_mac[0:6]+str(hex(int(base_mac[6:12],16)+2))[2:8].upper()
        mac_3 = base_mac[0:6]+str(hex(int(base_mac[6:12],16)+3))[2:8].upper()

        self.pexp.expect_action(10, lnxpmt, tmpdir + eeupdate + " /NIC=1 /MAC=" + base_mac)
        self.pexp.expect_action(10, lnxpmt, "")
        self.pexp.expect_action(10, lnxpmt, tmpdir + eeupdate + " /NIC=2 /MAC=" + mac_1)
        self.pexp.expect_action(10, lnxpmt, "")
        self.pexp.expect_action(10, lnxpmt, tmpdir + eeupdate + " /NIC=3 /MAC=" + mac_2)
        self.pexp.expect_action(10, lnxpmt, "")
        self.pexp.expect_action(10, lnxpmt, tmpdir + eeupdate + " /NIC=4 /MAC=" + mac_3)
        self.pexp.expect_action(10, lnxpmt, "")

        msg(60, "Finish write Intel 82599 MAC ...")

        if False:
            sstr = [
                "tftp",
                "-g",
                "-r images/" + self.board_id + "-fw.bin",
                "-l " + tmpdir + "upgrade.bin",
                self.tftp_server
            ]
            sstrj = ' '.join(sstr)

            self.pexp.expect_action(120, lnxpmt, sstrj)
            time.sleep(120)
            self.pexp.expect_action(10, "", "")

            sstr = [
                "tftp",
                "-g",
                "-r images/" + self.board_id + "-recovery",
                "-l " + tmpdir + "uImage.r",
                self.tftp_server
            ]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(10, lnxpmt, sstrj)
            time.sleep(60)
            self.pexp.expect_action(10, "", "")

            msg(80, "Succeeding in downloading the upgrade tarf file ...")
            self.pexp.expect_action(10, lnxpmt, "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin")
            self.pexp.expect_only(60, "Firmware version")
            self.pexp.expect_only(60, "Writing recovery")

            self.pexp.expect_action(300, "login:", "root")
            self.pexp.expect_action(60, "Password:", "ubnt")

        msg(90, "Checking final status ...")

        self.pexp.expect_action(10, lnxpmt, "dmesg")
        self.pexp.expect_action(10, lnxpmt, "")

        if False:
            self.pexp.expect_action(10, lnxpmt, "info")
            self.pexp.expect_only(10, infover[self.board_id])

            self.pexp.expect_action(10, lnxpmt, "cat /proc/ubnthal/system.info")
            self.pexp.expect_action(10, "systemid=" + self.board_id, "")
            self.pexp.expect_action(10, lnxpmt, "")

        self.pexp.expect_action(10, lnxpmt, "hexdump -C -s 0x0 -n 100 /dev/sda3")
        self.pexp.expect_action(10, lnxpmt, "")
        self.pexp.expect_action(10, lnxpmt, "hexdump -C -s 0xa000 -n 100 /dev/sda3")
        self.pexp.expect_action(10, lnxpmt, "")

        msg(100, "Completing firmware upgrading ...")
        time.sleep(2)
        exit(0)


def main():
    udm_factory = UDMXEONFactory()
    udm_factory.run()

if __name__ == "__main__":
    main()
