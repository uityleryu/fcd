#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.pserial import SerialExpect
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.ssh_client import SSHClient
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info

import sys
import time
import os
import re
import traceback
import subprocess as sp
import glob


PROVISION_ENABLE    = True
DOHELPER_ENABLE     = True
REGISTER_ENABLE     = True
DEVREG_CHECK_ENABLE = True
CERT_INSTALL        = True
FWUPDATE_ENABLE     = True
MODEM_UPDATE_ENABLE = True
CHECK_FW_VER        = True


class USWPUMA7FactoryGeneral(ScriptBase):
    def __init__(self):
        super(USWPUMA7FactoryGeneral, self).__init__()

        self.ver_extract()

        # script specific vars
        self.puma7_prompt = "mainMenu>"
        self.puma7_logger_prompt = "logger>"
        self.helperexe = "helper_PUMA7_ARM_release"
        self.helper_path = "usw_puma7"
        self.certs = "certs"
        self.devregpart = "/dev/disk/by-partlabel/EEPROM"
        self.dut_ip = "192.168.1.20"
        self.dut_default_ip = "192.168.100.1"
        self.username = "ubnt"
        self.password = "ubnt"
        self.mac_upper = self.mac.upper()
        self.certs_tftp_dir = os.path.join(self.tftpdir, self.certs)
        # Below used for FW version check. Remember to update when change firmware
        self.version = "US.mxl277_MFG_1.0.1"
        self.cm_version = "US.mxl277_MFG_CM_1.0.2"
        # overwrite
        self.tftp_server = "192.168.100.201"


        # number of Ethernet
        self.ethnum = {
            'ed60': "1",
        }

        # number of WiFi
        self.wifinum = {
            'ed60': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ed60': "0",
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def cert_upload(self):
        log_debug("Preparing certificates ...")
        certs_files_all = []
        pattern = "/*/*/{}".format(self.mac_upper)
        for dh in glob.glob(self.certs_tftp_dir + pattern):
            certs_files_all.append(dh.replace(self.certs_tftp_dir + '/', ''))
        tg = " ".join(certs_files_all)
        cmd = "cd {}; tar -cvzf certs.tar {}; chmod 777 certs.tar".format(self.certs_tftp_dir, tg)
        p = sp.run(cmd, shell=True, check=True, stdout=sp.PIPE, universal_newlines=True)
        log_debug(msg=p.stdout)

        log_debug("Send certificates from host to DUT ...")
        source = os.path.join(self.certs, "certs.tar")
        target = os.path.join(self.dut_tmpdir, "certs.tar")
        self.tftp_get(remote=source, local=target, timeout=10, post_en=self.linux_prompt)

        cmd = "tar -xzvf {0} -C {1}".format(target, self.dut_tmpdir)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        src = os.path.join(self.dut_tmpdir, "*")
        cmd = "chmod -R 777 {0}".format(src)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

    def cert_install(self):
        cert_install_tool = "/cli/docsis/Production/createAsset"
        d30_cert_path = os.path.join(self.dut_tmpdir, self.helper_path, "d30_certs/", self.mac_upper)
        d31_cert_path = os.path.join(self.dut_tmpdir, self.helper_path, "d31_certs/", self.mac_upper)
        log_debug(msg="d30 cert location: " + d30_cert_path)
        log_debug(msg="d31 cert location: " + d31_cert_path)
        d30_source_files = [
            "{}/{}_Cert.der".format(d30_cert_path, self.mac_upper),
            "{}/{}_privkey.der".format(d30_cert_path, self.mac_upper),
            "/etc/docsis/security/root_pub_key.bin",
            "/etc/docsis/security/mfg_cert.cer",
            "{}/mfg_key_pub.bin".format(d30_cert_path)
        ]
        log_debug(msg="d30 source files:")
        log_debug(msg=' '.join(d30_source_files))

        d30_target_files = [
            "/nvram/1/security/cm_cert.cer",
            "/nvram/1/security/cm_key_prv.bin",
            "/nvram/1/security/root_pub_key.bin",
            "/nvram/1/security/mfg_cert.cer",
            "/nvram/1/security/mfg_key_pub.bin"
        ]

        d31_source_files = [
            "{}/{}_Cert.der".format(d31_cert_path, self.mac_upper),
            "{}/{}_privkey.der".format(d31_cert_path, self.mac_upper),
            "{}/CableLabs_Root_CA_01.cer".format(d31_cert_path),
            "{}/CableLabs_Device_CA_04_Cert.cer".format(d31_cert_path)
        ]
        log_debug(msg="d31 source files:")
        log_debug(msg=' '.join(d31_source_files))

        d31_target_files = [
            "/nvram/1/security/D3_1_cm_device_cert.cer",
            "/nvram/1/security/D3_1_cm_device_prv_key.bin",
            "/nvram/1/security/D3_1_root_ca_cert.cer",
            "/nvram/1/security/D3_1_device_ca_cert.cer"
        ]

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm -r /nvram/1/security/", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "mkdir -p /nvram/1/security/", self.linux_prompt)

        # copy d30 certs from tmp to destination
        for i in range(len(d30_source_files)):
            cmd = "cp {} {}".format(d30_source_files[i], d30_target_files[i])
            log_debug(msg="cmd: " + cmd)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)

        # copy d31 certs from tmp to destination
        for i in range(len(d31_source_files)):
            cmd = "cp {} {}".format(d31_source_files[i], d31_target_files[i])
            log_debug(msg="cmd: " + cmd)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)

        retry_max = 3
        # install d30 certs
        d30_count = 0
        while True:
            try:
                for i in range(len(d30_target_files)):
                    target_file_name = d30_target_files[i].split("/")[-1]
                    cmd = "{} {} {} 1".format(cert_install_tool, d30_target_files[i], target_file_name)
                    log_debug(msg="cmd: " + cmd)
                    exp_return = "successfully created Secure Asset \"{}\"".format(target_file_name)
                    self.pexp.expect_lnxcmd(3, self.linux_prompt, cmd, exp_return)
                    time.sleep(2)
                break
            except Exception as e:
                d30_count += 1
                if d30_count == retry_max:
                    error_critical("Fail to install d30 certs ...")
                log_info("Fail to install cert, reboot DUT to retry")
                self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/syswrapper.sh restart")
                self.reboot_handler()

        # install d31 certs
        d31_count = 0
        while True:
            try:
                for i in range(len(d31_target_files)):
                    target_file_name = d31_target_files[i].split("/")[-1]
                    cmd = "{} {} {} 1".format(cert_install_tool, d31_target_files[i], target_file_name)
                    log_debug(msg="cmd: " + cmd)
                    exp_return = "successfully created Secure Asset \"{}\"".format(target_file_name)
                    self.pexp.expect_lnxcmd(3, self.linux_prompt, cmd, exp_return)
                    time.sleep(2)
                break
            except Exception as e:
                d31_count += 1
                if d31_count == retry_max:
                    error_critical("Fail to install d31 certs ...")
                log_info("Fail to install cert, reboot DUT to retry")
                self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/syswrapper.sh restart")
                self.reboot_handler()

        # clean up files
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm /nvram/1/security/cm_*", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm /nvram/1/security/root_*", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm /nvram/1/security/mfg_*", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm /nvram/1/security/D3_1_*", self.linux_prompt)

    def cert_verify(self):
        cmds = [
            "/cli/docsis/Production/readAsset cm_cert.cer \\\"\\\"",
            "/cli/docsis/Production/readAsset cm_key_prv.bin \\\"\\\"",
            "/cli/docsis/Production/readAsset root_pub_key.bin \\\"\\\"",
            "/cli/docsis/Production/readAsset mfg_cert.cer \\\"\\\"",
            "/cli/docsis/Production/readAsset mfg_key_pub.bin \\\"\\\"",
            "/cli/docsis/Production/readAsset D3_1_cm_device_cert.cer \\\"\\\"",
            "/cli/docsis/Production/readAsset D3_1_cm_device_prv_key.bin \\\"\\\"",
            "/cli/docsis/Production/readAsset D3_1_root_ca_cert.cer \\\"\\\"",
            "/cli/docsis/Production/readAsset D3_1_device_ca_cert.cer \\\"\\\""
        ]
        for cmd in cmds:
            exp_return = "successfully read Secure Asset \"{}\"".format(cmd.split()[-2])
            self.pexp.expect_lnxcmd(3, self.linux_prompt, cmd, exp_return)
            time.sleep(2)

    def fwupdate(self):
        # if not mx1277 fw, need to upgrade twice
        retry_max = 3
        count_fw = 0
        while True:
            arm_fw_ver = self.pexp.expect_get_output("cat /unifi_fs/lib/version", self.linux_prompt)
            #atom_fw_ver = self.pexp.expect_get_output("/unifi_fs/bin/rcli 1 \"cat /unifi_fs/lib/version\"", self.linux_prompt)
            if "US.mxl277" not in arm_fw_ver:
                count_fw = count_fw + 1
                if count_fw == retry_max:
                    error_critical("Fail to upgrade puma-to-mxl277 fw ...")
                log_debug("Upgrading puma-to-mxl277 count {} ...".format(count_fw))
                source = os.path.join(self.tftpdir, self.image, self.board_id + "-fw-puma-to-mxl277.bin")
                target = os.path.join(self.dut_tmpdir, "fwupdate.bin")
                self.scp_get("ubnt", "ubnt", self.dut_default_ip, source, target)
                self.pexp.expect_action(10, "", "")
                self.pexp.expect_action(10, self.linux_prompt, "md5sum {}".format(target))
                self.pexp.expect_action(10, self.linux_prompt, "syswrapper.sh upgrade2")
                result = self.reboot_handler()
                if result is False:
                    error_critical("Fail to reboot ...")
            else:
                break

        count_fw = 0
        while True:
            arm_fw_ver = self.pexp.expect_get_output("cat /unifi_fs/lib/version", self.linux_prompt)
            #atom_fw_ver = self.pexp.expect_get_output("/unifi_fs/bin/rcli 1 \"cat /unifi_fs/lib/version\"", self.linux_prompt)
            if self.version not in arm_fw_ver:
                count_fw = count_fw + 1
                if count_fw == retry_max:
                    error_critical("Fail to upgrade unifi fw ...")
                log_debug("Upgrading unifi fw count {} ...".format(count_fw))
                # file location:
                # tftp/images/ed60-fw.bin -> ../usw-fw/file.bin
                source = os.path.join(self.tftpdir, self.image, self.board_id+"-fw.bin")
                target = os.path.join(self.dut_tmpdir, "fwupdate.bin")
                self.scp_get("ubnt", "ubnt", self.dut_default_ip, source, target)
                self.pexp.expect_action(10, "", "")
                self.pexp.expect_action(10, self.linux_prompt, "md5sum {}".format(target))
                self.pexp.expect_action(10, self.linux_prompt, "syswrapper.sh upgrade2")
                result = self.reboot_handler()
                if result is False:
                    error_critical("Fail to reboot ...")
            else:
                break

    # To fix tftp not working issue
    def tftp_rescue_np_update(self):
        arm_fw_ver = self.pexp.expect_get_output("cat /usr/lib/version", self.linux_prompt)
        if "US.mxl277_MFG_CM_1.0.2+191.20230114.0512" in arm_fw_ver:
            log_debug("Upgrade CM np FW to fix tftp issue ...")
            self.reboot_by_watchdog()
            image_name = self.board_id + "-cm-np.bin"
            source = os.path.join(self.tftpdir, self.image, image_name)
            target = os.path.join(self.dut_tmpdir, image_name)
            self.scp_get("ubnt", "ubnt", self.dut_default_ip, source, target)
            self.pexp.expect_action(10, "", "")
            self.pexp.expect_action(10, self.linux_prompt, "md5sum {}".format(target))
            self.pexp.expect_action(10, self.linux_prompt, "update 1 {}".format(target))
            self.pexp.expect_only(10, "update: Exit OK")
            self.pexp.expect_action(10, self.linux_prompt, "update 2 {}".format(target))
            self.pexp.expect_only(10, "update: Exit OK")
            self.pexp.expect_action(10, self.linux_prompt, "rm {}".format(target))
            # self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/syswrapper.sh restart")
            self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/syswrapper.sh restart")
            result = self.reboot_handler(watchdog=True)
            if result is False:
                error_critical("Fail to reboot ...")

    def fwupdate_modem(self):
        retry_max = 3
        count_fw = 0
        while True:
            arm_fw_ver = self.pexp.expect_get_output("cat /usr/lib/version", self.linux_prompt)
            #atom_fw_ver = self.pexp.expect_get_output("/unifi_fs/bin/rcli 1 \"cat /usr/lib/version\"", self.linux_prompt)
            if self.cm_version not in arm_fw_ver:
                count_fw = count_fw + 1
                if count_fw == retry_max:
                    error_critical("Fail to upgrade cm fw ...")
                log_debug("Upgrading cm fw count {} ...".format(count_fw))
                self.reboot_by_watchdog()
                # file location:
                # tftp/images/ed60-modemfw.bin -> ../usw-fw/file.bin
                image_name = self.board_id+"-cm-app.bin"
                source = os.path.join(self.tftpdir, self.image, image_name)
                target = os.path.join(self.dut_tmpdir, image_name)
                self.scp_get("ubnt", "ubnt", self.dut_default_ip, source, target)
                self.pexp.expect_action(10, "", "")
                self.pexp.expect_action(10, self.linux_prompt, "md5sum {}".format(target))
                self.pexp.expect_action(10, self.linux_prompt, "update 1 {}".format(target))
                self.pexp.expect_only(10, "update: Exit OK")
                self.pexp.expect_action(10, self.linux_prompt, "update 2 {}".format(target))
                self.pexp.expect_only(10, "update: Exit OK")
                self.pexp.expect_action(10, self.linux_prompt, "rm {}".format(target))

                image_name = self.board_id + "-cm-np.bin"
                source = os.path.join(self.tftpdir, self.image, image_name)
                target = os.path.join(self.dut_tmpdir, image_name)
                self.scp_get("ubnt", "ubnt", self.dut_default_ip, source, target)
                self.pexp.expect_action(10, "", "")
                self.pexp.expect_action(10, self.linux_prompt, "md5sum {}".format(target))
                self.pexp.expect_action(10, self.linux_prompt, "update 1 {}".format(target))
                self.pexp.expect_only(10, "update: Exit OK")
                self.pexp.expect_action(10, self.linux_prompt, "update 2 {}".format(target))
                self.pexp.expect_only(10, "update: Exit OK")
                self.pexp.expect_action(10, self.linux_prompt, "rm {}".format(target))
                #self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/syswrapper.sh restart")
                self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/syswrapper.sh restart")
                result = self.reboot_handler(watchdog=True)
                if result is False:
                    error_critical("Fail to reboot ...")
            else:
                break

    def check_fw(self):
        if FWUPDATE_ENABLE is True:
            cmd = "cat /usr/lib/version | grep {}".format(self.cm_version)
            self.pexp.expect_action(10, "", "")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)
            cmd = "cat /unifi_fs/lib/version | grep {}".format(self.version)
            self.pexp.expect_action(10, "", "")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)
        if MODEM_UPDATE_ENABLE is True:
            cmd = "/unifi_fs/bin/rcli 1 \"cat /usr/lib/version\" | grep {}".format(self.cm_version)
            self.pexp.expect_action(10, "", "")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)
            cmd = "/unifi_fs/bin/rcli 1 \"cat /unifi_fs/lib/version\" | grep {}".format(self.version)
            self.pexp.expect_action(10, "", "")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)

    def wait_for_bootup(self, firstboot=False):
        debug = False
        if firstboot and debug:
            self.pexp.expect_lnxcmd(2, "", "", self.puma7_prompt)
        else:
            self.pexp.expect_lnxcmd(180, "Rule HAL_PHY_DS_LOCK_MON", "", self.puma7_prompt, retry=0)
        time.sleep(5)
        self.pexp.expect_lnxcmd(10, self.puma7_prompt, "logger", self.puma7_logger_prompt)
        self.pexp.expect_lnxcmd(10, self.puma7_logger_prompt, "AllComponentsConfig 0", self.puma7_logger_prompt)
        self.pexp.expect_lnxcmd(10, self.puma7_logger_prompt, "AllDebugModulesConfig 1 0", self.puma7_logger_prompt)
        self.pexp.expect_lnxcmd(10, self.puma7_logger_prompt, "exit", self.puma7_prompt)
        self.pexp.expect_lnxcmd(10, self.puma7_prompt, "shell", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        # below 2 command lines to disable console message
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "systemctl stop mcad", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "systemctl stop lcmd", self.linux_prompt)
        # export environment veriables
        cmd = "export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/unifi_fs/bin"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        # set DUT ip address
        # cmd = "/sbin/ip addr add {}/24 dev lan0".format(self.dut_ip)
        # self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        time.sleep(5)

    def eeprom_post_action(self):
        self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/syswrapper.sh restart")
        self.reboot_handler()
        log_info("==========SYS INFO==========")
        self.pexp.expect_get_output("cat /proc/ubnthal/system.info", self.linux_prompt)
        log_info("==========SYS INFO==========")

    # watchdog reboot, trigger reboot after 60s
    def reboot_by_watchdog(self):
        log_info("Trigger watchdog reboot")
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "/unifi_fs/bin/rcli 1 \"systemctl restart sw-watchdog\"")
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "/bin/systemctl stop rpc-ci-server")

    def reboot_handler(self, watchdog=False):
        expect_list = [
            "Input/output error",
            "Restarting system",
            "Cougar Mountain C0 - Boot Ram."
        ]
        index = self.pexp.expect_get_index(60, expect_list)
        if index != 0:
            self.wait_for_bootup()
            return True
        elif watchdog:
            try:
                # wait for watchdog action
                self.pexp.expect_only(70, "Cougar Mountain C0 - Boot Ram.")
                self.wait_for_bootup()
                return True
            except:
                return False
        else:
            return False

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        self.fcd.common.config_stty(self.dev)
        [buffer, returncode] = self.fcd.common.xcmd("ls /tftpboot/certs/usw_puma7/")
        if returncode != 0:
            self.fcd.common.xcmd("echo \"ubnt\" | sudo -S mkdir -p /tftpboot/certs/usw_puma7/")
            self.fcd.common.xcmd("echo \"ubnt\" | sudo -S tar -zxvf /tftpboot/certs/certs.tar.gz --directory "
                                 "/tftpboot/certs/usw_puma7/")
        cmd = "echo \"ubnt\" | sudo -S ip addr add {}/24 dev eth0".format(self.tftp_server)
        self.fcd.common.xcmd(cmd)
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        msg(5, "Open serial port successfully ...")

        self.wait_for_bootup(firstboot=True)
        self.tftp_rescue_np_update()

        if PROVISION_ENABLE is True:
            msg(10, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            log_debug("Finish sending tools to DUT and start generating 64K binary ...")
            self.data_provision_64k(netmeta=self.devnetmeta)
            msg(15, "Finish 64K binary generating ...")

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Finish erasing ee files ...")
            self.prepare_server_need_files()
            msg(25, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration()
            msg(35, "Finish doing registration ...")

        if DEVREG_CHECK_ENABLE is True:
            self.check_devreg_data()
            self.eeprom_post_action()
            msg(40, "Finish doing signed file and EEPROM checking ...")

        if CERT_INSTALL is True:
            self.cert_upload()
            self.cert_install()
            msg(50, "Finish installing certificates ...")
            self.cert_verify()
            msg(60, "Finish verifying certificates ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Finish updating FW ...")

        if MODEM_UPDATE_ENABLE is True:
            self.fwupdate_modem()
            msg(80, "Finish updating modem FW ...")

        if CHECK_FW_VER is True:
            self.check_fw()
            msg(90, "Finish checking FW ...")

        msg(100, "Completing registration ...")
        self.close_fcd()


def main():
    factory_general = USWPUMA7FactoryGeneral()
    factory_general.run()


if __name__ == "__main__":
    main()