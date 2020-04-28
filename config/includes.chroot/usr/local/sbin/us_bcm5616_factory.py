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

'''
    eb10: US-8-150W
    eb18: US-8-60W
    eb20: US-XG
    eb21: US-16-150W
    eb23: US-6-XG-150
    eb25: US-XG-24-550W (hold)
    eb26: US-XG-48-550W (hold)
    eb27: USW-XG-Aggregation (hold)
    eb30: US-24
    eb31: US-24-250W
    eb36: USW-PRO-24-PoE
    eb37: USW-PRO-24
    eb38: USW6-24-PoE
    eb60: US-48
    eb62: US-48-500W
    eb67: USW-PRO-48-PoE
    eb68: USW-PRO-48
'''

# U-boot erase start address
uberstaddr = {
    '0000': "0x1e0000",
    'eb10': "0xc0000",
    'eb18': "0xc0000",
    'eb20': "0x1e0000",
    'eb21': "0xc0000",
    'eb23': "0x1e0000",
    'eb25': "0x1e0000",
    'eb26': "0x1e0000",
    'eb27': "0x1e0000",
    'eb30': "0xc0000",
    'eb31': "0xc0000",
    'eb36': "0x1e0000",
    'eb37': "0x1e0000",
    'eb38': "0x1e0000",
    'eb60': "0xc0000",
    'eb62': "0xc0000",
    'eb67': "0x1e0000",
    'eb68': "0x1e0000"
}

# U-boot erase size
ubersz = {
    '0000': "0x10000",
    'eb10': "0x10000",
    'eb18': "0x10000",
    'eb20': "0x10000",
    'eb21': "0x10000",
    'eb23': "0x10000",
    'eb25': "0x10000",
    'eb26': "0x10000",
    'eb27': "0x10000",
    'eb30': "0x10000",
    'eb31': "0x10000",
    'eb36': "0x10000",
    'eb37': "0x10000",
    'eb38': "0x10000",
    'eb60': "0x10000",
    'eb62': "0x10000",
    'eb67': "0x10000",
    'eb68': "0x10000"
}

# Boot argument
bootargs = {
    '0000': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb10': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb18': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb20': "quiet console=ttyS0,115200 mem=496M " + flash_mtdparts_64M,
    'eb21': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb23': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb25': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb26': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb27': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb30': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb31': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb36': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb37': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb38': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb60': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb62': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + flash_mtdparts_32M,
    'eb67': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M,
    'eb68': "quiet console=ttyS0,115200 mem=1008M " + flash_mtdparts_64M
}

