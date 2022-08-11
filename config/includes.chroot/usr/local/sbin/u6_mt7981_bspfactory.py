#!/usr/bin/python3
import time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a642: U6-PLUS
    a643: U6-LRPLUS
    a667: UniFi-Express
'''


class U6MT7981BspFactory(ScriptBase):
    def __init__(self):
        super(U6MT7981BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = "images/{}-fw.bin".format(self.board_id)
        self.initramfs = "images/{}-initramfs.bin".format(self.board_id)
        self.gpt = "images/{}-gpt.bin".format(self.board_id)
        self.devregpart = "/dev/mtd0"
        self.bomrev = "113-{}".format(self.bom_rev)
        self.linux_prompt = "root@OpenWrt:/#"

        self.ethnum = {
            'a642': "1",
            'a643': "1"
        }

        self.wifinum = {
            'a642': "2",
            'a643': "2"
        }

        self.btnum = {
            'a642': "1",
            'a643': "1"
        }

        self.bootm_addr = {
            'a642': "0x50000000",
            'a643': "0x50000000"
        }

        # 650 U6-Pro, 651 U6-Mesh, 652 U6-IW, 653 U6-Extender, 656 U6-Enterprise-IW
        self.bootm_cmd = {
            'a642': "bootm $fileaddr#config@a650",
            'a643': "bootm $fileaddr#config@a650"
        }

        self.linux_prompt_select = {
            'a642': "#",
            'a643': "#"
        }

        self.lnx_eth_port = {
            'a642': "br-lan",
            'a643': "br-lan"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.BOOT_BSP_IMAGE    = True
        self.PROVISION_ENABLE  = True
        self.DOHELPER_ENABLE   = True
        self.REGISTER_ENABLE   = True
        self.FWUPDATE_ENABLE   = False
        self.DATAVERIFY_ENABLE = False
        self.FCD_TLV_data = False

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0)
        self.set_lnx_net(self.lnx_eth_port[self.board_id])
        self.is_network_alive_in_linux()

    def _ramboot_uap_fwupdate(self):
        self.pexp.expect_action(40, "to stop", "\033")
        self.set_ub_net(self.premac, ethact=self.uboot_eth_port[self.board_id])
        self.is_network_alive_in_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'tftpboot 0x50000000 {} && mmc erase 0x00000000 22 && '\
                                                           'mmc write 0x50000000 0x00000000 22'.format(self.gpt))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'setenv bootcmd "mmc read {} 0x00000022 0x00020022;'.format(self.bootm_addr[self.board_id]) + \
                                                           'bootm {}"'.format(self.bootm_addr[self.board_id]))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'setenv imgaddr 0x44000000')
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'saveenv')
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, 'tftpboot {} {}'.format(self.bootm_addr[self.board_id] ,self.initramfs))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, self.bootm_cmd[self.board_id])
        self.linux_prompt = self.linux_prompt_select[self.board_id]
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)
        self.disable_udhcpc()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "mtd erase /dev/mtd6", self.linux_prompt)
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "ifconfig br0", "inet addr", retry=12)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig br0 {}".format(self.dutip), self.linux_prompt)
        self.is_network_alive_in_linux()
        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
                     src_file=self.fwdir + "/" + self.board_id + "-fw.bin",
                     dst_file=self.dut_tmpdir + "/fwupdate.bin")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "syswrapper.sh upgrade2")
        self.linux_prompt = "#"

    def fwupdate(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
        self._ramboot_uap_fwupdate()
        # U6-IW, the upgrade fw process ever have more than 150sec, to increase 150 -> 300 sec to check if it still fail
        #sometimes DUT will fail log to interrupt the login in process so add below try process for it
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)

    def check_info(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
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
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if self.BOOT_BSP_IMAGE is True:
            self.init_bsp_image()
            msg(10, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            cmd = "mtd erase {}".format(self.devregpart)
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    factory = U6MT7981BspFactory()
    factory.run()

if __name__ == "__main__":
    main()