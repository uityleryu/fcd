#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical
from PAlib.Framework.fcd.common import Common

import re
import sys
import os
import time

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
DATAVERIFY_ENABLE = True


class UFBCM5616FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UFBCM5616FactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()
        self.cn = Common()

    def init_vars(self):
        self.bootloader_prompt = "u-boot>"
        self.product_class = "bcmswitch"
        self.helperexe = "helper_BCM5617x_release"
        self.devregpart = "/dev/mtdblock6"

    def stop_uboot(self, timeout=30):
        log_debug("Stopping U-boot")
        self.pexp.expect_ubcmd(timeout, "Hit any key to stop autoboot", "  ")

    def init_ub_network(self):
        self.set_ub_net()
        self.is_network_alive_in_uboot()

    def data_provision(self):
        msg(10, "Clearing the U-Boot Environment")
        self.spi_clean_in_uboot()

        msg(15, "Board ID/Revision set")
        self.set_data_in_uboot()

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "re")

        self.stop_uboot()
        self.init_ub_network()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
        msg(20, "Environment Variables set")

        self.check_info_in_uboot()
        msg(30, "Board ID/MAC address checked")

    def spi_clean_in_uboot(self):
        cmd = "bootubnt init"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        cmd = "sf probe"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        cmd = "go $ubntaddr uclearcfg"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, "Done")

    def set_mac_in_uboot(self):
        cmd = "bootubnt init"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        cmd = "go $ubntaddr usetmac {}".format(self.mac)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, "Done")

        cmd = "go $ubntaddr usetmac"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 1.5)
        pattern = r"MAC0: ((?:[0-9a-fA-F]:?){12})"
        m_mac0 = re.findall(pattern, output)
        if m_mac0:
            if self.mac == m_mac0[0].replace(":", ""):
                log_debug("The MAC0 comparision is correct")
            else:
                error_critical("The MAC0 comparision is incorrect")

        else:
            error_critical("Found no mac info by regular expression. Please checkout output")

        cmd = "setenv ethaddr {}".format(m_mac0[0])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        log_debug("MAC setting succeded")

    def set_data_in_uboot(self):
        cmd = "go $ubntaddr usetbid {}".format(self.board_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, "Done")

        cmd = "go $ubntaddr usetbrev {}".format(self.bom_rev)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, "Done")

    def check_info_in_uboot(self):
        '''
           check board id/ bom revision/ mac address
        '''
        cmd = "go $ubntaddr usetbid"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 1.5)
        match = re.search(r"Board ID: (.{4})", output)
        board_id = None
        if match:
            board_id = match.group(1)
        else:
            error_critical(msg="Found no Board ID info by regular expression. Please checkout output")
        if board_id != self.board_id:
            error_critical(msg="Board ID doesn't match!")

        cmd = "go $ubntaddr usetbrev"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 1.5)
        match = re.search(r"BOM Rev: (\d+-\d+)", output)
        bom_rev = None
        if match:
            bom_rev = match.group(1)
        else:
            error_critical(msg="Found no BOM Revision info by regular expression. Please checkout output")
        if bom_rev != self.bom_rev:
            error_critical(msg="BOM Revision  doesn't match!")

        cmd = "go $ubntaddr usetmac"
        output = self.pexp.expect_get_output(cmd, self.bootloader_prompt, 1.5)
        pattern = r"(?:[0-9a-f]:?){12}"
        m_macs = re.findall(pattern, output)
        mac_base = self.mac.replace(":", "")
        mac_tmp = (int(mac_base, 16)|0x020000000000)
        mac_admin = format(mac_tmp, 'x').zfill(12)
        if m_macs:
            mac_0 = m_macs[0].replace(":", "")
            mac_1 = m_macs[1].replace(":", "")
        else:
            error_critical(msg="Found no mac info by regular expression. Please checkout output")

        if mac_0 != mac_base or mac_1 != mac_admin:
            error_critical(msg="MAC address doesn't match!")

    def gen_and_upload_ssh_key(self):
        self.gen_rsa_key()
        self.gen_dss_key()

        # Upload the RSA key
        cmd = "tftpboot 0x01000000 {}".format(self.rsakey)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = "go $ubntaddr usetsshkey $fileaddr $filesize"
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")

        # Upload the DSS key
        cmd = "tftpboot 0x01000000 {}".format(self.dsskey)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = "go $ubntaddr usetsshkey $fileaddr $filesize"
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Done")
        log_debug(msg="ssh keys uploaded successfully")

    def recovery_program_firmware(self):
        self.set_ub_net()
        self.is_network_alive_in_uboot()

        log_debug("Boot from the recovery image")
        cmd = "tftpboot images/{}-recovery.bin; bootm".format(self.board_id)
        self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd, "Bytes transferred")
        self.login(timeout=120)
        self.set_lnx_net("eth0")
        self.is_network_alive_in_linux()

        log_debug("Upgrade to shipping FW for registration ...")
        cmd = "ubnt-upgrade -d /srv/upgrade.tar"
        postexp = [
            "Writing kernel",
            "Writing rootfs",
            "Upgrade completed"
        ]
        self.pexp.expect_lnxcmd(240, self.linux_prompt, cmd, postexp)
        self.login(timeout=240)
        self.set_lnx_net("eth0")
        self.is_network_alive_in_linux()

    def check_board_signed(self):
        cmd = r"grep flashSize /proc/ubnthal/system.info"
        self.pexp.expect_action(10, "", "")
        output = self.pexp.expect_get_output(cmd, self.linux_prompt, 1.5)
        match = re.search(r'flashSize=', output)
        if not match:
            error_critical(msg="Device Registration check failed!")

    def prepare_server_need_files(self, method="tftp"):
        log_debug("Starting to do " + self.helperexe + "...")
        # Ex: tools/uvp/helper_DVF99_release_ata_max
        srcp = os.path.join(self.tools, self.helper_path, self.helperexe)

        # Ex: /tmp/helper_DVF99_release_ata_max
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)

        if method == "tftp":
            self.tftp_get(remote=srcp, local=helperexe_path, timeout=60)
        elif method == "wget":
            self.dut_wget(srcp, helperexe_path, timeout=100)
        else:
            error_critical("Transferring interface not support !!!!")

        cmd = "chmod 777 {0}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt, valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            helperexe_path,
            "--pipeline --quiet --output-product-class-fields product_class={}".format(self.product_class),
            "-o field=flash_eeprom,format=binary,pathname={}".format(eebin_dut_path),
            "> {}".format(eetxt_dut_path)
        ]
        sstr = ' '.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)
        time.sleep(1)

        files = [self.eetxt, self.eebin]
        for fh in files:
            # Ex: /tftpboot/e.t.0
            srcp = os.path.join(self.tftpdir, fh)

            # Ex: /tmp/e.t.0
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send helper output files from DUT to host ...")

    def run(self):
        '''
            Main procedure of factory
        '''

        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(1, "Waiting - PULG in the device...")

        if PROVISION_ENABLE is True:
            self.stop_uboot()
            self.set_mac_in_uboot()
            self.init_ub_network()
            self.data_provision()
            self.recovery_program_firmware()

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
            self.pexp.expect_action(timeout=10, exptxt=self.linux_prompt, action="reboot")

        if DATAVERIFY_ENABLE is True:
            msg(70, "Checking registration ...")
            self.login(timeout=120)
            self.check_board_signed()
            msg(80, "Device Registration check OK...")

        msg(no=100, out="Formal firmware completed with MAC0: " + self.mac)
        self.close_fcd()


def main():
    factory = UFBCM5616FactoryGeneral()
    factory.run()

if __name__ == "__main__":
    main()
