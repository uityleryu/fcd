#!/usr/bin/python3

import re
import sys
import os
import time

from soc_lib.bcm5334x_lib import BCM5334xLIB
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True

flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

'''
    eb10: US-8-150W
    eb18: US-8-60W
    eb20: US-XG
    eb21: US-16-150W
    eb30: US-24
    eb31: US-24-250W
    eb60: US-48
    eb62: US-48-500W
'''


class USBCM5334xFactoryGeneral(BCM5334xLIB):
    def __init__(self):
        super(USBCM5334xFactoryGeneral, self).__init__()
        self.ver_extract()

    def update_firmware_in_uboot(self):
        """
        use urescue to update firmwre,
        after flash firmware, DUT will be resetting
        """
        cmd = "setenv do_urescue TRUE; urescue -u"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        extext_list = [
            "TFTPServer started. Wating for tftp connection...",
            "Listening for TFTP transfer"
        ]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to start urescue")
        elif index == 0 or index == 1:
            log_debug(msg="TFTP is waiting for file")

        fw_path = os.path.join(self.fwdir, self.board_id+".bin")
        cmd = "atftp --option \"mode octet\" -p -l {} {}".format(fw_path, self.dutip)
        log_debug(msg="host cmd:" + cmd)
        self.fcd.common.xcmd(cmd)

        cmd = "go $ubntaddr uwrite -f"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.pexp.expect_only(60, "Firmware Version:")
        log_debug("Firmware loaded")

        self.pexp.expect_only(60, "Image Signature Verfied, Success.")
        log_debug("Download image verified.")

        ker0_msg = "Copying to 'kernel0' partition. Please wait... :  done"
        ker1_msg = "Copying to 'kernel1' partition. Please wait... :  done"

        rt = self.pexp.expect_only(300, ker0_msg)
        if rt is False:
            error_critical(msg="Failed to flash kernel0.")
        else:
            log_debug("Completed to flash kernel0")

        rt = self.pexp.expect_only(300, ker1_msg)
        if rt is False:
            error_critical(msg="Failed to flash kernel1.")
        else:
            log_debug("Completed to flash kernel1")

        self.pexp.expect_only(150, "Starting kernel")

    def turn_on_console(self):
        cmd = "setenv bootargs '{0}'".format(bootargs[self.board_id])
        log_debug("cmd: " + cmd)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootcmd")
        self.pexp.expect_only(150, "Starting kernel")

    def set_data_in_uboot(self):
        cmd = "go $ubntaddr usetbid {0}".format(self.board_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = "go $ubntaddr usetbrev {0}".format(self.bom_rev)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = "go $ubntaddr usetmac {0}".format(self.mac)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = "go $ubntaddr usetmac"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt ,10)
        match = re.search(r"MAC0: (.{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2})", output)
        mac_str = ""
        if match:
            mac_str = match.group(1)
        else:
            error_critical("Found no mac info by regular expression. Please checkout output")

        cmd = "setenv ethaddr {0}; saveenv".format(mac_str)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "done")
        log_debug("MAC setting succeded")

    def gen_and_upload_ssh_key(self):
        self.gen_rsa_key()
        self.gen_dss_key()

        """
            The command: go $ubntaddr usetsshkey $fileaddr $filesize"
            will differentiate the key (RSA or DSS) we send to it.
        """
        # Upload the RSA key
        cmd = "tftpboot 0x01000000 {0}".format(self.rsakey)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = "go $ubntaddr usetsshkey $fileaddr $filesize"
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")

        # Upload the DSS key
        cmd = "tftpboot 0x01000000 {0}".format(self.dsskey)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = "go $ubntaddr usetsshkey $fileaddr $filesize"
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")

        log_debug(msg="ssh keys uploaded successfully")

    def check_info_in_uboot(self):
        """
           check board id/ bom revision/ mac address
        """
        cmd = "go $ubntaddr usetbid"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(r"Board ID: (.{4})", output)
        board_id = None
        if match:
            board_id = match.group(1)
        else:
            error_critical(msg="Found no Board ID info by regular expression. Please checkout output")
        if board_id != self.board_id:
            error_critical(msg="Board ID doesn't match!")

        cmd = "go $ubntaddr usetbrev"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(r"BOM Rev: (\d+-\d+)", output)
        bom_rev = None
        if match:
            bom_rev = match.group(1)
        else:
            error_critical(msg="Found no BOM Revision info by regular expression. Please checkout output")
        if bom_rev != self.bom_rev:
            error_critical(msg="BOM Revision  doesn't match!")

        cmd = "go $ubntaddr usetmac"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(
                        r"MAC0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*MAC1: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2})",
                        output,
                        re.S)
        mac_0 = None
        mac_1 = None
        mac_base = self.mac.replace(":", "")
        mac_tmp = (int(mac_base,16)|0x020000000000)
        mac_admin = format(mac_tmp, 'x').zfill(12)

        if match:
            mac_0 = match.group(1).replace(":", "")
            mac_1 = match.group(2).replace(":", "")
        else:
            error_critical(msg="Found no mac info by regular expression. Please checkout output")

        if mac_0 != mac_base or mac_1 != mac_admin:
            error_critical(msg="MAC address doesn't match!")

    def data_provision(self):
        msg(10, "Clearing the U-Boot Environment")
        self.ub_config_clean()

        msg(15, "Board ID/Revision set")
        self.set_data_in_uboot()

        # reset the U-boot
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        self.stop_uboot()
        self.ub_uapp_init()

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        msg(20, "Environment Variables set")

        self.set_ub_net()
        self.is_network_alive_in_uboot()
        self.gen_and_upload_ssh_key()
        msg(25, "SSH keys uploaded")

        self.check_info_in_uboot()
        msg(30, "Board ID/MAC address checked")

    def prepare_server_need_files(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cd /tmp")
        sstr = [
            self.helperexe,
            "-q",
            "-c product_class=bcmswitch",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin,
            ">",
            self.eetxt
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr)
        time.sleep(2)

        cmd = "tar zcf {0} {1} {2}".format(self.eetgz, self.eebin, self.eetxt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        log_debug("Sending EEPROM file to host")

        self.zmodem_recv_from_dut(file=self.eetgz, dest_path=self.tftpdir, retry=10)

        cmd = "tar zxf {0}".format(self.eetgz_path)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz + " files successfully")

    def check_board_signed(self):
        cmd = r"grep flashSize /proc/ubnthal/system.info"
        self.pexp.expect_action(10, "", "")
        output = self.pexp.expect_get_output(cmd, self.linux_prompt, 10)
        match = re.search(r'flashSize=', output)
        if not match:
            error_critical(msg="Device Registration check failed!")

        cmd = r"grep qrid /proc/ubnthal/system.info"
        output = self.pexp.expect_get_output(cmd, self.linux_prompt, 10)
        match = re.search(r'qrid=(.*)', output)
        if match:
            if match.group(1).strip() != self.qrcode:
                error_critical(msg="QR code doesn't match!")
        else:
            error_critical(msg="Unable to get qrid!, please checkout output by grep")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(1, "Waiting - PULG in the device...")
        self.stop_uboot()
        self.ub_chk_mdk_support()
        self.ub_uapp_init()
        if PROVISION_ENABLE is True:
            self.data_provision()
            self.pexp.expect_action(10, "", "re")

        if DOHELPER_ENABLE is True:
            self.login(timeout=210, press_enter=True)
            self.erase_eefiles()
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(zmodem=True)
            msg(50, "Finish doing signed file and EEPROM checking ...")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")

        if FWUPDATE_ENABLE is True:
            msg(60, "Updating firmware ...")
            self.stop_uboot()
            self.ub_uapp_init()
            self.set_ub_net()
            self.is_network_alive_in_uboot()
            self.update_firmware_in_uboot()

        if DATAVERIFY_ENABLE is True:
            msg(70, "Checking registration ...")
            self.login(timeout=210, press_enter=True)
            self.check_board_signed()
            msg(no=80, out="Device Registration check OK...")

        msg(no=100, out="Formal firmware completed with MAC0: " + self.mac)
        self.close_fcd()


def main():
    us_factory_general = USBCM5334xFactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
