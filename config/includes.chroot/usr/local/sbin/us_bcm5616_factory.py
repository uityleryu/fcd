#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import os
import time

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True
WAIT_LCMUPGRADE_ENABLE = True

flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

rsa_key = "dropbear_rsa_host_key"
dss_key = "dropbear_dss_host_key"

cmd_prefix = "go $ubntaddr"

# U-boot erase start address
uberstaddr = {
    '0000': "0x1e0000",
    'eb23': "0x1e0000",
    'eb25': "0x1e0000",
    'eb26': "0x1e0000",
    'eb27': "0x1e0000",
    'eb28': "0x1e0000",
    'eb36': "0x1e0000",
    'eb37': "0x1e0000",
    'eb38': "0x1e0000",
    'eb67': "0x1e0000",
    'eb68': "0x1e0000"
}

# U-boot erase size
ubersz = {
    '0000': "0x10000",
    'eb23': "0x10000",
    'eb25': "0x10000",
    'eb26': "0x10000",
    'eb27': "0x10000",
    'eb28': "0x10000",
    'eb36': "0x10000",
    'eb37': "0x10000",
    'eb38': "0x10000",
    'eb67': "0x10000",
    'eb68': "0x10000"
}

#
bootargs = {
    '0000': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb23': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb25': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb26': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb27': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb28': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb36': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb37': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb38': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb67': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb68': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M
}

helperexes = {
    '0000': "helper_BCM5341x",
    'eb20': "helper_BCM5341x",
    'eb25': "helper_BCM5617x",
    'eb26': "helper_BCM5617x",
    'eb27': "helper_BCM5617x",
    'eb28': "helper_BCM5617x",
    'eb23': "helper_BCM5616x",
    'eb36': "helper_BCM5616x",
    'eb37': "helper_BCM5616x",
    'eb38': "helper_BCM5616x",
    'eb67': "helper_BCM5616x",
    'eb68': "helper_BCM5616x"
}


