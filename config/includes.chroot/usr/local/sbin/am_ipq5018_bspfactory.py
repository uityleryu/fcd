#!/usr/bin/python3
import time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class AMIPQ5018BspFactory(ScriptBase):
    def __init__(self):
        super(AMIPQ5018BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ubimg = "images/" + self.board_id + "-uboot.bin"
        self.fwimg = "images/" + self.board_id + ".bin"
        
        self.devregpart = "/dev/mtdblock9"
        self.bomrev = "113-" + self.bom_rev
       
        self.uboot_address = {
            '0000': "0x00120000",
            'a659': "0x00120000"
        }
        self.ubaddr = self.uboot_address[self.board_id]

        self.uboot_size = {
            '0000': "0x000a0000",
            'a659': "0x000a0000"
        }
        self.ubsize = self.uboot_size[self.board_id]

        self.bootloader_prompt = "IPQ5018#"

        self.linux_prompt_select = {
            '0000': "#",    #prompt will be like "UBNT-BZ.5.65.0#"
            'a659': "#"
        }
        self.linux_prompt = "root@OpenWrt:/#"
        self.prod_prompt = "ubnt@OpenWrt:~#"

        self.ethnum = {
            '0000': "1",
            'a659': "1"
        }

        self.wifinum = {
            '0000': "2",
            'a659': "1"
        }

        self.btnum = {
            '0000': "1",
            'a659': "1"
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
        if self.board_id == "a656" :
            self.FWUPDATE_ENABLE   = False
            self.DATAVERIFY_ENABLE = False 
        else:
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0)
        self.is_network_alive_in_linux()


    def update_uboot(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")

        self.pexp.expect_action(40, "to stop", "\033")
        self.set_ub_net(self.premac)
        self.is_network_alive_in_uboot()

        cmd = "tftpboot $loadaddr " + self.ubimg

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "sf probe")

        cmd = "sf erase {0} +{1}; sf write $fileaddr {0} 0x$filesize".format(self.ubaddr, self.ubsize)

        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "re")

        self.pexp.expect_action(20, exptxt="Hit any key to stop autoboot|Autobooting in", 
                                action= "\x1b\x1b")

    def urescue(self):
        self.set_ub_net(self.premac)
        self.is_network_alive_in_uboot()

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue")

        cmd = "atftp --option \"mode octet\" -p -l /tftpboot/{0} {1}".format(self.fwimg, self.dutip)
        log_debug("Run cmd on host:" + cmd)
        self.fcd.common.xcmd(cmd=cmd)

        self.pexp.expect_only(30, "Version:")
        log_debug("urescue: FW loaded")

        self.pexp.expect_only(180, "Updating 0:HLOS partition")
        log_debug("urescue: HLOS partitio updated")

        self.pexp.expect_only(180, "Updating rootfs partition")
        log_debug("urescue rootfs updated")

        self.pexp.expect_only(180, "Updating bs partition")
        log_debug("urescue bs updated")

    def check_info(self):

        self.pexp.expect_action(300, "entered forwarding state", "")

        time.sleep (3)

        self.linux_prompt = "ubnt@OpenWrt:~#"

        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=False)

        self.pexp.expect_lnxcmd(5, self.linux_prompt, "cat /etc/version")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "grep board /proc/ubnthal/board.info")

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
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            self.update_uboot()
            msg(60, "Uboot upgrade success ...")
            self.urescue()
            msg(70, "Urescue success ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    amipq5018_bspfactory = AMIPQ5018BspFactory()
    amipq5018_bspfactory.run()

if __name__ == "__main__":
    main()
