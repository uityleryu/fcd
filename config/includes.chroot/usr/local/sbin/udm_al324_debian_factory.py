#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os


class UDM_AL324_DEBIAN_FACTORY(ScriptBase):
    def __init__(self):
        super(UDM_AL324_DEBIAN_FACTORY, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = "ALPINE_UBNT_UDM_PRO_SE>"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = "udm"
        self.bomrev = "113-" + self.bom_rev
        self.username = "root"
        self.password = "ubnt"
        self.linux_prompt = "#"

        # Base path
        self.tftpdir = self.tftpdir + "/"
        self.toolsdir = "tools/"

        # switch chip
        self.swchip = {
            'ea2c': "rtl83xx"
        }

        # number of Ethernet
        self.ethnum = {
            'ea2c': "11"
        }

        # number of WiFi
        self.wifinum = {
            'ea2c': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ea2c': "1"
        }

        # ethernet interface 
        self.netif = {
            'ea2c': "enp0s1"
        }

        self.infover = {
            'ea2c': "Version:"
        }

        self.devnetmeta = {
            'ethnum'          : self.ethnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.UPDATE_UBOOT          = False
        self.BOOT_RECOVERY_IMAGE   = True 
        self.INIT_RECOVERY_IMAGE   = True 
        self.NEED_DROPBEAR         = True 
        self.PROVISION_ENABLE      = True 
        self.DOHELPER_ENABLE       = True 
        self.REGISTER_ENABLE       = True 
        self.FWUPDATE_ENABLE       = False
        self.DATAVERIFY_ENABLE     = True
        self.LCM_CHECK_ENABLE      = False

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def update_uboot(self):
        pass

    def copy_fw_to_tftpserver(self, source, dest):
        sstr = [
            "cp",
            "-p",
            source,
            dest
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Copying FW to tftp server failed")

    def boot_recovery_image(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.set_boot_net()
        time.sleep(2)

        # copy recovery image
        self.copy_fw_to_tftpserver(
            source=os.path.join(self.fwdir, self.board_id + "-recovery"),
            dest=os.path.join(self.tftpdir, "uImage")
        )

        # copy FW image
        self.copy_fw_to_tftpserver(
            source=os.path.join(self.fwdir, self.board_id + "-fw.bin"),
            dest=os.path.join(self.tftpdir, "fw-image.bin")
        )

        self.is_network_alive_in_uboot(retry=9)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargsextra 'server={} factory'".format(self.tftp_server))
        self.pexp.expect_action(10, self.bootloader_prompt, "run bootcmdtftp")
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_only(180, "Welcome to UniFi")

    def init_recovery_image(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip))
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)        

    def fwupdate(self):
        pass

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def lcm_fw_ver_check(self):
        pass

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT is True:
            self.update_uboot()

        if self.BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()

        if self.INIT_RECOVERY_IMAGE is True:
            self.init_recovery_image()
            msg(10, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            self.fwupdate()
            self.login(self.username, self.password, timeout=180, log_level_emerg=True)

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.LCM_CHECK_ENABLE is True:
            msg(85, "Check LCM FW version ...")
            self.lcm_fw_ver_check()

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    udm_al324_debian_factory = UDM_AL324_DEBIAN_FACTORY()
    udm_al324_debian_factory.run()

if __name__ == "__main__":
    main()     
