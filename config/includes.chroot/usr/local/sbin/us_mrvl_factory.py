from script_base import ScriptBase
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

dummy = '*Notice* this is a dummy command for testing, please correct before release.'

class USW_MARVELL_FactoryGeneral(ScriptBase):
    CMD_PREFIX = "go $ubntaddr"

    def __init__(self):
        super(USW_MARVELL_FactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ver_extract()
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "Marvell>>"
        self.fwimg = self.board_id + "-fw.bin"

        # customize variable for different products
        self.wait_LCM_upgrade_en = {'ed41'}

        # number of Ethernet
        self.macnum = {
            'ed40': "3",  # usw-flex-xg
            'ed41': "3",  # u6-s8
        }

        # number of WiFi
        self.wifinum = {
            'ed40': "0",
            'ed41': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ed40': "0",
            'ed41': "0",
        }

        self.netif = {
            'ed40': "ifconfig eth0 ",
            'ed41': "ifconfig eth0 ",
        }

        devregpart = {
            'ed40': "/dev/mtdblock6",
            'ed41': "/dev/mtdblock6"
        }

        helper_path = {
            'ed40': "usw_flex_xg",
            'ed41': "usw_enterprise_8_poe",

        }

        helperexe = {
            'ed40': "helper_MRVL_XCAT3_release",
            'ed41': "helper_MRVL_XCAT3_release",
        }

        cfg_name = {
            'ed40': "usw-flex-xg",
            'ed41': "u6-s8",
        }

        ip_cfg = {
            'ed40': "00:50:43:05:00:01",
            'ed41': "00:50:43:08:00:01",
        }

        self.devregpart = devregpart[self.board_id]
        self.helper_path = helper_path[self.board_id]
        self.helperexe = helperexe[self.board_id]
        self.cfg_name = cfg_name[self.board_id]
        self.ip_cfg = ip_cfg[self.board_id]

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        self.UPDATE_UBOOT_ENABLE    = False
        self.BOOT_RECOVERY_IMAGE    = False
        self.PROVISION_ENABLE       = True
        self.DOHELPER_ENABLE        = True
        self.REGISTER_ENABLE        = True
        self.FWUPDATE_ENABLE        = True
        self.DATAVERIFY_ENABLE      = True
        self.CONF_ZEROIP_ENABLE     = False
        self.WAIT_LCMUPGRADE_ENABLE = True

    def stop_uboot(self, uappinit_en=False):
        log_debug("Stopping U-boot")
        self.pexp.expect_action(90, "Hit any key to stop autoboot", "\x1b")
        if uappinit_en is True:
            cmd = ' '.join([self.CMD_PREFIX,
                            "uappinit"])
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, post_exp="UBNT application initialized")

    def enable_console_in_uboot(self):
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "i2c mw 0x70 0x00 0x20")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "i2c mw 0x21 0x06 0xfc")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "run bootcmd")

    def clear_eeprom_and_config_in_uboot(self, timeout=30):
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "go $ubntaddr uclearcal -f", post_exp="Done")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "go $ubntaddr uclearcfg", post_exp="Done")

    def set_data_in_uboot(self):
        self.stop_uboot(uappinit_en=True)

        self.clear_eeprom_and_config_in_uboot()
        log_debug("Clearing EEPROM and config in U-Boot succeed")

        cmd = [
            self.CMD_PREFIX,
            "usetbid",
            self.board_id
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, post_exp="Done")
        log_debug("Board setting succeded")
        
        # self.enable_console_in_uboot()
        # for v3 for u6-s8

        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "reset")

    def upload_fw(self):
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "mini_xcat3")

        try:
            self.is_network_alive_in_uboot()
        except:
            log_error('Uboot network does not work.')
            return False

        self.pexp.expect_action(30, self.bootloader_prompt, "urescue -u")
        self.pexp.expect_only(60, "Listening for TFTP transfer on")

        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir + "/" + self.fwimg,
               self.dutip]
        cmdj = ' '.join(cmd)
        time.sleep(3)
        log_debug('FCD Host send: \n{}'.format(cmdj))
        
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            log_error("atftp failed.")
            log_error("The error message of atftp is \n{}".format(sto))
            return False

        log_debug("The logging of atftp is \n{}".format(sto))

        try:
            self.pexp.expect_only(60, "Bytes transferred = ")
        except:
            log_error('Expect "Bytes transferred =" failed.')
            return False
        
        return True

    def fwupdate(self):
        self.stop_uboot()

        msg(60, "Reboot into Uboot again for urescue")

        msg(65, "Uploading released firmware...")

        retry_cnt = 0
        while(retry_cnt <= 3):
            if (self.upload_fw() == True):
                log_debug("Uploading firmware image successfully")
                break
            else:
                log_error("Failed to upload firmware image")
                retry_cnt += 1
                log_error("FW upload retry {}".format(retry_cnt))
        else:
            error_critical("Failed to upload firmware image, after retry {} times.".format(retry_cnt - 1))

        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "go $ubntaddr uappinit")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "go $ubntaddr uwrite -f")

        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(60, "Signature Verfied, Success.")

        msg(70, "Updating released firmware...")
        self.pexp.expect_only(120, "Copying to 'kernel0' partition")
        self.pexp.expect_only(240, "done")
        self.pexp.expect_only(120, "Copying to 'kernel1' partition")
        self.pexp.expect_only(240, "done")

    def check_info(self):
        """under developing
        """
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno(mac) error")

    def wait_lcm_upgrade(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "lcm-ctrl -t dump", post_exp="version", retry=30)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "", post_exp=self.linux_prompt)

    def login_kernel(self, mode):
        if mode == "normal":
            log_debug("{} login".format(mode))
            self.login(timeout=240, press_enter=True)
        else:
            log_debug("{} login".format(mode))
            self.pexp.expect_only(200, "Starting kernel")
            time.sleep(40)

            login_retry_cnt = 0

            while login_retry_cnt < 5:
                try:
                    self.pexp.expect_lnxcmd(5, "", "", post_exp="login", retry=40)
                    self.pexp.expect_action(10, "", "ubnt")
                    self.pexp.expect_action(10, "Password:", "ubnt")
                    break
                except:
                    time.sleep(2)
                    login_retry_cnt += 1
                    log_error('Login failed, retry {}'.format(login_retry_cnt))
            else:
                error_critical('Login failed after {} retries'.format(login_retry_cnt))

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /lib/build.properties", post_exp=self.linux_prompt)

    def SetNetEnv(self):
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "killall ros && sleep 3")
        mac = str(self.dutip.strip()[-2:])
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "sed -i \"s/{}/00:50:43:05:00:{}/\" /usr/etc/{}.cfg".format(self.ip_cfg, mac, self.cfg_name))
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "appDemo -config /usr/etc/{}.cfg -daemon".format(self.cfg_name))

    def SetNetEnv_ip(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i \"/udhcpc/d\" /etc/inittab", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(timeout=5, pre_exp=self.linux_prompt, action='ifconfig', post_exp='eth0', retry=12)
        set_ip = self.netif[self.board_id] + self.dutip
        self.pexp.expect_lnxcmd(timeout=5, pre_exp=self.linux_prompt, action=set_ip, post_exp=self.linux_prompt, retry=12)

    def clear_uboot_env(self):
        self.stop_uboot()
        self.pexp.expect_action(10, self.bootloader_prompt, "env default -f -a")
        self.pexp.expect_action(10, self.bootloader_prompt, "saveenv")
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")

    def force_speed_to_1g(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "telnet 127.0.0.1 12345")
        self.pexp.expect_lnxcmd(20, "Console#", "configure")
        self.pexp.expect_lnxcmd(10, "", "interface ethernet 0/0")
        self.pexp.expect_lnxcmd(10, "", "speed 1000 mode SGMII")
        self.pexp.expect_lnxcmd(10, "", "end")
        self.pexp.expect_lnxcmd(10, "", "CLIexit")

    def is_network_alive_in_uboot(self, ipaddr=None, retry=5, timeout=5):
        is_alive = False
        if ipaddr is None:
            ipaddr = self.tftp_server

        cmd = "ping {0}".format(ipaddr)
        exp = "host {0} is alive".format(ipaddr)

        ping_retry_cnt = 0
        while ping_retry_cnt < 2:
            try:
                self.pexp.expect_ubcmd(timeout=timeout, exptxt="", action=cmd, post_exp=exp, retry=retry)
                log_debug('ping is successful, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -a')
                break
            except:
                log_error('ping is failed, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -a')
                ping_retry_cnt += 1

        else:
            error_critical('ping is failed in uboot, after {} retries.'.format(retry * (ping_retry_cnt)))

    def is_network_alive_in_linux(self, ipaddr=None, retry=5):
        if ipaddr is None:
            ipaddr = self.tftp_server

        cmd = "ifconfig; ping -c 3 {0}".format(ipaddr)
        exp = r"64 bytes from {0}".format(ipaddr)

        ping_retry_cnt = 0
        while ping_retry_cnt < 2:
            try:
                self.pexp.expect_lnxcmd(timeout=5, pre_exp=self.linux_prompt, action=cmd, post_exp=exp, retry=retry)
                log_debug('ping is successful, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -a')
                break
            except:
                log_error('ping is failed, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -a')
                ping_retry_cnt += 1
            
        else:
            error_critical('ping is failed in linux kernel, after {} retries.'.format(retry * (ping_retry_cnt)))
    
    def run(self):  
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE == True:
            pass
        if self.BOOT_RECOVERY_IMAGE == True:
            pass

        msg(5, "Set data in uboot")
        self.set_data_in_uboot()

        msg(15, "Login kernel")
        self.login_kernel("abnormal")

        # self.force_speed_to_1g() 
        # for v3 for u6-s8

        self.SetNetEnv()
        self.SetNetEnv_ip()
        self.is_network_alive_in_linux()

        msg(15, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        # reboot anyway
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot -f")

        if self.FWUPDATE_ENABLE is True:
            msg(55, "Starting firmware upgrade process...")
            self.fwupdate()
            msg(75, "Completing firmware upgrading ...")

        self.clear_uboot_env()
        self.login_kernel("abnormal")

        if self.DATAVERIFY_ENABLE is True:
            # self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id in self.wait_LCM_upgrade_en:
                msg(90, "Waiting LCM upgrading ...")
                self.wait_lcm_upgrade()

        msg(100, "Completing FCD process ...")
        self.close_fcd()

def main():
    us_factory_general = USW_MARVELL_FactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
