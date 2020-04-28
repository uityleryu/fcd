#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import os
import time

flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

rsa_key = "dropbear_rsa_host_key"
dss_key = "dropbear_dss_host_key"

'''
    eb10: US-8-150W
    eb18: US-8-60W
    eb20: US-XG
    eb21: US-16-150W
    eb23: US-6-XG-150
    eb25: US-XG-24-550W (hold)
    eb26: US-XG-48-550W (hold)
    eb27: USW-XG-Aggregation (hold)
    eb30: US-24
    eb31: US-24-250W
    eb36: USW-PRO-24-PoE
    eb37: USW-PRO-24
    eb38: USW6-24-PoE
    eb60: US-48
    eb62: US-48-500W
    eb67: USW-PRO-48-PoE
    eb68: USW-PRO-48
'''

# U-boot erase start address
uberstaddr = {
    '0000': "0x1e0000",
    'eb10': "0xc0000",
    'eb18': "0xc0000",
    'eb20': "0x1e0000",
    'eb21': "0xc0000",
    'eb23': "0x1e0000",
    'eb25': "0x1e0000",
    'eb26': "0x1e0000",
    'eb27': "0x1e0000",
    'eb31': "0xc0000",
    'eb36': "0x1e0000",
    'eb37': "0x1e0000",
    'eb38': "0x1e0000",
    'eb62': "0xc0000",
    'eb67': "0x1e0000",
    'eb68': "0x1e0000"
}

# U-boot erase size
ubersz = {
    '0000': "0x10000",
    'eb10': "0x10000",
    'eb18': "0x10000",
    'eb20': "0x10000",
    'eb21': "0x10000",
    'eb23': "0x10000",
    'eb25': "0x10000",
    'eb26': "0x10000",
    'eb27': "0x10000",
    'eb31': "0x10000",
    'eb36': "0x10000",
    'eb37': "0x10000",
    'eb38': "0x10000",
    'eb62': "0x10000",
    'eb67': "0x10000",
    'eb68': "0x10000"
}

# Boot argument
bootargs = {
    '0000': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb10': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb18': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb20': "quiet console=ttyS0,115200 mem=496M " + flash_mtdparts_64M,
    'eb21': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb23': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb25': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb26': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb27': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb31': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb36': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb37': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb38': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb62': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb67': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb68': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M
}

