#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import os
import time

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True

flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

rsa_key = "dropbear_rsa_host_key"
dss_key = "dropbear_dss_host_key"

cmd_prefix = "go $ubntaddr"

# U-boot erase start address
uberstaddr = {
    'eb23': "0x1e0000",
    'eb25': "0x1e0000",
    'eb26': "0x1e0000",
    'eb27': "0x1e0000",
    'eb36': "0x1e0000",
    'eb37': "0x1e0000",
    'eb38': "0x1e0000",
    'eb67': "0x1e0000",
    'eb68': "0x1e0000"
}

# U-boot erase size
ubersz = {
    'eb23': "0x10000",
    'eb25': "0x10000",
    'eb26': "0x10000",
    'eb27': "0x10000",
    'eb36': "0x10000",
    'eb37': "0x10000",
    'eb38': "0x10000",
    'eb67': "0x10000",
    'eb68': "0x10000"
}

#
bootargs = {
    'eb23': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb25': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb26': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb27': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb36': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb37': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb38': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb67': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb68': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M
}

helperexes = {
    'eb20': "helper_BCM5341x",
    'eb23': "helper_BCM5616x",
    'eb25': "helper_BCM5617x",
    'eb26': "helper_BCM5617x",
    'eb27': "helper_BCM5617x",
    'eb36': "helper_BCM5616x",
    'eb37': "helper_BCM5616x",
    'eb38': "helper_BCM5616x",
    'eb67': "helper_BCM5616x",
    'eb68': "helper_BCM5616x"
}


