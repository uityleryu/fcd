#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.ssh_client import SSHClient
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os


class UXG_AL524_FACTORY(ScriptBase):
    def __init__(self):
        super(UXG_AL524_FACTORY, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = "uxgpluspro"
        self.username = "root"
        self.password = "ubnt"
        self.linux_prompt = "#"
        self.bootloader_prompt = "ALPINE_UBNT_UXG"

        # Base path
        tool_name = {
            'ea31': "udm_pro_se"
        }

        self.tool_folder = os.path.join(self.fcd_toolsdir, tool_name[self.board_id])

        # model
        self.prodmodel = {
            'ea31': "uxgpluspro"
        }

        # switch chip
        self.swchip = {
            'ea31': "bcm50991"
        }

        # number of Ethernet
        self.ethnum = {
            'ea31': "6"
        }

        # number of WiFi
        self.wifinum = {
            'ea31': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ea31': "0"
        }

        # ethernet interface
        self.netif = {
            'ea31': "eth9"
        }

        self.infover = {
            'ea31': "Version:"
        }

        self.devnetmeta = {
            'ethnum'          : self.ethnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.UPDATE_UBOOT          = True
        self.BOOT_RECOVERY_IMAGE   = True
        self.INIT_RECOVERY_IMAGE   = True
        self.NEED_DROPBEAR         = True
        self.PROVISION_ENABLE      = True
        self.DOHELPER_ENABLE       = True
        self.REGISTER_ENABLE       = True
        self.DATAVERIFY_ENABLE     = True
        self.LCM_CHECK_ENABLE      = False

    def set_fake_info(self):
        '''
            Need to fill out several fake information in advance
        '''
        cmdset = [
            "sf probe",
            "sf read 0x08000000 0x1f0000 0x1000",
            "mw.l 0x08000000 a3d61804",
            "mw.l 0x08000004 1806ee97",
            "mw.l 0x08000008 ee97a3d6",
            "mw.l 0x0800000c 770731ea",
            "mw.l 0x08000010 050c0000",
            "mw.l 0x08008000 544E4255",
            "mw.l 0x08008010 31ea7707",
            "sf write 0x08000000 0x1f0000 0x1000",
            "sf read 0x08000000 0x1f0000 0x1000",
            "md 0x08000000 0x10"
        ]
        for cmd in cmdset:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

    def update_uboot(self):
        self.pexp.expect_action(40, "to stop", "\033\033")

        self.set_fake_info()

        cmdset = [
            "setenv tftpdir images/{}_signed_".format(self.board_id),
            "mii device al_eth1",
            self.swchip[self.board_id],
            "setenv model {}".format(self.prodmodel[self.board_id])
        ]
        for cmd in cmdset:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        self.set_ub_net()
        self.is_network_alive_in_uboot(retry=9, timeout=10, arp_logging_en=True, del_dutip_en=True)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_only(10, "bootupd done")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def boot_recovery_image(self):
        self.pexp.expect_action(60, "to stop", "\033\033")

        self.set_fake_info()

        cmdset = [
            "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server, self.dutip),
            "mii device al_eth1",
            self.swchip[self.board_id],
            "setenv model {}".format(self.prodmodel[self.board_id])
        ]
        for cmd in cmdset:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        # copy recovery image
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-recovery"),
            dest=os.path.join(self.tftpdir, "uImage")
        )

        # copy FW image
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-fw.bin"),
            dest=os.path.join(self.tftpdir, "fw-image.bin")
        )

        self.set_ub_net()
        self.is_network_alive_in_uboot(retry=9, timeout=10, arp_logging_en=True, del_dutip_en=True)

        cmd = "run bootcmdtftp"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred")

    def check_info(self):
        cmd = "cat /proc/ubnthal/system.info"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def lcm_fw_ver_check(self):
        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
                     src_file=os.path.join(self.tool_folder, "nvr-lcm-tools*"),
                     dst_file=self.dut_tmpdir)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dpkg -i /tmp/nvr-lcm-tools*")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "/usr/share/lcm-firmware/lcm-fw-info /dev/ttyACM0", post_exp="md5", retry=3)

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT is True:
            self.update_uboot()
            msg(10, "Finish boot updating")

        if self.BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()

        if self.INIT_RECOVERY_IMAGE is True:
            self.login(self.username, self.password, timeout=360, log_level_emerg=True)
            self.set_lnx_net(intf="br0")
            self.is_network_alive_in_linux(retry=9, arp_logging_en=True, del_dutip_en=True)
            cmd = "echo 5edfacbf > /proc/ubnthal/.uf"
            self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd)
            msg(15, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.DATAVERIFY_ENABLE is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")  # for correct ubnthal
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.LCM_CHECK_ENABLE is True:
            msg(85, "Check LCM FW version ...")
            self.lcm_fw_ver_check()

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    factory = UXG_AL524_FACTORY()
    factory.run()

if __name__ == "__main__":
    main()     
