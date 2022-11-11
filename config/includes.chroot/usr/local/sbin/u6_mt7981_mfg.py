#!/usr/bin/python3
import os, time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a642: U6-PLUS
    a643: U6-LRPLUS
    a667: UniFi-Express
'''


class U6MT7981MFGGeneral(ScriptBase):
    def __init__(self):
        super(U6MT7981MFGGeneral, self).__init__()
        self.bootloader_prompt = "MT7981"

    def stop_uboot(self, timeout=60):
        self.pexp.expect_action(40, "to stop", "\033\033")

    def bspimg_update(self):
        '''
            This case doesn't support clean the WiFi calibration data and signed data
        '''

        cmd = "tftpboot 0x46000000 images/{}-bspfw.bin".format(self.board_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        '''
            Clean GPT, partition table
        '''
        cmd = "mmc erase 0x0 0x23ff"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        cmd = "mmc write 0x46000000 0x0 0x23ff"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)

        '''
            Clean U-Boot
        '''
        md = "mmc erase 0x3400 0xfff"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "mmc write 0x46680000 0x3400 0xfff"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)

        '''
            Clean Kernel and Rootfs
        '''
        md = "mmc erase 0x4480 0x90000"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "mmc write 0x46890000 0x4480 0x90000"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)

    def run(self):
        """
        Main procedure of back to T1
        """

        # Connect into DUT using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        # Update NOR(uboot)
        self.stop_uboot()
        msg(10, 'Stop in uboot...')

        self.set_ub_net()
        self.is_network_alive_in_uboot()
        msg(20, 'Network in uboot works ...')

        self.bspimg_update()
        msg(40, 'Finshing updating to BSP image ...')

        msg(100, "Back to T1 has completed")
        self.close_fcd()

def main():
    mfg_general = U6MT7981MFGGeneral()
    mfg_general.run()

if __name__ == "__main__":
    main()
