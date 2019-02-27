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
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True

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
eepmexe = "al324-ee"
helperexe = "helper_AL324_release"
mtdpart = "/dev/mtdblock4"

# switch chip
swchip = {
    'ea11': "qca8k",
    'ea13': "rtl83xx",
    'ea15': "rtl83xx"
}

wsysid = {
    'ea11': "770711ea",
    'ea13': "770713ea",
    'ea15': "770715ea"
}

# number of Ethernet
ethnum = {
    'ea11': "5",
    'ea13': "7",
    'ea15': "9"
}

# number of WiFi
wifinum = {
    'ea11': "2",
    'ea13': "2",
    'ea15': "0"
}

# number of Bluetooth
btnum = {
    'ea11': "1",
    'ea13': "1",
    'ea15': "1"
}

netif = {
    'ea11': "ifconfig eth0 ",
    'ea13': "ifconfig eth1 ",
    'ea15': "ifconfig eth1 "
}

infover = {
    'ea11': "Version:",
    'ea13': "Version",
    'ea15': "Version:"
}

write_sysid_cmd = ""


class UDMALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UDMALPINEFactoryGeneral, self).__init__()
        global tftpdir
        global bomrev
        global write_sysid_cmd
        global lnxpmt
        global ubpmt
        tftpdir = self.tftpdir + "/"
        bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "UBNT"
        self.linux_prompt = "#"
        lnxpmt = self.linux_prompt
        ubpmt = self.bootloader_prompt

        # write system ID to the EEPROM partition
        write_sysid_cmd = "mw.l 0x08000000 " + wsysid[self.board_id]

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, ubpmt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, ubpmt, "setenv serverip " + self.tftp_server)

    def dutisfile(self, dir_filename):
        sstr = [
            "ls",
            dir_filename
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
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
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Unzipping the tools.tar in the DUT ...")
        self.dutisfile(tmpdir + "tools.tar")
        sstr = [
            "tar",
            "-xvzf",
            tmpdir + "tools.tar",
            "-C " + tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

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
                "cp",
                tmpdir + "dropbearkey_arm64",
                "/usr/bin/dropbearkey"
            ]
            sstrj = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

            log_debug("Starting to initialize the dropbear")
            sstr = [
                "mkdir",
                "-p",
                "/var/run/dropbear; ",
                "dropbear -R"
            ]
            sstrj = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

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
            "-k",
            "-p Factory"
        ]
        sstrj = ' '.join(sstr)

        postexp = [
            "ssh-dss",
            "ssh-rsa",
            "Fingerprint",
            lnxpmt
        ]
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, post_exp=postexp)

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

        sstr = [
            "tar",
            "cf",
            self.eetgz,
            self.eebin,
            self.eetxt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

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
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
        time.sleep(1)

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
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + tmpdir + self.eesign,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            tmpdir + helperexe,
            "-q",
            "-i field=flash_eeprom,format=binary,pathname=" + tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + mtdpart,
            "of=" + tmpdir + self.eechk
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)

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
        self.pexp.expect_lnxcmd(10, lnxpmt, sstrj, lnxpmt)
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

        msg(5, "Boot from tftp with installer ...")
        self.pexp.expect_action(15, "to stop", "\033\033")

        # Set the system ID to the DUT
        self.pexp.expect_ubcmd(10, ubpmt, write_sysid_cmd)
        self.pexp.expect_ubcmd(10, ubpmt, "sf probe")
        self.pexp.expect_ubcmd(10, ubpmt, "sf erase 0x1f0000 0x1000")
        self.pexp.expect_only(30, "Erased: OK")
        self.pexp.expect_ubcmd(10, ubpmt, "sf write 0x8000000 0x1f000c 0x4")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, ubpmt, "reset")
        self.pexp.expect_action(10, "to stop", "\033\033")

        self.pexp.expect_ubcmd(10, ubpmt, swchip[self.board_id])
        self.set_boot_net()
        self.pexp.expect_ubcmd(10, ubpmt, "setenv tftpdir images/" + self.board_id + "_signed_")
        time.sleep(2)
        self.pexp.expect_ubcmd(10, ubpmt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")
        self.pexp.expect_ubcmd(10, ubpmt, "run bootupd")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_only(10, "bootupd done")
        self.pexp.expect_ubcmd(10, ubpmt, "reset")
        self.pexp.expect_action(10, "to stop", "\033\033")

        # Set the Ethernet IP
        self.pexp.expect_ubcmd(10, ubpmt, swchip[self.board_id])
        self.set_boot_net()
        time.sleep(2)
        self.pexp.expect_ubcmd(10, ubpmt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")
        self.pexp.expect_ubcmd(10, ubpmt, "setenv bootargs ubnt-flash-factory pci=pcie_bus_perf console=ttyS0,115200")
        self.pexp.expect_action(10, ubpmt, "cp.b $fdtaddr $loadaddr_dt 7ffc")
        self.pexp.expect_action(10, ubpmt, "fdt addr $loadaddr_dt")
        self.pexp.expect_action(10, ubpmt, "tftpboot $loadaddr images/" + self.board_id + "-recovery")
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_action(10, ubpmt, "bootm $loadaddr - $fdtaddr")
        self.pexp.expect_action(60, "login:", username)
        self.pexp.expect_action(10, "Password:", password)

        self.pexp.expect_lnxcmd(10, lnxpmt, "dmesg -n 1", lnxpmt)
        self.pexp.expect_lnxcmd(10, lnxpmt, netif[self.board_id] + self.dutip, lnxpmt)
        time.sleep(2)

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

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        self.pexp.expect_action(200, "login:", username)
        self.pexp.expect_action(60, "Password:", password)

        self.pexp.expect_lnxcmd(10, lnxpmt, "dmesg -n 1", lnxpmt)

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
        udm_factory_general = UDMALPINEFactoryGeneral()
        udm_factory_general.run()

if __name__ == "__main__":
    main()
