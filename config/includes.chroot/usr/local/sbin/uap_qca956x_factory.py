#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
This back to MFG script is for ULTE-PRO, ULTE-PRO-US, ULTE-PRO-US
'''


class UAPQCA956xFactory(ScriptBase):
    def __init__(self):
        super(UAPQCA956xFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "ath>"
        self.linux_prompt = "# "
        self.cmd_prefix = "go 0x80200020 "
        self.product_class = "radio"  # For this product using radio

        devregpart = {
            'e611': "/dev/mtdblock5",
            'e612': "/dev/mtdblock5",
            'e613': "/dev/mtdblock5",
        }

        self.devregpart = devregpart[self.board_id]

        # helper path
        helppth = {
            'e611': "ulte_pro",
            'e612': "ulte_pro",
            'e613': "ulte_pro",
        }
        self.helper_path = helppth[self.board_id]

        self.helperexe = "helper_ARxxxx_musl"

        self.UPDATE_UBOOT          = True
        self.FWUPDATE_ENABLE       = True
        self.BOOT_RECOVERY_IMAGE   = False
        self.INIT_RECOVERY_IMAGE   = False
        self.PROVISION_ENABLE      = True
        self.DOHELPER_ENABLE       = True
        self.REGISTER_ENABLE       = True
        self.DATAVERIFY_ENABLE     = True
        self.SSH_ENABLE            = True

    def enter_uboot(self, init_uapp=False):
        self.pexp.expect_action(90, "Hit any key to stop autoboot", "\033")
        time.sleep(2)

        if init_uapp is True:
            log_debug(msg="Init uapp")
            # Init uapp. DUT will reset after init

            uboot_env_fixed = "uboot env fix. Clearing u-boot env and resetting the board.."
            reset_auto = "Resetting"
            ubnt_app_init = "UBNT application initialized"
            expect_list = [uboot_env_fixed, reset_auto, ubnt_app_init]

            self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uappinit")
            index = self.pexp.expect_get_index(timeout=30, exptxt=expect_list)
            if index == self.pexp.TIMEOUT:
                error_critical('UBNT Application failed to initialize!')
            elif index == 0:
                log_debug('uboot env fixed, rebooting...')
                self.enter_uboot(init_uapp=True)
            elif index == 1:
                log_debug('DUT is resetting automatically')
                self.enter_uboot(init_uapp=True)

        self.set_net_uboot()

    def set_net_uboot(self):
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.is_network_alive_in_uboot()

    def update_uboot(self):
        uboot_path = os.path.join(self.fwdir, self.board_id + "-uboot.bin")
        log_debug(msg="uboot bin path:" + uboot_path)

        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootfile {}".format(uboot_path))
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "tftpboot 0x80800000", "Bytes transferred")

        # erase and write flash
        self.pexp.expect_action(30, self.bootloader_prompt, 'erase 0x9f000000 +$filesize')
        self.pexp.expect_action(60, self.bootloader_prompt, 'cp.b  $fileaddr 0x9f000000 $filesize')
        self.pexp.expect_only(60, "done")

    def turn_on_console(self):
        # Boot into OS and enable console
        log_debug(msg="Turn on console")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootargs 'quiet console=ttyS0,115200 init=/init nowifi'")

    def fwupdate(self):
        # TFTP bin from TestServer
        fw_path = os.path.join(self.fwdir, self.board_id + ".bin")
        log_debug(msg="firmware path:" + fw_path)

        self.pexp.expect_action(30, self.bootloader_prompt, "setenv do_urescue TRUE;urescue -u -e")
        self.pexp.expect_only(30, "Waiting for connection")

        cmd = ["atftp",
               '--option "mode octet"',
               "-p",
               "-l",
               fw_path,
               self.dutip]
        cmdj = ' '.join(cmd)

        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(120, "Bytes transferred")
        log_debug(msg="TFTP Finished")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uwrite -f")
        self.pexp.expect_only(180, "U-Boot unifi")
        log_debug(msg="Firmware update complete")

    def set_eeprom_info(self):
        log_debug(msg="Set Board ID:" + self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid -f " + self.board_id)
        self.pexp.expect_only(10, 'Done')

        log_debug(msg="Set BOM rev:" + self.bom_rev)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev " + self.bom_rev)
        self.pexp.expect_only(10, 'Done')

        # DUT must have been calibrated otherwise usetrd be failed
        log_debug(msg="Set Regulatory Domain:" + self.region)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd " + self.region)
        self.pexp.expect_only(10, 'Done')

        log_debug(msg="Set MAC:" + self.mac)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac " + self.mac)
        self.pexp.expect_only(10, 'Done')

        log_debug(msg="Clear uboot env")
        # FIXME: Ansis is fixing bug
        # self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearenv")
        # self.pexp.expect_only(30, 'done')
        # self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearcfg")
        # self.pexp.expect_only(30, 'done')

        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uprintenv")
        # self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usaveenv")

    def check_eeprom_info(self):
        log_debug(msg="Check eeprom info")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid")
        self.pexp.expect_only(15, self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev")
        self.pexp.expect_only(15, self.bom_rev)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd")
        self.pexp.expect_only(15, self.region)

        # FIXME: check mac or not
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac")

    def login_kernel(self):
        log_debug(msg="Login kernel")
        self.login(timeout=180, press_enter=True)

        time.sleep(30)  # for stable system

        # up eth anyway
        self.pexp.expect_lnxcmd(10, "", "")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig br0 up")

        self.is_network_alive_in_linux(retry=30)

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
        log_debug(msg="ssh keys uploaded successfully")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, "", "")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())

    def enable_burnin(self):
        srcp = os.path.join(self.tools, self.helper_path, "burnin.cfg")
        dstp = os.path.join(self.dut_tmpdir, "system.cfg")
        self.tftp_get(remote=srcp, local=dstp, timeout=15)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cfgmtd -w -p /etc/ && killall -9 mcad && /etc/rc.d/rc restart")
        log_debug(msg="Waiting for 30 secs")
        time.sleep(30)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, 'grep burnin /tmp/system.cfg', post_exp='enabled', retry=30)

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT is True:
            msg(10, "Updating uboot...")
            self.enter_uboot(init_uapp=True)
            self.update_uboot()
            self.pexp.expect_action(60, self.bootloader_prompt, 'reset')

        if self.FWUPDATE_ENABLE is True:
            msg(20, "Updating firmware ...")
            self.enter_uboot(init_uapp=True)
            self.fwupdate()

        if self.PROVISION_ENABLE is True:
            msg(30, "Setting EEPROM ...")
            self.enter_uboot(init_uapp=True)
            self.set_eeprom_info()
            self.pexp.expect_action(30, self.bootloader_prompt, "reset")

            msg(35, "Checking EEPROM ...")
            self.enter_uboot(init_uapp=True)
            self.check_eeprom_info()

            msg(40, "Uploading ssh keys ...")
            self.gen_and_upload_ssh_key()
            self.pexp.expect_action(30, self.bootloader_prompt, "reset")

            msg(50, "Booting image ...")
            self.enter_uboot(init_uapp=False)
            self.turn_on_console()
            self.pexp.expect_action(30, self.bootloader_prompt, "boot")
            self.login_kernel()

        if self.DOHELPER_ENABLE is True:
            msg(55, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            msg(60, "Doing registration ...")
            self.registration()
            msg(65, "Checking signed file and EEPROM ...")
            self.check_devreg_data()

        if self.DATAVERIFY_ENABLE is True:
            msg(70, "Rebooting DUT ...")
            self.pexp.expect_lnxcmd(10, "", "reboot -f")
            self.enter_uboot(init_uapp=False)
            self.turn_on_console()
            self.pexp.expect_action(30, self.bootloader_prompt, "boot")
            msg(80, "Checking the devrenformation ...")
            self.login_kernel()
            self.check_info()
            self.enable_burnin()

        msg(100, "Completed FCD process ...")

        self.close_fcd()


def main():
    uap_qca956x_factory = UAPQCA956xFactory()
    uap_qca956x_factory.run()


if __name__ == "__main__":
    main()