class USBCM5616FactoryGeneral(ScriptBase):
    def __init__(self):
        super(USBCM5616FactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        self.bootloader_prompt = "u-boot>"
        self.helperexe = helperexes[self.board_id]
        self.devregpart = "/dev/`awk -F: '/EEPROM/{print \$1}' /proc/mtd|sed 's~mtd~mtdblock~g'`"
        self.USGH2_SERIES = None
        self.LCM_upgrade_NOT_SUPPORT = {'eb23'}

    def stop_uboot(self, timeout=30):
        log_debug("Stopping U-boot")

        expect_cal_case1 = "Switching to RD_DATA_DELAY Step"
        expect_cal_case2 = "Validate Shmoo parameters stored in flash ..... failed"
        expect_normal = "Hit any key to stop autoboot"

        expect_list = [expect_cal_case1, expect_cal_case2, expect_normal]
        index = self.pexp.expect_get_index(timeout=60, exptxt=expect_list)
        if expect_list[index] != expect_normal:
            log_debug("Waiting for self calibration in u-boot")
            timeout = 120
            self.pexp.expect_only(timeout, "Hit any key to stop autoboot")

        log_debug("Stop u-boot")
        self.pexp.expect_action(timeout, "", "")

        # bootubnt is only For USGH2 series. ex:usw-xg
        output = self.pexp.expect_get_output("bootubnt init", self.bootloader_prompt ,10)
        if "Unknown command" in output:
            self.USGH2_SERIES = False
            self.pexp.expect_action(timeout, self.bootloader_prompt, ' '.join([cmd_prefix, "uappinit"]))
            self.pexp.expect_only(timeout, "UBNT application initialized")
        elif "UBNT application initialized" in output:
            self.USGH2_SERIES = True
            log_debug("DUT is USGH2 series")
            pass

    def update_firmware_in_uboot(self):
        """
        use urescue to update firmwre,
        after flash firmware, DU will be resetting
        """
        if self.USGH2_SERIES is True:
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="bootubnt ubntrescue;bootubnt")
        else:
            self.pexp.expect_action(timeout=10, exptxt=self.bootloader_prompt, action="setenv do_urescue TRUE; urescue -u")

        extext_list = ["TFTPServer started. Wating for tftp connection...",
                       "Listening for TFTP transfer"]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to start urescue")
        elif index == 0 or index == 1:
            log_debug(msg="TFTP is waiting for file")

        fw_path = os.path.join(self.fwdir, self.board_id+".bin")
        atftp_cmd = "atftp --option \"mode octet\" -p -l {} {}".format(fw_path, self.dutip)
        log_debug(msg="Run cmd on host:" + atftp_cmd)
        self.fcd.common.xcmd(cmd=atftp_cmd)
        if self.USGH2_SERIES is False:
            self.pexp.expect_only(timeout=60, exptxt=self.bootloader_prompt)
            self.pexp.expect_action(10, "", "\003")
            self.pexp.expect_action(10, self.bootloader_prompt,  ' '.join([cmd_prefix, "uwrite -f"]))

        self.pexp.expect_only(timeout=60, exptxt="Firmware Version:")
        log_debug("Firmware loaded")

        self.pexp.expect_only(timeout=60, exptxt="Image Signature Verfied, Success.")
        log_debug("Download image verified.")

        if self.USGH2_SERIES is False:
            index = self.pexp.expect_get_index(timeout=300, exptxt="Copying to 'kernel0' partition. Please wait... :  done")
            if index == self.pexp.TIMEOUT:
                error_critical(msg="Failed to flash kernel0.")
            index = self.pexp.expect_get_index(timeout=300, exptxt="Copying to 'kernel1' partition. Please wait... :  done")
            if index == self.pexp.TIMEOUT:
                error_critical(msg="Failed to flash kernel1.")

            msg(no=70, out="Firmware flashed on kernel0")

            index = self.pexp.expect_get_index(timeout=300, exptxt="Firmware update complete.")
            if index == self.pexp.TIMEOUT:
                error_critical(msg="Failed to flash firmware.")
        else:
            self.pexp.expect_only(120, "Updating kernel0 partition \(and skip identical blocks\)")
            self.pexp.expect_only(180, "Done")
            self.pexp.expect_only(120, "Updating kernel1 partition \(and skip identical blocks\)")
            self.pexp.expect_only(180, "Done")
            msg(no=70, out="Firmware update complete.")

        self.pexp.expect_only(timeout=150, exptxt="Starting kernel")

    def turn_on_console(self):
        cmd = [
            "setenv",
            "bootargs",
            "'" + bootargs[self.board_id] + "'",
        ]
        cmd = ' '.join(cmd)
        log_debug(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, "run bootcmd")
        self.pexp.expect_only(150, "Starting kernel")

    def set_boot_net(self):
        self.pexp.expect_action(10, self.bootloader_prompt, "mdk_drv")
        self.pexp.expect_only(150, "Found MDK device")

        self.pexp.expect_action(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_action(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.is_network_alive_in_uboot()

    def spi_clean_in_uboot(self):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string}
        """
        cmd = [
            "sf probe;",
            "sf erase",
            uberstaddr[self.board_id],
            ubersz[self.board_id]
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(30, self.bootloader_prompt, cmd)

        cmd = [
            cmd_prefix,
            "uclearcfg"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Done")
        self.pexp.expect_action(10, "", "\003")

    def set_data_in_uboot(self):
        cmd = [
            cmd_prefix,
            "usetbid",
            self.board_id
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = [
            cmd_prefix,
            "usetbrev",
            self.bom_rev
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = [
            cmd_prefix,
            "usetmac",
            self.mac
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = [
            cmd_prefix,
            "usetmac"
        ]
        cmd = ' '.join(cmd)
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt ,10)
        match = re.search(r"MAC0: (.{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2})", output)
        mac_str = ""
        if match:
            mac_str = match.group(1)
        else:
            error_critical("Found no mac info by regular expression. Please checkout output")

        cmd = [
            "setenv",
            "ethaddr",
            mac_str + ";",
            "saveenv"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "done")
        self.pexp.expect_action(10, "", "\003")
        log_debug("MAC setting succeded")

    def gen_and_upload_ssh_key(self):
        self.gen_rsa_key()
        self.gen_dss_key()

        # Upload the RSA key
        cmd = [
            "tftpboot",
            "0x01000000",
            self.rsakey
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = [
            cmd_prefix,
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
            "0x01000000",
            self.dsskey
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = [
            cmd_prefix,
            "usetsshkey",
            "$fileaddr",
            "$filesize"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")
        log_debug(msg="ssh keys uploaded successfully")

    def check_info_in_uboot(self):
        """
           check board id/ bom revision/ mac address
        """
        cmd = [
            cmd_prefix,
            "usetbid"
        ]
        cmd = ' '.join(cmd)
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(r"Board ID: (.{4})", output)
        board_id = None
        if match:
            board_id = match.group(1)
        else:
            error_critical(msg="Found no Board ID info by regular expression. Please checkout output")
        if board_id != self.board_id:
            error_critical(msg="Board ID doesn't match!")

        cmd = [
            cmd_prefix,
            "usetbrev"
        ]
        cmd = ' '.join(cmd)
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(r"BOM Rev: (\d+-\d+)", output)
        bom_rev = None
        if match:
            bom_rev = match.group(1)
        else:
            error_critical(msg="Found no BOM Revision info by regular expression. Please checkout output")
        if bom_rev != self.bom_rev:
            error_critical(msg="BOM Revision  doesn't match!")

        cmd = [
            cmd_prefix,
            "usetmac"
        ]
        cmd = ' '.join(cmd)
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(
                        r"MAC0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*MAC1: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2})",
                        output,
                        re.S)
        mac_0 = None
        mac_1 = None
        mac_base = self.mac.replace(":", "")
        mac_tmp = (int(mac_base,16)|0x020000000000)
        mac_admin = format(mac_tmp, 'x').zfill(12)

        if match:
            mac_0 = match.group(1).replace(":", "")
            mac_1 = match.group(2).replace(":", "")
        else:
            error_critical(msg="Found no mac info by regular expression. Please checkout output")

        if mac_0 != mac_base or mac_1 != mac_admin:
            error_critical(msg="MAC address doesn't match!")

    def data_provision(self):
        msg(10, "Clearing the U-Boot Environment")
        self.spi_clean_in_uboot()

        msg(15, "Board ID/Revision set")
        self.set_data_in_uboot()

        if self.USGH2_SERIES is True:
            # for mdk_drv init correctly
            self.pexp.expect_action(15, self.bootloader_prompt, "env set boardmodel unknown")
            self.pexp.expect_action(20, self.bootloader_prompt, "bootubnt")
            self.pexp.expect_only(60, "Resetting to default environment")
            self.pexp.expect_only(60, "done")
        else:
            # reset the U-boot
            self.pexp.expect_action(10, self.bootloader_prompt, "re")

        self.stop_uboot()
        self.pexp.expect_action(10, self.bootloader_prompt, "printenv")
        self.pexp.expect_action(10, self.bootloader_prompt, "saveenv")
        msg(20, "Environment Variables set")

        self.set_boot_net()
        self.gen_and_upload_ssh_key()
        msg(25, "SSH keys uploaded")

        self.check_info_in_uboot()
        msg(30, "Board ID/MAC address checked")

    def prepare_server_need_files(self):
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "cd /tmp")
        sstr = [
            self.helperexe,
            "-q",
            "-c product_class=bcmswitch",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin,
            ">",
            self.eetxt
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_action(10, self.linux_prompt, sstr)
        time.sleep(2)

        sstr = [
            "tar",
            "zcf",
            self.eetgz,
            self.eebin,
            self.eetxt
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_action(10, self.linux_prompt, sstr)
        self.pexp.expect_action(10, self.linux_prompt, "")

        log_debug("Sending EEPROM file to host")

        self.zmodem_recv_from_dut(file=self.eetgz, dest_path=self.tftpdir, retry=10)

        sstr = [
            "tar",
            "zxf " + self.eetgz_path
        ]
        sstr = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz + " files successfully")

    def check_board_signed(self):
        cmd = r"grep flashSize /proc/ubnthal/system.info"
        self.pexp.expect_action(10, "", "")
        output = self.pexp.expect_get_output(cmd, self.linux_prompt, 10)
        match = re.search(r'flashSize=', output)
        if not match:
            error_critical(msg="Device Registration check failed!")

        cmd = r"grep qrid /proc/ubnthal/system.info"
        output = self.pexp.expect_get_output(cmd, self.linux_prompt, 10)
        match = re.search(r'qrid=(.*)', output)
        if match:
            if match.group(1).strip() != self.qrcode:
                error_critical(msg="QR code doesn't match!")
        else:
            error_critical(msg="Unable to get qrid!, please checkout output by grep")

    def wait_lcm_upgrade(self):
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "lcm-ctrl -t dump", post_exp="version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "", post_exp=self.linux_prompt)

    def login(self, username="ubnt", password="ubnt", timeout=10):
        """
        should be called at login console
        """
        self.pexp.expect_action(120, "Please press Enter to activate this console", "")
        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(timeout, "login:", username)
        self.pexp.expect_action(10, "Password:", password)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(1, "Waiting - PULG in the device...")

        if PROVISION_ENABLE is True:
            self.stop_uboot()
            self.data_provision()
            self.pexp.expect_action(10, "", "re")

        if DOHELPER_ENABLE is True:
            self.login()
            self.erase_eefiles()
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(zmodem=True)
            msg(50, "Finish doing signed file and EEPROM checking ...")
            self.pexp.expect_action(timeout=10, exptxt=self.linux_prompt, action="reboot")

        if FWUPDATE_ENABLE is True:
            msg(60, "Updating firmware ...")
            self.stop_uboot()
            self.set_boot_net()
            self.update_firmware_in_uboot()

        if DATAVERIFY_ENABLE is True:
            msg(70, "Checking registration ...")
            self.login()
            self.check_board_signed()
            msg(no=80, out="Device Registration check OK...")

        if WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id not in self.LCM_upgrade_NOT_SUPPORT:
                msg(90, "Waiting LCM upgrading ...")
                self.wait_lcm_upgrade()

        msg(no=100, out="Formal firmware completed with MAC0: " + self.mac)
        self.close_fcd()


def main():
    us_factory_general = USBCM5616FactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
