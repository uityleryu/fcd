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

'''
boardid = sys.argv[1]
macaddr = sys.argv[2]
pshr = sys.argv[3]
keydir = sys.argv[4]
tty = "/dev/"+sys.argv[5]
idx = sys.argv[6]
bomrev = sys.argv[7]
qrcode = sys.argv[8]
region = sys.argv[9]
svip = "192.168.1.19"
prod_ip_base = 31
prod_pfx_len = 34
prod_dev_ip_base = prod_ip_base + int(idx)
prod_dev_ip = "192.168.1." + str(prod_dev_ip_base)
 
prod_dev_tmp_mac = "00:15:6d:00:00:0"+idx
# U-boot prompt
ubpmt = {'ed10':"MT7621 #",
         'ec25':"MT7621 #",
         'ec26':"MT7621 #"}

# linux console prompt
lnxpmt = {'ed10':"#",
          'ec25':"#",
          'ec26':"#"}

# number of mac
macnum = {'ed10':"3",
          'ec25':"1",
          'ec26':"1"}

# number of WiFi
wifinum = {'ed10':"0",
           'ec25':"2",
           'ec26':"2"}

# number of Bluetooth
btnum = {'ed10':"0",
         'ec25':"1",
         'ec26':"1"}

vlanport_idx = {'ed10':"'6 4'",
              'ec25':"'6 0'",
              'ec26':"'6 0'"}

radio_check = {'ec25':('0x8052', '/dev/mtd2', '0x02')}

tmpdir = "/tmp/"
tftpdir = "/tftpboot/"
proddir = tftpdir+boardid+"/"
toolsdir = tftpdir+"tools/"
loadaddr = "84000000"

'''


