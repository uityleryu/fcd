#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os
import re

'''
    ea3d: UDM-Enterprise
'''


class UDM_CN96XX_FACTORY(ScriptBase):
    def __init__(self):
        super(UDM_CN96XX_FACTORY, self).__init__()
        self.LCM_FW_Check_ENABLE = None
        self.DATAVERIFY_ENABLE = None
        self.REGISTER_ENABLE = None
        self.DOHELPER_ENABLE = None
        self.PROVISION_ENABLE = None
        self.BOOT_RECOVERY_IMAGE = None
        self.INIT_RECOVERY_IMAGE = None
        self.UPDATE_UBOOT = None

    def init_vars(self):
        # script specific vars
        self.fw_img = self.board_id + "-fw.bin"
        self.recovery_img = self.board_id + "-recovery"
        self.bootloader_img = self.board_id + "-boot.img"
        self.bootloader_prompt = ">"
        self.linux_prompt = "#"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = ""
        self.helper_path = "udm"
        self.bom_rev = "113-" + self.bom_rev
        self.username = "ui"
        self.password = "ui"

        # Base Path
        tool_name = {
            'ea3d': "udm_ent"
        }

        self.toool_folder = os.path.join(self.fcd_toolsdir, tool_name[self.board_id])

        self.eeprom_offset = {
            'ea3d': "0x00a60000"
        }

        self.eeprom_offset_2 = {
            'ea3d': "0x00a68000"
        }

        self.wsysid = {
            'ea3d': "77073dea",
        }

        # active port
        self.activeport = {
            'ea3d': "al_eth3",
        }

        # number of Ethernet
        self.ethnum = {
            'ea3d': "13",
        }

        # number of Wi-Fi
        self.wifinum = {
            'ea3d': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ea3d': "1",
        }

        # ethernet interface
        self.netif = {
            'ea3d': "br0",
        }

        # LCM
        self.lcm = {
            'ea3d': True,
        }

        # Wifi cal data setting
        self.wifical = {
            'ea3d': False,
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.INIT_RECOVERY_IMAGE = True
        self.UPDATE_UBOOT = True
        self.BOOT_RECOVERY_IMAGE = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.DATAVERIFY_ENABLE = True
        self.LCM_FW_Check_ENABLE = True

    def set_fake_eeprom(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf erase {} 0x9000".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(60, "Erased: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + "544e4255")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800000c " + self.wsysid[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "mw.l 0x08000010 " + self.wsysid[self.board_id][4:] + self.wsysid[self.board_id][:4])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf write 0x08000000 {} 0x20".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "mw.l 0x08000018 " + str(self.row_id).zfill(2) + "01ac74")  # fake mac
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800001c " + "00032cbd")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "mw.l 0x08000010 " + self.wsysid[self.board_id][4:] + self.wsysid[self.board_id][:4])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf write 0x08000000 {} 0x20".format(self.eeprom_offset_2[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)

        self.copy_file(
            source=os.path.join(self.fwdir, self.bootloader_img),
            dest=os.path.join(self.tftpdir, "boot.img")
        )
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server,
                                                                                           self.dutip))
        self.pexp.expect_action(10, self.bootloader_prompt, "run bootupd")  # tranfer img and update
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_action(60, self.bootloader_prompt, "run delenv")

    def update_recovery(self):
        time.sleep(2)

    def update_fw(self):
        time.sleep(2)

    def set_kernel_net(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip))
        self.is_network_alive_in_linux(ipaddr=self.dutip)

    def unlock_eeprom_permission(self):
        log_debug(msg="Unlock eeprom permission")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "echo 5edfacbf > /proc/ubnthal/.uf")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def check_refuse_data(self):
        print('Wait Implement')

    def check_refuse_data(self):
        print('Wait Implement')

    def write_caldata_to_flash(self):
        print('Wait Implement')

    def lcm_fw_ver_check(self):
        print('Wait Implement')

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()
        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT:
            self.set_fake_eeprom()
            self.update_uboot()
            msg(10, "Boot up to linux console and network is good ...")

        if self.BOOT_RECOVERY_IMAGE:
            self.update_recovery()
            msg(15, "Boot up to linux console and network is good ...")

        if self.INIT_RECOVERY_IMAGE:
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            msg(20, "Boot up to linux console and network is good ...")
            self.update_fw()

        if self.PROVISION_ENABLE:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.DATAVERIFY_ENABLE is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")  # for correct ubnthal
            self.login(self.username, self.password, timeout=180, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.wifical[self.board_id]:
            msg(85, "Write and check calibration data")
            self.check_refuse_data()
            self.write_caldata_to_flash()

        if self.LCM_FW_Check_ENABLE:
            if self.lcm[self.board_id]:
                msg(90, "Check LCM FW version ...")
                self.lcm_fw_ver_check()


        cmd = "systemctl is-system-running"
        ct = 0
        retry_max = 150
        while ct < retry_max:
            output = self.pexp.expect_get_output(action=cmd, prompt="" ,timeout=3)
            m_run = re.findall("running", output)
            m_degraded = re.findall("degraded", output)
            if len(m_run) == 2 :
                rmsg = "The system is running good"
                log_debug(rmsg)
                break

            time.sleep(1)
            ct += 1
        else:
            rmsg = "The system is not booting up successfully, FAIL!!"
            error_critical(rmsg)

        msg(100, "Completing FCD process ...")
        self.close_fcd()

def main():
    udm_cn96xx_factory = UDM_CN96XX_FACTORY()
    udm_cn96xx_factory.run()


if __name__ == "__main__":
    main()
