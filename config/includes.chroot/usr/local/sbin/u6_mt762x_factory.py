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
    a612:    U6-Lite
    a620:    U6-LRv2
'''


class U6MT762xFactory(ScriptBase):
    def __init__(self):
        super(U6MT762xFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        # self.devregpart = "/dev/mtdblock3"
        # self.helperexe = "helper_UAP6_MT7621_release"
        # self.bootloader_prompt = "MT7621 #"
        self.fcdimg = self.board_id + "-fcd.bin"
        self.uboot_img = os.path.join(self.image, self.board_id+'-uboot.bin')
        self.uboot_size = os.stat(os.path.join(self.tftpdir, self.uboot_img)).st_size

        self.helper_path = "common"

        # Devreg location
        self.devregpart_select = {
            "a612": "/dev/mtdblock3",
            "a620": "/dev/mtdblock5"
        }
        self.devregpart = self.devregpart_select[self.board_id]

        # helper by Project(platoform)
        self.helperexe_select = {
            "a612": "helper_UAP6_MT7621_release",
            "a620": "helper_UAP6_MT7622_release"
        }
        self.helperexe = self.helperexe_select[self.board_id]

        # bootloader prompt
        self.bootloader_prompt_select = {
            "a612": "MT7621 #",     # uboot of BSP is "=>"
            "a620": "MT7622>"
        }
        self.bootloader_prompt = self.bootloader_prompt_select[self.board_id]

        # number of mac
        self.macnum = {
            'a612': "1",
            'a620': "1",
        }

        # number of WiFi
        self.wifinum = {
            'a612': "2",
            'a620': "2"
        }

        # number of Bluetooth
        self.btnum = {
            'a612': "1",
            'a620': "1",
        }

        # vlan port mapping
        self.vlanport_idx = {
            'a612': "'6 0'",
            'a620': "'6 0'",
        }

        # flash size map
        self.flash_size = {
            'a612': "33554432",
            'a620': "67108864",
        }

        self.recovery_addr = {
            "a612": "0x84000000",
            "a620": "0x5007ff28",
        }

        # firmware image
        self.fwimg = {
            'a612': self.board_id + ".bin",
            'a620': self.board_id + ".bin",
        }

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        self.UPDATE_UBOOT_ENABLE    = True
        self.BOOT_RECOVERY_IMAGE    = True
        self.PROVISION_ENABLE       = True
        self.DOHELPER_ENABLE        = True
        self.REGISTER_ENABLE        = True
        self.FWUPDATE_ENABLE        = True
        self.DATAVERIFY_ENABLE      = True


    def boot_recovery_image(self, Img):
        cmd = "tftpboot {} images/{}".format(self.recovery_addr[self.board_id], Img)

        if self.board_id == "a612":
            pass
        elif self.board_id == "a620":
            self.pexp.expect_action(15, self.bootloader_prompt, "nor init")

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred = "+str(os.stat(self.fwdir+"/"+Img).st_size))
        self.pexp.expect_action(10, self.bootloader_prompt, "bootm")
        self.login(timeout=240,press_enter=True)

    def init_recovery_image(self):
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dmesg -n 1", valid_chk=True)

        if self.board_id == "a612":
            cmd = "swconfig dev switch0 set enable_vlan 1"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "swconfig dev switch0 vlan 1 set vid 1"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "swconfig dev switch0 vlan 1 set ports {}".format(self.vlanport_idx[self.board_id])
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "swconfig dev switch0 set apply"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "[ $(ifconfig | grep -c eth0) -gt 0 ] || ifconfig eth0 up"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig br0", post_exp="inet addr:", retry=6, valid_chk=True)
            cmd = "ifconfig eth0 {}".format(self.dutip)
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)

        elif self.board_id == "a620":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig", "br0", retry=10)
            # To enable ethernet in 1G unit

        self.is_network_alive_in_linux(retry=10)

    def update_uboot(self):

        if self.board_id == "a612":
            log_debug("uboot_img: " + self.uboot_img)
            cmd = "tftpboot {} {}".format(self.recovery_addr[self.board_id], self.uboot_img)
            exp = "Bytes transferred = {}".format(self.uboot_size)
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, exp)
            cmd = "sf probe; sf erase 0x0 0x60000; sf write {} 0x0 ${{filesize}}".format(self.recovery_addr[self.board_id])

        elif self.board_id == "a620":
            self.pexp.expect_action(10, self.bootloader_prompt, "nor init")
            time.sleep(2)
            fake_EEPROM_img = os.path.join(self.image, self.board_id+"-fake_EEPROM.bin")
            log_debug("fake_EEPROM_img: " + fake_EEPROM_img)
            self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 0x4007ff28 {}".format(fake_EEPROM_img))
            time.sleep(1)
            self.pexp.expect_action(10, self.bootloader_prompt, "snor erase 0x110000 0x10000; snor write 0x4007ff28 0x110000 0x10000")
            time.sleep(2)
            self.pexp.expect_action(10, self.bootloader_prompt, "")
            time.sleep(2)

            log_debug("uboot_img: " + self.uboot_img)
            cmd = "tftpboot {}".format(self.uboot_img)
            exp = "Bytes transferred = {}".format(self.uboot_size)
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, exp)
            cmd = "snor erase 0x60000 0x60000; snor write ${loadaddr} 0x60000 ${filesize}"

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

    def enter_uboot(self):

        if self.board_id == "a612":
            rt = self.pexp.expect_action(30, "Hit any key to stop autoboot|Autobooting in 2 seconds, press", "\x1b\x1b")
            self.bootloader_prompt = "MT7621 #"  # here will need this because prompt could be changed with "=>" befoe on 1st uboot
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

        elif self.board_id == "a620":
            rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
            retry = 2
            while retry > 0:
                if rt != 0:
                    error_critical("Failed to detect device")
                try:
                    self.pexp.expect_action(10, self.bootloader_prompt, "")
                    break
                except Exception as e:
                    self.bootloader_prompt = "#"
                    log_debug("Change prompt to {}".format(self.bootloader_prompt))
                    retry -= 1

            self.pexp.expect_action(10, self.bootloader_prompt, "setenv ethaddr " + self.mac)
            self.pexp.expect_action(10, self.bootloader_prompt, "setenv ethcard AQR112C")

        self.set_ub_net(premac=self.premac)
        self.is_network_alive_in_uboot()

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

        cmd = "atftp -p -l {0}/{1} {2}".format(self.fwdir, self.fwimg[self.board_id], self.dutip)
        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
        self.pexp.expect_only(60, "Updating u-boot partition \(and skip identical blocks\)")
        self.pexp.expect_only(60, "done")
        self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(240, "done")

    def set_stp_env(self):
        if self.board_id == "a612":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv is_ble_stp true;saveenv", "OK")
        elif self.board_id == "a620":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv is_ble_stp true; saveenv", "done")

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def check_info(self):
        #Check BT FW is included or not
        bom = self.bom_rev.split("-")[0]
        rev_of_bomrev = int(self.bom_rev.split("-")[1])

        # U6-Lite, old bom is 113-00773-15 , if rev lower 15 , the uboot could be not "BT Power On result" message
        # U6-Lite, new bom is 113-01076
        if bom == "00773" and rev_of_bomrev < 15:
            pass
        else:   #for new bom U6-lIte and U6-LR
            self.pexp.expect_only(30, "\[BT Power On Result\] Success")

        self.login(timeout=240,press_enter=True)
        cmd = "dmesg -n 1"
        if self.board_id == "a612":
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        elif self.board_id == "a620":
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)

        cmd = "cat /proc/ubnthal/system.info"
        exp = [
            "flashSize={0}".format(self.flash_size[self.board_id]),
            "systemid={0}".format(self.board_id),
            "serialno={0}".format(self.mac.lower()),
            "qrid={0}".format(self.qrcode)
        ]
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, post_exp=exp)
        cmd = "cat /usr/lib/build.properties"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        cmd = "cat /usr/lib/version"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)

        number_time = 0 # one loop is 5sec for 1 time
        while number_time < 14:  #14 * 5 = max 70 sec wait for dmesg key word for BT FW check, it will be around 43 sec 
            time.sleep(5)
            cmd = 'dmesg | grep -i "btmtk_load_flash_programing"'
            output = self.pexp.expect_get_output(action=cmd, prompt= "" ,timeout=3)
            log_debug(output)
            if output.find("btmtk_load_flash_programing: btmtk_load_flash_chech_version pass, no need update") >= 0:
                log_debug("BT fw will 'not' need to be updated")
                break

            cmd = 'dmesg | grep -i "Get event result:"'
            output = self.pexp.expect_get_output(action=cmd, prompt= "" ,timeout=3)
            log_debug(output)
            if output.find("Get event result: NG") >= 0:
                log_debug("BT fw will need to be updated, it will reboot system automatically")
                if bom == "00773" and rev_of_bomrev < 15:
                    pass
                else:   #for new bom U6-lIte and U6-LR
                    self.pexp.expect_only(120, "\[BT Power On Result\] Success")
                self.login(timeout=240,press_enter=True)
                break

            number_time = number_time + 1

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "fw_setenv is_ble_stp true")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "fw_printenv", "is_ble_stp=true")
        self.pexp.expect_action(10, self.linux_prompt, "reboot")
        if bom == "00773" and rev_of_bomrev < 15:
            pass
        else:   #for new bom U6-lIte and U6-LR
            self.pexp.expect_only(120, "\[BT Power On Result\] Success")

        if self.board_id == "a612":
            self.login(timeout=240,press_enter=True)
        elif self.board_id == "a620":
            self.pexp.expect_action(30, "Hit any key to stop autoboot", "")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE is True:
            self.enter_uboot()
            self.update_uboot()
            msg(10, "Update uboot successfully ...")

        if self.BOOT_RECOVERY_IMAGE is True:
            self.enter_uboot()
            self.boot_recovery_image(self.fcdimg)
            msg(15, "Boot into recovery image for registration ...")
            self.init_recovery_image()

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        # retry for unstable helper_UAP6
        retry = 3
        while retry >= 0:
            if self.DOHELPER_ENABLE is True:
                self.erase_eefiles()
                msg(30, "Do helper to get the output file to devreg server ...")
                self.prepare_server_need_files()

                eetxt_dut_path = os.path.join(self.tftpdir, self.eetxt)
                cmd = "cat {0} | grep uid".format(eetxt_dut_path)
                log_debug("host cmd: " + cmd)
                [uid_long, rtc] = self.fcd.common.xcmd(cmd)
                uid = re.search(r'value=(.*)', uid_long, re.S).group(1).strip()
                log_debug("Flash UID="+str(uid))
                if uid is not '':
                    break
                else:
                    if retry == 0:
                        error_critical("Failed to gen files by helper")
                    log_debug("Retrying to run helper, remaining {}.".format(retry))
                    retry -= 1
                    time.sleep(2)

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
            msg(80, "Save STP_ENV...")
            self.enter_uboot()
            self.set_stp_env()
            msg(85, "Save STP_ENV done...")
            self.check_info()
            msg(90, "Succeeding in checking the devreg information ...")

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    u6mt762xfactory = U6MT762xFactory()
    u6mt762xfactory.run()

if __name__ == "__main__":
    main()
