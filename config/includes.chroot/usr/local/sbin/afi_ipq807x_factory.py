#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil


class AFIIPQ807XFactory(ScriptBase):
    def __init__(self):
        super(AFIIPQ807XFactory, self).__init__()

    def run(self):
        """
        Main procedure of factory
        """
        # Common folder
        tmpdir = "/tmp/"
        tftpdir = self.tftpdir + "/"
        self.afi_dir = os.path.join(self.fcd_toolsdir, "afi_aln")
        self.dut_afi_dir = os.path.join(self.dut_tmpdir, "afi_aln")
        wifi_cal_data_dir = os.path.join(tmpdir, "IPQ8074")

        # U-boot prompt
        ubpmt = {
            'da11': "IPQ807x",
            'da12': "IPQ807x",
            'da13': "IPQ807x",
            'da14': "IPQ807x"
        }

        # linux console prompt
        lnxpmt = {
            'da11': "ubnt@",
            'da12': "ubnt@",
            'da13': "ubnt@",
            'da14': "ubnt@"
        }

        # number of Ethernet
        ethnum = {
            'da11': "5",
            'da12': "1",
            'da13': "5",
            'da14': "1"
        }

        # number of WiFi
        wifinum = {
            'da11': "3",
            'da12': "3",
            'da13': "2",
            'da14': "2"
        }

        # number of Bluetooth
        btnum = {
            'da11': "1",
            'da12': "1",
            'da13': "1",
            'da14': "1"
        }

        # communicating Ethernet interface
        comuteth = {
            'da11': "br-lan",
            'da12': "br-lan",
            'da13': "br-lan",
            'da14': "br-lan"
        }

        # temporary eeprom binary file
        tempeeprom = {
            'da11': "da11-eeprom.bin",
            'da12': "da12-eeprom.bin",
            'da13': "da13-eeprom.bin",
            'da14': "da14-eeprom.bin"
        }

        # booting up the last message
        bootmsg_eth = "(eth\d: PHY Link up speed)"
        bootmsg_noeth = "Please press Enter to activate this console"

        bootloader = {
            'da11': "da11-bootloader.bin",
            'da12': "da12-bootloader.bin",
            'da13': "da13-bootloader.bin",
            'da14': "da14-bootloader.bin"
        }

        baseip = 31
        prod_dev_ip = "192.168.1." + str((int(self.row_id) + baseip))
        prod_dev_tmp_mac = "00:15:6d:00:00:0" + self.row_id
        eepmexe = "ipq807x-aarch64-ee"
        eeprom_bin = "e.b." + self.row_id
        eeprom_txt = "e.t." + self.row_id
        eeprom_tgz = "e." + self.row_id + ".tgz"
        eeprom_signed = "e.s." + self.row_id
        eeprom_check = "e.c." + self.row_id
        helperexe = "helper_IPQ807x_release"
        fcd_host_name = "{}@{}:".format(self.fcd_user, self.tftp_server)
        fcd_host_passw = self.fcd_passw
        bomrev = "113-" + self.bom_rev
        mtdpart = "/dev/mtdblock18"
        self.dut_helper_path = os.path.join(self.dut_afi_dir, helperexe)
        self.dut_eepmexe_path = os.path.join(self.dut_afi_dir, eepmexe)
        # This MD5SUM value is generated from a file with all 0xff
        md5sum_no_wifi_cal = "41d2e2c0c0edfccf76fa1c3e38bc1cf2"

        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)

        msg(10, "Update the U-boot")
        self.pexp.expect_action(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_action(30, ubpmt[self.board_id], "")
        time.sleep(3)
        self.pexp.expect_action(30, ubpmt[self.board_id], "setenv ipaddr " + prod_dev_ip)
        self.pexp.expect_action(30, ubpmt[self.board_id], "setenv serverip " + self.tftp_server)
        self.pexp.expect_action(30, ubpmt[self.board_id], "ping " + self.tftp_server)
        self.pexp.expect_action(30, "host " + self.tftp_server + " is alive", "")
        sstr = [
            "tftpboot",
            "0x44000000",
            "images/" + bootloader[self.board_id]
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, ubpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Bytes transferred", "sf probe")
        self.pexp.expect_action(30, ubpmt[self.board_id], "sf erase 0x490000 0xa0000")
        self.pexp.expect_action(30, "Erased: OK", "sf write 0x44000000 0x490000 0xa0000")
        self.pexp.expect_action(30, "Written: OK", "sf erase 0x480000 0x10000")
        self.pexp.expect_action(30, "Erased: OK", "")

        msg(15, "Flash EEPROM/TZ/DEVCFG partitions")
        sstr = [
            "tftpboot",
            "0x44000000",
            "images/" + tempeeprom[self.board_id]
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, ubpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Bytes transferred", "sf erase 0x610000 0x10000")
        self.pexp.expect_action(30, "Erased: OK", "sf write 0x44000000 0x610000 0x10000")
        self.pexp.expect_action(30, "Written: OK", "")

        sstr = [
            "tftpboot",
            "0x44000000",
            "images/" + self.board_id + "-tz.mbn"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, ubpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Bytes transferred", "sf erase 0xa0000 0x00300000")
        self.pexp.expect_action(30, "Erased: OK", "sf write 0x44000000 0xa0000  0x00180000")
        self.pexp.expect_action(30, "Written: OK", "sf write 0x44000000 0x220000 0x00180000")
        self.pexp.expect_action(30, "Written: OK", "")

        sstr = [
            "tftpboot",
            "0x44000000",
            "images/" + self.board_id + "-devcfg.mbn"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, ubpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Bytes transferred", "sf erase 0x3A0000 0x00020000")
        self.pexp.expect_action(30, "Erased: OK", "sf write 0x44000000 0x3A0000 0x00010000")
        self.pexp.expect_action(30, "Written: OK", "sf write 0x44000000 0x3B0000 0x00010000")
        self.pexp.expect_action(30, "Written: OK", "")

        msg(20, "Loading firmware")
        sstr = [
            "tftpboot",
            "0x44000000",
            "images/" + self.board_id + "-fw.img"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, ubpmt[self.board_id], sstrj)

        self.pexp.expect_action(120, "Bytes transferred", "nand erase 0 0x10000000")
        self.pexp.expect_action(30, "Erasing at 0xffe0000", "nand write 0x44000000 0 $filesize")
        self.pexp.expect_action(30, "written: OK", "reset")

        msg(25, "Configuring the EEPROM partition ...")
        self.pexp.expect_action(120, bootmsg_eth, "")
        self.pexp.expect_action(60, bootmsg_eth, "")
        sstr = [
            "ifconfig",
            comuteth[self.board_id],
            prod_dev_ip
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        self.pexp.expect_action(30, lnxpmt[self.board_id], "ping " + self.tftp_server)
        self.pexp.expect_action(30, "64 bytes from", '\003')

        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(30, lnxpmt[self.board_id], "[ ! -f ~/.ssh/known_hosts ] || rm ~/.ssh/known_hosts")

        log_debug("Send tools.tar from host to DUT ...")
        sstr = [
            "scp",
            fcd_host_name + self.fcd_toolsdir + "/tools.tar",
            tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Do you want to continue connecting?", "y")
        self.pexp.expect_action(30, "password:", fcd_host_passw)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        log_debug("Unzipping the tools.tar in the DUT ...")
        sstr = [
            "tar",
            "-xvzf",
            tmpdir + "tools.tar",
            "-C " + tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, lnxpmt[self.board_id], sstrj)

        log_debug("Change file permission - " + helperexe + " ...")
        sstr = ["chmod 777", self.dut_helper_path]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        log_debug("Change file permission - " + eepmexe + " ...")
        sstr = ["chmod 777", self.dut_eepmexe_path]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        log_debug("Starting to do " + eepmexe + "...")
        sstr = [
            "cd " + self.dut_afi_dir + ";" + " ./" + eepmexe,
            "-F",
            "-r " + bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + ethnum[self.board_id],
            "-w " + wifinum[self.board_id],
            "-b " + btnum[self.board_id]
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        msg(30, "Do helper to get the output file to devreg server ...")
        log_debug("Erase existed eeprom information files ...")
        rtf = os.path.isfile(tftpdir + eeprom_bin)
        if (rtf is True):
            log_debug("Erasing File - " + eeprom_bin + " ...")
            os.chmod(tftpdir + eeprom_bin, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + eeprom_bin)
        else:
            log_debug("File - " + eeprom_bin + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + eeprom_txt)
        if (rtf is True):
            log_debug("Erasing File - " + eeprom_txt + " ...")
            os.chmod(tftpdir + eeprom_txt, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + eeprom_txt)
        else:
            log_debug("File - " + eeprom_txt + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + eeprom_signed)
        if (rtf is True):
            log_debug("Erasing File - " + eeprom_signed + " ...")
            os.chmod(tftpdir + eeprom_signed, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + eeprom_signed)
        else:
            log_debug("File - " + eeprom_signed + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + eeprom_check)
        if (rtf is True):
            log_debug("Erasing File - " + eeprom_check + " ...")
            os.chmod(tftpdir + eeprom_check, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + eeprom_check)
        else:
            log_debug("File - " + eeprom_check + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + eeprom_tgz)
        if (rtf is True):
            log_debug("Erasing File - " + eeprom_tgz + " ...")
            os.chmod(tftpdir + eeprom_tgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + eeprom_tgz)
        else:
            log_debug("File - " + eeprom_tgz + " doesn't exist ...")

        log_debug("Starting to do " + helperexe + "...")
        sstr = [
            "cd " + self.dut_afi_dir + ";" + " ./" + helperexe,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + eeprom_bin,
            ">",
            eeprom_txt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)

        sstr = [
            "tar",
            "cf",
            eeprom_tgz,
            eeprom_bin,
            eeprom_txt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)

        os.mknod(tftpdir + eeprom_tgz)
        os.chmod(tftpdir + eeprom_tgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")
        sstr = [
            "scp",
            os.path.join(self.dut_afi_dir, eeprom_tgz),
            fcd_host_name + tftpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Do you want to continue connecting?", "y")
        self.pexp.expect_action(30, "password:", fcd_host_passw)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        cmd = [
            "tar",
            "xvf",
            tftpdir + eeprom_tgz,
            "-C",
            tftpdir
        ]
        cmdj = ' '.join(cmd)
        print("cmd: " + cmdj)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Decompressing " + eeprom_tgz + " file failed!!")
        else:
            log_debug("Decompressing " + eeprom_tgz + " files successfully")

        msg(35, "Starignt to do the registration")
        log_debug("Starting to do registration ...")
        cmd = [
            "cat",
            tftpdir + eeprom_txt,
            "|",
            'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
            "|",
            'grep -v \"eeprom\"',
            "|",
            "tr '\\n' ' '"
        ]
        cmdj = ' '.join(cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        regsubparams = sto
        if (int(rtc) > 0):
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")

        regparam = [
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            regsubparams,
            "-i field=flash_eeprom,format=binary,pathname=" + tftpdir + eeprom_bin,
            "-o field=flash_eeprom,format=binary,pathname=" + tftpdir + eeprom_signed,
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
        if (int(rtc) > 0):
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(tftpdir + eeprom_signed)
        if (rtf is not True):
            error_critical("Can't find " + eeprom_signed)

        msg(40, "Finish doing registration ...")
        log_debug("Send signed eeprom file from host to DUT ...")
        sstr = [
            "scp",
            fcd_host_name + tftpdir + eeprom_signed,
            tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Do you want to continue connecting?", "y")
        self.pexp.expect_action(30, "password:", fcd_host_passw)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        log_debug("Change file permission - " + eeprom_signed + " ...")
        sstr = ["chmod 777", tmpdir + eeprom_signed]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            "cd " + self.dut_afi_dir + ";" + " ./" + helperexe,
            "-q",
            "-i field=flash_eeprom,format=binary,pathname=" + tmpdir + eeprom_signed
        ]
        sstrj = ' '.join(sstr)
        print("cmd: " + sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + mtdpart,
            "of=" + tmpdir + eeprom_check
        ]
        sstrj = ' '.join(sstr)
        print("cmd: " + sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)

        os.mknod(tftpdir + eeprom_check)
        os.chmod(tftpdir + eeprom_check, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + eeprom_check + " from DUT to host ...")
        sstr = [
            "scp",
            tmpdir + eeprom_check,
            fcd_host_name + tftpdir
        ]
        sstrj = ' '.join(sstr)
        print("cmd: " + sstrj)
        self.pexp.expect_action(30, lnxpmt[self.board_id], sstrj)
        self.pexp.expect_action(30, "Do you want to continue connecting?", "y")
        self.pexp.expect_action(30, "password:", fcd_host_passw)
        self.pexp.expect_action(30, lnxpmt[self.board_id], "")

        if os.path.isfile(tftpdir + eeprom_check):
            log_debug("Starting to compare the" + eeprom_check + " and " + eeprom_signed + " files ...")
            cmd = [
                "/usr/bin/cmp",
                tftpdir + eeprom_check,
                tftpdir + eeprom_signed
            ]
            cmdj = ' '.join(cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmdj)
            if (int(rtc) > 0):
                error_critical("Comparing files failed!!")
            else:
                log_debug("Comparing files successfully")
        else:
            log_debug("Can't find the " + eeprom_check + " and " + eeprom_signed + " files ...")

        msg(50, "Finish doing signed file and EEPROM checking ...")

        log_debug("Booting up to linux console ...")
        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(30, lnxpmt[self.board_id], "reboot")
        self.pexp.expect_action(60, bootmsg_noeth, "")
        msg(70, "Firmware booting up successfully ...")
        self.pexp.expect_action(60, lnxpmt[self.board_id], "grep flashSize /proc/ubnthal/system.info")
        self.pexp.expect_action(60, "flashSize", "")
        msg(80, "Checking there's wifi calibration data exist.")
        cal_file = os.path.join(wifi_cal_data_dir, "caldata.bin")
        self.pexp.expect_action(10, lnxpmt[self.board_id], "md5sum " + cal_file)
        index = self.pexp.expect_get_index(10, md5sum_no_wifi_cal)
        if index == 0:
            error_critical(msg="Wifi calibration data empty!")
        else:
            log_debug(msg="Wifi calibration data is not empty, pass!")
        ssh_unlock_cmd = "echo ssh | prst_tool -w misc && prst_tool -e pairing && cfg.sh erase && echo cfg_done > /proc/afi_leds/mode && reboot -fd1"
        self.pexp.expect_action(10, lnxpmt[self.board_id], ssh_unlock_cmd)
        self.pexp.expect_only(10, "pairing erased")
        self.pexp.expect_action(120, bootmsg_noeth, "")
        self.pexp.expect_lnxcmd(10, lnxpmt[self.board_id], "ubus call firmware info", retry=12)
        self.pexp.expect_lnxcmd(10, lnxpmt[self.board_id], "cat /proc/ubnthal/system.info")
        self.pexp.expect_lnxcmd(10, lnxpmt[self.board_id], "cat /proc/ubnthal/board")
        msg(100, "Formal firmware completed...")
        self.close_fcd()

def main():
    afi_ipq807x_factory = AFIIPQ807XFactory()
    afi_ipq807x_factory.run()

if __name__ == "__main__":
    main()
