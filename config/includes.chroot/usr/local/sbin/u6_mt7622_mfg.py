#!/usr/bin/python3
import os
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

class MT7622MFGGeneral(ScriptBase):
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
        super(MT7622MFGGeneral, self).__init__()

    def write_img(self):
        log_debug(msg="Initializing sf => nor init")
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="nor init")

        cmd = "snor erase 0x0 0x4000000; snor write ${loadaddr} 0x0 0x3ff0000"
        log_debug(msg="run cmd " + cmd)
        self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(timeout=300, exptxt=self.bootloader_prompt)
        self.pexp.expect_action(timeout=10, exptxt="", action=" ")

    def stop_uboot(self, timeout=30):
        self.set_bootloader_prompt("MT7622> |MT7622 #|==>")
        if self.pexp is None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot", action="")
            try:
                self.pexp.expect_action(timeout=5, exptxt=self.bootloader_prompt, action="")
            except Exception as e:
                self.set_bootloader_prompt("=>")
                log_debug(msg="Changed uboot prompt to =>")
                self.pexp.expect_action(timeout=5, exptxt=self.bootloader_prompt, action="")

    def set_boot_netenv(self):
        # self.pexp.expect_action(10, self.bootloader_prompt, "mtk network on")
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ethcard AQR112C")
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ethaddr " + self.premac)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def transfer_img(self, filename):
        img = os.path.join(self.image, filename)
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpb ${loadaddr} " +img)
        self.pexp.expect_only(60, "Bytes transferred = "+img_size)

    def is_mfg_uboot(self):
        ret = self.pexp.expect_get_output("version", self.bootloader_prompt)
        log_debug("verison ret: "+str(ret))
        if "U-Boot " not in ret:
            return False
        return True

    def reset_uboot(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")
        self.pexp.expect_only(120, "BusyBox")

    def run(self):
        """
        Main procedure of back to ART
        """

        # Connect into DU using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)

        msg(no=10, out="Waiting - PULG in the device...")
        self.stop_uboot()

        msg(no=20, out='Setting up IP address in u-boot ...')
        self.set_boot_netenv()

        msg(no=30, out='Checking network connection to tftp server in u-boot ...')
        self.is_network_alive_in_uboot(retry=8)

        if self.board_id in 'a620':
            msg(no=50, out='flash back to T1 kernel and u-boot ...')
            self.transfer_img(self.board_id + "-mfg.kernel.uboot")
            self.write_img()

        msg(no=80, out='Waiting for T1 booting ...')
        self.reset_uboot()

        msg(no=100, out="Back to T1 has completed")
        self.close_fcd()

def main():
    mt7622_mfg_general = MT7622MFGGeneral()
    mt7622_mfg_general.run()

if __name__ == "__main__":
    main()
