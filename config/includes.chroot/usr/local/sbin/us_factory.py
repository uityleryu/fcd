#!/usr/bin/python3
import re
import sys
import os
import time
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

#launched with params: boardid=eb23; mac=b4fbe451f2ba; passphrase=4w3IYmVMHKzj; keydir=/media/usbdisk/keys; dev=ttyUSB1; idx=1; tftpserver=192.168.1.19; bomrev=13-02604-20; qrcode=mYvJIK ; qrhex=6d59764a494b


class USFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USFactoryGeneral, self).__init__()
    
    def sf_erase(self, address, erase_size):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string} 
        """
        log_debug(msg="Initializing sf => sf probe")
        self.pexp.expect_action(timeout=10, exptxt="", action="sf probe")
        self.pexp.expect_only(timeout=20, exptxt=self.variable.common.bootloader_prompt)

        earse_cmd = "sf erase " + address + " " +erase_size
        log_debug(msg="run cmd " + earse_cmd)
        self.pexp.expect_action(timeout=10, exptxt="", action=earse_cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.variable.common.bootloader_prompt)
    
    def stop_uboot(self, timeout=30):
        if self.pexp == None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot", action="")
            self.pexp.expect_action(timeout=timeout, exptxt=self.variable.common.bootloader_prompt, action="")

    def uclearcfg(self):
        """
        run cmd : uclearcfg
        clear linux config data
        """
        self.pexp.expect_action(timeout=10, exptxt="", action=self.variable.common.cmd_prefix + "uclearcfg")
        self.pexp.expect_only(timeout=20, exptxt="Done.")
        self.pexp.expect_only(timeout=20, exptxt=self.variable.common.bootloader_prompt)
        log_debug(msg="Linux configuration erased")

    def download_and_update_firmware_in_linux(self):
        """
        After update firmware, linux will be restarting
        """
        log_debug(msg="Download "+ self.variable.us_mfg.firmware_img + " from " + self.variable.common.tftp_server)
        self.pexp.proc.send('\r')
        return_code = self.pexp.expect_base(timeout=10, exptxt=r".*" + self.variable.common.linux_prompt, action="", end_if_timeout=False)
        if return_code == -1:
            error_critical(msg="Linux Hung!!")
        time.sleep(5)
        for retry in range(3):
            tftp_cmd = "cd /tmp/; tftp -r {0}/{1}/{2} -l fwupdate.bin -g {3}\r".format(
                                                    self.variable.common.firmware_dir,
                                                    self.variable.us_mfg.board_id,
                                                    self.variable.us_mfg.firmware_img,
                                                    self.variable.common.tftp_server)
            
            self.pexp.proc.send(tftp_cmd)
            extext_list = ["Invalid argument", 
                            r".*#"]
            (index, _) = self.pexp.expect_base(timeout=60, exptxt=extext_list, action ="", end_if_timeout=False, get_result_index=True)
            if index == -1:
                error_critical(msg="Failed to download Firmware")
            elif index == 0:
                continue
            elif index == 1:
                break
        log_debug(msg="Firmware downloaded")
        time.sleep(2)
        self.pexp.proc.sendline("syswrapper.sh upgrade2")
        return_code = self.pexp.expect_base(timeout=120, exptxt="Restarting system.", action="", end_if_timeout=False)
        if return_code == -1:
            error_critical(msg="Failed to download firmware !")
        msg(no=40, out="Firmware flashed")

    def is_network_alive_in_uboot(self, retry=1):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.variable.common.tftp_server)
            extext_list = ["host " + self.variable.common.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def reset_and_login_linux(self):
        """
        should be called in u-boot
        after login to linux, check if network works, if not, reboot and try again
        """
        self.pexp.proc.sendline("reset")
        is_network_alive = False
        for _ in range(3):
            self.pexp.expect2actu1(timeout=200, exptxt="Please press Enter to activate this console", action="\r")
            log_debug(msg="Booted Linux")
            self.pexp.expect2actu1(timeout=10, exptxt="login:", action="")
            log_debug(msg="Got Linux login prompt")
            self.login()
            time.sleep(10)
            is_network_alive = self.is_network_alive()
            if is_network_alive is False:
                self.pexp.proc.send('\003')
                self.pexp.proc.sendline('reboot')
                continue
            else:
                break
        if is_network_alive is False:
            error_critical(msg="Network is Unreachable")
        else:
            self.pexp.proc.send('\003')
            return_code = self.pexp.expect_base(timeout=10, exptxt=r".*" + self.variable.common.linux_prompt, action="\r", end_if_timeout=False)
            # return_code == -1 means timeout
            if return_code == -1:
                error_critical(msg="Linux Hung!!")
            return_code = self.pexp.expect_base(timeout=10, exptxt=r".*" + self.variable.common.linux_prompt, action="\r", end_if_timeout=False)
            if return_code == -1:
                error_critical(msg="Linux Hung!!")

    def decide_uboot_env_mtd_memory(self):
        """
        decide by output of cmd [print mtdparts]
        Returns:
            [string, string] -- address, size
        """
        self.pexp.expect_action(timeout=10, exptxt="", action="print mtdparts")
        self.pexp.expect_only(timeout=10, exptxt=self.variable.common.bootloader_prompt)
        output = self.pexp.proc.before
        if self.variable.us_factory.flash_mtdparts_64M in output:
            self.variable.us_factory.use_64mb_flash = 1
            return ("0x1e0000", "0x10000") #use 64mb flash
        else:
            return ("0xc0000", "0x10000")

    def set_board_info_in_uboot(self):
        cmd = "{0}usetbid {1}".format(self.variable.common.cmd_prefix, self.variable.us_factory.board_id)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=5, exptxt=self.variable.common.bootloader_prompt)

        cmd = "{0}usetbrev {1}".format(self.variable.common.cmd_prefix, self.variable.us_factory.bom_rev)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=5, exptxt=self.variable.common.bootloader_prompt)
        
        cmd = "{0}usetbrev".format(self.variable.common.cmd_prefix)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=5, exptxt=self.variable.common.bootloader_prompt)

    def set_mac_info_in_uboot(self):
        cmd = "{0}usetmac {1}".format(self.variable.common.cmd_prefix, self.variable.us_factory.mac)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=10, exptxt=self.variable.common.bootloader_prompt)

        cmd = "{0}usetmac".format(self.variable.common.cmd_prefix)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=10, exptxt=self.variable.common.bootloader_prompt)
        output = self.pexp.proc.before
        match = re.search(r"MAC0: (.{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2})", output)
        mac_str = None
        if match:
            mac_str = match.group(1)
        else:
            error_critical(msg="Found no mac info by regular expression. Please checkout output")
        cmd = "setenv ethaddr {0}; saveenv".format(mac_str)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=5, exptxt=self.variable.common.bootloader_prompt)
        log_debug(msg="MAC setting succeded")

    def set_network_env_in_uboot(self):
        is_network_alive = False
        for _ in range(3):
            if self.variable.us_factory.is_board_id_in_group(group=self.variable.us_factory.usw_group_1):
                self.pexp.expect_action(timeout=10, exptxt="", action="mdk_drv")
                self.pexp.expect_only(timeout=30, exptxt=self.variable.common.bootloader_prompt)
                time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="setenv serverip " + self.variable.common.tftp_server)
            self.pexp.expect_action(timeout=10, exptxt=self.variable.common.bootloader_prompt, action="setenv ipaddr " + self.variable.us_factory.ip)
            is_network_alive = self.is_network_alive_in_uboot()
            if is_network_alive is False:
                self.pexp.expect_action(timeout=10, exptxt="", action="re")
                self.stop_uboot(timeout=60)
            else:
                break
        if is_network_alive is False:
            error_critical(msg=self.variable.common.tftp_server + " is not reachable.")
        self.pexp.expect_action(timeout=10, exptxt="", action="")
        self.pexp.expect_only(timeout=10, exptxt=self.variable.common.bootloader_prompt)

    def setup_env(self):
        self.set_board_info_in_uboot()
        msg(no=10, out="Board ID/Revision set")
        (uboot_env_address, uboot_env_address_size) = self.decide_uboot_env_mtd_memory()
        log_debug(msg="Erasing uboot-env")
        self.sf_erase(address=uboot_env_address, erase_size=uboot_env_address_size)
        self.uclearcfg()
        msg(no=15, out="Configuration erased")
        self.set_mac_info_in_uboot()
        self.pexp.expect_action(timeout=10, exptxt="", action="re")
        self.stop_uboot()
        self.pexp.expect_action(timeout=10, exptxt="", action="printenv")
        self.pexp.expect_only(timeout=15, exptxt=self.variable.common.bootloader_prompt)
        self.pexp.expect_action(timeout=10, exptxt="", action="saveenv")
        self.pexp.expect_only(timeout=15, exptxt=self.variable.common.bootloader_prompt)
        msg(no=20, out="Environment Variables set")
        self.set_network_env_in_uboot()

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="qrcode_hex=" + self.variable.us_factory.qrcode_hex)

        cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
        [sto, _] = self.fcd.common.xcmd(cmd)
        if (int(sto.decode()) > 0):
            error_critical("Caps Lock is on")

        self.fcd.common.config_stty(self.variable.us_factory.dev)
        #self.fcd.common.print_current_fcd_version()

        #Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.variable.us_factory.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.variable.us_factory.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(no=1, out="Waiting - PULG in the device...")
        index = self.pexp.expect_get_index(timeout=60, exptxt="U-Boot")
        if index == 0:
            self.stop_uboot()
            msg(no=5, out="Go into U-boot")
            log_debug(msg="Initialize ubnt app by uappinit")
            self.pexp.expect_action(timeout=10, exptxt="", action=self.variable.common.cmd_prefix + "uappinit")
            self.pexp.expect_only(timeout=20, exptxt=self.variable.common.bootloader_prompt)
            log_debug(msg="ubntapp firmware.")
            self.setup_env()

        elif index == self.pexp.TIMEOUT:
            error_critical(msg="Device not found!")




def main():
    if len(sys.argv) < 10: # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        us_factory_general = USFactoryGeneral()
        us_factory_general.run()

main()

