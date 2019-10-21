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


class AMQCA955XXFactory(ScriptBase):
    def __init__(self):
        super(AMQCA955XXFactory, self).__init__()
        self.ver_extract()
        self._init_vars()

    def _init_vars(self):

        # U-boot prompt
        self.ubpmt = {
            'dc97': "ath>"
        }

        # linux console prompt
        self.lnxpmt = {
            'dc97': "XC#"
        }

        self.bootloader = {
            'dc97': "dc97-bootloader.bin"
        }

        baseip = 20
        self.prod_dev_ip = "192.168.1." + str((int(self.row_id) + baseip))

        tmpdir = "/tmp/"
        self.tftpdir = self.tftpdir + "/"
        self.am_dir = os.path.join(self.fcd_toolsdir, "am")
        self.common_dir = os.path.join(self.fcd_toolsdir, "common")
        self.id_rsa = self.am_dir + "/id_rsa"
        self.eeprom_bin = "e.b." + self.row_id
        self.eeprom_txt = "e.t." + self.row_id
        self.eeprom_tgz = "e." + self.row_id + ".tgz"
        self.eeprom_signed = "e.s." + self.row_id
        self.eeprom_check = "e.c." + self.row_id
        self.bomrev = "13-" + self.bom_rev
        helperexe = "helper_ARxxxx_11ac"
        flash_unclockexe = "fl_lock"
        self.dut_helper_path = os.path.join(self.am_dir , helperexe)
        self.dut_flunlock_path = os.path.join(self.am_dir , flash_unclockexe)
        eeexe = "x86-64k-ee"
        self.eetool = os.path.join(self.common_dir , eeexe)
        self.uboot_address =  "0x9f000000"
        self.uboot_size =  "0x50000"
        self.cfg_address = "0x9ffb0000"
        self.cfg_size = "0x40000"
        self.eeprom_address = "0x9fff0000"
        self.eeprom_size = "0x10000"
        self.dropbear_key = "/tmp/dropbear_key.rsa." + self.row_id
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
        cmd = "tftpboot 0x81000000 images/" + self.bootloader[self.board_id]
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        self.pexp.expect_only(30, "Bytes transferred")
        cmd = "erase {} +{} && cp.b 0x81000000 {} $filesize".format(self.uboot_address, self.uboot_size, self.uboot_address)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        time.sleep(1)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "re\r")
        self._stop_uboot()

        msg(15, "Check EEPROM Data")

        #self.pexp.expect_action(30, self.ubpmt[self.board_id], "cp.b {0} 0x81000000 {1}".format(self.eeprom_address, self.eeprom_size))
        output = self.pexp.expect_get_output("md.b 0x9fff5000 2", self.ubpmt[self.board_id])

        if ("9fff5000: 44 08" not in output):
            error_critical("Board is not callibrated")

        output = self.pexp.expect_get_output("md.b 0x9fff5006 3", self.ubpmt[self.board_id])

        if ("9fff5006: 00 03 7f" in output):
            error_critical("Board is not callibrated")
        else:
            log_debug("Board is callibrated")

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

        msg(20, "Write EEPROM Data")
        log_debug("Copying EEPROM to RAM")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "cp.b {0} 0x81000000 {1}".format(self.eeprom_address, self.eeprom_size))
    
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "md.b 0x81000000 128")
        #self.pexp.expect_action(30, self.ubpmt[self.board_id], "md.b 0x81005000 128")
        time.sleep(2)

        hw_rev = self.bom_rev.split('-')
        rev_hex = int(hw_rev[0])*256 + int(hw_rev[1])
        log_debug("{} {} {} {}".format(self.bom_rev, hw_rev[0], hw_rev[1],rev_hex))

        log_debug("Writing Data to RAM")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "mw.l 0x81000010 {0:0{1}x}".format(rev_hex, 8))
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "mw.b 0x81000014 0x52")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "mw.w 0x81000016 {0:0{1}x}".format(13,4))
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "mw.l 0x8100000c {0}0777\r".format(self.board_id))
        
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "md.b 0x81000000 128")
        #self.pexp.expect_action(30, self.ubpmt[self.board_id], "md.b 0x81005000 128")
        time.sleep(2)
        
        log_debug("Erasing EEPROM...")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetprotect spm off")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "erase {0} +{1}".format(self.eeprom_address, self.eeprom_size))
        time.sleep(3)
        
        log_debug("Copying RAM to EEPROM...")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "cp.b 0x81000000 {0} {1}".format(self.eeprom_address, self.eeprom_size))
        time.sleep(3)
        
        log_debug("SET MAC...")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetmac -a " + self.mac)

        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetmac")

        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetrd " + self.region + " 1 1")

        output = self.pexp.expect_get_output("md.b 0x9fff1000 2", self.ubpmt[self.board_id])

        if ("9fff1000: 02 02" in output):
            #Got Second Radio
            self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetrd " + self.region + " 1 0")

        self.pexp.expect_action(30, self.ubpmt[self.board_id], "md.b {} 128".format(self.eeprom_address))
        time.sleep(2)

        self.pexp.expect_action(30, self.ubpmt[self.board_id], "re")

        self._stop_uboot()
        time.sleep(3)
        self._set_uboot_network()

        #msg(20, "Do ubntw")
        #cmd = "ubntw all {0} {1} {2} 0".format(self.mac, self.board_id, self.bomrev) 
        #self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        #time.sleep(1)
        #self.pexp.expect_action(30, self.ubpmt[self.board_id], "ubntw dump")

        msg(25, "Flash a temporary config")
        self._set_uboot_network()
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "printenv")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "tftpboot 0x81000000 tools/am/cfg_part_qca9557.bin")
        self.pexp.expect_action(30, "Bytes transferred", "go ${ubntaddr} usetprotect spm off")

        cmd = "erase {0} +{1}; cp.b 0x81000000 {0} {1}".format(self.cfg_address, self.cfg_size)
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
        self.pexp.expect_only(30, "Image Signature Verified, Success")
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

        scp_cmd = "scp -i {0} -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ".format(self.id_rsa) \
                + "{0} fcd@{1}:/tmp/fl_lock".format(self.dut_flunlock_path, self.prod_dev_ip)
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
        regsubparams = sto
        if (int(rtc) > 0):
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")

        regparam = [
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            regsubparams,
            "-i field=flash_eeprom,format=binary,pathname=" + self.tftpdir + self.eeprom_bin,
            "-i field=fcd_id,format=hex,value=" + self.fcd_id,
            "-i field=fcd_version,format=hex,value=" + self.sem_ver,
            "-i field=sw_id,format=hex,value=" + self.sw_id,
            "-i field=sw_version,format=hex,value=" + self.fw_ver,
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

        cmd = "sudo /usr/local/sbin/client_x86_release_20190507 " + regparamj
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

        msg(70, "Write signed EEPROM")
        unlock_cmd = "chmod 555 /tmp/fl_lock; /tmp/fl_lock -l 0"
        self.pexp.expect_action(180, self.lnxpmt[self.board_id], unlock_cmd )
        
        scp_cmd = "scp -i {0} -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ".format(self.id_rsa) \
                + "{0}{1} fcd@{2}:/tmp/".format(self.tftpdir, self.eeprom_signed, self.prod_dev_ip)
        self.fcd.common.xcmd(cmd=scp_cmd)

        cmd = 'ls -als /tmp/*'
        self.pexp.expect_action(180, self.lnxpmt[self.board_id], cmd )

        helper_cmd2 = "cd /tmp/; ./helper -q -i field=flash_eeprom,format=binary,pathname=/tmp/{0}".format(self.eeprom_signed)
        self.pexp.expect_action(180, self.lnxpmt[self.board_id], helper_cmd2 )

        cmd = "hexdump /dev/mtdblock5 -n 40"
        self.pexp.expect_action(180, self.lnxpmt[self.board_id], cmd )

        self.pexp.expect_action(180, self.lnxpmt[self.board_id], "reboot -f" )
        self._stop_uboot()
        time.sleep(3)
        self._set_uboot_network()

        #msg(60, "Add RSA Key")
        #
        #cmd = "rm " + self.dropbear_key + "; dropbearkey -t rsa -f " + self.dropbear_key
        #[sto, rtc] = self.fcd.common.xcmd(cmd)
        #if (int(rtc) > 0):
        #    error_critical("Generate RSA key failed!!")
        #else:
        #    log_debug("Generate RSA key successfully")

        #cmd = self.eetool + " -f " + self.tftpdir + self.eeprom_signed + " -K " + self.dropbear_key
        #log_debug("cmd: " + cmd)
        #[sto, rtc] = self.fcd.common.xcmd(cmd)
        #if (int(rtc) > 0):
        #    error_critical("Append RSA key failed!!")
        #else:
        #    log_debug("Addend RSA key successfully")

        #
        #
        #cmd = "tftpboot 84000000 " + self.eeprom_signed
        #self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)
        #self.pexp.expect_action(30, "Bytes transferred", "usetprotect spm off")
        #log_debug("File sent. Writing eeprom")

        #self.pexp.expect_action(30, self.ubpmt[self.board_id], "sf probe")

        #cmd = "sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.eeprom_address, self.eeprom_size)
        #self.pexp.expect_action(30, self.ubpmt[self.board_id], cmd)

        msg(70, "Erase tempoarary config")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "erase {0} +{1}\r\r".format(self.cfg_address, self.cfg_size))	
        time.sleep(5)
        #log_progress 95 "Configuration erased"

        msg(80, "Write default setting")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} uclearcfg")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetenv NORESET")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetenv serverip 192.168.1.254")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetenv ipaddr 192.168.1.20")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetenv bootargs console=ttyS0,115200 rootfstype=squashfs init=/init")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usaveenv")
        time.sleep(3)
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "go ${ubntaddr} usetmac")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "printenv")

        msg(90, "Final Boot")
        self.pexp.expect_action(30, self.ubpmt[self.board_id], "reset\r")
        self.pexp.expect_action(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_action(10, "login:", "ubnt")
        self.pexp.expect_action(10, "Password:", "ubnt")
        self.pexp.expect_only(10, self.lnxpmt[self.board_id])

        msg(100, "Formal firmware completed...")


def main():
    am_9cq95xx_factory = AMQCA955XXFactory()
    am_9cq95xx_factory.run()

if __name__ == "__main__":
    main()
