#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

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

    def enter_uboot(self, set_network = True):
        self.pexp.expect_action(300, "Hit any key to", "")
        time.sleep(2)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uappinit")
        if set_network is True:
            self.set_ub_net(self.premac)
            self.is_network_alive_in_uboot()

    def fwupdate(self):
        # Clear uboot env
        self.enter_uboot(set_network = False)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearenv")
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

        # Uboot booting initial and Set IP on DUT
        self.enter_uboot(set_network = True)
        self.pexp.expect_action(50, self.bootloader_prompt, "setenv do_urescue TRUE; urescue -u -e")
        time.sleep(10)

        # TFTP bin from TestServer
        fw_path = os.path.join(self.fwdir, self.board_id + "-fw.bin")
        log_debug(msg="firmware path:" + fw_path)
        atftp_cmd = 'exec atftp --option "mode octet" -p -l {} {}'.format(fw_path, self.dutip)
        log_debug(msg="Run cmd on host:" + atftp_cmd)
        self.fcd.common.xcmd(cmd=atftp_cmd)

        # Check Bin from DUT
        self.pexp.expect_only(120, "Bytes transferred")
        self.pexp.expect_action(100, self.bootloader_prompt, self.cmd_prefix+ "uwrite -f" )
        log_debug(msg="TFTP Finished")

        # Set MAC
        self.enter_uboot(set_network = False)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid -f " + self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev " + self.bom_rev)
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
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac " + self.mac)
        self.pexp.expect_only(15, self.mac)


    def boot_image(self, boot_only = False):
        # Boot into OS and enable console
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootargs 'quiet console=ttyS0,115200 init=/init nowifi'" )
        self.pexp.expect_action(30, self.bootloader_prompt, "boot" )
        self.login(timeout=120, press_enter=True)
        if boot_only is False:
            self.disable_hostapd()
            self.set_lnx_net(intf="br0")
            self.is_network_alive_in_linux()

    def gen_and_upload_ssh_key(self):
        self.gen_rsa_key()
        self.gen_dss_key()

        # Upload the RSA key
        cmd = [
            "tftpboot",
            "80800000",
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
        #self.pexp.expect_only(15, "Done")

        # Upload the DSS key
        cmd = [
            "tftpboot",
            "0x01000000",
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
        #self.pexp.expect_only(15, "Done")
        log_debug(msg="ssh keys uploaded successfully")


    def check_info(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
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
        self.erase_eefiles()

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(10, "Succeeding in update bin file ...")
            self.boot_image()

        if DOHELPER_ENABLE is True:
            msg(20, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(30, "Finish doing registration ...")
            self.check_devreg_data()
            msg(40, "Finish doing signed file and EEPROM checking ...")

        if DATAVERIFY_ENABLE is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot")
            self.enter_uboot(set_network = False)
            self.boot_image(boot_only = True)
            self.check_info()
            msg(50, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()

def main():
    uAPQCA9563Factory = UAPQCA9563Factory()
    uAPQCA9563Factory.run()

if __name__ == "__main__":
    main()
