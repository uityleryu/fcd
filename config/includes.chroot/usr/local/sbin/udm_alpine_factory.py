#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp

SET_FAKE_EEPROM     = True
UPDATE_UBOOT        = True
BOOT_RECOVERY_IMAGE = True
INIT_RECOVERY_IMAGE = True
NEED_DROPBEAR       = True
PROVISION_ENABLE    = True
DOHELPER_ENABLE     = True
REGISTER_ENABLE     = True
FWUPDATE_ENABLE     = True
DATAVERIFY_ENABLE   = True

class UDMALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UDMALPINEFactoryGeneral, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.mtdpart = "/dev/mtdblock4"
        self.bomrev = "113-" + self.bom_rev
        self.eepmexe = "al324-ee"
        self.helperexe = "helper_AL324_release"
        self.username = "root"
        self.password = "ubnt"
        self.bootloader_prompt = "UBNT"
        self.linux_prompt = "#"
       
        # Base path 
        self.tftpdir = self.tftpdir + "/"
        self.toolsdir = "tools/"
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


 
        # switch chip
        self.swchip = {
            'ea11': "qca8k",
            'ea13': "rtl83xx",
            'ea15': "rtl83xx"
        }
        
        # sub-system ID
        self.wsysid = {
            'ea11': "770711ea",
            'ea13': "770713ea",
            'ea15': "770715ea"
        }
        
        # number of Ethernet
        self.ethnum = {
            'ea11': "5",
            'ea13': "8",
            'ea15': "11"
        }
        
        # number of WiFi
        self.wifinum = {
            'ea11': "2",
            'ea13': "2",
            'ea15': "0"
        }
        
        # number of Bluetooth
        self.btnum = {
            'ea11': "1",
            'ea13': "1",
            'ea15': "1"
        }
       
        # ethernet interface 
        self.netif = {
            'ea11': "ifconfig eth0 ",
            'ea13': "ifconfig eth1 ",
            'ea15': "ifconfig eth0 "
        }
        
        self.infover = {
            'ea11': "Version:",
            'ea13': "Version",
            'ea15': "Version:"
        }

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def set_fake_EEPROM(self):
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + self.wsysid[self.board_id])
        if self.board_id == 'ea15':
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000004 01d30200")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf erase 0x1f0000 0x1000")
        self.pexp.expect_only(30, "Erased: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 0x1f000c 0x4")
        if self.board_id == 'ea15':
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000004 0x1f0010 0x4")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def update_uboot(self):
        self.pexp.expect_action(10, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.set_boot_net()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv tftpdir images/" + self.board_id + "_signed_")
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootupd")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_only(10, "bootupd done")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def boot_recovery_image(self):
        self.pexp.expect_action(10, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, self.swchip[self.board_id])
        self.set_boot_net()
        time.sleep(2)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(10, "host " + self.tftp_server + " is alive")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs ubnt-flash-factory pci=pcie_bus_perf console=ttyS0,115200")
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpboot 0x08000004 images/" + self.board_id + "-recovery")
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_action(10, self.bootloader_prompt, "bootm $fitbootconf")

    def init_recovery_image(self):
        self.login(self.username, self.password, 60)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)
        tmp_mac = "fc:ec:da:00:00:1"+self.row_id
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 hw ether " + tmp_mac, self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip, self.linux_prompt)
        time.sleep(2)
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)        
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo 5edfacbf > /proc/ubnthal/.uf", self.linux_prompt) 
        
    def data_provision(self):
        log_debug("Change file permission - " + self.helperexe + " ...")
        sstr = [
            "chmod 777",
            self.helper_dut_path
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Change file permission - " + self.eepmexe + " ...")
        sstr = [
            "chmod 777",
            self.eepmexe_dut_path
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        if NEED_DROPBEAR is True:
            log_debug("Copying the dropbearkey to /usr/bin ...")
            sstr = [
                "cp",
                self.dut_udmdir + "/dropbearkey_arm64",
                "/usr/bin/dropbearkey"
            ]
            sstr = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

            log_debug("Change file permission - dropbearkey ...")
            sstr = [
                "chmod 777",
                "/usr/bin/dropbearkey"
            ]
            sstr = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

            log_debug("Starting to initialize the dropbear")
            sstr = [
                "mkdir",
                "-p",
                "/var/run/dropbear; ",
                "dropbear -R"
            ]
            sstr = ' '.join(sstr)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

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
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "cf",
            self.eetgz_dut_path,
            "-C",
            self.dut_udmdir,
            self.eebin,
            self.eetxt
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

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
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "xvf " + self.tftpdir + self.eetgz,
            "-C " + self.tftpdir
        ]
        sstr = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz + " files successfully")

    def registration(self):
        log_debug("Starting to do registration ...")
        cmd = [
            "cat " + self.tftpdir + self.eetxt,
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
            "-i field=flash_eeprom,format=binary,pathname=" + self.tftpdir + self.eebin,
            "-o field=flash_eeprom,format=binary,pathname=" + self.tftpdir + self.eesign,
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

        rtf = os.path.isfile(self.tftpdir + self.eesign)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

    def check_devreg_data(self):
        log_debug("Send signed eeprom file from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + self.eesign_dut_path,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            self.eesign_dut_path
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            self.helper_dut_path,
            "-q",
            "-i field=flash_eeprom,format=binary,pathname=" + self.eesign_dut_path 
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + self.mtdpart,
            "of=" + self.eechk_dut_path
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)

        os.mknod(self.tftpdir + self.eechk)
        os.chmod(self.tftpdir + self.eechk, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + self.eechk + " from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eechk,
            "-l " + self.eechk_dut_path,
            self.tftp_server
        ]
        sstr = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstr, self.linux_prompt)
        time.sleep(1)

        if os.path.isfile(self.tftpdir + self.eechk):
            log_debug("Starting to compare the " + self.eechk + " and " + self.eesign + " files ...")
            rtc = filecmp.cmp(self.tftpdir + self.eechk, self.tftpdir + self.eesign)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            log_debug("Can't find the " + self.eechk + " and " + self.eesign + " files ...")

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
        self.pexp.expect_lnxcmd_retry(10, self.linux_prompt, "info", self.infover[self.board_id], retry=5)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())

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
        msg(5, "Open serial port successfully ...")

        if SET_FAKE_EEPROM is True:
            self.set_fake_EEPROM()

        if UPDATE_UBOOT is True:
            self.update_uboot()

        if BOOT_RECOVERY_IMAGE is True:
            self.boot_recovery_image()

        if INIT_RECOVERY_IMAGE is True:
            self.init_recovery_image()
            msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)                                                                        
            self.data_provision()

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        self.login(self.username, self.password, 200)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1", self.linux_prompt)

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        udm_factory_general = UDMALPINEFactoryGeneral()
        udm_factory_general.run()

if __name__ == "__main__":
    main()
