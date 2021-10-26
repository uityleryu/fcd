#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os


class UDM_AL324_FACTORY(ScriptBase):
    def __init__(self):
        super(UDM_AL324_FACTORY, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = ">"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = "udm"
        self.bomrev = "113-" + self.bom_rev
        self.username = "ubnt"
        self.password = "ubnt"
        self.linux_prompt = "#"

        # Base path
        tool_name = {
            'ea2a': "udw",  # udw
            'ea2b': "udw",  # udw_pro, but tools same as udw
            'ea2c': "udm_se",  # udm_se
        }

        self.tool_folder = os.path.join(self.fcd_toolsdir, tool_name[self.board_id])

        self.eeprom_offset = {
            'ea2a': "0x220000",
            'ea2b': "0x220000",
            'ea2c': "0x1f0000",
        }

        self.wsysid = {
            'ea2a': "77072aea",
            'ea2b': "77072bea",
            'ea2c': "77072cea",
        }

        # active port
        self.activeport = {
            'ea2a': "al_eth3",
            'ea2b': "al_eth3",
            'ea2c': "al_eth0",  # set sfp 0 or 2 for SPF+
        }

        # number of Ethernet
        self.ethnum = {
            'ea2a': "20",
            'ea2b': "23",
            'ea2c': "11",
        }

        # number of WiFi
        self.wifinum = {
            'ea2a': "2",
            'ea2b': "3",
            'ea2c': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ea2c': "1",
            'ea2a': "1",
            'ea2b': "1",
        }

        # ethernet interface
        self.netif = {
            'ea2a': "br0",  # udw
            'ea2b': "psu0",  # udw_pro
            'ea2c': "eth9",  # udm_se
        }

        # LCM update
        self.lcmupdate = {
            'ea2a': True,
            'ea2b': False,
            'ea2c': True,
        }

        self.devnetmeta = {
            'ethnum'          : self.ethnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.UPDATE_UBOOT          = True
        self.BOOT_RECOVERY_IMAGE   = True
        self.INIT_RECOVERY_IMAGE   = True
        self.NEED_DROPBEAR         = True
        self.PROVISION_ENABLE      = True
        self.DOHELPER_ENABLE       = True
        self.REGISTER_ENABLE       = True
        self.FWUPDATE_ENABLE       = False
        self.DATAVERIFY_ENABLE     = True
        self.LCM_CHECK_ENABLE      = True

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))

    def set_fake_EEPROM(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + "544e4255")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800000c " + self.wsysid[self.board_id])
        # reverse 77072aea to 2aea7707
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000010 " + self.wsysid[self.board_id][4:] + self.wsysid[self.board_id][:4])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000018 " + str(self.row_id).zfill(2) + "01ac74")  # fake mac
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800001c " + "00032cbd")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf erase {} 0x9000".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 {} 0x20".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 {} 0x20".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def set_kernel_net(self):
        if self.board_id == "ea2c":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "systemctl stop udapi-server udapi-bridge")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ip link set br0 down")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "brctl delbr br0")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip))

        self.is_network_alive_in_linux(ipaddr=self.dutip)

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)

        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-uboot.bin"),
            dest=os.path.join(self.tftpdir, "boot.img")
        )

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server, self.dutip))
        self.pexp.expect_action(10, self.bootloader_prompt, "run bootupd")  # tranfer img and update
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_action(60, self.bootloader_prompt, "run delenv")

    def boot_recovery_image(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)

        # copy recovery image
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-recovery"),
            dest=os.path.join(self.tftpdir, "uImage")
        )

        # copy FW image
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-fw.bin"),
            dest=os.path.join(self.tftpdir, "fw-image.bin")
        )

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server, self.dutip))

        self.pexp.expect_action(10, self.bootloader_prompt, "run bootcmdtftp")
        self.pexp.expect_only(30, "Bytes transferred")

        self.pexp.expect_only(360, "Reboot system safely")

    def init_recovery_image(self):
        self.set_kernel_net()

    def fwupdate(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)

        log_debug("Updating FW image ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargsextra 'factory server={} client={} nc_transfer'".format(self.tftp_server, self.dutip))

        # copy recovery image to tftp server
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-recovery"),
            dest=os.path.join(self.tftpdir, "uImage")  # fixed name
        )

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootcmdtftp")
        log_debug(msg="Enter factory install mode ...")
        self.pexp.expect_only(120, "Wait for nc client to push firmware")

        nc_cmd = "nc -q 1 {} 5566 < {}".format(self.dutip, os.path.join(self.fwdir, self.board_id + "-fw.bin"))
        log_debug(msg=nc_cmd)

        [buf, rtc] = self.fcd.common.xcmd(nc_cmd)
        if (int(rtc) > 0):
            error_critical("cmd: \"{}\" fails, return value: {}".format(nc_cmd, rtc))

        log_debug(msg="Upgrading FW ...")
        self.pexp.expect_only(240, "Reboot system safely")
        log_debug(msg="FW update done ...")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def lcm_fw_ver_check(self):
        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
                     src_file=os.path.join(self.tool_folder, "nvr-lcm-tools*"),
                     dst_file=self.dut_tmpdir)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dpkg -i /tmp/nvr-lcm-tools*")
        try:
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "/usr/share/lcm-firmware/lcm-fw-info /dev/ttyACM0", post_exp="md5", retry=3)
        except Exception as e:
            self.pexp.expect_lnxcmd(30, "", "cat /var/log/ulcmd.log")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "")
            raise e

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")
        '''
        if self.UPDATE_UBOOT is True:
            self.set_fake_EEPROM()
            self.update_uboot()
            self.pexp.expect_action(10, self.bootloader_prompt, "reset")
            msg(10, "Finish boot updating")

        if self.BOOT_RECOVERY_IMAGE is True:
            msg(15, "Updating FW")
            self.fwupdate()
        '''
        if self.INIT_RECOVERY_IMAGE is True:
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            msg(15, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
        if self.DATAVERIFY_ENABLE is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")  # for correct ubnthal
            self.login(self.username, self.password, timeout=180, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.LCM_CHECK_ENABLE is True:
            if self.lcmupdate[self.board_id] is True:
                msg(85, "Check LCM FW version ...")
                self.lcm_fw_ver_check()
        '''
        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    udm_al324_factory = UDM_AL324_FACTORY()
    udm_al324_factory.run()

if __name__ == "__main__":
    main()