class USFLEXFactory(ScriptBase):
    def __init__(self):
        super(USFLEXFactory, self).__init__()

    def GetImgfromSrv(self, Img):
        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "tftpboot 84000000 "+Img)
        self.pexp.expect_action(30, "Bytes transferred = "+str(os.stat(Img).st_size), "")

    def SetBootNet(self):
        #self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "set ethaddr "+prod_dev_tmp_mac)
        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "set ipaddr " + self.variable.us_factory.ip)
        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "set serverip " + self.variable.us_factory.tftp_server)

    def CheckBootNet(self, MaxCnt):
        cnt = 0
        while(cnt < MaxCnt):
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "ping " + self.variable.us_factory.tftp_server)
            if self.pexp.expect_action(20, "host " + self.variable.us_factory.tftp_server + " is alive", "") == 0:
                break
            cnt = cnt + 1
        return 0 if cnt < MaxCnt else -1
        
    def is_network_alive_in_uboot(self, retry=1):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.variable.us_factory.tftp_server)
            extext_list = ["host " + self.variable.us_factory.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def CheckRadioStat(self):
        radio_check = {'ec25':('0x8052', '/dev/mtd2', '0x02')}
        if self.variable.us_factory.board_id in radio_check:
            log_debug('Checking radio calibration status...')
            ckaddr = radio_check[self.variable.us_factory.board_id][0]
            factorymtd = radio_check[self.variable.us_factory.board_id][1]
            checkrst = radio_check[self.variable.us_factory.board_id][2]

            cmd = ['hexdump', '-n 1 -s', ckaddr, '-e', ' \'\"0x%02x\\n\" \' ', factorymtd]
            cmd = ' '.join(cmd)

            rtbuf = []
            self.pexp.expect_actionnrd(30, self.variable.common.bootloader_prompt, cmd, rtbuf)
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
        eeprom_bin = "e.b."+self.variable.us_factory.row_id
        eeprom_txt = "e.t."+self.variable.us_factory.row_id
        eeprom_tgz = "e."+self.variable.us_factory.row_id+".tgz"
        eeprom_signed = "e.s."+self.variable.us_factory.row_id
        eeprom_check = "e.c."+self.variable.us_factory.row_id
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

        log_debug(msg="qrcode_hex=" + self.variable.us_factory.qrcode_hex)
        cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
        [sto, _] = self.fcd.common.xcmd(cmd)
        if (int(sto.decode()) > 0):
            error_critical("Caps Lock is on")

        self.fcd.common.config_stty(self.variable.us_factory.dev)
        self.fcd.common.print_current_fcd_version()
        self.variable.common.set_bootloader_prompt("MT7621 #")
        
        bootimg = "{}/{}/{}/{}/{}".format(self.variable.common.tftp_server_dir,
                                          self.variable.common.firmware_dir,
                                          self.variable.us_factory.board_id,
                                          "fcd",
                                          self.variable.us_factory.board_id+".uboot")

        fcdimg = "{}/{}/{}/{}/{}".format(self.variable.common.tftp_server_dir,
                                         self.variable.common.firmware_dir,
                                         self.variable.us_factory.board_id,
                                         "fcd",
                                         self.variable.us_factory.board_id+"-fcd.kernel")

        fwimg = "{}/{}/{}/{}/{}".format(self.variable.common.tftp_server_dir,
                                        self.variable.common.firmware_dir,
                                        self.variable.us_factory.board_id,
                                        "fw",
                                        self.variable.us_factory.firmware_img)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.variable.us_factory.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.variable.us_factory.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(6, "Waiting for device, 1st time...")
        rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
        if rt != 0:
            error_critical("Failed to detect device")

        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "sf probe")
        self.pexp.expect_only(30, "flash manufacture id:")

        msg(6, "Setting IP address and checking network in u-boot, 1st time...")
        self.SetBootNet()

        if self.is_network_alive_in_uboot(retry=3) is False:
            error_critical("Failed to ping tftp server in u-boot")

        msg(8, "Getting uboot from tftp server, 1st time...")
        
        self.GetImgfromSrv(bootimg)
        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "sf probe")
        self.pexp.expect_action(30, "flash manufacture id:", "")
        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "reset")

        msg(8, "Waiting for device, 2nd time...")
        rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
        if rt != 0:
            error_critical("Failed to detect device")
        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "")

        msg(8, "Setting IP address and checking network in u-boot, 2nd time...")
        self.SetBootNet()
      
        if self.is_network_alive_in_uboot(retry=3) is False:
            error_critical("Failed to ping tftp server in u-boot")

        msg(10, "Getting manufacturing kernel from tftp server, 1st time...")
        self.GetImgfromSrv(fcdimg)
        self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "bootm")

        msg(12, 'Waiting for manufacturing kernel ready, 1st time...')
        rt = self.pexp.expect_action(90, "Please press Enter to activate this console","")
        if rt != 0:
            error_critical("Failed to boot manufacturing kernel")

        self.pexp.expect_action(30, "UBNT login: ", "ubnt")
        self.pexp.expect_action(30, "Password: ", "ubnt")

        self.CheckRadioStat()

        self.pexp.expect_action(30, self.variable.common.linux_prompt, "dmesg -n 1")

        msg(14, 'Setting hardware ID in EEPROM...')

        sstr = [eepmexe,
                "-F",
                "-r "+"113-"+self.variable.us_factory.bom_rev,
                "-s 0x"+self.variable.us_factory.board_id,
                "-m "+self.variable.us_factory.mac,
                "-c 0x"+self.variable.us_factory.region,
                "-e "+macnum[self.variable.us_factory.board_id],
                "-w "+wifinum[self.variable.us_factory.board_id],
                "-b "+btnum[self.variable.us_factory.board_id],
                "-k",
                "-p Factory"]
        sstrj = ' '.join(sstr)
    
        if(1):#for devlop
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)
            self.pexp.expect_action(60, self.variable.common.linux_prompt, eepmexe + " -I -v 2>&1")
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
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "")
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "cmp  /tmp/dropbear_key.dss /tmp/dropbear_key_dump.dss 2>&1 ; echo $?")
            self.pexp.expect_action(30, "0", "")

            msg(16, 'Rebooting manufacturing kernel...')
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "reboot -f")

            msg(18, "Waiting for device, 3rd time...")
            self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "")

            msg(20, "Setting IP address and checking network in u-boot, 3rd time...")
            self.SetBootNet()
            
            if self.is_network_alive_in_uboot(retry=3) is False:
                error_critical("Failed to ping tftp server in u-boot")
    
            msg(22, "Getting manufacturing kernel from tftp server, 2nd time...")
            self.GetImgfromSrv(fcdimg)
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "bootm")

            msg(24, 'Waiting for manufacturing kernel ready, 2nd time...')
            self.pexp.expect_action(90, "Please press Enter to activate this console","")
            self.pexp.expect_action(30, "UBNT login: ", "ubnt")
            self.pexp.expect_action(30, "Password: ", "ubnt")
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "dmesg -n 1")
            if(0):
                msg(26, 'Checking hardware ID in EEPROM...')
                self.pexp.expect_action(30, self.variable.common.linux_prompt, eepmexe + " -I -v 2>&1")
                self.pexp.expect_action(30, "DEBUG: SBD Magic: 55424e54 \(OK\)")
                self.pexp.expect_action(30, "DEBUG: SBD CRC:")
                self.pexp.expect_action(30, "\(OK, expect:")
                self.pexp.expect_action(30, "DEBUG: SBD Length: 100")
                self.pexp.expect_action(30, "DEBUG: SBD Format: 0x0002")
                self.pexp.expect_action(30, "DEBUG: SBD Version: 0x0001")
                self.pexp.expect_action(30, "DEBUG: SBD system ID: 0777:"+self.variable.us_factory.board_id)
                self.pexp.expect_action(30, "DEBUG: SBD HW revision: "+self.variable.us_factory.bom_rev)
                self.pexp.expect_action(30, "DEBUG: SBD HW Address Base: "+self.variable.us_factory.mac.lower())
                self.pexp.expect_action(30, "DEBUG: SBD Ethernet MAC count: "+macnum[self.variable.us_factory.board_id])
                self.pexp.expect_action(30, "DEBUG: SBD WiFi RADIO count: "+wifinum[self.variable.us_factory.board_id])
                self.pexp.expect_action(30, "DEBUG: SBD BT RADIO count: "+btnum[self.variable.us_factory.board_id])
                self.pexp.expect_action(30, "DEBUG: SBD Regulatory Domain: 0x"+self.variable.us_factory.region)
                self.pexp.expect_action(30, "DEBUG: SBD PartitionSHA key:")
                self.pexp.expect_action(30, "DEBUG: DBD eth0 hwaddr: "+self.variable.us_factory.mac.lower())
                self.pexp.expect_action(30, "DEBUG: DBD system ID: 0777:"+self.variable.us_factory.board_id)
                self.pexp.expect_action(30, "DEBUG: DBD HW revision: "+self.variable.us_factory.bom_rev)
                self.pexp.expect_action(30, "DEBUG: EXTRA ENTRY\[0\]: DSS KEY")
                self.pexp.expect_action(30, "DEBUG: EXTRA ENTRY\[1\]: RSA KEY")

            msg(28, 'Configuring ethernet switch...')
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "swconfig dev switch0 set enable_vlan 1")
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "swconfig dev switch0 vlan 1 set vid 1")
            self.pexp.expect_action(30, self.variable.common.linux_prompt, 
                                    "swconfig dev switch0 vlan 1 set ports "+vlanport_idx[self.variable.us_factory.board_id])
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "swconfig dev switch0 set apply")

            msg(30, 'Checking network in manufacturing kernel...')
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "[ $(ifconfig | grep -c eth0) -gt 0 ] || ifconfig eth0 up")
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "ifconfig eth0 "+self.variable.us_factory.ip)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "ping -c 1 "+self.variable.us_factory.tftp_server)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "1 packets received")

            msg(32, 'Running registration helper...')
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "cd "+tmpdir)
            sstr = [self.variable.us_factory.get_helper(),
                    "-c product_class=basic",
                    "-o field=flash_eeprom,format=binary,pathname="+eeprom_bin,
                    ">",
                    eeprom_txt]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)

            #msg(34, 'Uploading registration helper out files...')
            os.system("rm -f " + self.variable.common.tftp_server_dir+"/"+eeprom_tgz)
            os.system("touch " + self.variable.common.tftp_server_dir+"/"+eeprom_tgz)
            os.system("chmod 777 " + self.variable.common.tftp_server_dir+"/"+eeprom_tgz)
  
            sstr = ["tar",
                    "cf",
                    eeprom_tgz,
                    eeprom_bin,
                    eeprom_txt]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)

            sstr = ["tftp",
                    "-p",
                    "-l",
                    eeprom_tgz,
                    self.variable.us_factory.tftp_server]
            sstrj = ' '.join(sstr)
            msg(34, 'Uploading registration helper out files...')
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)
    
            #time.sleep(2)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "")
            cmd = "tar xvf "+self.variable.common.tftp_server_dir+"/"+eeprom_tgz+" -C " + self.variable.common.tftp_server_dir
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                error_critical("Decompressing "+eeprom_tgz+" file failed!!")
            else:
                log_debug("Decompressing "+eeprom_tgz+" files successfully")

            msg(36, 'Starting to do registration...')
            log_debug("Starting to do registration ...")
            # cmd = ["cat "+tftpdir+eeprom_txt,
            #        "|",
            #        'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
            #        "|",
            #        'grep -v \"eeprom\"',
            #        "|",
            #        "tr '\\n' ' '"]
   
            eeprom_txt_1 = self.variable.common.tftp_server_dir+"/"+eeprom_txt+"-1"
            cmd = ["grep field=",
                   self.variable.common.tftp_server_dir+"/"+eeprom_txt,
                   "|",
                   "grep -v flash_eeprom",
                   "|",
                   'while read line; do echo -n "-i $line "; done ',
                   ">"+eeprom_txt_1]
            cmdj = ' '.join(cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmdj)

   # cmd = ["grep field=",
   #         tftpdir+eeprom_txt,
   #         "|",
   #         "sed 's/^\(^field.*\)/-i \1 /g'"
   #         "grep -v flash_eeprom",
   #         "|",
   #         "tr '\n' ' '"]
   # cmdj = ' '.join(cmd)
   # [sto, rtc] = xcmd(cmdj)
   # regsubparams = sto.decode('UTF-8')
    
            cmd = ["cat "+eeprom_txt_1]
            cmdj = ' '.join(cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmdj)
            regsubparams = sto.decode('UTF-8')
            if (int(rtc) > 0):
                error_critical("Extract parameters failed!!")
            else:
                log_debug("Extract parameters successfully")

            regparam = ["-k "+self.variable.us_factory.pass_phrase,
                        regsubparams,
                        "-i field=qr_code,format=hex,value="+self.variable.us_factory.qrcode_hex,
                        "-i field=flash_eeprom,format=binary,pathname="+self.variable.common.tftp_server_dir+"/"+eeprom_bin,
                        "-o field=flash_eeprom,format=binary,pathname="+self.variable.common.tftp_server_dir+"/"+eeprom_signed,
                        "-o field=registration_id",
                        "-o field=result",
                        "-o field=device_id",
                        "-o field=registration_status_id",
                        "-o field=registration_status_msg",
                        "-o field=error_message",
                        "-x "+self.variable.us_factory.key_dir+"ca.pem",
                        "-y "+self.variable.us_factory.key_dir+"key.pem",
                        "-z "+self.variable.us_factory.key_dir+"crt.pem",
                        "-h devreg-prod.ubnt.com"]

            regparamj = ' '.join(regparam)
            cmd = "sudo /usr/local/sbin/client_x86_release "+regparamj
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            time.sleep(5)
            if (int(rtc) > 0):
                error_critical("client_x86 registration failed!!")
            else:
                log_debug("Excuting client_x86 registration successfully")

            rtf = os.path.isfile(self.variable.common.tftp_server_dir+"/"+eeprom_signed)
            if (rtf != True):
                error_critical("Can't find "+eeprom_signed)
    
                msg(38, 'Finalizing device registration...')
            log_debug("Send signed eeprom file from host to DUT ...")
            sstr = ["tftp",
                    "-g",
                    "-r",
                    eeprom_signed,
                    self.variable.us_factory.tftp_server]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)

            log_debug("Starting to write signed information to SPI flash ...")
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "cd "+tmpdir)
            sstr = [self.variable.us_factory.get_helper(),
                    "-q",
                    "-i field=flash_eeprom,format=binary,pathname="+tmpdir+eeprom_signed]
            # sstr = ["dd",
            #        "if="+tmpdir+eeprom_signed,
            #        "of="+tmpdir+eeprom_check,
            #        "bs=64k",
            #        "count=1"]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)
            time.sleep(2)
    
            log_debug("Starting to extract the EEPROM content from SPI flash ...")
            self.pexp.expect_action(30, self.variable.common.linux_prompt,"sync")
            sstr = ["dd",
                    "if="+mtdpart,
                    "of="+tmpdir+eeprom_check]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)
            time.sleep(2)

            log_debug("Send "+eeprom_check+" from DUT to host ...")

            os.system("rm -f " + self.variable.common.tftp_server_dir+"/"+eeprom_check)
            os.system("touch " + self.variable.common.tftp_server_dir+"/"+eeprom_check)
            os.system("chmod 777 " + self.variable.common.tftp_server_dir+"/"+eeprom_check)

            sstr = ["tftp",
                    "-p",
                    "-l",
                    eeprom_check,
                    self.variable.us_factory.tftp_server]
            sstrj = ' '.join(sstr)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, sstrj)
            time.sleep(2)

            if os.path.isfile(self.variable.common.tftp_server_dir+"/"+eeprom_check):
                log_debug("Starting to compare the"+eeprom_check+" and "+eeprom_signed+" files ...")
                cmd = ["/usr/bin/cmp",
                       self.variable.common.tftp_server_dir+"/"+eeprom_check,
                       self.variable.common.tftp_server_dir+"/"+eeprom_signed]
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
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "reboot -f")
    
            rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")
            if rt != 0:
                error_critical("Failed to detect device")
        
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "")

            msg(52, "Setting IP address and checking network in u-boot, 4th time...")
            self.SetBootNet()
            
            if self.is_network_alive_in_uboot(retry=3) is False:
                error_critical("Failed to ping tftp server in u-boot")


            msg(54, "Putting device to urescue mode...")
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "set ubnt_clearcfg TRUE")
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "set ubnt_clearenv TRUE")
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "set do_urescue TRUE")
            self.pexp.expect_action(30, self.variable.common.bootloader_prompt, "bootubnt -f")
            self.pexp.expect_action(30, "Listening for TFTP transfer on", "")
    
            msg(56, "Uploading released firmware...")
            cmd = ["atftp",
                   "-p",
                   "-l",
                   fwimg,
                   self.variable.us_factory.ip]
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
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "dmesg -n 1")

            msg(64, 'Checking EEPROM...')
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "cat /proc/ubnthal/system.info")
            self.pexp.expect_only(30, "flashSize=33554432")
            self.pexp.expect_only(30, "systemid="+self.variable.us_factory.board_id)
            self.pexp.expect_only(30, "serialno="+self.variable.us_factory.mac.lower())
            self.pexp.expect_only(30, "qrid="+self.variable.us_factory.qrcode)
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "cat /usr/lib/build.properties")
            self.pexp.expect_action(30, self.variable.common.linux_prompt, "cat /usr/lib/version")

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