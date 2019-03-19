#!/usr/bin/python3
import sys
import time
import os
import stat
import filecmp
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = False


class UNASALPINEFactory(ScriptBase):
    def __init__(self):
        super(UNASALPINEFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # override the base vars
        self.user = "root"
        self.ubpmt = "UBNT"
        self.linux_prompt = ["UniFi-NAS", "Error-A12"]

        # script specific vars
        self.devregpart = "/dev/mtdblock9"
        self.bomrev = "113-" + self.bom_rev
        self.eepmexe = "al324-ee"
        self.helperexe = "helper_UNAS-AL324_release"
        self.dut_nasdir = os.path.join(self.dut_tmpdir, "unas")
        self.helper_path = os.path.join(self.dut_nasdir, self.helperexe)
        self.eepmexe_path = os.path.join(self.dut_nasdir, self.eepmexe)

        # EEPROM related files path on DUT
        self.eesign_dut_path = os.path.join(self.dut_nasdir, self.eesign)
        self.eetgz_dut_path = os.path.join(self.dut_nasdir, self.eetgz)
        self.eechk_dut_path = os.path.join(self.dut_nasdir, self.eechk)
        self.eebin_dut_path = os.path.join(self.dut_nasdir, self.eebin)
        self.eetxt_dut_path = os.path.join(self.dut_nasdir, self.eetxt)

        self.fcd_unasdir = os.path.join(self.tftpdir, "tmp", "unas")

        # number of Ethernet

        self.ethnum = {
            'ea16': "1",
            'ea18': "1"
        }

        # number of WiFi
        self.wifinum = {
            'ea16': "0",
            'ea18': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ea16': "0",
            'ea18': "0"
        }

        self.netif = {
            'ea16': "ifconfig enp0s1 ",
            'ea18': "ifconfig enp0s1 "
        }
        # TO-DO remove if no need
        self.infover = {
            'ea16': "Version:",
            'ea18': "Version:"
        }

    def data_provision(self):
        log_debug("Change file permission - " + self.helperexe + " ...")
        sstr = [
            "chmod 777",
            self.helper_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        log_debug("Change file permission - " + self.eepmexe + " ...")
        sstr = [
            "chmod 777",
            self.eepmexe_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

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
            "-k",
            "-p Factory"
        ]
        sstrj = ' '.join(sstr)

        postexp = [
            "ssh-dss",
            "ssh-rsa",
            "Fingerprint",
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj, post_exp=postexp)

    def prepare_server_need_files(self):
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
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "cf",
            self.eetgz_dut_path,
            self.eebin_dut_path,
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        os.mknod(self.eetgz_path)
        os.chmod(self.eetgz_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetgz_path,
            "-l " + self.eetgz_dut_path,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "xvf " + self.eetgz_path,
            "-C " + self.tftpdir
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz_path + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz_path + " files successfully")
        eetxt = os.path.join(self.fcd_unasdir, self.eetxt)
        eebin = os.path.join(self.fcd_unasdir, self.eebin)
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
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

    def fwupdate(self):
        fcd_fwpath = os.path.join(self.fwdir, self.board_id + "-fw.bin")
        fwpath = os.path.join(self.dut_tmpdir, "firmware.bin")
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
            "ubntnas",
            "system",
            "upgrade",
            fwpath
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(300, self.linux_prompt, sstrj)
        self.pexp.expect_only(60, "Restarting system")

    def check_info(self):
        """under developing
        """
        self.pexp.expect_action(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno error")

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

        msg(5, "Boot to linux console ...")
        self.pexp.expect_action(60, "login:", self.user)
        self.pexp.expect_action(10, "Password:", self.password)

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip)
        time.sleep(2)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, ["64 bytes from"])
        msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=30)
            self.data_provision()

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(dut_tmp_subdir="unas")
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the fw file ...")
            self.pexp.expect_action(300, "login:", self.user)
            self.pexp.expect_action(15, "Password:", self.password)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    unas_alpine_factory = UNASALPINEFactory()
    unas_alpine_factory.run()

if __name__ == "__main__":
    main()
