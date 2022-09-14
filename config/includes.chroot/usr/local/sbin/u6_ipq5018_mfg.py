#!/usr/bin/python3
import os, time
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical


class U6IPQ5018MFGGeneral(ScriptBase):
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
        super(U6IPQ5018MFGGeneral, self).__init__()
        self.mem_addr = "0x44000000"
        self.nor_bin = "{}-nor.bin".format(self.board_id)
        self.emmc_img = "{}-emmc.img".format(self.board_id)
        self.set_bootloader_prompt("IPQ5018#")

    def update_nor(self):
        cmd = "sf probe; sf erase 0x0 0x1C0000; sf write {} 0x0 0x1C0000".format(self.mem_addr)
        log_debug(cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_only(60, "Written: OK")

        if self.erasecal == "True":
            cal_offset = "0x1C0000"
            cmd = "sf erase 0x1C0000 0x070000"
            log_debug("Erase calibration data ...")
            log_debug(cmd)
            self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(60, "Erased: OK")

        if self.erase_devreg == "True":
            devreg_offset = "0x230000"
            cmd = "sf erase 0x230000 0x010000"
            log_debug("Erase devreg data ...")
            log_debug(cmd)
            self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(60, "Erased: OK")

        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action="reset")

    def update_emmc(self):
        cmd = "imgaddr={}; source $imgaddr:script; sf probe; sf erase 0x110000 +0x10000".format(self.mem_addr)
        log_debug(cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(60, "Flashing u-boot")
        self.pexp.expect_only(60, "Flashing rootfs_data")
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action="reset")

    def stop_uboot(self, timeout=60):
        self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot|Autobooting in", 
                                action= "\x1b\x1b")

    def transfer_img(self, address, filename):
        img = os.path.join(self.image, filename)
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpb {} {}".format(address, img))
        self.pexp.expect_only(60, "Bytes transferred = {}".format(img_size))

    def t1_image_check(self):
        self.pexp.expect_only(30, "Starting kernel")
        self.pexp.expect_lnxcmd(120, "UBNT BSP INIT", "dmesg -n1", "#", retry=0)

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
        # U6-Enterprise-IW , default Eth0 is not work but Eth1 work
        if self.board_id == "a656":
            self.set_ub_net(self.premac, ethact="eth1")
        elif  self.board_id == "a667":
            comma_mac = self.mac_format_str2comma(self.mac)
            self.set_ub_net(comma_mac, ethact="eth1")
        else:
            self.set_ub_net(self.premac)

        self.is_network_alive_in_uboot()
        msg(20, 'Network in uboot works ...')
        self.transfer_img(address=self.mem_addr, filename=self.nor_bin)
        msg(30, 'Transfer NOR done')
        self.update_nor()
        msg(40, 'Update NOR done ...')

        # Update EMMC(kernel)
        self.stop_uboot()
        msg(50, 'Stop in uboot...')
        # U6-Enterprise-IW , default Eth0 is not work but Eth1 work
        if self.board_id == "a656":
            self.set_ub_net(self.premac, ethact="eth1")
        elif  self.board_id == "a667":
            comma_mac = self.mac_format_str2comma(self.mac)
            self.set_ub_net(comma_mac, ethact="eth1")
        else:
            self.set_ub_net(self.premac)

        self.is_network_alive_in_uboot()
        msg(60, 'Network in uboot works ...')
        self.transfer_img(address=self.mem_addr, filename=self.emmc_img)
        msg(70, 'Transfer EMMC done')
        self.update_emmc()
        msg(80, 'Update EMMC done ...')

        # Check if we are in T1 image
        self.t1_image_check()
        msg(90, 'Check T1 image done ...')

        msg(100, "Back to T1 has completed")
        self.close_fcd()

def main():
    u6_ipq5018_mfg_general = U6IPQ5018MFGGeneral()
    u6_ipq5018_mfg_general.run()

if __name__ == "__main__":
    main()
