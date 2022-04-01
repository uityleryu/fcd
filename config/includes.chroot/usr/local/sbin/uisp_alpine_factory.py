#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp


class UISPALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UISPALPINEFactoryGeneral, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = "UBNT"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.bomrev = "113-" + self.bom_rev
        self.username = "ubnt"
        self.password = "ubnt"
        self.diag_prompt = "UBNT_Diag>"
        self.linux_prompt = "/ #"

        # Base path
        self.tftpdir = self.tftpdir + "/"
        self.toolsdir = "tools/"

        # helper path
        helperpath = {
            'ee6d': "uisp-r-pro",
        }

        self.helper_path = helperpath[self.board_id]

        # switch chip
        self.swchip = {
            'ee6d': "rtl83xx",
        }

        # sub-system ID
        self.wsysid = {
            'ee6d': "77076dee",
        }

        # number of Ethernet
        self.ethnum = {
            'ee6d': "13",
        }

        # number of WiFi
        self.wifinum = {
            'ee6d': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ee6d': "1",
        }

        # ethernet interface
        self.netif = {
            'ee6d': "enp0s1",
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def set_fake_EEPROM(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + self.wsysid[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000004 01d30200")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000008 ffdaecfc")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.w 0x0800000c 000" + str(self.row_id))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf erase 0x410000 0x1000")
        self.pexp.expect_only(30, "Erased: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 0x41000c 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000004 0x410010 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000008 0x410000 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x0800000c 0x410004 0x2")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000008 0x410006 0x4")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x0800000c 0x41000a 0x2")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_ub_net()
        time.sleep(2)
        self.is_network_alive_in_uboot()

        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-uboot.bin"),
            dest=os.path.join(self.tftpdir, "boot.img")
        )

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_only(10, "bootupd done")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def reset_uboot_env(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "env default -a -f")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")  # for second partition
        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def boot_initramfs_image(self, image):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.set_ub_net()
        time.sleep(2)
        self.is_network_alive_in_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ubnt_debug_legacy_boot on")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs ubnt-flash-factory pci=pcie_bus_perf console=ttyS0,115200")

        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 0x18000004 {}".format(image))
        self.pexp.expect_only(90, "Bytes transferred")
        self.pexp.expect_action(11, self.bootloader_prompt, "bootm 0x18000004#uisprproxg@3")

    def init_diag_image(self):
        self.pexp.expect_lnxcmd(120, self.diag_prompt, "exec sh\r", self.linux_prompt)

        self.set_lnx_net(intf=self.netif[self.board_id])
        time.sleep(2)

        self.is_network_alive_in_linux(ipaddr=self.dutip, retry=30)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /etc/version", self.linux_prompt)

    def fwupdate(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_ub_net()
        time.sleep(2)
        self.is_network_alive_in_uboot()

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "rescue -e")
        self.pexp.expect_only(30, "Listening for TFTP transfer on")

        # Recovery FW included shipping FW
        cmd = "atftp -p -l {0}/{1} {2}".format(self.fwdir, self.board_id + "-recovery.bin", self.dutip)
        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(180, "Firmware version:")

    def fwupdate_diag(self):
        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-fw.bin",
            "-l " + self.dut_tmpdir + "/upgrade.bin",
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(180, self.linux_prompt, sstr, self.linux_prompt, valid_chk=True)

        msg(60, "Succeeding in downloading the upgrade tar file ...")

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "sh",
            "/usr/bin/ubnt-upgrade",
            "-d",
            self.dut_tmpdir + "/upgrade.bin",
    	    ";reboot",
	        "-f"
        ]
        sstr = ' '.join(sstr)

        postexp = ["U-Boot"]
        self.pexp.expect_lnxcmd(300, self.linux_prompt, sstr, postexp)

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/version")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/board")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def ssh_enable(self):
        '''
        unms-r-pro default ssh connection is disabled
        need to enable it manually before FTU test
        '''
        cmd = 'ubios-udapi-client put -r /services "$(ubios-udapi-client get -r /services | jq \'.sshServer.enabled = true\')"'
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True, retry=5)

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

        msg(10, "Setting fake EEPROM ...")
        self.set_fake_EEPROM()

        msg(15, "Updating uboot ...")
        self.update_uboot()

        msg(20, "Resetting uboot environment ...")
        self.reset_uboot_env()

        msg(25, "Booting diag image ...")
        self.boot_initramfs_image(image=os.path.join(self.fwdir, self.board_id + "-diag.bin"))

        msg(30, "Initializing diag image ...")
        self.init_diag_image()

        msg(35, "Sending tools to DUT and data provision ...")
        self.data_provision_64k(self.devnetmeta)

        msg(40, "Do helper to get the output file to devreg server ...")
        self.erase_eefiles()
        self.prepare_server_need_files()

        msg(45, "Doing registration ...")
        self.registration()

        msg(50, "Checking registration ...")
        self.check_devreg_data()

        msg(55, "Upgrading FW by ubnt-upgrade ...")
        self.fwupdate_diag()
        self.reset_uboot_env()

        msg(75, "Login kernel ...")
        self.pexp.expect_lnxcmd(120, self.diag_prompt, "exec sh\r", self.linux_prompt)

        msg(85, "Checking info ...")
        self.check_info()

        msg(90, "Completed checking info ...")

        '''
        self.ssh_enable()
        For legacy process.
        '''

        msg(100, "Completed FCD process ...")
        self.close_fcd()


def main():
    uisp_alpine_factory_general = UISPALPINEFactoryGeneral()
    uisp_alpine_factory_general.run()

if __name__ == "__main__":
    main()
