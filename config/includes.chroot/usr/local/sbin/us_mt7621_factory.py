#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class USFLEXFactory(ScriptBase):
    def __init__(self):
        super(USFLEXFactory, self).__init__()

    def GetImgfromSrv(self, Img):
        self.pexp.expect_action(30, self.bootloader_prompt, "tftpboot 84000000 "+Img)
        self.pexp.expect_action(30, "Bytes transferred = "+str(os.stat(Img).st_size), "")

    def SetBootNet(self):
        #self.pexp.expect_action(30, self.bootloader_prompt, "set ethaddr "+prod_dev_tmp_mac)
        self.pexp.expect_action(30, self.bootloader_prompt, "set ipaddr " + self.var.us.ip)
        self.pexp.expect_action(30, self.bootloader_prompt, "set serverip " + self.tftp_server)

    def CheckBootNet(self, MaxCnt):
        cnt = 0
        while(cnt < MaxCnt):
            self.pexp.expect_action(30, self.bootloader_prompt, "ping " + self.tftp_server)
            if self.pexp.expect_action(20, "host " + self.tftp_server + " is alive", "") == 0:
                break
            cnt = cnt + 1
        return 0 if cnt < MaxCnt else -1

    def is_network_alive_in_uboot(self, retry=1):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.tftp_server)
            extext_list = ["host " + self.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def CheckRadioStat(self):
        radio_check = {'ec25': ('0x8052', '/dev/mtd2', '0x02')}
        if self.board_id in radio_check:
            log_debug('Checking radio calibration status...')
            ckaddr = radio_check[self.board_id][0]
            factorymtd = radio_check[self.board_id][1]
            checkrst = radio_check[self.board_id][2]

            cmd = ['hexdump', '-n 1 -s', ckaddr, '-e', ' \'\"0x%02x\\n\" \' ', factorymtd]
            cmd = ' '.join(cmd)

            ret = self.pexp.expect_get_output(cmd, self.bootloader_prompt)
            if rtbuf[1] == checkrst:
                log_debug('Radio was calibrated')
            else:
                error_critical("Radio was NOT calibrated, status result is {}".format(rtbuf[1]))
        else:
            print("Pass checking radio status")

    def run(self):
        """
        Main procedure of factory
        """

        eepmexe = "mt7621-ee"
        eeprom_bin = "e.b."+self.row_id
        eeprom_txt = "e.t."+self.row_id
        eeprom_tgz = "e."+self.row_id+".tgz"
        eeprom_signed = "e.s."+self.row_id
        eeprom_check = "e.c."+self.row_id
        mtdpart = "/dev/mtdblock3"
        tmpdir = "/tmp/"

        # number of mac
        macnum = {'ed10': "3",
                  'ec25': "1",
                  'ec26': "1"}

        # number of WiFi
        wifinum = {'ed10': "0",
                   'ec25': "2",
                   'ec26': "2"}

        # number of Bluetooth
        btnum = {'ed10': "0",
                 'ec25': "1",
                 'ec26': "1"}

        vlanport_idx = {'ed10': "'6 4'",
                        'ec25': "'6 0'",
                        'ec26': "'6 0'"}

        log_debug(msg="qrcode_hex=" + self.var.us.qrcode_hex)
        cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
        [sto, _] = self.fcd.common.xcmd(cmd)
        if (int(sto.decode()) > 0):
            error_critical("Caps Lock is on")

        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()
        self.set_bootloader_prompt("MT7621 #")

        bootimg = "{}/{}".format(self.fwdir,
                                 self.board_id+"-uboot.bin")

        fcdimg = "{}/{}".format(self.fwdir,
                                self.board_id+"-fcd.bin")

        fwimg = "{}/{}".format(self.fwdir,
                               self.fwimg)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(6, "Waiting for device, 1st time...")
        rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
        if rt != 0:
            error_critical("Failed to detect device")

        self.pexp.expect_action(30, self.bootloader_prompt, "sf probe")
        self.pexp.expect_only(30, "flash manufacture id:")

        msg(6, "Setting IP address and checking network in u-boot, 1st time...")
        self.SetBootNet()

        if self.is_network_alive_in_uboot(retry=3) is False:
            error_critical("Failed to ping tftp server in u-boot")

        msg(8, "Getting uboot from tftp server, 1st time...")
        
        self.GetImgfromSrv(bootimg)
        self.pexp.expect_action(30, self.bootloader_prompt, "sf probe")
        self.pexp.expect_action(30, "flash manufacture id:", "")
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

        msg(8, "Waiting for device, 2nd time...")
        rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
        if rt != 0:
            error_critical("Failed to detect device")
        self.pexp.expect_action(30, self.bootloader_prompt, "")

        msg(8, "Setting IP address and checking network in u-boot, 2nd time...")
        self.SetBootNet()
      
        if self.is_network_alive_in_uboot(retry=3) is False:
            error_critical("Failed to ping tftp server in u-boot")

        msg(10, "Getting manufacturing kernel from tftp server, 1st time...")
        self.GetImgfromSrv(fcdimg)
        self.pexp.expect_action(30, self.bootloader_prompt, "bootm")

        msg(12, 'Waiting for manufacturing kernel ready, 1st time...')
        rt = self.pexp.expect_action(90, "Please press Enter to activate this console","")
        if rt != 0:
            error_critical("Failed to boot manufacturing kernel")

        self.pexp.expect_action(30, "UBNT login: ", "ubnt")
        self.pexp.expect_action(30, "Password: ", "ubnt")

        self.CheckRadioStat()

        self.pexp.expect_action(30, self.linux_prompt, "dmesg -n 1")

        msg(14, 'Setting hardware ID in EEPROM...')

        sstr = [eepmexe,
                "-F",
                "-r "+"113-"+self.bom_rev,
                "-s 0x"+self.board_id,
                "-m "+self.mac,
                "-c 0x"+self.region,
                "-e "+macnum[self.board_id],
                "-w "+wifinum[self.board_id],
                "-b "+btnum[self.board_id],
                "-k",
                "-p Factory"]
        sstrj = ' '.join(sstr)
    
        if(1):#for devlop
            self.pexp.expect_action(30, self.linux_prompt, sstrj)
            self.pexp.expect_action(60, self.linux_prompt, eepmexe + " -I -v 2>&1")
            # self.pexp.expect_action(30, "DEBUG: SBD Magic: 55424e54 \(OK\)", "")
            # self.pexp.expect_action(30, "DEBUG: SBD CRC:", "")
            # self.pexp.expect_action(30, "\(OK, expect:", "")
            # self.pexp.expect_action(30, "DEBUG: SBD Length: 100", "")
            # self.pexp.expect_action(30, "DEBUG: SBD Format: 0x0002", "")
            # self.pexp.expect_action(30, "DEBUG: SBD Version: 0x0001", "")
            # self.pexp.expect_action(30, "DEBUG: SBD system ID: 0777:"+boardid, "")
            # self.pexp.expect_action(30, "DEBUG: SBD HW revision: "+bomrev, "")
            # self.pexp.expect_action(30, "DEBUG: SBD HW Address Base: "+macaddr.lower(), "")
            # self.pexp.expect_action(30, "DEBUG: SBD Ethernet MAC count: "+macnum[boardid], "")
            # self.pexp.expect_action(30, "DEBUG: SBD WiFi RADIO count: "+wifinum[boardid], "")
            # self.pexp.expect_action(30, "DEBUG: SBD BT RADIO count: "+btnum[boardid], "")
            # self.pexp.expect_action(30, "DEBUG: SBD Regulatory Domain: 0x"+region, "")
            # self.pexp.expect_action(30, "DEBUG: SBD PartitionSHA key:", "")
            # self.pexp.expect_action(30, "DEBUG: DBD eth0 hwaddr: "+macaddr.lower(), "")
            # self.pexp.expect_action(30, "DEBUG: DBD system ID: 0777:"+boardid, "")
            # self.pexp.expect_action(30, "DEBUG: DBD HW revision: "+bomrev, "")
            # self.pexp.expect_action(30, "DEBUG: EXTRA ENTRY\[0\]: DSS KEY", "")
            self.pexp.expect_only(30, "DEBUG: EXTRA ENTRY\[1\]: RSA KEY")
            self.pexp.expect_action(30, self.linux_prompt, "")
            self.pexp.expect_action(30, self.linux_prompt, "cmp  /tmp/dropbear_key.dss /tmp/dropbear_key_dump.dss 2>&1 ; echo $?")
            self.pexp.expect_action(30, "0", "")

            msg(16, 'Rebooting manufacturing kernel...')
            self.pexp.expect_action(30, self.linux_prompt, "reboot -f")

            msg(18, "Waiting for device, 3rd time...")
            self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
            self.pexp.expect_action(30, self.bootloader_prompt, "")

            msg(20, "Setting IP address and checking network in u-boot, 3rd time...")
            self.SetBootNet()
            
            if self.is_network_alive_in_uboot(retry=3) is False:
                error_critical("Failed to ping tftp server in u-boot")
    
            msg(22, "Getting manufacturing kernel from tftp server, 2nd time...")
            self.GetImgfromSrv(fcdimg)
            self.pexp.expect_action(30, self.bootloader_prompt, "bootm")

            msg(24, 'Waiting for manufacturing kernel ready, 2nd time...')
            self.pexp.expect_action(90, "Please press Enter to activate this console","")
            self.pexp.expect_action(30, "UBNT login: ", "ubnt")
            self.pexp.expect_action(30, "Password: ", "ubnt")
            self.pexp.expect_action(30, self.linux_prompt, "dmesg -n 1")
            if(0):
                msg(26, 'Checking hardware ID in EEPROM...')
                self.pexp.expect_action(30, self.linux_prompt, eepmexe + " -I -v 2>&1")
                self.pexp.expect_action(30, "DEBUG: SBD Magic: 55424e54 \(OK\)")
                self.pexp.expect_action(30, "DEBUG: SBD CRC:")
                self.pexp.expect_action(30, "\(OK, expect:")
                self.pexp.expect_action(30, "DEBUG: SBD Length: 100")
                self.pexp.expect_action(30, "DEBUG: SBD Format: 0x0002")
                self.pexp.expect_action(30, "DEBUG: SBD Version: 0x0001")
                self.pexp.expect_action(30, "DEBUG: SBD system ID: 0777:"+self.board_id)
                self.pexp.expect_action(30, "DEBUG: SBD HW revision: "+self.bom_rev)
                self.pexp.expect_action(30, "DEBUG: SBD HW Address Base: "+self.mac.lower())
                self.pexp.expect_action(30, "DEBUG: SBD Ethernet MAC count: "+macnum[self.board_id])
                self.pexp.expect_action(30, "DEBUG: SBD WiFi RADIO count: "+wifinum[self.board_id])
                self.pexp.expect_action(30, "DEBUG: SBD BT RADIO count: "+btnum[self.board_id])
                self.pexp.expect_action(30, "DEBUG: SBD Regulatory Domain: 0x"+self.region)
                self.pexp.expect_action(30, "DEBUG: SBD PartitionSHA key:")
                self.pexp.expect_action(30, "DEBUG: DBD eth0 hwaddr: "+self.mac.lower())
                self.pexp.expect_action(30, "DEBUG: DBD system ID: 0777:"+self.board_id)
                self.pexp.expect_action(30, "DEBUG: DBD HW revision: "+self.bom_rev)
                self.pexp.expect_action(30, "DEBUG: EXTRA ENTRY\[0\]: DSS KEY")
                self.pexp.expect_action(30, "DEBUG: EXTRA ENTRY\[1\]: RSA KEY")

            msg(28, 'Configuring ethernet switch...')
            self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 set enable_vlan 1")
            self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 vlan 1 set vid 1")
            self.pexp.expect_action(30, self.linux_prompt, 
                                    "swconfig dev switch0 vlan 1 set ports "+vlanport_idx[self.board_id])
            self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 set apply")

            msg(30, 'Checking network in manufacturing kernel...')
            self.pexp.expect_action(30, self.linux_prompt, "[ $(ifconfig | grep -c eth0) -gt 0 ] || ifconfig eth0 up")
            self.pexp.expect_action(30, self.linux_prompt, "ifconfig eth0 "+self.var.us.ip)
            self.pexp.expect_action(30, self.linux_prompt, "ping -c 1 "+self.tftp_server)
            self.pexp.expect_action(30, self.linux_prompt, "1 packets received")

            msg(32, 'Running registration helper...')
            self.pexp.expect_action(30, self.linux_prompt, "cd "+tmpdir)
            sstr = [self.var.us.get_helper(self.board_id),
                    "-c product_class=basic",
                    "-o field=flash_eeprom,format=binary,pathname="+eeprom_bin,
                    ">",
                    eeprom_txt]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.linux_prompt, sstrj)

            #msg(34, 'Uploading registration helper out files...')
            os.system("rm -f " + self.tftpdir+"/"+eeprom_tgz)
            os.system("touch " + self.tftpdir+"/"+eeprom_tgz)
            os.system("chmod 777 " + self.tftpdir+"/"+eeprom_tgz)
  
            sstr = ["tar",
                    "cf",
                    eeprom_tgz,
                    eeprom_bin,
                    eeprom_txt]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.linux_prompt, sstrj)

            sstr = ["tftp",
                    "-p",
                    "-l",
                    eeprom_tgz,
                    self.tftp_server]
            sstrj = ' '.join(sstr)
            msg(34, 'Uploading registration helper out files...')
            self.pexp.expect_action(30, self.linux_prompt, sstrj)

            #time.sleep(2)
            self.pexp.expect_action(30, self.linux_prompt, "")
            cmd = "tar xvf "+self.tftpdir+"/"+eeprom_tgz+" -C " + self.tftpdir
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                error_critical("Decompressing "+eeprom_tgz+" file failed!!")
            else:
                log_debug("Decompressing "+eeprom_tgz+" files successfully")

            msg(36, 'Starting to do registration...')
            log_debug("Starting to do registration ...")

            eeprom_txt_1 = self.tftpdir+"/"+eeprom_txt+"-1"
            cmd = ["grep field=",
                   self.tftpdir+"/"+eeprom_txt,
                   "|",
                   "grep -v flash_eeprom",
                   "|",
                   'while read line; do echo -n "-i $line "; done ',
                   ">"+eeprom_txt_1]
            cmdj = ' '.join(cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmdj)

            cmd = ["cat "+eeprom_txt_1]
            cmdj = ' '.join(cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmdj)
            regsubparams = sto.decode('UTF-8')
            if (int(rtc) > 0):
                error_critical("Extract parameters failed!!")
            else:
                log_debug("Extract parameters successfully")

            regparam = ["-k "+self.pass_phrase,
                        regsubparams,
                        "-i field=qr_code,format=hex,value="+self.var.us.qrcode_hex,
                        "-i field=flash_eeprom,format=binary,pathname="+self.tftpdir+"/"+eeprom_bin,
                        "-o field=flash_eeprom,format=binary,pathname="+self.tftpdir+"/"+eeprom_signed,
                        "-o field=registration_id",
                        "-o field=result",
                        "-o field=device_id",
                        "-o field=registration_status_id",
                        "-o field=registration_status_msg",
                        "-o field=error_message",
                        "-x "+self.key_dir+"ca.pem",
                        "-y "+self.key_dir+"key.pem",
                        "-z "+self.key_dir+"crt.pem",
                        "-h devreg-prod.ubnt.com"]

            regparamj = ' '.join(regparam)
            cmd = "sudo /usr/local/sbin/client_x86_release "+regparamj
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            time.sleep(5)
            if (int(rtc) > 0):
                error_critical("client_x86 registration failed!!")
            else:
                log_debug("Excuting client_x86 registration successfully")

            rtf = os.path.isfile(self.tftpdir+"/"+eeprom_signed)
            if (rtf is not True):
                error_critical("Can't find "+eeprom_signed)

                msg(38, 'Finalizing device registration...')
            log_debug("Send signed eeprom file from host to DUT ...")
            sstr = ["tftp",
                    "-g",
                    "-r",
                    eeprom_signed,
                    self.tftp_server]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.linux_prompt, sstrj)

            log_debug("Starting to write signed information to SPI flash ...")
            self.pexp.expect_action(30, self.linux_prompt, "cd "+tmpdir)
            sstr = [self.var.us.get_helper(self.board_id),
                    "-q",
                    "-i field=flash_eeprom,format=binary,pathname="+tmpdir+eeprom_signed]
            # sstr = ["dd",
            #        "if="+tmpdir+eeprom_signed,
            #        "of="+tmpdir+eeprom_check,
            #        "bs=64k",
            #        "count=1"]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.linux_prompt, sstrj)
            time.sleep(2)
    
            log_debug("Starting to extract the EEPROM content from SPI flash ...")
            self.pexp.expect_action(30, self.linux_prompt, "sync")
            sstr = ["dd",
                    "if="+mtdpart,
                    "of="+tmpdir+eeprom_check]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.linux_prompt, sstrj)
            time.sleep(2)

            log_debug("Send "+eeprom_check+" from DUT to host ...")

            os.system("rm -f " + self.tftpdir+"/"+eeprom_check)
            os.system("touch " + self.tftpdir+"/"+eeprom_check)
            os.system("chmod 777 " + self.tftpdir+"/"+eeprom_check)

            sstr = ["tftp",
                    "-p",
                    "-l",
                    eeprom_check,
                    self.tftp_server]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.linux_prompt, sstrj)
            time.sleep(2)

            if os.path.isfile(self.tftpdir+"/"+eeprom_check):
                log_debug("Starting to compare the"+eeprom_check+" and "+eeprom_signed+" files ...")
                cmd = ["/usr/bin/cmp",
                       self.tftpdir+"/"+eeprom_check,
                       self.tftpdir+"/"+eeprom_signed]
                cmdj = ' '.join(cmd)
                [sto, rtc] = self.fcd.common.xcmd(cmdj)
                if (int(rtc) > 0):
                    error_critical("Comparing files failed!!")
                else:
                    log_debug("Comparing files successfully")
            else:
                log_debug("Can't find the "+eeprom_check+" and "+eeprom_signed+" files ...")

            msg(50, "Finish doing signed file and EEPROM checking ...")
    
            log_debug("Change to product firware...")
            self.pexp.expect_action(30, self.linux_prompt, "reboot -f")
    
            rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
            if rt != 0:
                error_critical("Failed to detect device")
        
            self.pexp.expect_action(30, self.bootloader_prompt, "")

            msg(52, "Setting IP address and checking network in u-boot, 4th time...")
            self.SetBootNet()
            
            if self.is_network_alive_in_uboot(retry=3) is False:
                error_critical("Failed to ping tftp server in u-boot")


            msg(54, "Putting device to urescue mode...")
            self.pexp.expect_action(30, self.bootloader_prompt, "set ubnt_clearcfg TRUE")
            self.pexp.expect_action(30, self.bootloader_prompt, "set ubnt_clearenv TRUE")
            self.pexp.expect_action(30, self.bootloader_prompt, "set do_urescue TRUE")
            self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
            self.pexp.expect_action(30, "Listening for TFTP transfer on", "")
    
            msg(56, "Uploading released firmware...")
            cmd = ["atftp",
                   "-p",
                   "-l",
                   fwimg,
                   self.var.us.ip]
            cmdj = ' '.join(cmd)

            [sto, rtc] = self.fcd.common.xcmd(cmdj)
            if (int(rtc) > 0):
                error_critical("Failed to upload firmware image")
            else:
                log_debug("Uploading firmware image successfully")
    
            msg(58, "Checking firmware...")
            self.pexp.expect_only(30, "Bytes transferred = ")
            self.pexp.expect_only(30, "Firmware Version:")
            self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
    
            msg(60, "Updating released firmware...")
            self.pexp.expect_only(60, "Updating u-boot partition \(and skip identical blocks\)")
            self.pexp.expect_only(60, "done")
            self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
            self.pexp.expect_only(120, "done")

            msg(62, 'Booting into released firmware...')
            rt = self.pexp.expect_action(120, "Please press Enter to activate this console","")
            if rt != 0:
                error_critical("Failed to boot manufacturing kernel")

            os.system("sleep 5")
            self.pexp.expect_action(30, "", "")
            self.pexp.expect_action(30, "UBNT login: ", "ubnt")
            self.pexp.expect_action(30, "Password: ", "ubnt")
            self.pexp.expect_action(30, self.linux_prompt, "dmesg -n 1")

            msg(64, 'Checking EEPROM...')
            self.pexp.expect_action(30, self.linux_prompt, "cat /proc/ubnthal/system.info")
            self.pexp.expect_only(30, "flashSize=33554432")
            self.pexp.expect_only(30, "systemid="+self.board_id)
            self.pexp.expect_only(30, "serialno="+self.mac.lower())
            self.pexp.expect_only(30, "qrid="+self.qrcode)
            self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/build.properties")
            self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/version")

            msg(100, "Completing firmware upgrading ...")

            exit(0)


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        us_flex_factory = USFLEXFactory()
        us_flex_factory.run()

main()
