#!/usr/bin/python3

import re
import sys
import os
import time

from soc_lib.bcm5334x_lib import BCM5334xLIB
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical

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


class USBCM5334x_MFG(BCM5334xLIB):
    def __init__(self):
        super(USBCM5334x_MFG, self).__init__()

    # Using urescue to update MFG
    def update_firmware_in_uboot(self):
        """
        use urescue to update firmwre,
        after flash firmware, DU will be resetting
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
        else:
            log_debug(msg="TFTP is waiting for file")

        fw_path = os.path.join(self.fwdir, self.board_id+"-mfg.bin")
        cmd = "atftp --option \"mode octet\" -p -l {} {}".format(fw_path, self.dutip)
        log_debug("host cmd:" + cmd)
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

    def update_firmware_in_kernel(self):
        src_path = os.path.join(self.image, self.board_id+"-mfg.bin")
        dst_path = os.path.join(self.dut_tmpdir, "fwupdate.bin")
        ret = self.tftp_get(remote=src_path, local=dst_path, timeout=210, post_en=True)
        if ret is False:
            error_critical("Transfer {} failed".format(src_path))

        cmd = "md5sum {}".format(dst_path)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        cmd = "syswrapper.sh upgrade2"
        self.pexp.expect_lnxcmd(120, self.linux_prompt, cmd, "Restarting system.")

    def set_data_in_uboot(self):
        cmd = "go $ubntaddr usetbid {0}".format(self.board_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = "setenv ethaddr {0}; saveenv".format(self.fakemac)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "done")

        self.pexp.expect_action(10, "", "")
        log_debug("MAC setting succeded")

        cmd = "setenv serverip {0}".format(self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "setenv ipaddr {0}".format(self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(1, "Waiting - PULG in the device...")
        self.stop_uboot()
        self.ub_chk_mdk_support()
        if self.isMDK is False:
            log_debug("Updating MFG from the FW image ...")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
            self.login(timeout=210, press_enter=True)
            self.is_network_alive_in_linux()
            msg(30, "Network is good. Starting update firmware")

            # Update kernel_partition_0
            self.update_firmware_in_kernel()
            msg(40, "MFG Firmware flashed by syswrapper tool.")

            log_debug("Rebooting system after upgrade")
            self.stop_uboot()
            self.ub_uapp_init()
            self.ub_config_clean()
            self.set_data_in_uboot()  # set boardid in advanced for network enabling
            self.is_network_alive_in_uboot()

            # Update kernel_partition_1
            log_debug("Starting upgrade firmware by urescue")
            self.update_firmware_in_uboot()
            msg(80, "Firmware update complete.")
        else:
            log_debug("Updating MFG by urescue directly ...")
            self.ub_uapp_init()
            self.ub_config_clean()
            self.set_data_in_uboot()
            self.is_network_alive_in_uboot()
            msg(50, "Network is good. Starting update firmware")

            log_debug("Starting upgrade firmware by urescue")
            self.update_firmware_in_uboot()
            msg(80, "Firmware update complete.")

        self.login(timeout=210, press_enter=True)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
        self.stop_uboot()
        self.ub_clean_shmoo()
        msg(100, "Back to T1 completed.")
        self.close_fcd()


def main():
    us_mfg = USBCM5334x_MFG()
    us_mfg.run()

if __name__ == "__main__":
    main()
