#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
This back to MFG script is for ULTE-PRO, ULTE-PRO-US, ULTE-PRO-US
'''


class UAPQCA956xMFG(ScriptBase):
    def __init__(self):
        super(UAPQCA956xMFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.bootloader_prompt = "ath>"
        self.linux_prompt = "# "
        self.cmd_prefix = "go 0x80200020 "
        self.ram_addr = "0x81000000"

        self.erase_partition = {
            'uboot_kernel': {'addr': '0x9f000000', 'size': '+0xff0000'},
            'calibration': {'addr': '0x9fff0000', 'size': '+0x10000'},
        }

        self.write_partition = {
            'uboot_kernel': {'addr': '0x9f000000', 'size': '0xff0000'},  # size syntax is different from erase_partion
        }

    def enter_uboot(self, init_uapp=False):
        self.pexp.expect_action(90, "Hit any key to stop autoboot", "\033")
        time.sleep(2)

        if init_uapp is True:
            log_debug(msg="Init uapp")
            # Init uapp. DUT will reset after init

            uboot_env_fixed = "uboot env fix. Clearing u-boot env and resetting the board.."
            reset_auto = "Resetting"
            ubnt_app_init = "UBNT application initialized"
            expect_list = [uboot_env_fixed, reset_auto, ubnt_app_init]

            self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uappinit")
            index = self.pexp.expect_get_index(timeout=30, exptxt=expect_list)
            if index == self.pexp.TIMEOUT:
                error_critical('UBNT Application failed to initialize!')
            elif index == 0:
                log_debug('uboot env fixed, rebooting...')
                self.enter_uboot()
            elif index == 1:
                log_debug('DUT is resetting automatically')
                self.enter_uboot()

        self.set_net_uboot()

    def set_net_uboot(self):
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.is_network_alive_in_uboot()

    def tranfer_art_fw(self):
        art_path = os.path.join(self.fwdir, self.board_id + "-art.bin")
        log_debug(msg="art bin path:" + art_path)

        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootfile {}".format(art_path))
        self.pexp.expect_ubcmd(90, self.bootloader_prompt, "tftpboot {}".format(self.ram_addr), "Bytes transferred")

    def erase_flash(self, addr, size):
        # erase cal data + FW
        cmd = "erase {} {}".format(addr, size)
        log_debug(msg="erasing flash, cmd: {}".format(cmd))
        self.pexp.expect_ubcmd(90, self.bootloader_prompt, cmd, "done")

    def write_flash(self, addr, size):
        cmd = "cp.b {} {} {}".format(self.ram_addr, addr, size)
        log_debug(msg="writing flash, cmd: {}".format(cmd))
        self.pexp.expect_ubcmd(120, self.bootloader_prompt, cmd, "done")

    def login_kernel(self):
        log_debug(msg="Login kernel")
        self.login(username="root", password="5up", timeout=120, press_enter=False)

        self.is_network_alive_in_linux(retry=30)

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

        msg(20, "Setting uboot environment")
        self.enter_uboot(init_uapp=True)
        msg(30, "Transferring ART image")
        self.tranfer_art_fw()

        msg(40, "Erasing uboot and kernel")
        self.erase_flash(
            addr=self.erase_partition['uboot_kernel']['addr'],
            size=self.erase_partition['uboot_kernel']['size']
        )

        if self.erasecal == "True":
            msg(40, "Erasing calibration")
            self.erase_flash(
                addr=self.erase_partition['calibration']['addr'],
                size=self.erase_partition['calibration']['size']
            )

        msg(50, "Writing flash")
        self.write_flash(
            addr=self.write_partition['uboot_kernel']['addr'],
            size=self.write_partition['uboot_kernel']['size']
        )

        msg(60, "login kernel")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
        self.login_kernel()

        msg(100, "Completed back to MFG ...")
        self.close_fcd()


def main():
    uap_qca956x_mfg = UAPQCA956xMFG()
    uap_qca956x_mfg.run()


if __name__ == "__main__":
    main()
