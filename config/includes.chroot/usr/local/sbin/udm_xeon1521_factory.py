#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp


PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
PROGRAM_MAC = True
FWUPDATE_ENABLE = False
DATAVERIFY_ENABLE = True


class UDMXEONFactory(ScriptBase):
    def __init__(self):
        super(UDMXEONFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # override the base vars
        self.user = "root"
        self.linux_prompt = "# $"

        # script specific vars
        self.devregpart = "/dev/sda3"
        self.bomrev = "113-" + self.bom_rev
        self.eepmexe = "xeon1521-ee"
        self.eeupdate = "eeupdate64e"
        self.helperexe = "helper_XEON1521_release"
        self.dut_udmxgdir = os.path.join(self.dut_tmpdir, "udm_xg")
        self.helper_path = os.path.join(self.dut_udmxgdir, self.helperexe)
        self.eepmexe_path = os.path.join(self.dut_udmxgdir, self.eepmexe)
        self.eeupdate_path = os.path.join(self.dut_udmxgdir, self.eeupdate)

        # EEPROM related files path on DUT
        self.eesign_dut_path = os.path.join(self.dut_udmxgdir, self.eesign)
        self.eetgz_dut_path = os.path.join(self.dut_udmxgdir, self.eetgz)
        self.eechk_dut_path = os.path.join(self.dut_udmxgdir, self.eechk)
        self.eebin_dut_path = os.path.join(self.dut_udmxgdir, self.eebin)
        self.eetxt_dut_path = os.path.join(self.dut_udmxgdir, self.eetxt)

        self.fcd_udmxgsdir = os.path.join(self.tftpdir, "tmp", "udm_xg")

        # switch chip
        self.swchip = {
            'ea17': "qca8k",
        }

        self.wsysid = {
            'ea17': "770711ea"
        }

        # number of Ethernet
        self.ethnum = {
            'ea17': "2"
        }

        # number of WiFi
        self.wifinum = {
            'ea17': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ea17': "0"
        }

        self.netif = {
            'ea17': "ifconfig eth0 "
        }

        self.infover = {
            'ea17': "Version:"
        }

    def data_provision(self):
        log_debug("Change file permission - " + self.helperexe + " ...")
        sstr = [
            "chmod 777",
            self.helper_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        log_debug("Change file permission - " + self.eepmexe + " ...")
        sstr = [
            "chmod 777",
            self.eepmexe_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        log_debug("Change file permission - " + self.eeupdate + " ...")
        sstr = [
            "chmod 777",
            self.eeupdate_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        log_debug("Change file permission - dropbearkey ...")
        dropbear_path = os.path.join(self.dut_udmxgdir, "dropbearkey")
        sstr = [
            "chmod 777",
            dropbear_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        log_debug("Copy missing library ...")
        dut_lib_path = os.path.join(self.dut_udmxgdir, "lib")
        sstr = [
            "cp",
            dut_lib_path + "/*",
            "/lib/"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        sstr = [
            "cp",
            dropbear_path,
            "/usr/bin/dropbearkey"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

    def do_eeprom(self):
        log_debug("Starting to do " + self.eepmexe + "...")
        # ./xeon1521-ee -F -r 113-02719-11 -s 0xea17 -m 0418d6a0f7f7 -c 0x0000 -e 2 -w 2 -b 0 -k
        sstr = [
            self.eepmexe_path,
            "-F",
            "-r " + self.bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
            "-k"
        ]
        sstrj = ' '.join(sstr)

        postexp = [
            "ssh-dss",
            "ssh-rsa"
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj, post_exp=postexp)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")
        sstr = [
            self.helper_path,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin_dut_path,
            ">",
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "cf",
            self.eetgz_dut_path,
            self.eebin_dut_path,
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        os.mknod(self.eetgz_path)
        os.chmod(self.eetgz_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetgz,
            "-l " + self.eetgz_dut_path,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "xvf " + self.eetgz_path,
            "-C " + self.tftpdir
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz_path + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz_path + " files successfully")
        eetxt = os.path.join(self.fcd_udmxgsdir, self.eetxt)
        eebin = os.path.join(self.fcd_udmxgsdir, self.eebin)
        sstr = [
            "mv",
            eetxt,
            self.eetxt_path
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        sstr = [
            "mv",
            eebin,
            self.eebin_path
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)

    def program_macs(self):
        log_debug("Write Intel 82599 MAC address ...")
        base_mac = self.mac
        mac_1 = self.mac[0:6]+str(hex(int(self.mac[6:12], 16)+1))[2:8].upper()
        mac_2 = self.mac[0:6]+str(hex(int(self.mac[6:12], 16)+2))[2:8].upper()
        mac_3 = self.mac[0:6]+str(hex(int(self.mac[6:12], 16)+3))[2:8].upper()

        self.pexp.expect_action(10, "", self.eeupdate_path + " /NIC=1 /MAC=" + base_mac)
        self.pexp.expect_action(10, self.linux_prompt, self.eeupdate_path + " /NIC=2 /MAC=" + mac_1)
        self.pexp.expect_action(10, self.linux_prompt, self.eeupdate_path + " /NIC=3 /MAC=" + mac_2)
        self.pexp.expect_action(10, self.linux_prompt, self.eeupdate_path + " /NIC=4 /MAC=" + mac_3)

    def fwupdate(self):
        fcd_fwpath = os.path.join(self.image, self.board_id + "-fw.bin")
        fwpath = os.path.join(self.dut_tmpdir, "upgrade.bin")
        sstr = [
            "tftp",
            "-g",
            "-r " + fcd_fwpath,
            "-l " + fwpath,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(120, self.linux_prompt, sstrj)
        time.sleep(120)
        rec_fwpath = os.path.join(self.image, self.board_id + "-recovery")
        recpath = os.path.join(self.dut_tmpdir, "uImage.r")
        sstr = [
            "tftp",
            "-g",
            "-r " + rec_fwpath,
            "-l " + recpath,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        time.sleep(60)

        msg(80, "Succeeding in downloading the upgrade tarf file ...")
        self.pexp.expect_action(10, self.linux_prompt, "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin")
        self.pexp.expect_only(60, "Firmware version")
        self.pexp.expect_only(60, "Writing recovery")

        self.pexp.expect_action(300, "login:", self.user)
        self.pexp.expect_action(60, "Password:", self.password)

    def check_info(self):
        """under developing
        """
        if False:
            self.pexp.expect_action(10, self.linux_prompt, "info")
            self.pexp.expect_only(10, self.infover[self.board_id])

            self.pexp.expect_action(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
            self.pexp.expect_action(10, "systemid=" + self.board_id, "")
            self.pexp.expect_action(10, self.linux_prompt, "")

        self.pexp.expect_action(10, self.linux_prompt, "hexdump -C -s 0x0 -n 100 /dev/sda3")
        self.pexp.expect_action(10, self.linux_prompt, "")
        self.pexp.expect_action(10, self.linux_prompt, "hexdump -C -s 0xa000 -n 100 /dev/sda3")
        self.pexp.expect_action(10, self.linux_prompt, "")

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Login to DUT ...")
        self.pexp.expect_action(300, "Welcome to UbiOS", self.pexp.newline)
        time.sleep(0.5)

        self.pexp.expect_action(300, "login:", self.user)
        self.pexp.expect_action(10, "Password:", self.password)

        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "dmesg -n 1")

        msg(10, "Config DUT IP ...")
        self.pexp.expect_action(10, self.linux_prompt, self.netif[self.board_id] + self.dutip)
        time.sleep(2)
        self.pexp.expect_action(10, self.linux_prompt, "ping " + self.tftp_server)
        self.pexp.expect_action(10, "64 bytes from", '\003')
        self.pexp.expect_action(10, self.linux_prompt, "")

        if PROVISION_ENABLE is True:
            msg(15, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=30)
            msg(20, "Send EEPROM command and set info to EEPROM ...")
            self.data_provision()
            msg(25, "Run " + self.eepmexe + " ...")
            self.do_eeprom()

        if DOHELPER_ENABLE is True:
            msg(30, "Prepeare files for registration ...")
            self.erase_eefiles()
            msg(40, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(60, "Finish doing registration ...")
            self.check_devreg_data(dut_tmp_subdir="udm_xg", mtd_count=128)
            msg(65, "Finish doing signed file and EEPROM checking ...")

        if PROGRAM_MAC is True:
            self.program_macs()
            msg(70, "Finish write Intel 82599 MAC ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            self.pexp.expect_action(300, "login:", self.user)
            self.pexp.expect_action(15, "Password:", self.password)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1")
            msg(80, "Succeeding in fw upgrading...")

        if DATAVERIFY_ENABLE is True:
            msg(90, "Checking final status ...")
            self.check_info()
            msg(95, "Succeeding in checking the devreg information ...")

        msg(100, "Completing FCD process")
        time.sleep(2)
        self.close_fcd()


def main():
    udm_factory = UDMXEONFactory()
    udm_factory.run()

if __name__ == "__main__":
    main()
