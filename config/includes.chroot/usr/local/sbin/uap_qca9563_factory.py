#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True

class UAPQCA9563Factory(ScriptBase):
    def __init__(self):
        super(UAPQCA9563Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.helperexe = "helper_ARxxxx_musl"
        self.helper_path = "uap"
        self.user = "root"
        self.bootloader_prompt = "ath>"
        self.linux_prompt = "# "
        self.cmd_prefix = "go 0x80200020 "
        self.product_class = "radio"  # For this product using radio
        self.devregpart = "/dev/mtdblock6"

    def enter_uboot(self, boot_only = False):
        uboot_env_fixed = "uboot env fix. Clearing u-boot env and resetting the board.."
        ubnt_app_init = "UBNT application initialized"
        expect_list = [uboot_env_fixed, ubnt_app_init]

        self.pexp.expect_action(120, "Hit any key to", "")
        time.sleep(2)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix+ "uappinit" )
        index = self.pexp.expect_get_index(timeout=30, exptxt=expect_list)
        if index == self.pexp.TIMEOUT:
            error_critical('UBNT Application failed to initialize!')
        elif index == 0:
            log_debug('uboot env fixed, rebooting...')
            self.enter_uboot()
 
        if boot_only is False:
            self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
            self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
            self.pexp.expect_lnxcmd(10, self.bootloader_prompt,  "ping " + self.tftp_server, "host " + self.tftp_server + " is alive",  retry=5 )

    def fwupdate(self):
        # Uboot booting initial and Set IP on DUT
        self.enter_uboot(boot_only = True)
        self.pexp.expect_action(10, self.bootloader_prompt, "{} uclearenv".format(self.cmd_prefix))
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")
        self.enter_uboot()
        self.pexp.expect_action(50, self.bootloader_prompt, "setenv do_urescue TRUE; urescue -u -e")
        time.sleep(2)

        # TFTP bin from TestServer
        fw_path = os.path.join(self.fwdir, self.board_id + "-fw.bin")
        log_debug(msg="firmware path:" + fw_path)
        atftp_cmd = 'exec atftp --option "mode octet" -p -l {} {}'.format(fw_path, self.dutip)
        log_debug(msg="Run cmd on host:" + atftp_cmd)
        self.fcd.common.xcmd(cmd=atftp_cmd)

        # Check Bin from DUT
        self.pexp.expect_only(120, "Bytes transferred")
        log_debug(msg="TFTP Finished")
        self.pexp.expect_action(10, self.bootloader_prompt, self.cmd_prefix+ "uwrite -f" )
        self.pexp.expect_only(180, "U-Boot unifi")
        log_debug(msg="Firmware update complete")

        # Set MAC
        self.enter_uboot(boot_only = True)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid -f " + self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev " + self.bom_rev)
        # It seems not working at all, the region domain came from calibration area
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd " + self.region)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearenv")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearcfg")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac " + self.mac)
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

        # Check Info
        self.enter_uboot()
        self.gen_and_upload_ssh_key()
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid")
        self.pexp.expect_only(15, self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev")
        self.pexp.expect_only(15, self.bom_rev)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd")
        self.pexp.expect_only(15, self.region)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac")
        self.pexp.expect_only(15, ':'.join(self.mac[i:i+2] for i in range(0,12,2)).upper())


    def boot_image(self, registration_mode = False):
        # Boot into OS and enable console
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootargs 'quiet console=ttyS0,115200 init=/init nowifi'" )
        self.pexp.expect_action(30, self.bootloader_prompt, "boot" )
        self.login(timeout=120, press_enter=True)
        if registration_mode is True:
    	    self.disable_hostapd()
    	    self.is_network_alive_in_linux()

    def gen_and_upload_ssh_key(self):
        self.gen_rsa_key()
        self.gen_dss_key()

        # Upload the RSA key
        cmd = [
            "tftpboot",
            "0x80800000",
            self.rsakey
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = [
            self.cmd_prefix,
            "usetsshkey",
            "$fileaddr",
            "$filesize"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")

        # Upload the DSS key
        cmd = [
            "tftpboot",
            "0x80800000",
            self.dsskey
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = [
            self.cmd_prefix,
            "usetsshkey",
            "$fileaddr",
            "$filesize"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")
        log_debug(msg="ssh keys uploaded successfully")


    def check_info(self):
        self.pexp.expect_action(10, self.linux_prompt, "reboot -f")
        self.enter_uboot(boot_only = True)
        self.boot_image(registration_mode = False)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if FWUPDATE_ENABLE is True:
            self.erase_eefiles()
            msg(10, "Erase eefiles successfully ...")
            self.fwupdate()
            msg(30, "Updating FW successfully ...")
            self.boot_image(registration_mode = True)
            msg(40, "Boot into kerenl successfully ...")

        if DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(50, "Do helper to get the output file to devreg server ...")
        if REGISTER_ENABLE is True:
            self.registration()
            msg(70, "Finish doing registration ...")
            self.check_devreg_data()
            msg(80, "Finish doing signed file and EEPROM checking ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(90, "Succeeding in checking the devrenformation ...")

        msg(100, "Complete FCD procedure ...")
        self.close_fcd()

def main():
    uap_qca9563_factory = UAPQCA9563Factory()
    uap_qca9563_factory.run()

if __name__ == "__main__":
    main()
