#!/usr/bin/python3
import time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a642: U6-PLUS
    a643: U6-LRPLUS
        Although the U6-LRPLUS is IPQ5018, it use the same process of U6-PLUS
    a667: UniFi-Express
'''


class U6MT7981BspFactory(ScriptBase):
    def __init__(self):
        super(U6MT7981BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.devregpart = "/dev/mtd0"
        self.bomrev = "113-{}".format(self.bom_rev)
        self.bootloader_prompt = "MT7981"
        self.linux_prompt = "root@OpenWrt:/#"
        self.linux_prompt_fw = "#"

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

        self.BOOT_BSP_IMAGE = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.CHECK_CAL_DATA = True
        self.REGISTER_ENABLE = True
        self.FWUPDATE_ENABLE = True
        self.DATAVERIFY_ENABLE = True
        self.FCD_TLV_data = False

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0)

        comma_mac = self.mac_format_str2comma(self.mac)
        cmd = "ifconfig eth0 hw ether {}".format(comma_mac)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        self.set_lnx_net(self.lnx_eth_port[self.board_id])
        self.is_network_alive_in_linux(arp_logging_en=True, del_dutip_en=True, retry=10)

    def uboot_update(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.set_ub_net(premac=self.mac)
        self.is_network_alive_in_uboot(arp_logging_en=True, del_dutip_en=True)

        cmd = "sf probe"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "sf erase 0x10000 0x80000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        cmd = "tftpboot 0x46000000 images/{}-uboot.bin".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "mmc erase 0x3400 0xfff"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "mmc write 0x46000000 0x3400 0xfff"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "reset")
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.set_ub_net(premac=self.mac)
        self.is_network_alive_in_uboot(arp_logging_en=True, del_dutip_en=True)

    def fwupdate(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
        self.uboot_update()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubnt_clearcfg TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubnt_clearenv TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv do_urescue TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
        self.pexp.expect_action(30, "Listening for TFTP transfer on", "")

        cmd = "atftp -p -l {0}/{1}-fw.bin {2}".format(self.fwdir, self.board_id, self.dutip)
        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "")

        self.linux_prompt = "#"
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)

    def check_info(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def check_caldata(self):
        cmd = "ifconfig ra0 up"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        if self.board_id == "a642":
            cmdset = [
                ["iwpriv ra0 e2p 190", "0x5212"],
                ["iwpriv ra0 e2p 192", "0x4848"],
                ["iwpriv ra0 e2p 19a", "0x0007"]
            ]
        elif self.board_id == "a643":
            cmdset = [
                ["iwpriv ra0 e2p 190", "0x5B12"],
                ["iwpriv ra0 e2p 192", "0x4C48"],
                ["iwpriv ra0 e2p 19a", "0x0007"]
            ]
        else:
            log_deubg("The Board ID is not support!!!")
            return RC.E_FTU_GENERIC

        for cmd in cmdset:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd[0])
            self.pexp.expect_only(10, cmd[1])

    def run(self):
        """
        Main procedure of factory
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

        if self.CHECK_CAL_DATA is True:
            self.check_caldata()
            msg(40, "Finish checking the calibration data ...")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(50, "Finish doing registration ...")
            cmd = "mtd erase {}".format(self.devregpart)
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
            self.check_devreg_data()
            msg(60, "Finish doing signed file and EEPROM checking ...")

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
