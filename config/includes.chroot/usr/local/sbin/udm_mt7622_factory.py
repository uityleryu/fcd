#!/usr/bin/python3
import time
import os
import stat
from udm_alpine_factory import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

BOOT_RECOVERY_IMAGE = True
PROVISION_ENABLE = True
DOHELPER_ENABLE = True

REGISTER_ENABLE = True
FWUPDATE_ENABLE = False
DATAVERIFY_ENABLE = False  # to do, wait where to check info


class UDMALPINEMT7622Factory(ScriptBase):
    def __init__(self):
        super(UDMALPINEMT7622Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.devregpart = "/dev/mtdblock4"
        self.bomrev = "113-" + self.bom_rev
        self.eepmexe = "al324-ee"
        self.helperexe = "helper_MT7622_release"
        self.user = "root"
        self.bootloader_prompt = "MT7622"
        self.linux_prompt = "#"

        self.dut_udmdir = os.path.join(self.dut_tmpdir, "udm")
        # Helper and ee-tool path on DUT
        self.helper_dut_path = os.path.join(self.dut_udmdir, self.helperexe)
        self.eepmexe_dut_path = os.path.join(self.dut_udmdir, self.eepmexe)
        # EEPROM related files path on DUT
        self.eesign_dut_path = os.path.join(self.dut_udmdir, self.eesign)
        self.eetgz_dut_path = os.path.join(self.dut_udmdir, self.eetgz)
        self.eechk_dut_path = os.path.join(self.dut_udmdir, self.eechk)
        self.eebin_dut_path = os.path.join(self.dut_udmdir, self.eebin)
        self.eetxt_dut_path = os.path.join(self.dut_udmdir, self.eetxt)
        self.fcd_udmdir = os.path.join(self.tftpdir, "tmp", "udm")

        self.ethnum = {
            'ec28': "5"
        }

        self.wifinum = {
            'ec28': "2"
        }

        self.btnum = {
            'ec28': "1"
        }

        # ethernet interface
        self.netif = {
            'ec28': "ifconfig eth0 "
        }

        self.infover = {
            'ec28': "Version:"
        }

    def boot_recovery_image(self):
        self.pexp.expect_action(300, "Hit any key to", "")
        time.sleep(2)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        time.sleep(2)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        time.sleep(2)
        self.pexp.expect_action(10, self.bootloader_prompt, "ping " + self.tftp_server)
        time.sleep(2)
        self.pexp.expect_only(15, "host " + self.tftp_server + " is alive")
        time.sleep(2)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot images/" + self.board_id + "-recovery")
        time.sleep(2)
        self.pexp.expect_only(120, "Bytes transferred")
        time.sleep(2)
        self.pexp.expect_action(10, self.bootloader_prompt, "bootm 0x4007ff28")

    def init_recovery_image(self):
        self.login(self.user, self.password, 60)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)
        time.sleep(2)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
        time.sleep(2)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, "64 bytes from")
        time.sleep(2)

    def do_eepmexe(self):
        log_debug("Starting to do " + self.eepmexe + "...")
        sstr = [
            self.eepmexe_dut_path,
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
        sstr = ' '.join(sstr)

        postexp = [
            "ssh-dss",
            "ssh-rsa",
            "Fingerprint",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, post_exp=postexp)
        time.sleep(2)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")
        sstr = [
            self.helper_dut_path,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin_dut_path,
            ">",
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        time.sleep(2)
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
            "-r " + self.eetgz,
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
        eetxt = os.path.join(self.fcd_udmdir, self.eetxt)
        eebin = os.path.join(self.fcd_udmdir, self.eebin)
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

    def fwupdate(self):
        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-fw.bin",
            "-l " + self.dut_tmpdir + "/upgrade.bin",
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(300, self.linux_prompt, sstr, self.linux_prompt)

        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-recovery",
            "-l " + self.dut_tmpdir + "uImage.r",
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(90, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "sh",
            "/usr/bin/ubnt-upgrade",
            "-d",
            self.dut_tmpdir + "/upgrade.bin"
        ]
        sstr = ' '.join(sstr)

        postexp = [
            "Firmware version",
            "Writing recovery"
        ]
        self.pexp.expect_lnxcmd(300, self.linux_prompt, sstr, postexp)

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())

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

        if BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()
            self.init_recovery_image()
            msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.do_eepmexe()

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(dut_tmp_subdir="udm")
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        #self.login(self.username, self.password, 200)
        #self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    udmmt7622_factory = UDMALPINEMT7622Factory()
    udmmt7622_factory.run()

if __name__ == "__main__":
    main()
