#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical


BOOT_BSP_IMAGE    = True 
PROVISION_ENABLE  = True 
DOHELPER_ENABLE   = True 
REGISTER_ENABLE   = True 
FWUPDATE_ENABLE   = True 
DATAVERIFY_ENABLE = True
DIAG_MODE_ENABLE  = True
SET_NTP_ENABLE    = True

class UDMMT7622BspFactory(ScriptBase):
    def __init__(self):
        super(UDMMT7622BspFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fw_img = os.path.join(self.fwdir, self.board_id + "-fw.bin")
        self.fw_uboot = os.path.join(self.image, self.board_id + "-fw.uboot")
        self.fw_recovery = os.path.join(self.image, self.board_id + "-recovery")
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "MT7622"
        self.linux_prompt = "#"

        self.ethnum = {
            'eccc': "5"
        }

        self.wifinum = {
            'eccc': "2"
        }

        self.btnum = {
            'eccc': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def enter_uboot(self, timeout=60):
        self.pexp.expect_ubcmd(timeout, "Hit any key to stop autoboot", "")
        log_debug("Setting network in uboot ...")
        self.set_ub_net(premac="00:11:22:33:44:5" + str(self.row_id))
        self.is_network_alive_in_uboot()

    def update_uboot(self, uboot_image):
        log_debug("Updating uboot ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpb {}".format(uboot_image), "Bytes transferred")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "nor init; snor erase 0x60000 0x160000;")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "snor write ${loadaddr} 0x60000 ${filesize};")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "invaild_env")

    def boot_bsp_image(self):
        self.enter_uboot()
        # Update uboot
        self.update_uboot(self.fcd_uboot)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
        self.enter_uboot()
        # Update kernel
        log_debug("Updating FCD image ...")
        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "tftpb {}".format(self.fcd_img), "Bytes transferred")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run boot_wr_img")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "boot")

    def init_bsp_image(self):
        self.pexp.expect_lnxcmd(120, "BusyBox", "dmesg -n1", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.is_network_alive_in_linux()

    def fwupdate(self):
        self.enter_uboot()
        # Update uboot
        self.update_uboot(self.fw_uboot)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
        self.enter_uboot()
        log_debug("Updating FW image ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargsextra 'factory client={} nc_transfer'".\
                               format(self.dutip))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootargsemmcdual0")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "nor init")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "mmc init")

        # copy recovery image to tftp server
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-recovery"),
            dest=os.path.join(self.tftpdir, "uImage")  # fixed name
        )

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot uImage")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm")
        self.pexp.expect_only(120, "enter factory install mode")
        log_debug(msg="Enter factory install mode ...")
        self.pexp.expect_only(120, "Wait for nc client")
        log_debug(msg="nc ready ...")
        nc_cmd = "nc -q 1 {} 5566 < {}".format(self.dutip, self.fw_img)
        [buf, rtc] = self.fcd.common.xcmd(nc_cmd)
        if (int(rtc) > 0):
            error_critical("cmd: \"{}\" fails, return value: {}".format(nc_cmd, rtc))
        log_debug(msg="Upgrading FW ...")
        self.pexp.expect_only(120, "Reboot system safely")
        log_debug(msg="FW update done ...")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def enter_diag_mode(self):
        # Disable some services (protect/network controller app) to speed up the time of booting up
        self.pexp.expect_lnxcmd(180, self.linux_prompt, "systemctl disable unifi-core unifi-protect unifi postgresql postgresql@9.6-main postgresql@9.6-protect postgresql-cluster@9.6-main postgresql-cluster@9.6-protect-cleanup postgresql-cluster@9.6-protect ulp-go bt ble-http-transport --now")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dpkg -r ubnt-report")

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if BOOT_BSP_IMAGE is True:
            self.init_bsp_image()
            msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot -f")
            self.fwupdate()
            msg(70, "Rebooting ...")

        if DATAVERIFY_ENABLE is True:
            self.login(timeout=600, log_level_emerg=True)
            time.sleep(5)
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        if DIAG_MODE_ENABLE is True:
            self.enter_diag_mode()

        if SET_NTP_ENABLE is True:
            self.set_ntptime_to_dut(rtc_tool="busybox hwclock")
            msg(95, "Set NTP time to DUT ...")

        msg(100, "Completed FCD process ...")
        self.close_fcd()


def main():
    udmmt7622_bspfactory = UDMMT7622BspFactory()
    udmmt7622_bspfactory.run()


if __name__ == "__main__":
    main()
