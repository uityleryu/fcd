#!/usr/bin/python3
import os
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical


class MT7621MFGGeneral(ScriptBase):
    """
    command parameter description for BackToT1
    command: python3
    para0:   script
    para1:   slot ID
    para2:   UART device number
    para3:   FCD host IP
    para4:   system ID
    para5:   Erase calibration data selection
    ex: [script, 1, 'ttyUSB1', '192.168.1.19', 'eb23', True]
    """
    def __init__(self):
        super(MT7621MFGGeneral, self).__init__()

    def write_img(self):
        if self.erase_devreg == "True":
            log_debug(msg="Write T1 image, delete devreg data")
            cmd = "sf probe; sf erase 0x0 0x2000000; sf update 0x80010000 0x0 0x2000000;"
            log_debug(msg="run cmd " + cmd)
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(timeout=600, exptxt=self.bootloader_prompt)
            self.pexp.expect_action(timeout=10, exptxt="", action=" ")
        elif self.erase_devreg == "False":
            log_debug(msg="Write T1 image, NO delete devreg data")
            cmd = "sf probe; sf erase 0x0 0xb0000; sf update 0x80010000 0x0 0xb0000;"
            log_debug(msg="run cmd " + cmd)
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(timeout=600, exptxt=self.bootloader_prompt)
            self.pexp.expect_action(timeout=10, exptxt="", action=" ")
            cmd = "sf probe; sf erase 0xc0000 0x1f40000; sf update 0x800d0000 0xc0000 0x1f40000;"
            log_debug(msg="run cmd " + cmd)
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(timeout=600, exptxt=self.bootloader_prompt)
            self.pexp.expect_action(timeout=10, exptxt="", action=" ")

    def stop_uboot(self, timeout=30):
        self.set_bootloader_prompt("MT7621> |MT7621 #|==>")
        if self.pexp is None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot|Autobooting in 2 seconds, press", action= "\x1b\x1b")
            try:
                self.pexp.expect_action(timeout=5, exptxt=self.bootloader_prompt, action="\x1b\x1b")
            except Exception as e:
                self.set_bootloader_prompt("=>")
                log_debug(msg="Changed uboot prompt to =>")
                self.pexp.expect_action(timeout=5, exptxt=self.bootloader_prompt, action="\x1b\x1b")

    def transfer_img(self, address, filename):
        img = os.path.join(self.image, filename)
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        cmd = "tftpb {} {}".format(address, img)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(160, "Bytes transferred = " + img_size)

    def is_mfg_uboot(self):
        ret = self.pexp.expect_get_output("version", self.bootloader_prompt)
        log_debug("verison ret: "+str(ret))
        if "U-Boot " not in ret:
            return False
        return True

    def reset_uboot(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")
        self.pexp.expect_only(120, "Linux version 4.4.198")

    def run(self):
        """
        Main procedure of back to ART
        """

        # Connect into DU using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)

        msg(no=10, out="Waiting - PULG in the device...")
        self.stop_uboot()

        msg(no=20, out='Setting up IP address in u-boot ...')
        self.set_ub_net()

        msg(no=30, out='Checking network connection to tftp server in u-boot ...')
        self.is_network_alive_in_uboot(retry=8)

        msg(no=50, out='flash back to T1 kernel and u-boot ...')
        self.transfer_img(address="0x80010000", filename= self.board_id + "-mfg.bin")
        self.write_img()

        msg(no=80, out='Waiting for T1 booting ...')
        self.reset_uboot()

        msg(no=100, out="Back to T1 has completed")
        self.close_fcd()

def main():
    mt7621_mfg_general = MT7621MFGGeneral()
    mt7621_mfg_general.run()

if __name__ == "__main__":
    main()
