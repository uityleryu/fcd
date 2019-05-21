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
NEED_UBUPDATE_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True

diagsh = ""


class USUDCALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USUDCALPINEFactoryGeneral, self).__init__()
        global diagsh

        self.ver_extract('UniFiSwitch', 'USW-LEAF')
        self.bomrev = "113-" + self.bom_rev
        self.dut_util_dir = os.path.join(self.dut_tmpdir, "usw_leaf")
        self.host_util_dir = os.path.join(self.tftpdir, "tools", "usw_leaf")
        self.bootloader_prompt = "UDC"
        self.devregpart = "/dev/mtdblock4"
        self.diagsh = "UBNT"
        self.eepmexe = "x86-64k-ee"
        self.helperexe = "helper_f060_AL324_release"
        self.eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        self.eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        self.lcmfwver = "v2.0.1-0-g8cc9eeb"

        # number of Ethernet
        self.ethnum = {
            'f060': "73"
        }

        # number of WiFi
        self.wifinum = {
            'f060': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'f060': "0"
        }

        self.netif = {
            'f060': "ifconfig eth0 "
        }

        self.infover = {
            'f060': "Version:"
        }

    def stop_at_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        time.sleep(1)

    def ubupdate(self):
        self.stop_at_uboot()
        self.set_boot_net()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "bootupd done")
        self.pexp.expect_only(30, "variables are deleted from flash using the delenv script")
        time.sleep(1)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv tftpdir images/" + self.board_id + "-fw-")
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")

    def lnx_netcheck(self, netifen=False):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth1 down", self.linux_prompt)
        if netifen is True:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
            time.sleep(2)

        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)

    def data_provision(self):
        log_debug("Change files permission ...")
        util_path = os.path.join(self.dut_util_dir, "*")

        cmd = "chmod 777 {0}".format(util_path)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

        self.gen_rsa_key()

        otmsg = "Starting to do {0} ...".format(self.eepmexe)
        log_debug(otmsg)
        flasheditor = os.path.join(self.host_util_dir, self.eepmexe)
        sstr = [
            flasheditor,
            "-F",
            "-f " + self.eegenbin_path,
            "-r " + self.bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
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
        helperexe_path = os.path.join(self.dut_util_dir, self.helperexe)
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin_dut_path,
            ">",
            self.eetxt_dut_path
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        cmd = "cd /tmp; tar cf {0} {1} {2}".format(self.eetgz, self.eebin, self.eetxt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

        os.mknod(self.eetgz_path)
        os.chmod(self.eetgz_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")

        cmd = "tftp -p -r {0} -l /tmp/{0} {1}".format(self.eetgz, self.tftp_server)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        time.sleep(1)

        cmd = "tar xvf {0} -C {1}/".format(self.eetgz_path, self.tftpdir)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            otmsg = "Decompressing {0} file failed!!".format(self.eetgz)
            error_critical(otmsg)
        else:
            otmsg = "Decompressing {0} files successfully".format(self.eetgz)
            log_debug(otmsg)

        rtc = filecmp.cmp(self.eebin_path, self.eegenbin_path)
        if rtc is True:
            otmsg = "Comparing files {0} and {1} are the same".format(self.eebin, self.eegenbin)
            log_debug(otmsg)
        else:
            otmsg = "Comparing files failed!! {0}, {1} are not the same".format(self.eebin, self.eegenbin)
            error_critical(otmsg)

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

        regparamj = ' '.join(regparam)

        cmd = "sudo /usr/local/sbin/client_x86_release_20190507 {0}".format(regparamj)
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

    def fwupdate(self):
        cmd = "tftp -g -r images/{0}-fw-uImage -l /tmp/uImage.r {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, self.linux_prompt)

        cmd = "tftp -g -r images/{0}-fw-boot.img -l /tmp/boot.img {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd_retry(300, self.linux_prompt, cmd, self.linux_prompt)

        log_debug("Is flashing U-boot")
        postexp = [
            r"Erasing blocks:.*\(50%\)",
            r"Erasing blocks:.*\(100%\)",
            r"Writing data:.*\(50%\)",
            r"Writing data:.*\(100%\)",
            r"Verifying data:.*\(50%\)",
            r"Verifying data:.*\(100%\)",
            self.linux_prompt
        ]
        cmd = "flashcp -v /tmp/boot.img {0}".format("/dev/mtd0")
        self.pexp.expect_lnxcmd_retry(600, self.linux_prompt, cmd, self.linux_prompt)

        log_debug("Is flashing recovery image")
        postexp = [
            r"Erasing blocks:.*\(50%\)",
            r"Erasing blocks:.*\(100%\)",
            r"Writing data:.*\(50%\)",
            r"Writing data:.*\(100%\)",
            r"Verifying data:.*\(50%\)",
            r"Verifying data:.*\(100%\)",
            self.linux_prompt
        ]
        cmd = "flashcp -v /tmp/uImage.r {0}".format("/dev/mtd5")
        self.pexp.expect_lnxcmd_retry(600, self.linux_prompt, cmd, postexp)

        self.pexp.expect_lnxcmd(60, self.linux_prompt, "reboot", self.linux_prompt)

        self.login(username="ubnt", password="ubnt", timeout=80)

        log_debug("Starting to do fwupdate ... ")

        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        cmd = "ping -c 1 {0}".format(self.tftp_server)
        self.pexp.expect_lnxcmd_retry(15, self.linux_prompt, cmd, postexp)

        cmd = "tftp -g -r images/{0}-fw.bin -l /tmp/upgrade.bin {1}".format(self.board_id, self.tftp_server)
        self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, self.linux_prompt)

        postexp = [
            "Firmware version",
        ]
        cmd = "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin"
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, postexp)
        self.login(username="root", password="ubnt", timeout=100)

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "info")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, "qrid=" + self.qrcode)
        self.pexp.expect_only(10, self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "lcm-ctrl -t dump", self.lcmfwver)

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
        # detect the BSP U-boot
        self.pexp.expect_only(30, "May 06 2019 - 12:15:33")
        self.pexp.expect_only(80, "Welcome to UBNT PyShell")
        self.pexp.expect_lnxcmd(10, diagsh, "diag", "DIAG")
        self.pexp.expect_lnxcmd(10, "DIAG", "npsdk speed 0 10", "DIAG")
        self.pexp.expect_lnxcmd(10, "DIAG", "shell", self.linux_prompt)

        self.lnx_netcheck(True)
        msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut()
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

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    usudc_factory_general = USUDCALPINEFactoryGeneral()
    usudc_factory_general.run()

if __name__ == "__main__":
    main()