class USBCM5616_MFG(ScriptBase):
    def __init__(self):
        super(USBCM5616_MFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.bootloader_prompt = "u-boot>"
        self.helperexe = helperexes[self.board_id]
        self.devregpart = "/dev/`awk -F: '/EEPROM/{print \$1}' /proc/mtd|sed 's~mtd~mtdblock~g'`"
        self.USGH2_SERIES = None
        self.fakemac = "00:90:4c:06:a5:7"+self.row_id

    def stop_uboot(self, timeout=30):
        log_debug("Stopping U-boot")

        expect_cal_case1 = "Switching to RD_DATA_DELAY Step"
        expect_cal_case2 = "Validate Shmoo parameters stored in flash ..... failed"
        expect_normal = "Hit any key to stop autoboot"

        expect_list = [expect_cal_case1, expect_cal_case2, expect_normal]
        index = self.pexp.expect_get_index(timeout=60, exptxt=expect_list)
        if expect_list[index] != expect_normal:
            log_debug("Waiting for self calibration in u-boot")
            timeout = 120
            self.pexp.expect_only(timeout, "Hit any key to stop autoboot")

        self.pexp.expect_action(timeout, "", "")
        log_debug("Stopped u-boot")

    def is_network_alive_in_uboot(self, retry=3):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.tftp_server)
            extext_list = ["host " + self.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=30, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def check_net(self, retry=10):
        for _ in range(retry):
            is_network_alive = self.is_network_alive_in_linux()
            if is_network_alive is True:
                break
            time.sleep(5)
        if is_network_alive is not True:
            error_critical("Network is not good")

    def check_USGH2(self):
        # bootubnt is only For USGH2 series. ex:usw-xg
        output = self.pexp.expect_get_output("bootubnt init", self.bootloader_prompt, 10)
        if "Unknown command" in output:
            self.USGH2_SERIES = False
            self.pexp.expect_action(10, self.bootloader_prompt, ' '.join([cmd_prefix, "uappinit"]))
            self.pexp.expect_only(10, "UBNT application initialized")
        elif "UBNT application initialized" in output:
            self.USGH2_SERIES = True
            log_debug("DUT is USGH2 series")

    def is_MFG_firmware(self):
        log_debug("Checking if U-boot has MDK")

        output = self.pexp.expect_get_output("mdk_drv", self.bootloader_prompt, 10)
        log_debug("mdk_drv output: "+str(output))

        if "Found MDK device" in output:
            return True
        elif "Unknown command" in output:
            return False
        elif "MDK initialized failed" in output:
            error_critical("MDK initialized failed")

    def update_firmware_in_uboot(self):
        """
        use urescue to update firmwre,
        after flash firmware, DU will be resetting
        """
        if self.USGH2_SERIES is True:
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="bootubnt ubntrescue;bootubnt")
        else:
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="setenv do_urescue TRUE; urescue -u")

        extext_list = ["TFTPServer started. Wating for tftp connection...",
                       "Listening for TFTP transfer"]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to start urescue")
        elif index == 0 or index == 1:
            log_debug(msg="TFTP is waiting for file")

        fw_path = os.path.join(self.fwdir, self.board_id+"-mfg.bin")
        atftp_cmd = "atftp --option \"mode octet\" -p -l {} {}".format(fw_path, self.dutip)
        log_debug(msg="Run cmd on host:" + atftp_cmd)
        self.fcd.common.xcmd(cmd=atftp_cmd)
        if self.USGH2_SERIES is False:
            self.pexp.expect_only(timeout=60, exptxt=self.bootloader_prompt)
            self.pexp.expect_action(10, "", "\003")
            self.pexp.expect_action(10, self.bootloader_prompt,  ' '.join([cmd_prefix, "uwrite -f"]))

        self.pexp.expect_only(timeout=60, exptxt="Firmware Version:")
        log_debug("Firmware loaded")

        self.pexp.expect_only(timeout=60, exptxt="Image Signature Verfied, Success.")
        log_debug("Download image verified.")

        if self.USGH2_SERIES is False:
            ker0_msg = "Copying to 'kernel0' partition. Please wait... :  done"
            ker1_msg = "Copying to 'kernel1' partition. Please wait... :  done"
        else:
            ker0_msg = r"Updating kernel0 partition \(and skip identical blocks\).*Done"
            ker1_msg = r"Updating kernel1 partition \(and skip identical blocks\).*Done"

        index = self.pexp.expect_get_index(timeout=300, exptxt=ker0_msg)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to flash kernel0.")
        log_debug("Completed to flash kernel0")

        index = self.pexp.expect_get_index(timeout=300, exptxt=ker1_msg)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to flash kernel1.")
        log_debug("Completed to flash kernel1")

        self.pexp.expect_only(timeout=150, exptxt="Starting kernel")

    def update_firmware_in_kernel(self):
        src_path = os.path.join(self.image, self.board_id+"-mfg.bin")
        dst_path = os.path.join(self.dut_tmpdir, "fwupdate.bin")
        ret = self.tftp_get(remote=src_path, local=dst_path, timeout=60, post_en=True)
        if ret is False:
            error_critical("Transfer {} failed".format(src_path))

        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "md5sum {}".format(dst_path))
        self.pexp.expect_action(10, self.linux_prompt, "syswrapper.sh upgrade2")
        self.pexp.expect_only(120, "Restarting system.")

    def spi_clean_in_uboot(self, clean_registration=False):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string}
        """
        cmd = [
            "sf probe;",
            "sf erase",
            uberstaddr[self.board_id],
            ubersz[self.board_id]
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(30, self.bootloader_prompt, cmd)

        cmd = [
            cmd_prefix,
            "uclearcfg"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Done")
        self.pexp.expect_action(10, "", "\003")
        if clean_registration is True:
            cmd = [
                cmd_prefix,
                "uclearcal -f -e"
            ]
            cmd = ' '.join(cmd)
            self.pexp.expect_action(10, self.bootloader_prompt, cmd)
            self.pexp.expect_only(30, "Done")

        self.pexp.expect_action(10, "", "\003")

    def set_data_in_uboot(self):
        cmd = [
            cmd_prefix,
            "usetbid",
            self.board_id
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = [
            "setenv",
            "ethaddr",
            self.fakemac + ";",
            "saveenv"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "done")
        self.pexp.expect_action(10, "", "\003")
        log_debug("MAC setting succeded")

        self.pexp.expect_action(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)

    def login(self, username="ubnt", password="ubnt", timeout=10):
        """
        should be called at login console
        """
        self.pexp.expect_action(120, "Please press Enter to activate this console", "")
        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(timeout, "login:", username)
        self.pexp.expect_action(10, "Password:", password)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)

    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.config_stty(self.dev)

        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(1, "Waiting - PULG in the device...")

        self.stop_uboot()
        self.check_USGH2()

        isMFG = self.is_MFG_firmware()
        if isMFG is False:
            # it means current fw is production version
            self.spi_clean_in_uboot(clean_registration=False)
            msg(20, "Cleaned Env in uboot.")

            self.pexp.expect_action(10, self.bootloader_prompt, "reset")
            self.login()
            self.pexp.expect_action(10, "", "")

            self.check_net()
            msg(30, "Network is good. Starting update firmware")

            self.update_firmware_in_kernel()
            msg(40, "MFG Firmware flashed by syswrapper tool.")

            log_debug("Rebooting system after upgrade")

            self.stop_uboot()
            self.check_USGH2()
            self.set_data_in_uboot()  # set boardid in advanced for network enabling
            isMFG = self.is_MFG_firmware()
            if isMFG is False:
                error_critical("Failed to init MDK_DRV after upgrade")
            else:
                log_debug("Inited MDK_DRV after upgrade")
        else:
            pass

        self.spi_clean_in_uboot(clean_registration=True)
        msg(50, "Cleaned Env in uboot ...")

        self.set_data_in_uboot()

        if self.is_network_alive_in_uboot() is False:
            error_critical("Network in uboot is not working")

        log_debug("Starting upgrade firmware by urescue")
        self.update_firmware_in_uboot()
        msg(no=80, out="Firmware update complete.")

        self.login()
        msg(no=100, out="Back to T1 completed.")
        self.close_fcd()


def main():
    us_bcm5616_mfg = USBCM5616_MFG()
    us_bcm5616_mfg.run()

if __name__ == "__main__":
    main()