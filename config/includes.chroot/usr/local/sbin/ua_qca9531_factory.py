#!/usr/bin/python3
import time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class UAQCA9531Factory(ScriptBase):
    def __init__(self):
        super(UAQCA9531Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ubimg = "images/" + "ua-readerlite-uboot.bin"
        self.fwimg = "images/" + "ua-readerlite-fcd.bin"
        self.devregpart = "/dev/mtd6"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "ath>"
        self.linux_prompt = "root@OpenWrt:/#"

        self.ethnum = {
            'ec4d': "1"
        }

        self.wifinum = {
            'ec4d': "0",
        }

        self.btnum = {
            'ec4d': "1"
        }
        
        self.bootm_addr = {
            'ec4d': "0x50000000"
        }
        
        self.linux_prompt_select = {
            'ec4d': "#"
        }
        
        self.uboot_eth_port = {
            'ec4d': "eth0"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.row_dev_ip = "192.168.1." + str((int(self.row_id)))
        self.BOOT_BSP_IMAGE    = True 
        self.PROVISION_ENABLE  = True 
        self.DOHELPER_ENABLE   = True 
        self.REGISTER_ENABLE   = True 
        if self.board_id == "xxx" :
            self.FWUPDATE_ENABLE   = False
            self.DATAVERIFY_ENABLE = False 
        else:
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True

    def init_bsp_image(self):
        self.pexp.expect_ubcmd(300, "Please press Enter to activate this console.", "\n\n")
        time.sleep(3)
        self.pexp.expect_ubcmd(5, self.linux_prompt, "\n", retry=10)

    def _bootloader_fwupdate(self):
        self.pexp.expect_ubcmd(20, self.linux_prompt, "reboot",retry=3)
        self.pexp.expect_ubcmd(20, "Hit any key to stop autoboot:", " ")
        self.pexp.expect_ubcmd(1, self.bootloader_prompt, " ", retry=5)
        self.set_ub_net()
        self.is_network_alive_in_uboot()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'tftpboot 0x80060000 {}  && erase 0x9f000000 +0x60000 \
        && cp.b 0x80060000 0x9f000000 0x532b6'.format(self.ubimg))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        self.bootloader_prompt = "ar7240>"
        self.pexp.expect_ubcmd(20, "Hit any key to stop autoboot:", " ")

    def _fcd_fwupdate(self):
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "\n", retry=10)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "go 0x80200020  uappinit", retry=10)
        self.set_ub_net()
        self.is_network_alive_in_uboot()
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "setenv do_urescue TRUE;urescue -u -e", retry=10)
        cmd = "atftp --option \"mode octet\" -p -l /tftpboot/{0} {1}".format(self.fwimg, self.dutip)
        log_debug("Run cmd on host:" + cmd)
        self.fcd.common.xcmd(cmd=cmd)
        time.sleep(5)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "go 0x80200020  uwrite -f", retry=0)

    def fwupdate(self):
        log_debug('Upgrading bootloader')
        self._bootloader_fwupdate()
        log_debug('Upgrade bootloader done')
        log_debug('Upgrading fcd fw')
        self._fcd_fwupdate()
        log_debug('Upgrading fcd fw done')

    def check_info(self):
        self.linux_prompt = "#"
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt")
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
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if self.BOOT_BSP_IMAGE is True:
            self.init_bsp_image()
            msg(10, "Boot up to linux console is good ...")

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
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "mtd erase /dev/mtd6", self.linux_prompt)
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    uaqca9531_factory = UAQCA9531Factory()
    uaqca9531_factory.run()

if __name__ == "__main__":
    main()
