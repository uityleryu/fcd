#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical


class UCMT7628Factory(ScriptBase):
    def __init__(self):
        super(UCMT7628Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()

        self.fwimg = "images/" + self.board_id + "-fw.bin"
        self.initramfs = "images/" + self.board_id + "-initramfs.bin"
        self.ubootimg = "images/" + self.board_id + "-uboot.bin"

        self.devregpart = "/dev/mtdblock3"
        self.helperexe = "helper_MT7628_release"
        self.bootloader_prompt = ">"

        self.factory_param = "factory=1"

        helper_path = {
            "ed14": "afi_ups",
            "ed15": "usp_pdu_hd",
            "ea2e": "udw_pro_pu",
        }

        self.helper_path = helper_path[self.board_id]

        # number of mac
        self.macnum = {
            'ed14': "0",  # afi-ups, project is canceled
            'ed15': "1",  # usp-pro-pdu
            'ea2e': "1",  # udw-pro-pu
        }
        # number of WiFi
        self.wifinum = {
            'ed14': "1",
            'ed15': "0",
            'ea2e': "0",
        }
        # number of Bluetooth
        self.btnum = {
            'ed14': "1",
            'ed15': "0",
            'ea2e': "0",
        }
        # flash size map
        self.flash_size = {
            'ed14': "33554432",
            'ed15': "16777216",
            'ea2e': "16777216",
        }
        # firmware image
        self.fwimg = self.board_id + "-fw.bin"
        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum': self.macnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum,
        }

        self.UPDATE_UBOOT_ENABLE = {
            'ed14': True,  # afi-ups, project is canceled
            'ed15': True,  # usp-pro-pdu, FIXME: disable uboot update process next build
            'ea2e': True,  # udw-pro-pu
        }

        self.BOOT_RAMFS_IMAGE = {
            'ed14': True,
            'ed15': True,
            'ea2e': True,
        }

        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.FWUPDATE_ENABLE = True
        self.DATAVERIFY_ENABLE = True

        self.LCM_FW_CHECK_ENABLE = {
            'ed14': False,
            'ed15': False,
            'ea2e': True,
        }

        self.OFF_POWER_UNIT_ENABLE = {
            'ed14': False,
            'ed15': False,
            'ea2e': True,
        }

    def enter_uboot(self):
        self.pexp.expect_action(60, "Hit any key to stop autoboot", "")
        self.set_boot_net()

    def enable_factory_mode_in_boot(self, enable=True):
        """
        To avoid dhcp ip waiting(this takes 2 mins), so set factory mode in uboot
        This parameter will skip plugin init within FW.
        """

        if enable is True:
            log_debug("Enable factory mode for FCD")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargs 'console=ttyS0,115200 {}'".format(self.factory_param))
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv", self.factory_param)

        else:
            log_debug("Reset env to default")
            self.pexp.expect_ubcmd(5, self.bootloader_prompt, "env default -a")
            self.pexp.expect_ubcmd(5, self.bootloader_prompt, "saveenv")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv")

    def check_factory_mode_in_kernel(self):
        """
        factory mode should be clear after FW update.
        """

        log_debug("Check factory mode have be cleared or not")

        result = self.pexp.expect_get_output("cat /proc/cmdline", self.linux_prompt, 3)
        log_debug(result)
        if self.factory_param in result:
            error_critical("Failed to reset env environment to defualt")

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv loadaddr 0x81000000")
        self.is_network_alive_in_uboot()

    def update_uboot_image(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot ${{loadaddr}} {}".format(self.ubootimg))
        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf probe; sf erase 0x0 0x60000; sf write ${loadaddr} 0x0 ${filesize}")

        # Uboot of BSP, AFi-UPS
        # SF: Detected mx25l25635e with page size 256 Bytes, erase size 64 KiB, total 32 MiB
        # SF: 393216 bytes @ 0x0 Erased: OK
        # device 0 offset 0x0, size 0x2c3f0
        # SF: 181232 bytes @ 0x0 Written: OK
        # =>

        # Uboot of FW, AFi-UPS
        # SF: Detected mx25l25635e with page size 256 Bytes, erase size 64 KiB, total 32 MiB
        # SF: 16777216 bytes @ 0x0 Erased: OK
        # uboot>

        self.pexp.expect_only(120, "Erased: OK")
        # self.pexp.expect_only(120, "Written: OK")  #BSP uboot, have "Written", FW Uboot have no Written
        # Uboot, if you enter the "Enter", uboot will run previous command so "^c" is to avoid to re-run re-program flash again
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "^c")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def clear_eeprom(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo \"EEPROM,388caeadd99840d391301bec20531fcef05400f4\" > " +
                                                       "/sys/module/mtd/parameters/write_perm", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, 'dd if=/dev/zero ibs=1 count=64K | tr "\000" "\377" > /tmp/ff.bin', self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if=/tmp/ff.bin of={} bs=1k count=64".format(self.devregpart), self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sync;sync;sync", self.linux_prompt)

    def init_ramfs_image(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot ${{loadaddr}} {}".format(self.initramfs))
        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm")

        self.pexp.expect_only(30, "Loading kernel")

    def init_kernel_net(self):
        log_debug("Config net interface")

        if self.board_id == "ed14":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "hexdump -C -n 512 /dev/mtdblock3", self.linux_prompt)
            try:
                self.disable_udhcpc()
            except Exception as e:
                log_debug("ERROR:{}".format(e))

            try:
                self.disable_wpa_supplicant()
            except Exception as e:
                log_debug("ERROR:{}".format(e))
        else:
            pass

        if self.board_id == "ed14":
            # AFi-UPS
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", self.linux_prompt)
            # time.sleep(45)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig wlan0 down", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "swconfig dev switch0 set reset", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ps", self.linux_prompt)

        elif self.board_id == "ea2e":
            log_debug("Config net interface")

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 {}".format(self.dutip), self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "swconfig dev switch0 set reset 1", self.linux_prompt)

        elif self.board_id == "ed12":
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "ifconfig eth0 " + self.dutip, self.linux_prompt)
        else:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "swconfig dev switch0 set reset", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 up", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, r"ifconfig eth0 {} netmask 255.255.255.0".format(self.dutip), self.linux_prompt)

        log_debug("Checking internet")
        self.is_network_alive_in_linux(retry=10)

    def fwupdate(self, image, reboot_en):
        if reboot_en is True:
            self.pexp.expect_action(30, self.linux_prompt, "reboot -f")
        self.enter_uboot()
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearcfg TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearenv TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv do_urescue TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
        self.pexp.expect_action(30, "Listening for TFTP transfer on", "")

        # to use Desktop atftp to transfer image to DUT
        # atftp -p -l /tftpboot/images/ea2e-fw.bin 192.168.1.20
        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir + "/" + image,
               self.dutip]
        cmdj = ' '.join(cmd)

        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
        self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(240, "done")

    def check_info(self):
        self.pexp.expect_action(30, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(30, "flashSize=" + self.flash_size[self.board_id])
        self.pexp.expect_only(30, "systemid=" + self.board_id)
        self.pexp.expect_only(30, "serialno=" + self.mac.lower())
        self.pexp.expect_only(30, "qrid=" + self.qrcode)
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/build.properties")
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/version")

    def lcm_fw_check(self):
        self.pexp.expect_lnxcmd(30, self.linux_prompt, 'cat /var/log/ulcmd.log', 'version', retry=6)
        self.pexp.expect_only(30, self.linux_prompt)

    def mcu_fw_check(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, 'ubus call power.outlet.meter_mcu info', 'version', retry=48)

    def off_power_unit_power(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "i2ctransfer -y 4 w4@0xb 0x00 0x10 0x00 0x44", self.linux_prompt)
        time.sleep(1)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "i2ctransfer -y 4 w4@0xb 0x00 0x10 0x00 0x44", self.linux_prompt)
        time.sleep(1)

    def run(self):
        self.fcd.common.config_stty(self.dev)
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE[self.board_id] is True:
            self.enter_uboot()
            self.update_uboot_image()
            msg(10, "Update Uboot image successfully ...")
        else:
            self.enter_uboot()
            self.enable_factory_mode_in_boot(enable=True)
            msg(10, "Set factory mode successfully ...")
            self.pexp.expect_ubcmd(5, self.bootloader_prompt, "bootubnt")

        if self.BOOT_RAMFS_IMAGE[self.board_id] is True:
            msg(15, "Boot into initRamfs image for registration ...")
            self.enter_uboot()
            self.init_ramfs_image()
        else:
            self.login(press_enter=True, log_level_emerg=True, timeout=90)
            msg(15, "Login system ...")

        self.init_kernel_net()
        self.clear_eeprom()

        if self.PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(30, "Do helper to get the output file to devreg server ...")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            msg(60, "Updating released firmware ...")
            self.fwupdate(self.fwimg, reboot_en=True)
            msg(70, "Updating released firmware done...")
        else:
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "reboot", self.linux_prompt)

        if self.UPDATE_UBOOT_ENABLE[self.board_id] is False:
            self.enter_uboot()
            self.enable_factory_mode_in_boot(enable=False)
            self.pexp.expect_ubcmd(5, self.bootloader_prompt, "bootubnt")

        if self.DATAVERIFY_ENABLE is True:
            self.login(press_enter=True, log_level_emerg=True, timeout=90)
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.LCM_FW_CHECK_ENABLE[self.board_id] is True:
            self.lcm_fw_check()
            msg(85, "Succeeding in checking the LCM FW information ...")

        if self.OFF_POWER_UNIT_ENABLE[self.board_id] is True:
            pass
            # self.off_power_unit_power()
            msg(90, "Power off battery ...")

        self.check_factory_mode_in_kernel()

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    uc_mt7628_factory = UCMT7628Factory()
    uc_mt7628_factory.run()


if __name__ == "__main__":
    main()
