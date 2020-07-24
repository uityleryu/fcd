#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.common import Common
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a620: U6-PRO
'''


class U6MT7622Factory(ScriptBase):
    def __init__(self):
        super(U6MT7622Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.devregpart = "/dev/mtdblock5"
        self.helperexe = "helper_UAP6_MT7622_release"
        self.bootloader_prompt = "MT7622"
        self.fcdimg = self.board_id + "-fcd.bin"
        self.helper_path = "common"

        # number of mac
        self.macnum = {
            'a620': "1",
        }

        # number of WiFi
        self.wifinum = {
            'a620': "2",
        }

        # number of Bluetooth
        self.btnum = {
            'a620': "1",
        }

        # vlan port mapping
        self.vlanport_idx = {
            'a620': "'6 0'",
        }

        # flash size map
        self.flash_size = {
            'a620': "67108864",
        }

        # firmware image
        self.fwimg = {
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
        recoveryImg = self.board_id + '-fcd.bin'
        cmd = "tftpboot ${loadaddr} images/" + recoveryImg
        self.pexp.expect_action(15, self.bootloader_prompt, "nor init")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred = "+str(os.stat(self.fwdir+"/"+recoveryImg).st_size))
        self.pexp.expect_action(10, self.bootloader_prompt, "bootm")
        self.login(timeout=240,press_enter=True)

    def init_recovery_image(self):
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dmesg -n 1", valid_chk=True)
        self.is_network_alive_in_linux()

    def update_uboot(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "nor init")
        time.sleep(2)
        self.pexp.expect_action(10, self.bootloader_prompt, "")
        time.sleep(2)

        uboot_img = os.path.join(self.image, self.board_id+'-uboot.bin')
        uboot_size = os.stat(os.path.join(self.tftpdir, uboot_img)).st_size
        log_debug("uboot_img: " + uboot_img)
        cmd = "tftpboot {0}".format(uboot_img)
        exp = "Bytes transferred = {0}".format(uboot_size)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, exp)
        cmd = "snor erase 0x60000 0x60000; snor write ${loadaddr} 0x60000 ${filesize}"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")


    def enter_uboot(self):
        rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")

        retry = 2
        while retry > 0:
            if rt != 0:
                error_critical("Failed to detect device")
            try:
                self.pexp.expect_action(10, self.bootloader_prompt, "")
                break
            except Exception as e:
                self.bootloader_prompt = "=>"
                log_debug("Change prompt to {}".format(self.bootloader_prompt))
                retry -= 1

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
        self.pexp.expect_only(120, "done")

    def check_info(self):
        #Check BT FW is included or not
        self.pexp.expect_only(30, "\[BT Power On Result\] Success")
        self.pexp.expect_only(30, "\[HIC LE  SET ADVERTISING DATA Result\] Success")

        self.login(timeout=240,press_enter=True)
        cmd = "dmesg -n 1"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        cmd = "cat /proc/ubnthal/system.info"
        exp = [
            "flashSize={0}".format(self.flash_size[self.board_id]),
            "systemid={0}".format(self.board_id),
            "serialno={0}".format(self.mac.lower()),
            "qrid={0}".format(self.qrcode),
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
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    u6mt7622factory = U6MT7622Factory()
    u6mt7622factory.run()

if __name__ == "__main__":
    main()
