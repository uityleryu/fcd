#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import stat
import filecmp


class UDMMT7622FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UDMALPINEFactoryGeneral, self).__init__()

    def SetBootNet(self):
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def GetImgfromSrv(self, Img):
        self.pexp.expect_action(30, self.bootloader_prompt, "tftpboot 0x4007ff28 "+"images/"+Img)
        self.pexp.expect_action(30, "Bytes transferred = "+str(os.stat(self.fwdir+"/"+Img).st_size), "")

    def is_network_alive_in_uboot(self, retry=1):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.tftp_server)
            extext_list = ["host " + self.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=30, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def run(self):
        """
        Main procedure of factory
        """
        tmpdir = "/tmp/"
        tftpdir = self.tftpdir + "/"
        toolsdir = "tools/"
        bomrev = "113-" + self.bom_rev
        eepmexe = "mt7622-ee"
        helperexe = "helper_MT7622_release"
        mtdpart = "/dev/mtdblock4"

        self.set_bootloader_prompt("MT7622>")
        fcdimg = "{}".format(self.board_id+"-recovery.bin")
        # model ID

        wsysid = {
            'ec28': "770728ec"
        }

        # number of Ethernet
        ethnum = {
            'ec28': "3"
        }

        # number of WiFi
        wifinum = {
            'ec28': "0"
        }

        # number of Bluetooth
        btnum = {
            'ec28': "1"
        }

        netif = {
            'ec28': "ifconfig eth0 "
        }

        infover = {
            'ec28': "Version:"
        }

        # write system ID to the EEPROM partition
        write_sysid_cmd = "mw.l 0x40000000 " + wsysid[self.board_id]

        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(10, "Boot from tftp with installer ...")
        self.pexp.expect_action(15, "Hit any key to stop autoboot", "")

        # Set the system ID to the DUT
        self.pexp.expect_action(10, self.bootloader_prompt, write_sysid_cmd)
        self.pexp.expect_action(10, self.bootloader_prompt, "snor erase 0x1f0000 0x10000")
        self.pexp.expect_only(30, "successful")
        self.pexp.expect_action(10, self.bootloader_prompt, "snor write 0x40000000 0x1f000c 0x4")
        self.pexp.expect_action(10, self.bootloader_prompt, "reset")

        self.pexp.expect_action(15, "Hit any key to stop autoboot", "")
        self.SetBootNet()

        if self.is_network_alive_in_uboot(retry=3) is False:
            error_critical("Failed to ping tftp server in u-boot")

        self.GetImgfromSrv(fcdimg)
        self.pexp.expect_action(10, self.bootloader_prompt, "bootm")
        self.pexp.expect_action(60, "login:", "root")
        self.pexp.expect_action(10, "Password:", "ubnt")

        self.pexp.expect_action(10, self.linux_prompt, "dmesg -n 1")

        msg(15, 'Checking network in FCD kernel...')
        self.pexp.expect_action(10, self.linux_prompt, netif[self.board_id] + self.dutip)
        time.sleep(2)
        self.pexp.expect_action(10, self.linux_prompt, "ping " + self.tftp_server)
        self.pexp.expect_action(10, "64 bytes from", '\003')

        msg(20, "Send EEPROM command and set info to EEPROM ...")

        log_debug("Send tools.tar from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + toolsdir + "tools.tar",
            "-l " + tmpdir + "tools.tar",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        time.sleep(2)

        log_debug("Unzipping the tools.tar in the DUT ...")
        sstr = [
            "tar",
            "-xvzf",
            tmpdir + "tools.tar",
            "-C " + tmpdir
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        log_debug("Change file permission - " + helperexe + " ...")
        sstr = [
            "chmod 777",
            tmpdir + helperexe
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        log_debug("Change file permission - " + eepmexe + " ...")
        sstr = [
            "chmod 777",
            tmpdir + eepmexe
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        log_debug("Starting to initialize the dropbear")
        sstr = [
            "mkdir",
            "-p",
            "/var/run/dropbear; ",
            "dropbear -R"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        time.sleep(1)

        log_debug("Starting to do " + eepmexe + "...")
        sstr = [
            tmpdir + eepmexe,
            "-F",
            "-r " + bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + ethnum[self.board_id],
            "-w " + wifinum[self.board_id],
            "-b " + btnum[self.board_id],
            "-k",
            "-p Factory"
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        self.pexp.expect_action(10, "ssh-dss", "")
        self.pexp.expect_action(10, "ssh-rsa", "")

        msg(30, "Do helper to get the output file to devreg server ...")
        log_debug("Erase existed eeprom information files ...")
        rtf = os.path.isfile(tftpdir + self.eebin)
        if rtf is True:
            log_debug("Erasing File - " + self.eebin + " ...")
            os.chmod(tftpdir + self.eebin, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + self.eebin)
        else:
            log_debug("File - " + self.eebin + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + self.eetxt)
        if rtf is True:
            log_debug("Erasing File - " + self.eetxt + " ...")
            os.chmod(tftpdir + self.eetxt, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + self.eetxt)
        else:
            log_debug("File - " + self.eetxt + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + self.eesign)
        if rtf is True:
            log_debug("Erasing File - " + self.eesign + " ...")
            os.chmod(tftpdir + self.eesign, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + self.eesign)
        else:
            log_debug("File - " + self.eesign + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + self.eechk)
        if rtf is True:
            log_debug("Erasing File - " + self.eechk + " ...")
            os.chmod(tftpdir + self.eechk, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + self.eechk)
        else:
            log_debug("File - " + self.eechk + " doesn't exist ...")

        rtf = os.path.isfile(tftpdir + self.eetgz)
        if rtf is True:
            log_debug("Erasing File - " + self.eetgz + " ...")
            os.chmod(tftpdir + self.eetgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.remove(tftpdir + self.eetgz)
        else:
            log_debug("File - " + self.eetgz + " doesn't exist ...")

        log_debug("Starting to do " + helperexe + "...")
        sstr = [
            tmpdir + helperexe,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin,
            ">",
            self.eetxt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        sstr = [
            "tar",
            "cf",
            self.eetgz,
            self.eebin,
            self.eetxt
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        os.mknod(tftpdir + self.eetgz)
        os.chmod(tftpdir + self.eetgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetgz,
            "-l " + self.eetgz,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        time.sleep(2)

        cmd = "tar xvf " + tftpdir + self.eetgz + " -C " + tftpdir
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz + " files successfully")

        log_debug("Starting to do registration ...")
        cmd = [
            "cat " + tftpdir + self.eetxt,
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
            "-i field=flash_eeprom,format=binary,pathname=" + tftpdir + self.eebin,
            "-o field=flash_eeprom,format=binary,pathname=" + tftpdir + self.eesign,
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

        rtf = os.path.isfile(tftpdir + self.eesign)
        if rtf is not True:
            error_critical("Can't find " + self.eesign)

        msg(40, "Finish doing registration ...")
        log_debug("Send signed eeprom file from host to DUT ...")
        sstr = [
            "tftp",
            "-g",
            "-r " + self.eesign,
            "-l " + tmpdir + self.eesign,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        time.sleep(2)

        log_debug("Change file permission - " + self.eesign + " ...")
        sstr = [
            "chmod 777",
            tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        log_debug("Starting to write signed info to SPI flash ...")
        sstr = [
            tmpdir + helperexe,
            "-q",
            "-i field=flash_eeprom,format=binary,pathname=" + tmpdir + self.eesign
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        sstr = [
            "dd",
            "if=" + mtdpart,
            "of=" + tmpdir + self.eechk
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        time.sleep(1)

        os.mknod(tftpdir + self.eechk)
        os.chmod(tftpdir + self.eechk, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send " + self.eechk + " from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eechk,
            "-l " + tmpdir + self.eechk,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        time.sleep(2)

        if os.path.isfile(tftpdir + self.eechk):
            log_debug("Starting to compare the " + self.eechk + " and " + self.eesign + " files ...")
            rtc = filecmp.cmp(tftpdir + self.eechk, tftpdir + self.eesign)
            if rtc is True:
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            log_debug("Can't find the " + self.eechk + " and " + self.eesign + " files ...")

        msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-fw.bin",
            "-l " + tmpdir + "upgrade.bin",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(120, self.linux_prompt, sstrj)
        self.pexp.expect_action(10, "", "")
        time.sleep(120)
        self.pexp.expect_action(10, "", "")

        sstr = [
            "tftp",
            "-g",
            "-r images/" + self.board_id + "-recovery",
            "-l " + tmpdir + "uImage.r",
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, sstrj)
        self.pexp.expect_action(10, "", "")
        time.sleep(60)
        self.pexp.expect_action(10, "", "")

        msg(80, "Succeeding in downloading the upgrade tarf file ...")
        self.pexp.expect_action(10, self.linux_prompt, "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin")
        self.pexp.expect_only(60, "Firmware version")
        self.pexp.expect_only(60, "Writing recovery")

        self.pexp.expect_action(200, "login:", "root")
        self.pexp.expect_action(60, "Password:", "ubnt")

        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "dmesg -n 1")

        self.pexp.expect_action(10, self.linux_prompt, "info")
        self.pexp.expect_only(10, infover[self.board_id])

        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_action(10, "systemid=" + self.board_id, "")
        '''
        msg(100, "Completing firmware upgrading ...")
        time.sleep(2)
        exit(0)


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        udm_factory_general = UDMMT7622FactoryGeneral()
        udm_factory_general.run()

if __name__ == "__main__":
    main()
