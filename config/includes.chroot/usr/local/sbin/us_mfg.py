#!/usr/bin/python3
import re
import sys
import os
import time
from script_base import ScriptBase
from ubntlib.Commonlib import log_debug, log_error, msg, error_critical, pcmd, xcmd, ExpttyProcess


class USMFGGeneral(ScriptBase):
    def __init__(self):
        super(USMFGGeneral, self).__init__()
    
    def uclearcfg(self):
        """
        run cmd : uclearcfg
        clear linux config data
        """
        self.pexpect_helper.proc.sendline(self.variable_helper.common_variable.cmd_prefix + "uclearcfg")
        self.pexpect_helper.expect2actu1(timeout=20, exptxt="Done.", action="")
        self.pexpect_helper.expect2actu1(timeout=20, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
        log_debug(msg="Linux configuration erased")

    def download_and_update_firmware_in_linux(self):
        """
        After update firmware, linux will be restarting
        """
        log_debug(msg="Download "+ self.variable_helper.mfg_broadcom.firmware_img + " from " + self.variable_helper.common_variable.tftp_server)
        self.pexpect_helper.proc.send('\r')
        return_code = self.pexpect_helper.expect_base(timeout=10, exptxt=r".*" + self.variable_helper.common_variable.linux_prompt, action="", end_if_timeout=False)
        if return_code == -1:
            error_critical(msg="Linux Hung!!")
        time.sleep(5)
        for retry in range(3):
            self.pexpect_helper.proc.send('cd /tmp/; tftp -r images/{0}/{1} -l fwupdate.bin -g {2}\r'
                                            .format(self.variable_helper.mfg_broadcom.board_id,
                                                    self.variable_helper.mfg_broadcom.firmware_img,
                                                    self.variable_helper.common_variable.tftp_server))
            extext_list = ["Invalid argument", 
                            r".*#"]
            (index, _) = self.pexpect_helper.expect_base(timeout=60, exptxt=extext_list, action ="", end_if_timeout=False, get_result_index=True)
            if index == -1:
                error_critical(msg="Failed to download Firmware")
            elif index == 0:
                continue
            elif index == 1:
                break
        log_debug(msg="Firmware downloaded")
        time.sleep(2)
        self.pexpect_helper.proc.sendline("syswrapper.sh upgrade2")
        return_code = self.pexpect_helper.expect_base(timeout=120, exptxt="Restarting system.", action="", end_if_timeout=False)
        if return_code == -1:
            error_critical(msg="Failed to download firmware !")
        msg(no=40, out="Firmware flashed")

    def is_network_alive(self):
        time.sleep(3)
        self.pexpect_helper.proc.sendline('\rifconfig;ping ' + self.variable_helper.common_variable.tftp_server)
        extext_list = ["ping: sendto: Network is unreachable", 
                       r"64 bytes from " + self.variable_helper.common_variable.tftp_server,
                       "host " + self.variable_helper.common_variable.tftp_server + " is alive"]
        (index, _) = self.pexpect_helper.expect_base(timeout=60, exptxt=extext_list, action ="", end_if_timeout=False, get_result_index=True)
        if index == 0 or index == -1:
            return False
        elif index == 1 or index == 2:
            return True

    def reset_and_login_linux(self):
        """
        should be called in u-boot
        after login to linux, check if network works, if not, reboot and try again
        """
        self.pexpect_helper.proc.sendline("reset")
        is_network_alive = False
        for _ in range(3):
            self.pexpect_helper.expect2actu1(timeout=200, exptxt="Please press Enter to activate this console", action="\r")
            log_debug(msg="Booted Linux")
            self.pexpect_helper.expect2actu1(timeout=10, exptxt="login:", action="")
            log_debug(msg="Got Linux login prompt")
            self.login()
            time.sleep(10)
            is_network_alive = self.is_network_alive()
            if is_network_alive is False:
                self.pexpect_helper.proc.send('\003')
                self.pexpect_helper.proc.sendline('reboot')
                continue
            else:
                break
        if is_network_alive is False:
            error_critical(msg="Network is Unreachable")
        else:
            self.pexpect_helper.proc.send('\003')
            return_code = self.pexpect_helper.expect_base(timeout=10, exptxt=r".*" + self.variable_helper.common_variable.linux_prompt, action="\r", end_if_timeout=False)
            # return_code == -1 means timeout
            if return_code == -1:
                error_critical(msg="Linux Hung!!")
            return_code = self.pexpect_helper.expect_base(timeout=10, exptxt=r".*" + self.variable_helper.common_variable.linux_prompt, action="\r", end_if_timeout=False)
            if return_code == -1:
                error_critical(msg="Linux Hung!!")

    def decide_uboot_env_mtd_memory(self):
        """
        decide by output of cmd [print mtdparts]
        Returns:
            [string, string] -- address, size
        """
        self.pexpect_helper.proc.sendline("print mtdparts")
        self.pexpect_helper.expect2actu1(timeout=10, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
        output = self.pexpect_helper.proc.before
        if self.variable_helper.mfg_broadcom.flash_mtdparts_64M in output:
            return ("0x1e0000", "0x10000") #use 64mb flash
        else:
            return ("0xc0000", "0x10000")

    def flash_firmware_no_mdk(self):
        (uboot_env_address, uboot_env_address_size) = self.decide_uboot_env_mtd_memory()
        
        log_debug(msg="Erasing uboot-env")
        self.sf_erase(address=uboot_env_address, erase_size=uboot_env_address_size)

        self.reset_and_login_linux()
        self.download_and_update_firmware_in_linux()
        self.stop_uboot()
        log_debug(msg="Flashed firmware with no mdk package and currently stopped at u-boot....")
        log_debug(msg="Initialize ubnt app by uappinit")
        self.pexpect_helper.proc.sendline(self.variable_helper.common_variable.cmd_prefix + "uappinit")
        self.pexpect_helper.expect2actu1(timeout=20, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")


    def flash_firmware_with_mdk(self): 
        """
        after flash firmware, DU will be resetting
        """
        log_debug(msg="Starting in the urescue mode to program the firmware")        
        if self.variable_helper.mfg_broadcom.is_board_id_in_group(group=self.variable_helper.mfg_broadcom.usw_group_1):
            time.sleep(1)
            self.pexpect_helper.proc.sendline("mdk_drv")
            self.pexpect_helper.expect2actu1(timeout=30, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
            time.sleep(3)

        setenv_cmd = 'setenv ethaddr {0}; setenv serverip {1}; setenv ipaddr {2}'.format(self.variable_helper.mfg_broadcom.fake_mac, 
                                                                                         self.variable_helper.common_variable.tftp_server,
                                                                                         self.variable_helper.mfg_broadcom.ip)
        self.pexpect_helper.proc.sendline(setenv_cmd)
        if self.is_network_alive() is False:
            error_critical(msg="Can't ping the FCD server !")
        self.pexpect_helper.proc.sendline("urescue -u")
        extext_list = ["TFTPServer started. Wating for tftp connection...", 
                       "Listening for TFTP transfer"]
        (index, _) = self.pexpect_helper.expect_base(timeout=60, exptxt=extext_list, action ="", end_if_timeout=False, get_result_index=True)
        if index == -1:
            error_critical(msg="Failed to start urescue")
        elif index == 0 or index == 1:
            log_debug(msg="TFTP is waiting for file")
        atftp_cmd = "atftp --option \"mode octet\" -p -l /tftpboot/images/{0}/{1} {2}".format(self.variable_helper.mfg_broadcom.board_id,
                                                                                              self.variable_helper.mfg_broadcom.firmware_img,
                                                                                              self.variable_helper.mfg_broadcom.ip)
        msg(no=70, out="DUT is requesting the firmware from FCD server") 
        log_debug(msg="Run cmd on host:"+ atftp_cmd)
        xcmd(cmd=atftp_cmd)
        self.pexpect_helper.expect2actu1(timeout=150, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
        log_debug(msg="FCD completed the firmware uploading")
        self.uclearcfg()
        msg(no=80, out="DUT completed erasing the calibration data")
        
        self.pexpect_helper.proc.sendline(self.variable_helper.common_variable.cmd_prefix + "uwrite -f")
        self.pexpect_helper.expect2actu1(timeout=20, exptxt="Firmware Version:", action="")
        log_debug(msg="DUT finds the firmware version")
        (index, _) = self.pexpect_helper.expect_base(timeout=300, exptxt="Copying to 'kernel0' partition. Please wait... :  done", action ="", end_if_timeout=False, get_result_index=True)
        if index == -1:
            error_critical(msg="Failed to flash firmware.")
        log_debug(msg="DUT starts to program the firmware to flash")
        (index, _) = self.pexpect_helper.expect_base(timeout=200, exptxt="Firmware update complete.", action ="", end_if_timeout=False, get_result_index=True)
        if index == -1:
            error_critical(msg="Failed to flash firmware.")
        log_debug(msg="DUT completed programming the firmware into flash, will be rebooting")

        self.pexpect_helper.expect2actu1(timeout=120, exptxt="Verifying Checksum ... OK", action="")


    def run(self):
        """
        Main procudure of back to ART
        """
        self.config_stty(self.variable_helper.mfg_broadcom.dev)
        self.print_current_fcd_version(file=filepath)

        #Connect into DU using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.variable_helper.mfg_broadcom.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_helper = ExpttyProcess(self.variable_helper.mfg_broadcom.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_helper=pexpect_helper)
        time.sleep(1)
        
        self.pexpect_helper.proc.send('\003')
        self.pexpect_helper.proc.send('\r')
        msg(no=1, out="Waiting - PULG in the device...")
        
        self.stop_uboot()
        msg(no=5, out="Go into U-boot")

        log_debug(msg="Initialize ubnt app by uappinit")
        self.pexpect_helper.proc.sendline(self.variable_helper.common_variable.cmd_prefix + "uappinit")
        self.pexpect_helper.expect2actu1(timeout=20, exptxt=self.variable_helper.common_variable.bootloader_prompt, action="")
        
        if self.is_mdk_exist_in_uboot() is True:
            log_debug(msg="There is MDK available")
            self.flash_firmware_with_mdk()
        else:
            log_debug(msg="There isn't MDK available")
            self.flash_firmware_no_mdk()
            self.flash_firmware_with_mdk()

        msg(no=100, out="Back to ART has completed")  


def main():
    if len(sys.argv) < 7: # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        us_mfg_general = USMFGGeneral()
        us_mfg_general.run()

main()

