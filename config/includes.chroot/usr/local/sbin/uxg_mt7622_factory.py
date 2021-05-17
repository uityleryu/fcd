#!/usr/bin/python3
import time
import os
import stat
from udm_alpine_factory import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

BOOT_RECOVERY_IMAGE = True
PROVISION_ENABLE = True
DOHELPER_ENABLE = True

REGISTER_ENABLE = True
FWUPDATE_ENABLE = False
DATAVERIFY_ENABLE = True  # to do, wait where to check info

'''
    b080: UXG-LITE
'''


class UXGMT7622Factory(ScriptBase):
    def __init__(self):
        super(UXGMT7622Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.helper_path = "uxg"
        self.helperexe = "helper_MT7622_release"
        self.user = "root"
        self.bootloader_prompt = "MT7622"
        self.linux_prompt = "#"

        self.ethnum = {
            'b080': "5"
        }

        self.wifinum = {
            'b080': "2"
        }

        self.btnum = {
            'b080': "1"
        }

        # ethernet interface
        self.netif = {
            'b080': "ifconfig eth0 "
        }

        self.infover = {
            'b080': "Version:"
        }
        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def boot_recovery_image(self):
        self.pexp.expect_action(300, "Hit any key to", "")
        self.pexp.expect_action(30, self.bootloader_prompt, 'set bootargs "console=ttyS0,115200n1 earlyprintk ubnt-flash-factory"' )
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        time.sleep(2)

        cmd = "ping {0}".format(self.tftp_server)
        postexp = "host {0} is alive".format(self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, postexp)

        cmd = "tftpb tools/uxg/fake_uxglite_eeprom; nor init; snor erase 0x220000 0x10000; snor write $loadaddr 0x220000 0x10000"
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)

        cmd = "tftpboot 0x4007ff28 images/{0}-recovery".format(self.board_id)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(120, "Bytes transferred")

        self.pexp.expect_action(10, self.bootloader_prompt, "bootm 0x4007ff28")

    def init_recovery_image(self):
        self.login(self.user, self.password, 60)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
        time.sleep(2)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, "64 bytes from")

    def fwupdate(self):
        srcp = "images/{0}-fw.bin".format(self.board_id)
        dstp = "{0}/upgrade.bin".format(self.dut_tmpdir)
        self.tftp_get(remote=srcp, local=dstp, timeout=300)

        srcp = "images/{0}-recovery".format(self.board_id)
        dstp = "{0}/uImage.r".format(self.dut_tmpdir)
        self.tftp_get(remote=srcp, local=dstp, timeout=90)

        log_debug("Starting to do fwupdate ... ")
        cmd = "sh /usr/bin/ubnt-upgrade -d {0}/upgrade.bin".format(self.dut_tmpdir)
        postexp = [
            "Firmware version",
            "Writing recovery"
        ]
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, postexp)

    def check_info(self):
        """ Use preliminary FW , no gating so far """
        self.login( timeout=160 )
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        # self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        # self.pexp.expect_only(30, "qrid="+self.qrcode)
        # self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/build.properties")
        # self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/version")

    def run(self):
        """
            Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()
            self.init_recovery_image()
            msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(dut_tmp_subdir="uxg")
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    factory = UXGMT7622Factory()
    factory.run()

if __name__ == "__main__":
    main()
