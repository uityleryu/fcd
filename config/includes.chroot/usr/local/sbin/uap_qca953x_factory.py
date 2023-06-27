#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os

class UAP_QCA953X_Factory(ScriptBase):
    def __init__(self):
        super(UAP_QCA953X_Factory, self).__init__() 
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        self.uappaddr = "0x80200020"
        self.uappext_printenv = 'go {} uprintenv'.format(self.uappaddr)
        self.uappext_saveenv = "go {} usaveenv".format(self.uappaddr)
        self.uappext_setenv = "go {} usetenv".format(self.uappaddr)
        self.uappext = "go {}".format(self.uappaddr)
        self.fwimg = self.board_id + "-fw.bin"
        self.user = "ubnt"
        self.passwd = "ubnt"
        self.bootloader_prompt = "ar7240>"
        self.devreg_host = "-h devreg-prod.ubnt.com"
        self.linux_prompt= '#'
        self.helperexe = "helper_ARxxxx_release"
        self.helper_path = "lvdu_4_24"
        self.bomrev = "113-" + self.bom_rev
        self.regdmn = '0000'
        self.devregpart = "/dev/mtdblock10"
        self.product_class = "radio"
        self.dl_addr = '80800000'

        # number of Ethernet
        self.macnum = {
            'ec3d': "2",  
            'ec41': "2"  
        }

        # number of Ethernet
        self.ethnum = {
            'ec3d': "1",
            'ec41': "1"
        }

        # number of WiFi
        self.wifinum = {
            'ec3d': "1",
            'ec41': "1"
        }

        # number of Bluetooth
        self.btnum = {
            'ec3d': "0",
            'ec41': "0"
        }

        # ethernet interface 
        self.netif = {
            'ec3d': "eth0",
            'ec41': "eth0"
        }

        self.devnetmeta = {
            'ethnum'          : self.ethnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }
        
        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        self.UPDATE_UBOOT          = True
        self.BOOT_RECOVERY_IMAGE   = True 
        self.INIT_RECOVERY_IMAGE   = True 
        self.NEED_DROPBEAR         = True 
        self.PROVISION_ENABLE      = True 
        self.DOHELPER_ENABLE       = True 
        self.REGISTER_ENABLE       = True 
        self.FWUPDATE_ENABLE       = True
        self.DATAVERIFY_ENABLE     = True
        self.LCM_CHECK_ENABLE      = True

    def stop_uboot(self):
        log_debug("Stopping U-boot")
        self.pexp.expect_action(60, "Hit any key to stop autoboot", "\x1b")
        log_debug("Stopped U-boot @ {}".format(self.bootloader_prompt))
        self.pexp.expect_action(5, self.bootloader_prompt, "")
        time.sleep(1)
        log_debug("uappext: {}".format(self.uappext))

        if str(self.uappext) != "":
            uboot_env_fixed = "uboot env fix. Clearing u-boot env and resetting the board.." 
            ubnt_app_init = "UBNT application initialized"
            expect_list = [uboot_env_fixed, ubnt_app_init]
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, '{} uappinit'.format(self.uappext))
            index = self.pexp.expect_get_index(timeout=30, exptxt=expect_list)
            if index == self.pexp.TIMEOUT:
                error_critical('UBNT Application failed to initialize!')
            elif index == 0:
                log_debug('uboot env fixed, rebooting...')
                self.stop_uboot()
            elif index == 1:
                self.pexp.expect_action(5, self.bootloader_prompt, "")

    def debug_eeprom(self):
        log_debug('Logging "hexdump /dev/mtdblock10 | head -10"')
        self.pexp.expect_lnxcmd(10, self.linux_prompt, 'hexdump /dev/mtdblock10 | head -10')

    def handle_uboot(self):
        msg(5, "Got INTO U-boot uappext {}".format(self.uappext))
        time.sleep(1)
        self.pexp.expect_action(30, self.bootloader_prompt,"")
        if self.uappext != "":
            msg(8, 'running uappinit')
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, '{} uappinit'.format(self.uappext), post_exp="UBNT application initialized")

        time.sleep(2)

        if self.uappext != "":
            msg(9, "running uclearenv")
            self.pexp.expect_ubcmd(20, self.bootloader_prompt, "{} uclearenv".format(self.uappext), post_exp='done')
        else: 
            msg(9, "erasing uboot-env")
            self.pexp.expect_ubcmd(20, self.bootloader_prompt, "erase 1:4", post_exp='done')
            
        time.sleep(1)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, 'reset')
        
    def set_network_env_in_uboot(self):
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.is_network_alive_in_uboot()

    def fwupdate(self):
        log_debug("Firmware is {}".format(self.fwimg))

        if self.uappext != '':
            self.pexp.expect_action(30, self.bootloader_prompt, "setenv do_urescue TRUE;urescue -u -e")
        else:
            self.pexp.expect_action(30, self.bootloader_prompt, "urescue -f -e")
            
        self.pexp.expect_only(60, "Waiting for connection")
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
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "TFTP Transfer Complete")
        log_debug('Download complete')
        
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "{} uwrite -f".format(self.uappext))
        self.pexp.expect_only(30, "Firmware Version:")
        msg(10, "Firmware loaded")
        self.pexp.expect_only(15, "Copying partition 'u-boot' to flash memory:")
        msg(15, "Flashing firmware...")
        self.pexp.expect_only(15, "Copying partition 'kernel' to flash memory:")
        msg(20, "Flashing firmware...")
        self.pexp.expect_only(240, "Firmware update complete")
        msg(45, "Firmware flashed")

    def erase_linux_config(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "{} uclearcfg".format(self.uappext), post_exp=' done')

    def set_mac(self):
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "{} usetmac {}".format(self.uappext, self.mac), post_exp='Done.')
        log_debug("* MAC setting succeded *")
    
    def turn_on_console(self):
        result = self.ser.execmd_getmsg('exec /usr/local/sbin/eot_md5.sh {} {}'.format(self.mac, self.board_id), ignore=True)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "{}$uappext uappinit ; {}$uappext uttyctl free {}$result".format(self.uappext, self.uappext, result), post_exp=self.bootloader_prompt)

    def SetNetEnv(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sed -i.bak s/192.168.1.20/$ip/g /etc/udhcpc/udhcpc_eth", post_exp=self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, 'ifconfig eth0 {}'.format(self.dutip), post_exp=self.linux_prompt)
        self.is_network_alive_in_linux()

    def set_data_in_uboot(self):
        ## RUN 2, set IDs
        self.stop_uboot()
        self.unlock_uboot_flash()
        # set Board ID
        time.sleep(2)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt,"{} usetbid -f {}".format(self.uappext, self.board_id), post_exp='Done.')
        
        # set BOM Revision
        time.sleep(2)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt,"{} usetbrev {}".format(self.uappext, self.bom_rev), post_exp='Done.')
        msg(50, "Board ID/Revision set")

        # set Regulatory Domain
        time.sleep(2)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "{} usetrd {}".format(self.uappext, self.regdmn), post_exp='Done.')
        msg(55, "Regulatory Domain set")

        # erase uboot-env
        time.sleep(2)
        if self.uappext != "":
            self.pexp.expect_ubcmd(20, self.bootloader_prompt, "{} uclearenv".format(self.uappext), post_exp='done')
        else: 
            self.pexp.expect_ubcmd(20, self.bootloader_prompt, "erase 1:4", post_exp='Done.')
        
        time.sleep(2) 
        self.erase_linux_config() 
        msg(60, "Configuration erased")

        # set Ethernet mac address
        self.set_mac()
        msg(65, "MAC set")

        # reboot
        time.sleep(1)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "re")
        self.stop_uboot()

        time.sleep(1)
        self.set_network_env_in_uboot()
        self.set_rsa_dss_key()

        time.sleep(1)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "boot")

    def login_kernel(self):
        self.pexp.expect_lnxcmd(300, "Please press Enter to activate this console", "")
        self.login()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /lib/build.properties", post_exp=self.linux_prompt)

    def unlock_dd(self):
        cmds = [
            'echo 5edfacbf > /proc/gpio/.fwp',
            'echo 5edfacbf > /proc/ubnthal/.uf',
            'echo tp101 > /proc/ubnthal/.uf'
        ]
        for cmd in cmds:
            self.pexp.expect_lnxcmd(5, self.linux_prompt, cmd)
        time.sleep(1)

    def unlock_uboot_flash(self):
        cmd = 'go {} uappinit;go {} uflprot h off'.format(self.uappaddr, self.uappaddr)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")

        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno(mac) error")

        check_signed = 'grep -c flashSize /proc/ubnthal/system.info'
        log_debug('Check signed ?')
        self.pexp.expect_lnxcmd(5, self.linux_prompt, check_signed, post_exp='1')

        self.check_defult_ip_networking_shipping_fw()
        self.check_ssh_for_ftu()

    def check_defult_ip_networking_shipping_fw(self):
        self.pexp.expect_lnxcmd(15, self.linux_prompt, 'ifconfig', post_exp='192.168.1.20')
        self.is_network_alive_in_linux()

    def unlock_kernel_flash(self):
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "[ ! -f /proc/gpio/.fwp ] || echo 5edfacbf > /proc/gpio/.fwp")
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "[ ! -f /proc/ubnthal/.uf ] || echo 5edfacbf > /proc/ubnthal/.uf")
    
    def gen_and_load_key_to_dut(self, key):
        src = os.path.join(self.tftpdir, "dropbear_{}_host_key.0".format(key))
        cmd = "dropbearkey -t {} -f {}".format(key, src)
        self.cnapi.xcmd(cmd)
        
        cmd = "chmod 777 {0}".format(src)
        self.cnapi.xcmd(cmd)
        
        srcp = "dropbear_{}_host_key.0".format(key)
        dstp = os.path.join(self.dut_tmpdir, "dropbear_{}_host_key.0").format(key)
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, 'tftp {} {}'.format(self.dl_addr, srcp), 
        
        post_exp='Bytes transferred =')
        self.pexp.expect_ubcmd(16, self.bootloader_prompt, '{} usetsshkey  ${{fileaddr}} ${{filesize}}'.format(self.uappext), post_exp='Done.')
        
    def check_ssh_for_ftu(self):
        self.pexp.expect_lnxcmd(15, self.linux_prompt, 'ssh', post_exp='Version')

    def set_rsa_dss_key(self):
        self.gen_and_load_key_to_dut('rsa')
        self.gen_and_load_key_to_dut('dss')
        self.pexp.expect_ubcmd(16, self.bootloader_prompt, 'setenv fileaddr;setenv filesize')

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        self.stop_uboot()
        self.handle_uboot()

        self.stop_uboot()
        self.set_network_env_in_uboot()
        self.fwupdate()
        self.set_data_in_uboot()

        self.login_kernel()
        self.unlock_kernel_flash()
        self.SetNetEnv()
        
        if self.PROVISION_ENABLE is True:
           msg(70, "Send tools to DUT and data provision ...")
           self.copy_and_unzipping_tools_to_dut(timeout=60)

        if self.DOHELPER_ENABLE is True:
            msg(75, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()

            msg(85, "Finish doing registration ...")
            self.check_devreg_data()
            
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
        self.login_kernel()

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(95, "Succeeding in checking the devreg information ...")
        
        msg(100, "Completed with MAC0: {} ".format(self.mac)) 
        self.close_fcd()

def main():
    uap_factory_general = UAP_QCA953X_Factory()
    uap_factory_general.run()

if __name__ == "__main__":
    main()
