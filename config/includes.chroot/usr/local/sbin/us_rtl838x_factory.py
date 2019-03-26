#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPGRADE_ENABLE = True
DATAVERIFY_ENABLE = True


class USWLITEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USWLITEFactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ubpmt = "UBNT"
        self.devregpart = "/dev/mtdblock6"
        self.bomrev = "113-" + self.bom_rev
        self.eepmexe = "rtl838x-ee"
        self.helperexe = "helper_rtl838x"
        self.dut_uswdir = os.path.join(self.dut_tmpdir, "usw_lite")
        self.helper_path = os.path.join(self.dut_uswdir, self.helperexe)
        self.eepmexe_path = os.path.join(self.dut_uswdir, self.eepmexe)

        # EEPROM related files path on DUT
        self.eesign_dut_path = os.path.join(self.dut_uswdir, self.eesign)
        self.eetgz_dut_path = os.path.join(self.dut_uswdir, self.eetgz)
        self.eechk_dut_path = os.path.join(self.dut_uswdir, self.eechk)
        self.eebin_dut_path = os.path.join(self.dut_uswdir, self.eebin)
        self.eetxt_dut_path = os.path.join(self.dut_uswdir, self.eetxt)

        self.fcd_uswdir = os.path.join(self.tftpdir, "tmp", "usw_lite")

        # number of Ethernet
        self.ethnum = {
            'ed20': "17",
            'ed21': "25",
            'ed22': "49"
        }

        # number of WiFi
        self.wifinum = {
            'ed20': "0",
            'ed21': "0",
            'ed22': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ed20': "0",
            'ed21': "0",
            'ed22': "0"
        }

    def data_provision(self):
        log_debug("Change file permission - " + self.helperexe + " ...")
        self.is_dutfile_exist(self.helper_path)
        self.is_dutfile_exist(self.eepmexe_path)
        sstr = [
            "chmod 777",
            self.helper_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        log_debug("Change file permission - " + self.eepmexe + " ...")
        sstr = [
            "chmod 777",
            self.eepmexe_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)

        log_debug("Starting to do " + self.eepmexe + "...")
        sstr = [
            self.eepmexe_path,
            "-F",
            "-r " + self.bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
            "-k"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(60, "ssh-dss")
        self.pexp.expect_only(90, "ssh-rsa")
        self.pexp.expect_only(30, self.linux_prompt)

    def prepare_sever_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")
        sstr = [
            self.helper_path,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin_dut_path,
            ">",
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)

        sstr = [
            "tar",
            "cf",
            self.eetgz_dut_path,
            self.eebin_dut_path,
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)

        os.mknod(self.eetgz_path)
        os.chmod(self.eetgz_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetgz,
            "-l " + self.eetgz_dut_path,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)

        sstr = [
            "tar",
            "xvf " + self.eetgz_path,
            "-C " + self.tftpdir
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz + " files successfully")
        eetxt = os.path.join(self.fcd_uswdir, self.eetxt)
        eebin = os.path.join(self.fcd_uswdir, self.eebin)
        sstr = [
            "mv",
            eetxt,
            self.eetxt_path
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        sstr = [
            "mv",
            eebin,
            self.eebin_path
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)

    def registration(self):
        log_debug("Starting to do registration ...")
        cmd = [
            "cat " + self.eetxt_path,
            "|",
            'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
            "|",
            'grep -v \"eeprom\"',
            "|",
            "tr '\\n' ' '"
        ]
        cmdj = ' '.join(cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        regsubparams = sto.decode('UTF-8')
        if int(rtc) > 0:
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")

        regparam = [
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            regsubparams,
            "-i field=qr_code,format=hex,value=" + self.qrhex,
            "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
            "-o field=flash_eeprom,format=binary,pathname=" + self.eesign_path,
            "-o field=registration_id",
            "-o field=result",
            "-o field=device_id",
            "-o field=registration_status_id",
            "-o field=registration_status_msg",
            "-o field=error_message",
            "-x " + self.key_dir + "ca.pem",
            "-y " + self.key_dir + "key.pem",
            "-z " + self.key_dir + "crt.pem"
        ]

        regparamj = ' '.join(regparam)

        cmd = "sudo /usr/local/sbin/client_x86_release " + regparamj
        print("cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(6)
        if int(rtc) > 0:
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

    def fwupdate(self):
        fcd_fwpath = os.path.join(self.image, self.board_id + "-fw.bin")
        fwpath = os.path.join(self.dut_tmpdir, "fwupdate.bin")
        sstr = [
            "tftp",
            "-g",
            "-r " + fcd_fwpath,
            "-l " + fwpath,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "syswrapper.sh",
            "upgrade2"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(300, self.linux_prompt, sstrj)
        self.pexp.expect_only(300, "Restarting system")

    def check_info(self):
        """under developing
        """
        self.pexp.expect_action(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno(mac) error")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        self.pexp.expect_action(300, "Please press Enter to activate this console", "")
        self.pexp.expect_action(30, "login:", self.user)
        self.pexp.expect_action(10, "Password:", self.password)
        self.pexp.expect_action(10, self.linux_prompt, "initd")

        for _ in range(3):
            is_network_alive = self.is_network_alive_in_linux()
            if is_network_alive is True:
                break
            time.sleep(5)
        if is_network_alive is not True:
            error_critical("Network is not good")
        msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.data_provision()

        if DOHELPER_ENABLE is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_sever_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(dut_tmp_subdir="usw_lite")
            msg(50, "Finish doing signed file and EEPROM checking ...")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
            self.pexp.expect_action(300, "Please press Enter to activate this console", "")
            self.pexp.expect_action(30, "login:", self.user)
            self.pexp.expect_action(10, "Password:", self.password)
            self.pexp.expect_action(10, self.linux_prompt, "initd")
            for _ in range(3):
                is_network_alive = self.is_network_alive_in_linux()
                if is_network_alive is True:
                    break
                time.sleep(5)
            if is_network_alive is not True:
                error_critical("Network is not good")
            msg(10, "Boot up to linux console and network is good ...")

        if FWUPGRADE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the fw file ...")
            self.pexp.expect_action(300, "Please press Enter to activate this console", "")
            self.pexp.expect_action(15, "login:", self.user)
            self.pexp.expect_action(15, "Password:", self.password)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1")
            msg(75, "Completing firmware upgrading ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    us_factory_general = USWLITEFactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
