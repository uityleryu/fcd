#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
flash layout for eccc
0x000000000000-0x000000040000 : "Preloader" 256
0x000000040000-0x000000060000 : "ATF" 128
0x000000060000-0x0000001c0000 : "Bootloader" 1408
0x0000001c0000-0x0000001d0000 : "uboot-env" 64
0x0000001d0000-0x0000001e0000 : "uboot-env2" 64
0x0000001e0000-0x000000220000 : "Factory" 256
0x000000220000-0x000000230000 : "EEPROM" 64
'''


class UDMMT7622MFG(ScriptBase):
    def __init__(self):
        super(UDMMT7622MFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.mfg_uboot_cal = os.path.join(self.image, self.board_id + "-mfg.bin")
        self.mfg_img = os.path.join(self.image, self.board_id + "-fcd.bin")

        self.bootloader_prompt = "MT7622"
        self.linux_prompt = "#"

    def enter_uboot(self, timeout=60):
        self.pexp.expect_ubcmd(timeout, "Hit any key to stop autoboot", "")

        log_debug("Setting network in uboot ...")
        self.set_ub_net(premac="00:11:22:33:44:5" + str(self.row_id))
        self.is_network_alive_in_uboot()

    def transfer_img(self, image):
        log_debug("Transfer image ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpb {}".format(image), "Bytes transferred")

    def erase_partition(self, start, length):
        log_debug("Erase flash from {} to {}...".format(start, length))
        self.pexp.expect_ubcmd(30, "", "\033")  # for prompt
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "nor init")
        self.pexp.expect_ubcmd(90, self.bootloader_prompt, "snor erase {} {}".format(start, length), self.bootloader_prompt)

    def write_image(self, start, length):
        log_debug("Write flash from {} to {}...".format(start, length))
        self.pexp.expect_ubcmd(30, "", "\033")  # for prompt
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "nor init")
        self.pexp.expect_ubcmd(90, self.bootloader_prompt, "snor write ${{loadaddr}} {} {}".format(start, length), self.bootloader_prompt)

    def update_uboot(self, erase_cal):
        log_debug("Updating uboot ...")
        if erase_cal == "True":
            log_debug("Clearing uboot and calibration data ...")
            self.erase_partition(start="0x0", length="0x230000")
            self.write_image(start="0x0", length="0x230000")
        else:
            log_debug("Clearing uboot ...")
            self.erase_partition(start="0x0", length="0x1e0000")
            self.write_image(start="0x0", length="0x1e0000")

    def update_kernel(self):
        log_debug("Updating kernel ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run boot_wr_img")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "boot")

    def init_bsp_image(self):
        log_debug("Login kernel ...")
        self.pexp.expect_lnxcmd(120, "BusyBox", "dmesg -n1", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.is_network_alive_in_linux()

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
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        self.enter_uboot()
        msg(10, "Finish network setting in uboot ...")

        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "md 0x102140bc 0x1", "102140bc: ae22aa22")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "md 0x102140b8 0x1", "102140b8: aa22aa22")
        msg(20, "check default DDR config in uboot ...")

        log_debug("Transfer image ...")
        self.ddr_config_img = os.path.join(self.image, self.board_id + "-ddr-config.bin")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, f"tftpb ${{loadaddr}} {self.ddr_config_img}", "Bytes transferred")
        
        
        log_debug("Erase flash from 0x00000 to 0x40000...")
        self.pexp.expect_ubcmd(30, "", "\033")  # for prompt
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "nor init")
        self.pexp.expect_ubcmd(90, self.bootloader_prompt, "snor erase 0x00000 0x40000; snor write ${loadaddr} 0x00000 0x40000", self.bootloader_prompt)
        msg(40, "Finish DDR Config updating...")

        self.pexp.expect_ubcmd(30, "", "\033")  # for prompt
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "reset")

        self.enter_uboot()
        msg(60, "Finish network setting in uboot ...")

        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "md 0x102140bc 0x1", "102140bc: ae22ff22")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "md 0x102140b8 0x1", "102140b8: ff22ff22")
        msg(80, "check modified DDR config in uboot ...")


        # self.transfer_img(self.mfg_img)
        # msg(50, "Finish kernel image transferring ...")

        # self.update_kernel()
        # msg(60, "Finish kernel updating...")

        # self.init_bsp_image()
        # msg(70, "Finish kernel login...")

        # msg(100, "Completed back to T1 process ...")
        msg(100, "Completed modified DDR config process ...")
        self.close_fcd()


def main():
    udmmt7622_mfg = UDMMT7622MFG()
    udmmt7622_mfg.run()


if __name__ == "__main__":
    main()
