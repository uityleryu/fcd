#!/usr/bin/python3
import time
import os
import stat

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical


class UAPQCA9563Factory(ScriptBase):
    def __init__(self):
        super(UAPQCA9563Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-{}".format(self.bom_rev)
        self.helperexe = "helper_ARxxxx_musl"
        self.helper_path = "uap"
        self.user = "root"
        self.bootloader_prompt = "ath>"
        self.linux_prompt = "# "
        self.cmd_prefix = "go 0x80200020 "

        # For this product using radio
        self.product_class = "radio"
        self.devregpart = "/dev/mtdblock6"

        self.UPDATE_UBOOT_ENABLE = False
        if self.board_id in ["e587", "dca8"]:
            self.UPDATE_UBOOT_ENABLE = True

        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.FWUPDATE_ENABLE = True
        self.DATAVERIFY_ENABLE = True

    def enter_uboot(self):
        uboot_env_fixed = "uboot env fix. Clearing u-boot env and resetting the board.."
        ubnt_app_init = "UBNT application initialized"
        expect_list = [uboot_env_fixed, ubnt_app_init]

        self.pexp.expect_action(120, "Hit any key to", "")
        time.sleep(2)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uappinit")
        index = self.pexp.expect_get_index(timeout=30, exptxt=expect_list)
        if index == self.pexp.TIMEOUT:
            error_critical('UBNT Application failed to initialize!')
        elif index == 0:
            log_debug('uboot env fixed, rebooting...')
            self.enter_uboot()

        self.set_ub_net()
        self.is_network_alive_in_uboot(retry=10, arp_logging_en=True, del_dutip_en=True)

    def update_uboot(self):
        if self.board_id == "e587":
            tftp_upload_cmd = "tftp 0x80800000 images/{}-uboot.bin".format(self.board_id)
            erase_cmd = "erase 0x9f000000 +$filesize"
            copy_cmd = "cp.b $fileaddr 0x9f000000 $filesize"
        elif self.board_id == "dca8":
            tftp_upload_cmd = "tftp 0x81000000 images/{}-uboot.bin".format(self.board_id)
            erase_cmd = "erase 0x9f000000 +0x60000; protect off all"
            copy_cmd = "cp.b 0x81000000 0x9f000000 0x60000"
        else:
            rmsg = "Update U-Boot, system ID: {} is not supported!".format(self.board_id)
            error_critical(rmsg)

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, tftp_upload_cmd)
        self.pexp.expect_ubcmd(120, "Bytes transferred", erase_cmd)
        self.pexp.expect_ubcmd(180, "Erased", copy_cmd)
        self.pexp.expect_ubcmd(180, "done", "reset")
        self.enter_uboot()

    def update_old_art(self):
        self.set_ub_net()
        cmd = "tftp 0x81000000 images/{}-oldart.bin".format(self.board_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        cmd = "erase 0x9f000000 +0xf90000; protect off all"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "cp.b 0x81000144 0x9f000000 0xf90000"
        self.pexp.expect_ubcmd(240, self.bootloader_prompt, cmd)

        cmd = "reset"
        self.pexp.expect_ubcmd(240, self.bootloader_prompt, cmd)

    def fwupdate(self):
        # Uboot booting initial and Set IP on DUT
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
        self.pexp.expect_action(10, self.bootloader_prompt, self.cmd_prefix + "uwrite -f")
        self.pexp.expect_only(180, "U-Boot unifi")
        log_debug(msg="Firmware update complete")

        # Set MAC
        self.enter_uboot()
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

    def boot_image(self):
        # Boot into OS and enable console
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootargs 'quiet console=ttyS0,115200 init=/init nowifi'")
        self.pexp.expect_action(30, self.bootloader_prompt, "boot")
        self.login(timeout=120, press_enter=True)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1")
        self.is_network_alive_in_linux(retry=10, arp_logging_en=True, del_dutip_en=True)

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
        self.enter_uboot()
        self.boot_image()

        if self.board_id != "dca8":
            '''
                To check if the hostpad is running because it is an indirect method to check if the signed data is well stored in the
                memory. If the signed data is not correct, hostapd can't work well
            '''
            cmd = "while ! grep -q \"hostapd\" /etc/inittab; do echo 'Wait hostapd...'; sleep 1; done"
            self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt)

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
            self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
            self.pexp.expect_only(10, "systemid=" + self.board_id)
            self.pexp.expect_only(10, "serialno=" + self.mac.lower())
            self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        """
            Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")

        msg(5, "Open serial port successfully ...")

        self.enter_uboot()
        if self.UPDATE_UBOOT_ENABLE is True:
            self.update_uboot()

        if self.FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(30, "Updating FW successfully ...")
            self.boot_image()
            msg(40, "Boot into kerenl successfully ...")
            self.erase_eefiles()
            msg(45, "Erase eefiles successfully ...")

        if self.DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(50, "Do helper to get the output file to devreg server ...")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(70, "Finish doing registration ...")
            cmd = "echo 5edfacbf > /proc/ubnthal/.uf"
            self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, valid_chk=True)
            self.check_devreg_data()
            msg(80, "Finish doing signed file and EEPROM checking ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(90, "Succeeding in checking the devreg information ...")

        if self.ps_state is True:
            time.sleep(2)
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        msg(100, "Complete FCD procedure ...")
        self.close_fcd()

def main():
    uap_qca9563_factory = UAPQCA9563Factory()
    uap_qca9563_factory.run()

if __name__ == "__main__":
    main()