helperexes = {
    '0000': "helper_BCM5341x",
    'eb10': "helper_BCM5334x",
    'eb18': "helper_BCM5334x",
    'eb20': "helper_BCM5341x",
    'eb21': "helper_BCM5334x",
    'eb25': "helper_BCM5617x",
    'eb26': "helper_BCM5617x",
    'eb27': "helper_BCM5617x",
    'eb23': "helper_BCM5616x",
    'eb30': "helper_BCM5334x",
    'eb31': "helper_BCM5334x",
    'eb36': "helper_BCM5616x",
    'eb37': "helper_BCM5616x",
    'eb38': "helper_BCM5616x",
    'eb60': "helper_BCM5334x",
    'eb62': "helper_BCM5334x",
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
        self.isMDK = False
        self.gen1_model = [
            "0000", "eb10", "eb18", "eb20", "eb21",
            "eb30", "eb31", "eb60", "eb62"
        ]
        self.bcm5617x_model = [
            "eb25", "eb26", "eb27"
        ]

    def stop_uboot(self):
        log_debug("Stopping U-boot")
        # 1st, Check if U-Boot support MDK from the initial message of U-Boot
        self.pexp.expect_action(40, "Hit any key to stop autoboot", "")

    '''
        The U-Boot will enable the networking configuration when booting up in
        the BCM5334x series so that it needn't give an extra mdk_drv command to
        enable it.
        On the contrary, the U-Boot has to do mdk_drv for the BCM5616x series for
        the reason that it doesn't enable the networking configuration as default.
    '''
    def ub_uapp_init(self):
        if self.board_id in self.bcm5617x_model:
            cmd = "bootubnt init"
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            log_debug("DUT is BCM5617x series")
        else:
            cmd = "go $ubntaddr uappinit"
            self.pexp.expect_action(5, "", "")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            self.pexp.expect_only(10, "UBNT application initialized")

    def ub_chk_mdk_support(self):
        if self.board_id in self.gen1_model:
            log_file_path = os.path.join("/tftpboot/", "log_slot" + self.row_id + ".log")
            cmd = "cat {0}".format(log_file_path)
            [stdo, rtc] = self.fcd.common.xcmd(cmd)
            match = re.findall("Found MDK device", stdo, re.S)
            if match:
                self.isMDK = True
                log_debug("MDK is supported from U-Boot booting message")
            else:
                self.isMDK = False
                log_debug("MDK is not supported from U-Boot booting message")
        else:
            # 2nd, Check if U-Boot support MDK by using mdk_drv command
            self.isMDK = self.is_MDK_support()
            if self.isMDK is True:
                log_debug("MDK is supported by mdk_drv command")
            else:
                log_debug("MDK is not supported by mdk_drv command")

    def ub_set_net(self):
        cmd = "setenv serverip {0}".format(self.tftp_server)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)
        cmd = "setenv ipaddr {0}".format(self.dutip)
        self.pexp.expect_action(10, self.bootloader_prompt, cmd)

    def ub_netcheck(self):
        for i in range(0, 3):
            cmd = "ping {0}".format(self.tftp_server)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            exp = "host {0} is alive".format(self.tftp_server)
            rtc = self.pexp.expect_get_index(10, exp)
            if rtc > 0:
                break

    def update_firmware_in_uboot(self):
        """
        use urescue to update firmwre,
        after flash firmware, DUT will be resetting
        """
        if self.board_id in self.bcm5617x_model:
            cmd = "bootubnt ubntrescue;bootubnt"
        else:
            cmd = "setenv do_urescue TRUE; urescue -u"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        extext_list = [
            "TFTPServer started. Wating for tftp connection...",
            "Listening for TFTP transfer"
        ]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to start urescue")
        elif index == 0 or index == 1:
            log_debug(msg="TFTP is waiting for file")

        fw_path = os.path.join(self.fwdir, self.board_id+".bin")
        cmd = "atftp --option \"mode octet\" -p -l {} {}".format(fw_path, self.dutip)
        log_debug(msg="host cmd:" + cmd)
        self.fcd.common.xcmd(cmd)

        if self.board_id not in self.bcm5617x_model:
            cmd = "go $ubntaddr uwrite -f"
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.pexp.expect_only(60, "Firmware Version:")
        log_debug("Firmware loaded")

        self.pexp.expect_only(60, "Image Signature Verfied, Success.")
        log_debug("Download image verified.")

        if self.board_id not in self.bcm5617x_model:
            ker0_msg = "Copying to 'kernel0' partition. Please wait... :  done"
            ker1_msg = "Copying to 'kernel1' partition. Please wait... :  done"
        else:
            ker0_msg = r"Updating kernel0 partition \(and skip identical blocks\).*Done"
            ker1_msg = r"Updating kernel1 partition \(and skip identical blocks\).*Done"

        rt = self.pexp.expect_only(300, ker0_msg)
        if rt is False:
            error_critical(msg="Failed to flash kernel0.")
        else:
            log_debug("Completed to flash kernel0")

        rt = self.pexp.expect_only(300, ker1_msg)
        if rt is False:
            error_critical(msg="Failed to flash kernel1.")
        else:
            log_debug("Completed to flash kernel1")

        self.pexp.expect_only(150, "Starting kernel")

    def turn_on_console(self):
        cmd = "setenv bootargs '{0}'".format(bootargs[self.board_id])
        log_debug("cmd: " + cmd)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootcmd")
        self.pexp.expect_only(150, "Starting kernel")

    def ub_config_clean(self):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string}
        """
        cmd = "sf probe; sf erase {0} {1}".format(uberstaddr[self.board_id], ubersz[self.board_id])
        self.pexp.expect_action(30, self.bootloader_prompt, cmd)

        cmd = "go $ubntaddr uclearcfg"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Done")

        """
            cmd: go $ubntaddr uclearcal -f -e
            will clean all the EEPROM partition (64KB)
        """
        # cmd = "go $ubntaddr uclearcal -f -e"
        # self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        # self.pexp.expect_only(30, "Done")

    def set_data_in_uboot(self):
        cmd = "go $ubntaddr usetbid {0}".format(self.board_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = "go $ubntaddr usetbrev {0}".format(self.bom_rev)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = "go $ubntaddr usetmac {0}".format(self.mac)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Done")

        cmd = "go $ubntaddr usetmac"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt ,10)
        match = re.search(r"MAC0: (.{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2})", output)
        mac_str = ""
        if match:
            mac_str = match.group(1)
        else:
            error_critical("Found no mac info by regular expression. Please checkout output")

        cmd = "setenv ethaddr {0}; saveenv".format(mac_str)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "done")
        log_debug("MAC setting succeded")

    def gen_and_upload_ssh_key(self):
        self.gen_rsa_key()
        self.gen_dss_key()

        """
            The command: go $ubntaddr usetsshkey $fileaddr $filesize"
            will differentiate the key (RSA or DSS) we send to it.
        """
        # Upload the RSA key
        cmd = "tftpboot 0x01000000 {0}".format(self.rsakey)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = "go $ubntaddr usetsshkey $fileaddr $filesize"
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")

        # Upload the DSS key
        cmd = "tftpboot 0x01000000 {0}".format(self.dsskey)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = "go $ubntaddr usetsshkey $fileaddr $filesize"
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")

        log_debug(msg="ssh keys uploaded successfully")

    def check_info_in_uboot(self):
        """
           check board id/ bom revision/ mac address
        """
        cmd = "go $ubntaddr usetbid"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(r"Board ID: (.{4})", output)
        board_id = None
        if match:
            board_id = match.group(1)
        else:
            error_critical(msg="Found no Board ID info by regular expression. Please checkout output")
        if board_id != self.board_id:
            error_critical(msg="Board ID doesn't match!")

        cmd = "go $ubntaddr usetbrev"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(r"BOM Rev: (\d+-\d+)", output)
        bom_rev = None
        if match:
            bom_rev = match.group(1)
        else:
            error_critical(msg="Found no BOM Revision info by regular expression. Please checkout output")
        if bom_rev != self.bom_rev:
            error_critical(msg="BOM Revision  doesn't match!")

        cmd = "go $ubntaddr usetmac"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 10)
        match = re.search(
                        r"MAC0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*MAC1: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2})",
                        output,
                        re.S)
        mac_0 = None
        mac_1 = None
        mac_base = self.mac.replace(":", "")
        mac_tmp = hex(int(mac_base[0:2], 16) | 0x2)
        mac_admin = mac_tmp[2:] + mac_base[2:]

        if match:
            mac_0 = match.group(1).replace(":", "")
            mac_1 = match.group(2).replace(":", "")
        else:
            error_critical(msg="Found no mac info by regular expression. Please checkout output")

        if mac_0 != mac_base or mac_1 != mac_admin:
            error_critical(msg="MAC address doesn't match!")

    def data_provision(self):
        msg(10, "Clearing the U-Boot Environment")
        self.ub_config_clean()

        msg(15, "Board ID/Revision set")
        self.set_data_in_uboot()

        if self.board_id in self.bcm5617x_model:
            # for mdk_drv init correctly
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, "env set boardmodel unknown")
            self.pexp.expect_ubcmd(20, self.bootloader_prompt, "bootubnt")
            self.pexp.expect_only(60, "Resetting to default environment")
            self.pexp.expect_only(60, "done")
        else:
            # reset the U-boot
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
            self.stop_uboot()
            self.ub_uapp_init()

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        msg(20, "Environment Variables set")

        self.ub_set_net()
        self.ub_netcheck()
        self.gen_and_upload_ssh_key()
        msg(25, "SSH keys uploaded")

        self.check_info_in_uboot()
        msg(30, "Board ID/MAC address checked")

    def prepare_server_need_files(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cd /tmp")
        sstr = [
            self.helperexe,
            "-q",
            "-c product_class=bcmswitch",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin,
            ">",
            self.eetxt
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr)
        time.sleep(2)

        cmd = "tar zcf {0} {1} {2}".format(self.eetgz, self.eebin, self.eetxt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        log_debug("Sending EEPROM file to host")

        self.zmodem_recv_from_dut(file=self.eetgz, dest_path=self.tftpdir, retry=10)

        cmd = "tar zxf {0}".format(self.eetgz_path)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
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

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(1, "Waiting - PULG in the device...")
        self.stop_uboot()
        self.ub_chk_mdk_support()
        self.ub_uapp_init()
        if PROVISION_ENABLE is True:
            self.data_provision()
            self.pexp.expect_action(10, "", "re")

        if DOHELPER_ENABLE is True:
            self.login(timeout=210, press_enter=True)
            self.erase_eefiles()
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(zmodem=True)
            msg(50, "Finish doing signed file and EEPROM checking ...")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")

        if FWUPDATE_ENABLE is True:
            msg(60, "Updating firmware ...")
            self.stop_uboot()
            self.ub_uapp_init()
            self.ub_set_net()
            self.ub_netcheck()
            self.update_firmware_in_uboot()

        if DATAVERIFY_ENABLE is True:
            msg(70, "Checking registration ...")
            self.login(timeout=210, press_enter=True)
            self.check_board_signed()
            msg(no=80, out="Device Registration check OK...")

        if WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id not in self.gen1_model:
                msg(90, "Waiting LCM upgrading ...")
                self.wait_lcm_upgrade()

        msg(no=100, out="Formal firmware completed with MAC0: " + self.mac)
        self.close_fcd()


def main():
    us_factory_general = USBCM5616FactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
