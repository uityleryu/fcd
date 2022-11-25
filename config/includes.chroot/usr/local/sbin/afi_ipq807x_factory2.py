#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.ssh_client import SSHClient
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil


class AFIIPQ807XFactory(ScriptBase):
    def __init__(self):
        super(AFIIPQ807XFactory, self).__init__()

        # Common folder
        self.wifi_cal_data_dir = os.path.join(self.dut_tmpdir, "IPQ8074")

        # This MD5SUM value is generated from a file with all 0xff
        self.md5sum_no_wifi_cal = "41d2e2c0c0edfccf76fa1c3e38bc1cf2"

        # booting up the last message
        bootmsg_eth = "(eth\d: PHY Link up speed)"
        bootmsg_noeth = "Please press Enter to activate this console"

        self.helperexe = "helper_IPQ807x_release"
        self.devregpart = "/dev/mtdblock18"

        # U-boot prompt
        ubpmt = {
            'da11': "IPQ807x",
            'da12': "IPQ807x",
            'da13': "IPQ807x",
            'da14': "IPQ807x",
            'da15': "IPQ807x"
        }

        # linux console prompt
        lnxpmt = {
            'da11': "ubnt@",
            'da12': "ubnt@",
            'da13': "ubnt@",
            'da14': "ubnt@",
            'da15': "ubnt@"
        }

        # number of Ethernet
        ethnum = {
            'da11': "5",
            'da12': "1",
            'da13': "5",
            'da14': "1",
            'da15': "5"
        }

        # number of WiFi
        wifinum = {
            'da11': "3",
            'da12': "3",
            'da13': "2",
            'da14': "2",
            'da15': "3"
        }

        # number of Bluetooth
        btnum = {
            'da11': "1",
            'da12': "1",
            'da13': "1",
            'da14': "1",
            'da15': "1"
        }

        # communicating Ethernet interface
        self.comuteth = {
            'da11': "br-lan",
            'da12': "br-lan",
            'da13': "br-lan",
            'da14': "br-lan",
            'da15': "br-lan"
        }

        self.devnetmeta = {
            'ethnum': ethnum,
            'wifinum': wifinum,
            'btnum': btnum
        }

        self.linux_prompt = lnxpmt[self.board_id]
        self.bootloader_prompt = ubpmt[self.board_id]

        self.WRITE_REQUIRED_IMAGES = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.DATAVERIFY_ENABLE = True

    def flash_images(self):
        msg(10, "Update the U-boot")
        log_debug("Clean the ARP table")
        self.del_arp_table(self.dutip)
        log_debug("The ARP table before ping the server")
        self.display_arp_table()
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
        time.sleep(3)
        comma_mac = self.mac_format_str2comma(self.mac)
        self.set_ub_net(comma_mac)
        self.is_network_alive_in_uboot()
        log_debug("The ARP table after ping the server")
        self.display_arp_table()

        cmd = "tftpboot 0x44000000 images/{}-bootloader.bin".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(60, "Bytes transferred", "sf probe")

        cmd = "sf erase 0x490000 0xa0000"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "sf write 0x44000000 0x490000 0xa0000"
        self.pexp.expect_ubcmd(60, "Erased: OK", cmd)
        cmd = "sf erase 0x480000 0x10000"
        self.pexp.expect_ubcmd(60, "Written: OK", cmd)
        self.pexp.expect_ubcmd(60, "Erased: OK", "")

        msg(15, "Flash EEPROM/TZ/DEVCFG partitions")
        cmd = "tftpboot 0x44000000 images/{}-eeprom.bin".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "sf erase 0x610000 0x10000"
        self.pexp.expect_ubcmd(60, "Bytes transferred", cmd)
        cmd = "sf write 0x44000000 0x610000 0x10000"
        self.pexp.expect_ubcmd(60, "Erased: OK", cmd)
        self.pexp.expect_ubcmd(60, "Written: OK", "")

        cmd = "tftpboot 0x44000000 images/{}-tz.mbn".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "sf erase 0xa0000 0x00300000"
        self.pexp.expect_ubcmd(60, "Bytes transferred", cmd)
        cmd = "sf write 0x44000000 0xa0000  0x00180000"
        self.pexp.expect_ubcmd(60, "Erased: OK", cmd)
        cmd = "sf write 0x44000000 0x220000 0x00180000"
        self.pexp.expect_ubcmd(60, "Written: OK", cmd)
        self.pexp.expect_ubcmd(60, "Written: OK", "")

        cmd = "tftpboot 0x44000000 images/{}-devcfg.mbn".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "sf erase 0x3A0000 0x00020000"
        self.pexp.expect_ubcmd(60, "Bytes transferred", cmd)
        cmd = "sf write 0x44000000 0x3A0000 0x00010000"
        self.pexp.expect_ubcmd(60, "Erased: OK", cmd)
        cmd = "sf write 0x44000000 0x3B0000 0x00010000"
        self.pexp.expect_ubcmd(60, "Written: OK", cmd)
        self.pexp.expect_ubcmd(60, "Written: OK", "")

        msg(20, "Loading firmware")
        cmd = "tftpboot 0x44000000 images/{}-fw.img".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "nand erase 0 0x10000000"
        self.pexp.expect_ubcmd(120, "Bytes transferred", cmd)
        cmd = "nand write 0x44000000 0 $filesize"
        self.pexp.expect_ubcmd(60, "Erasing at 0xffe0000", cmd)
        self.pexp.expect_ubcmd(60, "written: OK", "reset")

    def check_info(self):
        log_debug("Booting up to linux console ...")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")

        '''
            Currently, the FW image is not a formal image, so it doesn't require
            the username and password
        '''
        # self.login(timeout=180, log_level_emerg=True, press_enter=True)
        self.pexp.expect_lnxcmd(180, "Please press Enter to activate this console", "")
        msg(70, "Firmware booting up successfully ...")

        cmd = "grep flashSize /proc/ubnthal/system.info"
        self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, "flashSize")
        log_debug("Checking if there's wifi calibration data exist.")

        # /tmp/IPQ8074/caldata.bin
        cal_file = os.path.join(self.wifi_cal_data_dir, "caldata.bin")
        cmd = "md5sum {}".format(cal_file)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        index = self.pexp.expect_get_index(10, [self.md5sum_no_wifi_cal])
        if index == 0:
            error_critical(msg="WiFi calibration data empty!!, FAIL!!")
        else:
            log_debug(msg="WiFi calibration data is not empty, PASS")

        '''
            To unlock the SSH
        '''
        cmd = "echo ssh | prst_tool -w misc && prst_tool -e pairing && cfg.sh erase && echo cfg_done > /proc/afi_leds/mode && reboot -fd1"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, "pairing erased")
        self.pexp.expect_lnxcmd(180, "Please press Enter to activate this console", "")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info", "flashSize", retry=12)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ubus call firmware info", "version")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/board", "bomrev")

    def run(self):
        """
            Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if self.WRITE_REQUIRED_IMAGES is True:
            self.flash_images()
            # self.login(timeout=180, log_level_emerg=True, press_enter=True)
            self.pexp.expect_lnxcmd(180, "Please press Enter to activate this console", "")
            time.sleep(30)
            self.set_lnx_net(self.comuteth[self.board_id])
            self.is_network_alive_in_linux(arp_logging_en=True, del_dutip_en=True)
            msg(25, "Configuring the EEPROM partition ...")
            cmd = "[ ! -f ~/.ssh/known_hosts ] || rm ~/.ssh/known_hosts"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)

        if self.PROVISION_ENABLE is True:
            if self.board_id == "da11" or self.board_id == "da12":
                ssh_dut = SSHClient(host=self.dutip, username=constant.DEFAULT_DUT_USERNAME,
                        password=constant.DEFAULT_DUT_PASSWORD)
                src_path = os.path.join(self.fcd_toolsdir, "tftp")
                ssh_dut.put_file(src_path, dst_path, "/usr/bin/tftp")

            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False, rsa_en=False)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()

        msg(100, "Formal firmware completed...")
        self.close_fcd()

def main():
    afi_ipq807x_factory = AFIIPQ807XFactory()
    afi_ipq807x_factory.run()

if __name__ == "__main__":
    main()
