#!/usr/bin/python3
import time
import os
import stat
from udm_alpine_factory import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

BOOT_BSP_IMAGE    = True 
PROVISION_ENABLE  = True 
DOHELPER_ENABLE   = True 
REGISTER_ENABLE   = True 
FWUPDATE_ENABLE   = True 
DATAVERIFY_ENABLE = False

class U6IPQ5018BspFactory(ScriptBase):
    def __init__(self):
        super(U6IPQ5018BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = "images/" + self.board_id + "-fw.bin"
        self.initramfs = "images/" + self.board_id + "-initramfs.bin"
        self.devregpart = "/dev/mtdblock9"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "IPQ5018#"
        self.linux_prompt = "root@OpenWrt:/#"

        self.ethnum = {
            'a650': "1",
            'a651': "1",
            'a652': "1",
            'a653': "1"
        }

        self.wifinum = {
            'a650': "2",
            'a651': "2",
            'a652': "2",
            'a653': "2"
        }

        self.btnum = {
            'a650': "1",
            'a651': "1",
            'a652': "1",
            'a653': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def init_bsp_image(self):
        self.pexp.expect_only(30, "Starting kernel")
        self.pexp.expect_lnxcmd(90, "UBNT BSP INIT", "dmesg -n1", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.is_network_alive_in_linux()

    def set_boot_net(self):                                                                                                 
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.is_network_alive_in_uboot()

    def _ramboot_uap_fwupdate(self):
        self.pexp.expect_action(40, "to stop", "\033")
        self.set_boot_net()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'setenv bootcmd "mmc read 0x44000000 0x00000022 0x00020022;      bootm 0x44000000"')
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'setenv imgaddr 0x44000000')
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'saveenv')
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'tftpboot 0x44000000 {}'.format(self.initramfs))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'bootm')
        self.linux_prompt = "UBNT-BZ.ca-spf113cs#"
        self.login(self.user, self.password, timeout=120, log_level_emerg=True, press_enter=True)
        time.sleep(30)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig br0 {}".format(self.dutip), self.linux_prompt)
        self.is_network_alive_in_linux()
        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
                     src_file=self.fwdir + "/" + self.board_id + "-fw.bin",
                     dst_file=self.dut_tmpdir + "/fwupdate.bin")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "fwupdate.real -m {}".format(self.dut_tmpdir + "/fwupdate.bin"))

    def fwupdate(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
        self._ramboot_uap_fwupdate()
        self._ramboot_uap_fwupdate()
        self.login(self.user, self.password, timeout=120, log_level_emerg=True, press_enter=True)

    def check_info(self):
        self.pexp.expect_lnxcmd(3, "", "info", self.linux_prompt)
        self.pexp.expect_lnxcmd(3, self.linux_prompt, "info", "Version", retry=5)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
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
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    u6ipq5018_bspfactory = U6IPQ5018BspFactory()
    u6ipq5018_bspfactory.run()

if __name__ == "__main__":
    main()
