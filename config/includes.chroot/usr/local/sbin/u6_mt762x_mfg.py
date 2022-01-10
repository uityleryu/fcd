#!/usr/bin/python3
import os
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class MT762xMFGGeneral(ScriptBase):
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
        super(MT762xMFGGeneral, self).__init__()

    def write_img(self):
        
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            log_debug(msg="write_img")
            cmd = "sf probe; sf erase 0x0 0x2000000; sf update 0x80010000 0x0 0x2000000; "
            log_debug(msg="run cmd " + cmd)
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(timeout=600, exptxt=self.bootloader_prompt)
            self.pexp.expect_action(timeout=10, exptxt="", action=" ")
        elif self.board_id == "a620":
            log_debug(msg="Initializing sf => nor init")
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="nor init")
            # cmd = "snor erase 0x0 0x4000000; snor write ${loadaddr} 0x0 0x3ff0000"  #tmp to keep in case
            cmd = "snor erase 0x0 0x4000000; snor write 0x4007FF28 0x0 0x3ff0000"
            log_debug(msg="run cmd " + cmd)
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(timeout=300, exptxt=self.bootloader_prompt)
            self.pexp.expect_action(timeout=10, exptxt="", action=" ")

    def stop_uboot(self, timeout=30):
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
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

        elif self.board_id == "a620":
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
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            self.pexp.expect_action(10, self.bootloader_prompt, "mtk network on")
        elif self.board_id == "a620":
            self.pexp.expect_action(10, self.bootloader_prompt, "setenv ethcard AQR112C")
            self.pexp.expect_action(10, self.bootloader_prompt, "setenv ethaddr " + self.premac)
        
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def transfer_img(self, address, filename):
        img = os.path.join(self.image, filename)
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpb {} {}".format(address, img))
        self.pexp.expect_only(160, "Bytes transferred = "+img_size)

    def is_mfg_uboot(self):
        ret = self.pexp.expect_get_output("version", self.bootloader_prompt)
        log_debug("verison ret: "+str(ret))
        if "U-Boot " not in ret:
            return False
        return True

    def reset_uboot(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            self.pexp.expect_only(120, "Write EEPROM buffer back to eFuse")
        elif self.board_id == "a620":
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

        msg(no=50, out='flash back to T1 kernel and u-boot ...')
        if self.board_id in 'a612' or self.board_id == "a614" or self.board_id == "a640":
            self.transfer_img(address="0x80010000", filename= self.board_id + "-mfg.kernel.uboot")
        elif self.board_id in 'a620':
            self.transfer_img(address="0x4007FF28", filename= self.board_id + "-mfg.kernel.uboot")
        self.write_img()

        msg(no=80, out='Waiting for T1 booting ...')
        self.reset_uboot()

        msg(no=100, out="Back to T1 has completed")
        self.close_fcd()

def main():
    mt762x_mfg_general = MT762xMFGGeneral()
    mt762x_mfg_general.run()

if __name__ == "__main__":
    main()
