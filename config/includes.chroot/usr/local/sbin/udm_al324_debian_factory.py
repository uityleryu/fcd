#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os


class UDM_AL324_DEBIAN_FACTORY(ScriptBase):
    def __init__(self):
        super(UDM_AL324_DEBIAN_FACTORY, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = "ALPINE_UBNT_UDM_PRO_SE>"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = "udm"
        self.bomrev = "113-" + self.bom_rev
        self.username = "ubnt"
        self.password = "ubnt"
        self.linux_prompt = "#"

        # Base path
        tool_name = {
            'ea2c': "udm_pro_se"
        }

        self.tool_folder = os.path.join(self.fcd_toolsdir, tool_name[self.board_id])

        # switch chip
        self.swchip = {
            'ea2c': "rtl83xx"
        }

        # number of Ethernet
        self.ethnum = {
            'ea2c': "11"
        }

        # number of WiFi
        self.wifinum = {
            'ea2c': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ea2c': "1"
        }

        # ethernet interface 
        self.netif = {
            'ea2c': "eth9"
        }

        self.infover = {
            'ea2c': "Version:"
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

        # FIXME: Use SFP port for temp due to FW is not ready
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ethact al_eth0")  # # set sfp 0 or 2 for SPF+

    def set_kernel_net(self):
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
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
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

        # copy pub key
        self.copy_file(
            source=os.path.join(self.tool_folder, "unas.pub"),
            dest=os.path.join(self.tftpdir, "unas.pub")
        )

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server, self.dutip))
        self.pexp.expect_action(10, self.bootloader_prompt, "run bootcmdtftp")
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_only(360, "Restarting system")

    def init_recovery_image(self):
        self.set_kernel_net()

    def fwupdate(self):
        pass

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
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "/usr/share/lcm-firmware/lcm-fw-info /dev/ttyACM0", post_exp="md5", retry=3)

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

        if self.UPDATE_UBOOT is True:
            self.update_uboot()
            self.pexp.expect_action(10, self.bootloader_prompt, "reset")
            msg(10, "Finish boot updating")

        if self.BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()

        if self.INIT_RECOVERY_IMAGE is True:
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            self.init_recovery_image()
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

        if self.DATAVERIFY_ENABLE is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")  # for correct ubnthal
            self.login(self.username, self.password, timeout=180, log_level_emerg=True)
            self.set_kernel_net()
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.LCM_CHECK_ENABLE is True:
            msg(85, "Check LCM FW version ...")
            self.lcm_fw_ver_check()

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    udm_al324_debian_factory = UDM_AL324_DEBIAN_FACTORY()
    udm_al324_debian_factory.run()

if __name__ == "__main__":
    main()     
