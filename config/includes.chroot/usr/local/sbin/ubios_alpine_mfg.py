#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class UbiosAlpineFactoryMFG(ScriptBase):
    def __init__(self):
        super(UbiosAlpineFactoryMFG, self).__init__()
        self.init_vars()
        self.cmd_prefix = "go ${ubntaddr}"

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-bsp.bin"
        self.bootloader_prompt = "ALL>"
        self.linux_prompt = "# "

    # def erase_cal_data(self):
    #     self.pexp.expect_action(10, self.bootloader_prompt, "{} uclearcal -f -e".format(self.cmd_prefix))
    #     self.pexp.expect_only(30, "Done.")

    def enter_uboot(self, stop_uboot_only):
        self.pexp.expect_action(90, "Autobooting in 2 seconds, press", "\033\033")
        if stop_uboot_only is False:
            time.sleep(2)
            # self.pexp.expect_action(30, self.bootloader_prompt, "{} uappinit".format(self.cmd_prefix))
            self.pexp.expect_action(30, self.bootloader_prompt, "qca8k")
            time.sleep(1)
            self.set_net_uboot()
            time.sleep(1)
            self.is_network_alive_in_uboot()

    def set_net_uboot(self):
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def update_bsp_image(self):
        #ubnt_udm_all_v1_boot.img for Nustream package test
        self.pexp.expect_action(30, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(20, "done")
        self.pexp.expect_only(30, "bootupd done")
        self.pexp.expect_action(30, self.bootloader_prompt, "run delenv")
        self.pexp.expect_only(20, "ALL>")

    # def fwupdate(self, filename):
    #     self.pexp.expect_action(10, self.bootloader_prompt, "{} uclearenv".format(self.cmd_prefix))
    #     self.pexp.expect_action(10, self.bootloader_prompt, "setenv mtdparts \"mtdparts=ath-nor0:384k(u-boot)," \
    #                                                         "64k(u-boot-env),1280k(uImage), 14528k(rootfs)," \
    #                                                         "64k(mib0),64k(ART)\"".format(self.cmd_prefix))
    #     self.pexp.expect_action(30, self.bootloader_prompt, "{} uappinit".format(self.cmd_prefix))
    #     self.pexp.expect_action(10, self.bootloader_prompt, "setenv do_urescue TRUE; urescue -u -e")                        
    #     # TFTP bin from TestServer
    #     fw_path = os.path.join(self.fwdir, self.board_id + "-art.bin")
    #     log_debug(msg="firmware path:" + fw_path)
    #     atftp_cmd = 'exec atftp --option "mode octet" -p -l {} {}'.format(fw_path, self.dutip)
    #     log_debug(msg="Run cmd on host:" + atftp_cmd)
    #     self.fcd.common.xcmd(cmd=atftp_cmd)
    #     self.pexp.expect_only(120, "Bytes transferred")
    #     self.pexp.expect_action(10, self.bootloader_prompt, "{} uwrite -f".format(self.cmd_prefix))
    #     self.pexp.expect_only(180, "U-Boot unifi")

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        msg(5, "Open serial port successfully ...")

        os.system("rm /tftpboot/boot.img")
        time.sleep(1)
        os.system(f"ln -sf /tftpboot/images/{self.fwimg} /tftpboot/boot.img")
        
        msg(10, 'Stop in uboot ...')
        self.enter_uboot(stop_uboot_only = False)
        msg(20, 'Finish net env in setting u-boot ...')
        
        msg(30, 'update to BSP image ...')
        self.update_bsp_image()
        
        os.system("rm /tftpboot/boot.img")
        
        
        
        # if self.erasecal == "True":
        #     msg(30, 'Erase calibration data ...')
        #     self.erase_cal_data()
        # else:
        #     msg(30, 'Keep calibration data ...')

        # msg(40, 'Start fwupdate ...')
        # self.fwupdate(filename=self.board_id + "-mfg.bin")
        # msg(80, 'Finish fwupdate ...')

        # self.enter_uboot(stop_uboot_only = True)
        # msg(90, 'Stop in uboot again ...')

        msg(100, "Completed back to T1 ...")
        self.close_fcd()


def main():
    ubios_alpine_factory_mfg = UbiosAlpineFactoryMFG()
    ubios_alpine_factory_mfg.run()

if __name__ == "__main__":
    main()
