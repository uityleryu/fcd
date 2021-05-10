#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical

'''
Flash layout
- 0x000000000000-0x000000080000 : "u-boot"
- 0x000000080000-0x000000090000 : "u-boot-env"
- 0x000000090000-0x0000000a0000 : "eeprom"
- 0x0000000a0000-0x0000000b0000 : "bs1"
- 0x0000000b0000-0x0000000c0000 : "bs2"
- 0x0000000c0000-0x0000000d0000 : "prst"
- 0x0000000d0000-0x000000150000 : "cfg"
- 0x000000150000-0x0000001f0000 : "stats"
- 0x0000001f0000-0x0000002f0000 : "lcmfw"
- 0x0000002f0000-0x0000022f0000 : "ltefw"
- 0x0000022f0000-0x0000026a0000 : "recovery"
- 0x0000026a0000-0x000003350000 : "firmware" <-- sysupgrade file goes here
- 0x000003350000-0x000004000000 : "fw_inactive"
'''


class UAPQCA956xMFG(ScriptBase):
    def __init__(self):
        super(UAPQCA956xMFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.bootloader_prompt = "ath>"
        self.linux_prompt = "# "

    def enter_uboot(self, init_uapp=False):
        self.pexp.expect_action(90, "Hit any key to stop autoboot", "\033")
        time.sleep(2)

        if init_uapp is True:
            log_debug(msg="Init uapp")
            # Init uapp. DUT will reset after init
            self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uappinit")

        self.set_net_uboot()

    def set_net_uboot(self):
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.is_network_alive_in_uboot()

    def transfer_img(self, filename):
        img = os.path.join(self.fwdir, filename)
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        log_debug("Transferring file: {}, size: {}".format(img, img_size))
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootfile {}".format(img))
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "tftpboot 0x81000000", "Bytes transferred = {}".format(img_size))

    def update_uboot(self):
        # erase and write flash
        self.pexp.expect_action(90, self.bootloader_prompt, "erase_ext 0x0 0x90000")
        self.pexp.expect_action(90, self.bootloader_prompt, "write_ext 0x81000000 0x0 0x90000")

    def erase_cal_data(self):
        # erase cal data
        self.pexp.expect_action(90, self.bootloader_prompt, "erase_ext 0x90000 0x10000")

    def update_kernel(self):
        # erase and write flash
        self.pexp.expect_action(90, self.bootloader_prompt, "erase_ext 0xa0000 0xF60000")
        self.pexp.expect_action(90, self.bootloader_prompt, "write_ext 0x810a0000 0xa0000 0xF60000")

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

        self.enter_uboot()
        msg(20, 'Finished net env in setting u-boot ...')

        self.transfer_img(filename=self.board_id + "-mfg.bin")
        msg(30, 'Finished MFG file transferring ...')

        self.update_uboot()
        msg(40, 'Finished MFG uboot update ...')

        if self.erasecal == "True":
            self.erase_cal_data()
            msg(45, 'Erased calibration data ...')

        self.update_kernel()
        msg(50, 'Finished MFG kernel update ...')

        self.pexp.expect_action(90, self.bootloader_prompt, 'reset')

        self.login(username="root", password="5up", timeout=120, press_enter=False)

        msg(100, "Completed back to MFG ...")
        self.close_fcd()


def main():
    uap_qca956x_mfg = UAPQCA956xMFG()
    uap_qca956x_mfg.run()


if __name__ == "__main__":
    main()
