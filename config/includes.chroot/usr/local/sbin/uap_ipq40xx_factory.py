#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil


class UAPIPQ40XXFactory(ScriptBase):
    def __init__(self):
        super(UAPIPQ40XXFactory, self).__init__()
        self._init_vars()

    def _init_vars(self):

        # U-boot prompt
        self.ubpmt = {
            'dc98': "\(IPQ40xx\) # "
        }

        # linux console prompt
        self.lnxpmt = {
            'dc98': "UBB#"
        }

        # number of Ethernet
        self.ethnum = {
            'dc98': "1"
        }

        # number of WiFi
        self.wifinum = {
            'dc98': "1"
        }

        # number of Bluetooth
        self.btnum = {
            'dc98': "1"
        }

        # communicating Ethernet interface
        self.comuteth = {
            'dc98': "br-lan"
        }

        # temporary eeprom binary file
        self.tempeeprom = {
            'dc98': "cfg_part.bin"
        }

        self.bootloader = {
            'dc98': "dc98-bootloader.bin"
        }

        baseip = 20
        self.prod_dev_ip = "192.168.1." + str((int(self.row_id) + baseip))

        tmpdir = "/tmp/"
        self.tftpdir = self.tftpdir + "/"
        self.uap_dir = os.path.join(self.fcd_toolsdir, "uap")
        self.id_rsa = self.uap_dir + "/id_rsa"
        self.eeprom_bin = "e.b." + self.row_id
        self.eeprom_txt = "e.t." + self.row_id
        self.eeprom_tgz = "e." + self.row_id + ".tgz"
        self.eeprom_signed = "e.s." + self.row_id
        self.eeprom_check = "e.c." + self.row_id
        self.bomrev = "13-" + self.bom_rev
        helperexe = "helper_IPQ40xx"
        self.dut_helper_path = os.path.join(self.uap_dir , helperexe)
        self.uboot_address =  "0xf0000"
        self.uboot_size =  "0x80000"
        self.cfg_address = "0x1fc0000"
        self.cfg_size = "0x40000"
        self.eeprom_address = "0x170000"
        self.eeprom_size = "0x10000"

        self.fcd.common.config_stty(self.dev)

    def _stop_uboot(self):
        self.pexp.expect_action(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "")

    def _set_uboot_network(self):
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv ipaddr " + self.prod_dev_ip)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv serverip " + self.tftp_server)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "ping " + self.tftp_server)
        self.pexp.expect_only(30, "host " + self.tftp_server + " is alive")
        time.sleep(1)

    def run(self):
        """
        Main procedure of factory
        """

        msg(1, "Start Procedure")
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Stop U-boot")
        self._stop_uboot()
        time.sleep(3)
        self._set_uboot_network()

        msg(10, "Update U-boot")

        cmd = "tftpboot 84000000 images/" + self.bootloader[self.board_id]
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        self.pexp.expect_action(30, "Bytes transferred", "usetprotect spm off")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "sf probe")
        cmd = "sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.uboot_address, self.uboot_size)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        time.sleep(1)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "re\r")
        self._stop_uboot()

        msg(15, "Check EEPROM Data")

        self.pexp.expect_action(30, self.ubpmt[self.board_id], "sf probe")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "sf read 0x84000000 {0} {1}".format(self.eeprom_address, self.eeprom_size))
        output = self.pexp.expect_get_output("md.b 0x84005000 2", self.ubpmt[self.board_id])

        if ("84005000: 20 2f" in output):
            log_debug("Board is callibrated")
        else:
            error_critical("Board is not callibrated")

        if (False) :
            output = self.pexp.expect_get_output("md.b 0x84005006 6", self.ubpmt[self.board_id])
            out_list = output.split('\r')
            outmac = ""
            for line in out_list:
                if("84005006:" in line):
                    out = line.split(' ')
                    outmac = out[1] + out[2] + out[3] + out[4] + out[5] + out[6]
            
            if (self.mac in outmac):
                log_debug("Board calibration MAC correct")
            else:
                error_critical("Board calibration MAC incorrect %s %s" %(self.mac, outmac))
            self.pexp.expect_only(30, self.ubpmt[self.board_id])

        msg(20, "Do ubntw")

        cmd = "ubntw all {0} {1} {2} 0".format(self.mac, self.board_id, self.bomrev) 
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        time.sleep(1)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "ubntw dump")

        msg(25, "Flash a temporary config")
        self._set_uboot_network()
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "printenv")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "tftpboot 0x84000000 tools/uap/cfg_part.bin")
        self.pexp.expect_action(30, "Bytes transferred", "usetprotect spm off")

        cmd = "sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.cfg_address, self.cfg_size)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        time.sleep(10)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "printenv")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "urescue -e -f")

        msg(30, "Doing urescue")

        atftp_cmd = "atftp --option \"mode octet\" -p -l {0}{1}/{2} {3}".format(self.tftpdir, "images", self.fwimg,
                                                                                 self.prod_dev_ip)
        log_debug(msg="Run cmd on host:" + atftp_cmd)
        self.fcd.common.xcmd(cmd=atftp_cmd)

        self.pexp.expect_only(30, "Firmware Version:")
        msg(31, "urescue: FW loaded")
        self.pexp.expect_only(30, "Image Signature Verfied, Success.")
        msg(32, "urescue: FW verified")
        self.pexp.expect_only(30, "Copying partition 'kernel' to flash memory:")
        msg(33, "urescue: uboot updated")
        self.pexp.expect_only(30, "Copying partition 'rootfs' to flash memory:")
        msg(34, "urescue: kernel updated")
        self.pexp.expect_only(180, "Firmware update complete.")
        msg(35, "urescue: complete")

        msg(40, "Doing registration")

        self.pexp.expect_action(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_action(10, "login:", "fcd")
        self.pexp.expect_action(10, "Password:", "fcduser")

        self.pexp.expect_action(10, self.lnxpmt[self.board_id], "ifconfig eth0 {0} up".format(self.prod_dev_ip))

        change_cmd = "chmod 400 " + self.id_rsa
        self.fcd.common.xcmd(cmd=change_cmd)

        scp_cmd = "scp -i {0} -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ".format(self.id_rsa) \
                    + "{0} fcd@{1}:/tmp/helper".format(self.dut_helper_path, self.prod_dev_ip)
        self.fcd.common.xcmd(cmd=scp_cmd)

        helper_cmd = "cd /tmp/; ./helper -q -c product_class=radio -o field=flash_eeprom,format=binary,pathname={0} > {1}".format(self.eeprom_bin, self.eeprom_txt)
        self.pexp.expect_action(180, self.lnxpmt[self.board_id], helper_cmd )

        scp_cmd = "scp -i {0} -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ".format(self.id_rsa) \
                    + "fcd@{0}:/tmp/e.* {1}".format(self.prod_dev_ip, self.tftpdir)
        self.fcd.common.xcmd(cmd=scp_cmd)

        cmd = [
            "cat",
            self.tftpdir + self.eeprom_txt,
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
        if (int(rtc) > 0):
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")

        regparam = [
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            regsubparams,
            "-i field=qr_code,format=hex,value=" + self.qrhex,
            "-i field=flash_eeprom,format=binary,pathname=" + self.tftpdir + self.eeprom_bin,
            "-o field=flash_eeprom,format=binary,pathname=" + self.tftpdir + self.eeprom_signed,
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
        if (int(rtc) > 0):
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.tftpdir + self.eeprom_signed)
        if (rtf is not True):
            error_critical("Can't find " + self.eeprom_signed)

        msg(50, "Finish do registration ...")

        self.pexp.expect_action(180, self.lnxpmt[self.board_id], "reboot -f" )
        self._stop_uboot()
        time.sleep(3)
        self._set_uboot_network()

        msg(60, "Write signed EEPROM")
        cmd = "tftpboot 84000000 " + self.eeprom_signed
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        self.pexp.expect_action(30, "Bytes transferred", "usetprotect spm off")
        log_debug("File sent. Writing eeprom")

        self.pexp.expect_action(30, self.ubpmt[self.board_id], "sf probe")

        cmd = "sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.eeprom_address, self.eeprom_size)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)

        msg(70, "Erase tempoarary config")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "sf erase {0} {1}".format(self.cfg_address, self.cfg_size))	
        #log_progress 95 "Configuration erased"

        msg(80, "Write default setting")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv NORESET")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv serverip 192.168.1.254")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv ipaddr 192.168.1.20")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "setenv bootargs root=/dev/mtdblock5 init=/init")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "saveenv")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "ubntw dump")

        msg(90, "Final Boot")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "reset\r")
        self.pexp.expect_action(240, "Please press Enter to activate this console.", "")

        msg(100, "Formal firmware completed...")


def main():
    ubb_ipq840xx_factory = UAPIPQ40XXFactory()
    ubb_ipq840xx_factory.run()

if __name__ == "__main__":
    main()
