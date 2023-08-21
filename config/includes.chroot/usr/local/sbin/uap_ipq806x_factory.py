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

'''
    e530: UAP-AC-HD
    e540: UAP-AC-SHD
    e560: UAP-AC-XG
    e570: UAP-XG-MESH
    e580: UWB-XG
    e585: UWB-XG-BK
'''


class UAPWIFIBASESTATIONFactory(ScriptBase):
    def __init__(self):
        super(UAPWIFIBASESTATIONFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.devregpart = "/dev/mtdblock10"
        self.helperexe = "helper_IPQ806x_release"
        self.bootloader_prompt = "\(IPQ\) #"
        self.helper_path = "uap"

        # MAC HID
        self.machid = {
            'e530': "13ec",
            'e540': "13fb",
            'e560': "13fd",
            'e570': "1402",
            'e580': "1403",
            'e585': "1403"
        }

        # number of mac
        self.macnum = {
            'e530': "2",
            'e540': "2",
            'e560': "2",
            'e570': "2",
            'e580': "2",
            'e585': "2"
        }

        # number of WiFi
        self.wifinum = {
            'e530': "2",
            'e540': "2",
            'e560': "4",
            'e570': "4",
            'e580': "4",
            'e585': "4"
        }

        # number of Bluetooth
        self.btnum = {
            'e530': "0",
            'e540': "1",
            'e560': "1",
            'e570': "1",
            'e580': "1",
            'e585': "1"
        }

        self.boot_arg = {
            'e530': '$fileaddr',
            'e540': '$fileaddr',
            'e560': '$fileaddr#config@5117_2',
            'e570': '$fileaddr#config@5117_2',
            'e580': '$fileaddr#config@5123_2',
            'e585': '$fileaddr#config@5123_2'
        }

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        self.UPDATE_FACTORY_EN = True
        self.BOOT_RECOVERY_IMAGE = True
        self.SET_BT_BDADDR_EN = True
        self.UPDATE_UBOOT_EN = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.FWUPDATE_ENABLE = True
        self.DATAVERIFY_ENABLE = True

    def enter_uboot(self):
        rt = self.pexp.expect_action(120, "Hit any key to stop autoboot|Autobooting in 2 seconds, press", "\x1b\x1b")

        retry = 2
        while retry > 0:
            if rt != 0:
                error_critical("Failed to detect device")

            try:
                self.pexp.expect_action(10, self.bootloader_prompt, "\x1b\x1b")
                break
            except Exception as e:
                self.bootloader_prompt = "=>"
                log_debug("Change prompt to {}".format(self.bootloader_prompt))
                retry -= 1

        mac_comma = self.mac_format_str2comma(self.mac)
        cmd = "set eth1addr {}".format(mac_comma)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.set_ub_net()
        self.is_network_alive_in_uboot()

    def update_factory(self):
        cmd = "sf probe; tftpboot 0x42000000 images/{}-factory.bin".format(self.board_id)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, "Bytes transferred")

        cmd = "set machid {}".format(self.machid[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "imgaddr=0x42000000; source $imgaddr:script"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd, "Flashing debug:")

        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

    def update_uboot(self):
        cmd = "sf probe; tftpboot 0x44000000 images/{}-uboot.bin".format(self.board_id)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, "Bytes transferred")

        cmd = "sf probe; sf erase 0x000F0000 +0x000C0000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "sf write 0x44000000 0x000F0000 $filesize"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

    def boot_fcd_kernel(self):
        cmd = "tftpboot 0x44000000 images/{}-fcd-kernel.bin".format(self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd, "Bytes transferred")

        cmd = "setenv bootargs 'console=ttyHSL1,115200n8 quiet'"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "pcideinit")

        cmd = "bootm 0x44000000#config@${dtb_cfg_name}"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        self.login(timeout=240, press_enter=True)

    def boot_fcd_new_kernel(self):
        cmd = "tftpboot 0x44000000 images/{}-fcd-new-kernel.bin".format(self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd, "Bytes transferred")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "pcideinit")

        cmd = "bootm {}".format(self.boot_arg[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        self.login(timeout=240, press_enter=True)

    def data_provision_64k(self, netmeta, post_en=True, rsa_en=True):
        cmdset = [
            "/sbin/ipq806x-ee -F",
            "-r 113-{}".format(self.bom_rev),
            "-s 0x{}".format(self.board_id),
            "-m {}".format(self.mac),
            "-c 0x{}001f".format(self.region),
            "-e {}".format(netmeta['ethnum'][self.board_id]),
            "-w {}".format(netmeta['wifinum'][self.board_id])
        ]
        if rsa_en is True:
            cmdset.append("-k")

        cmd = ' '.join(cmdset)
        log_debug("flash editor cmd: " + cmd)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)
        time.sleep(0.5)

        cmd = "/sbin/ipq806x-ee -I -v 2>&1"
        rtmsg = self.pexp.expect_get_output(cmd, self.linux_prompt, timeout=20)
        time.sleep(1)
        expmsg_set = [
            "DEBUG: SBD system ID: 0777:{}".format(self.board_id),
            "DEBUG: SBD HW revision: 113-{}".format(self.bom_rev),
            "DEBUG: SBD HW Address Base: {}".format(self.mac),
            "DEBUG: SBD Ethernet MAC count: {}".format(netmeta['ethnum'][self.board_id]),
            "DEBUG: SBD WiFi RADIO count: {}".format(netmeta['wifinum'][self.board_id])
        ]
        for expmsg in expmsg_set:
            if expmsg not in rtmsg:
                error_critical("The output information is wrong")

            time.sleep(0.5)

        cmd = "cmp -s /tmp/dropbear_key.dss /tmp/dropbear_key_dump.dss 2>&1; echo $?"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)

        cmd = "cmp -s /tmp/dropbear_key.rsa /tmp/dropbear_key_dump.rsa 2>&1 ; echo $?"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)

    def config_ethernet_switch(self):
        cmdset = [
            "echo \"0x4054 0x3FFFFFFF\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6418 0x00020001\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6428 0x00010001\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6438 0x00010001\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6448 0x00010001\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x65a8 0x00020001\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x65b8 0x00010001\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0xc000 0x4800001c\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0xc004 0xfff\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0xc008 0x4800010\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0xc010 0x44000002\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0xc014 0xfff\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0xc018 0x4800020\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6414 0\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6424 0\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6434 0\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x6444 0\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x65a4 0\" > /sys/kernel/debug/qca-85xx-sw/write-reg",
            "echo \"0x65b4 0\" > /sys/kernel/debug/qca-85xx-sw/write-reg"
        ]
        for cmd in cmdset:
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)

    def fwupdate(self):
        log_debug("Change to product firware...")
        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(30, self.linux_prompt, "reboot -f")
        self.enter_uboot()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubnt_clearcfg TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubnt_clearenv TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv do_urescue TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
        self.pexp.expect_action(30, "Listening for TFTP transfer on", "")

        # Example: atftp --option "mode octet" -p -l /tftpboot/images/e580.bin 192.168.1.31
        cmd = "atftp --option \"mode octet\" -p -l {0}/{1}.bin {2}".format(self.fwdir, self.board_id, self.dutip)
        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
        self.pexp.expect_only(60, "Updating SBL1 partition")
        self.pexp.expect_only(60, "Updating SBL2 partition")
        self.pexp.expect_only(60, "Updating SBL3 partition")
        self.pexp.expect_only(60, "TZ partition")
        self.pexp.expect_only(60, "RPM partition")
        self.pexp.expect_only(120, "kernel0 partition")
        self.pexp.expect_only(300, "bootselect partition")

        self.login(timeout=240, press_enter=True)
        cmd = "dmesg -n 1"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)

    def check_pci(self):
        cmd = "lspci -m"
        # cmd_reply = self.pexp.expect_get_output(cmd, self.linux_prompt, timeout=20)
        if self.board_id == "e530":
            postexp_set = [
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e535"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e5a2"'
            ]
        elif self.board_id == "e540":
            postexp_set = [
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e535"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0050" "0000" "0000"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e5a2"'
            ]
        elif self.board_id == "e560":
            postexp_set = [
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e575"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:03.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:07.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '03:00.0 "Class 0280" "168c" "0046" "0777" "e5a2"',
                '04:00.0 "Class 0280" "168c" "0050" "0000" "0000"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e555"'
            ]
        elif self.board_id == "e570":
            postexp_set = [
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e575"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:03.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:07.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '03:00.0 "Class 0280" "168c" "0046" "0777" "e5a2"',
                '04:00.0 "Class 0280" "168c" "0050" "0000" "0000"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e555"'
            ]
        elif self.board_id == "e580":
            postexp_set = [
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e575"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:03.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:07.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '03:00.0 "Class 0280" "168c" "0046" "0777" "e565"',
                '04:00.0 "Class 0280" "168c" "0050" "0000" "0000"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e585"'
            ]
        elif self.board_id == "e585":
            postexp_set = [
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e575"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:03.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '02:07.0 "Class 0604" "1b21" "1182" "1b21" "118f"',
                '03:00.0 "Class 0280" "168c" "0046" "0777" "e565"',
                '04:00.0 "Class 0280" "168c" "0050" "0000" "0000"',
                '00:00.0 "Class 0604" "17cb" "0101" "0000" "0000"',
                '01:00.0 "Class 0280" "168c" "0046" "0777" "e585"'
            ]

        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, post_exp=postexp_set)

    def check_info(self):
        cmd = "cat /proc/ubnthal/system.info"
        exp = [
            "flashSize=",
            "systemid={}".format(self.board_id),
            "serialno={}".format(self.mac.lower()),
            "qrid={}".format(self.qrcode)
        ]
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, post_exp=exp)
        cmd = "cat /usr/lib/build.properties"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        cmd = "cat /usr/lib/version"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")

        msg(5, "Open serial port successfully ...")

        if self.UPDATE_FACTORY_EN is True:
            self.enter_uboot()
            self.update_factory()
            msg(10, "Update uboot successfully ...")

        if self.PROVISION_ENABLE is True:
            self.enter_uboot()
            self.boot_fcd_kernel()
            self.set_lnx_net(intf="eth0")
            self.is_network_alive_in_linux()

            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)
            cmd = "reboot"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)

        if self.UPDATE_UBOOT_EN is True:
            self.enter_uboot()
            self.update_uboot()
            self.enter_uboot()
            self.boot_fcd_new_kernel()

        if self.DOHELPER_ENABLE is True:
            self.set_lnx_net(intf="br0")
            self.is_network_alive_in_linux()
            self.config_ethernet_switch()
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            msg(60, "Updating released firmware ...")
            self.fwupdate()
            msg(70, "Updating released firmware done...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_pci()
            self.check_info()
            msg(90, "Succeeding in checking the devreg information ...")

        if self.ps_state is True:
            time.sleep(2)
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    factory = UAPWIFIBASESTATIONFactory()
    factory.run()


if __name__ == "__main__":
    main()