helperexes = {
    '0000': "helper_BCM5341x",
    'eb10': "helper_BCM5334x",
    'eb18': "helper_BCM5334x",
    'eb20': "helper_BCM5341x",
    'eb21': "helper_BCM5334x",
    'eb23': "helper_BCM5616x",
    'eb25': "helper_BCM5617x",
    'eb26': "helper_BCM5617x",
    'eb27': "helper_BCM5617x",
    'eb31': "helper_BCM5334x",
    'eb36': "helper_BCM5616x",
    'eb37': "helper_BCM5616x",
    'eb38': "helper_BCM5616x",
    'eb62': "helper_BCM5334x",
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
        self.fakemac = "00:90:4c:06:a5:7{}".format(self.row_id)
        self.isMDK = False
        self.gen1_model = [
            "0000", "eb10", "eb18", "eb20", "eb21",
            "eb30", "eb31", "eb60", "eb62"
        ]
        self.bcm5617x_model = [
            "eb25", "eb26", "eb27"
        ]

    def stop_uboot(self):
        log_debug("Stopping U-boot")
        # 1st, Check if U-Boot support MDK from the initial message of U-Boot
        self.pexp.expect_action(40, "Hit any key to stop autoboot", "")

    '''
        The U-Boot will enable the networking configuration when booting up in
        the BCM5334x series so that it needn't give an extra mdk_drv command to
        enable it.
        On the contrary, the U-Boot has to do mdk_drv for the BCM5616x series for
        the reason that it doesn't enable the networking configuration as default.
    '''
    def ub_chk_mdk_support(self):
        if self.board_id in self.gen1_model:
            log_file_path = os.path.join("/tftpboot/", "log_slot" + self.row_id + ".log")
            cmd = "cat {0}".format(log_file_path)
            [stdo, rtc] = self.fcd.common.xcmd(cmd)
            match = re.findall("Found MDK device", stdo, re.S)
            if match:
                self.isMDK = True
                log_debug("MDK is supported from U-Boot booting message")
            else:
                self.isMDK = False
                log_debug("MDK is not supported from U-Boot booting message")
        else:
            # 2nd, Check if U-Boot support MDK by using mdk_drv command
            self.isMDK = self.is_MDK_support()
            if self.isMDK is True:
                log_debug("MDK is supported by mdk_drv command")
            else:
                log_debug("MDK is not supported by mdk_drv command")

    def ub_netcheck(self):
        for i in range(0, 3):
            cmd = "ping {0}".format(self.tftp_server)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            exp = "host {0} is alive".format(self.tftp_server)
            rtc = self.pexp.expect_get_index(20, exp)
            if rtc > 0:
                break

    def lnx_netcheck(self):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        cmd = "ping -c 1 {}".format(self.tftp_server)
        self.pexp.expect_lnxcmd(15, self.linux_prompt, cmd, postexp, retry=5)
        self.chk_lnxcmd_valid()

    def ub_uapp_init(self):
        if self.board_id in self.bcm5617x_model:
            cmd = "bootubnt init"
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            log_debug("DUT is BCM5617x series")
        else:
            cmd = "go $ubntaddr uappinit"
            self.pexp.expect_action(5, "", "")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            self.pexp.expect_only(10, "UBNT application initialized")

    def is_MDK_support(self):
        log_debug("Checking if U-boot include MDK by mdk_drv")

        output = self.pexp.expect_get_output("mdk_drv", self.bootloader_prompt, 10)
        log_debug("mdk_drv output: " + str(output))

        if "Found MDK device" in output:
            return True
        elif "Unknown command" in output:
            return False
        elif "MDK initialized failed" in output:
            error_critical("MDK initialized failed")

    # Using urescue to update MFG
    def update_firmware_in_uboot(self):
        """
        use urescue to update firmwre,
        after flash firmware, DU will be resetting
        """
        if self.board_id in self.bcm5617x_model:
            cmd = "bootubnt ubntrescue; bootubnt"
        else:
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

        if self.board_id not in self.bcm5617x_model:
            cmd = "go $ubntaddr uwrite -f"
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.pexp.expect_only(60, "Firmware Version:")
        log_debug("Firmware loaded")

        self.pexp.expect_only(60, "Image Signature Verfied, Success.")
        log_debug("Download image verified.")

        if self.board_id not in self.bcm5617x_model:
            ker0_msg = "Copying to 'kernel0' partition. Please wait... :  done"
            ker1_msg = "Copying to 'kernel1' partition. Please wait... :  done"
        else:
            ker0_msg = r"Updating kernel0 partition \(and skip identical blocks\).*Done"
            ker1_msg = r"Updating kernel1 partition \(and skip identical blocks\).*Done"

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

    def ub_config_clean(self):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string}
        """
        cmd = "sf probe; sf erase {0} {1}".format(uberstaddr[self.board_id], ubersz[self.board_id])
        self.pexp.expect_action(30, self.bootloader_prompt, cmd)

        cmd = "go $ubntaddr uclearcfg"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Done")

        """
            cmd: go $ubntaddr uclearcal -f -e
            will clean all the EEPROM partition (64KB)
        """
        # cmd = "go $ubntaddr uclearcal -f -e"
        # self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        # self.pexp.expect_only(30, "Done")

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
            self.lnx_netcheck()
            msg(30, "Network is good. Starting update firmware")

            # Update kernel_partition_0
            self.update_firmware_in_kernel()
            msg(40, "MFG Firmware flashed by syswrapper tool.")

            log_debug("Rebooting system after upgrade")
            self.stop_uboot()
            self.ub_uapp_init()
            self.ub_config_clean()
            self.set_data_in_uboot()  # set boardid in advanced for network enabling
            self.ub_netcheck()

            # Update kernel_partition_1
            log_debug("Starting upgrade firmware by urescue")
            self.update_firmware_in_uboot()
            msg(80, "Firmware update complete.")
        else:
            log_debug("Updating MFG by urescue directly ...")
            self.ub_uapp_init()
            self.ub_config_clean()
            self.set_data_in_uboot()
            self.ub_netcheck()
            msg(50, "Network is good. Starting update firmware")

            log_debug("Starting upgrade firmware by urescue")
            self.update_firmware_in_uboot()
            msg(80, "Firmware update complete.")

        self.login(timeout=210, press_enter=True)
        self.pexp.expect_only(10, self.linux_prompt)
        msg(100, "Back to T1 completed.")
        self.close_fcd()


def main():
    us_bcm5616_mfg = USBCM5616_MFG()
    us_bcm5616_mfg.run()

if __name__ == "__main__":
    main()
