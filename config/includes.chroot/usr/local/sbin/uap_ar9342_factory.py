#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import subprocess

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    E801: 113-10358 UniFi Device Bridge
    E7FC: 113-00556 NanoBeam 5AC Gen2(W)
'''


class AMAR9342Factory(ScriptBase):
    def __init__(self):
        super(AMAR9342Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.fcd_id = "0x0004"
        self.product_class = "basic"
        self.devregpart = "/dev/mtdblock6"
        self.helperexe = "helper_ARxxxx_11ac_20210329"
        self.unlockexe = "fl_lock_11ac_re"
        self.bootloader_prompt = ">"
        self.uboot_img = "{}/{}-uboot.bin".format(self.image, self.board_id)
        self.cfg_part = os.path.join(self.tools, "uap", "cfg_part_ac_series.bin")
        self.helper_path = os.path.join("uap")
        self.uboot_w_app = False
        self.lock_dfs = False
        self.unlock_mark = "52ff"
        self.clear_mark = "ffff"
        self.host_ip = self.tftp_server
        self.ssh_DUT = None

        # Country Lock is a value
        self.country_lock = 0

        self.second_wifi_found = False

        self.is_wasp = [
            "e7fc", "e801"
        ]

        self.dfs_lock_list = [
            "e1f5", "e2c5", "e2c7", "e2f3", "e3d5", "e3d6", "e3d8", "e3f5", "e4f3", "e4f5", "e5f5", "e6f5",
            "e7e5", "e7e6", "e7e7", "e7e8", "e7e9", "e7f5", "e7f7", "e7f9", "e8f5", "e9f5", "e7ff", "e7fe",
            "e7fb", "e8e5"
        ]

        # number of WiFi
        self.wifinum = {
            'e7fc': "2", 'e801': "1"
        }

        self.ethnum = {
            'e801': "2",

        }

        self.wifinum = {
            'e801': "1",
        }

        self.btnum = {
            'e801': "0",
        }
          
        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }


        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        #self.zero_ip = self.get_zeroconfig_ip(self.mac)

        self.UPDATE_UBOOT_EN    = True
        self.PROVISION_EN       = True
        self.LOADCFG_EN         = False
        self.FWUPDATE_EN        = True
        self.DOHELPER_EN        = True
        self.REGISTER_EN        = True
        self.ADDUNIFIEEPROM_EN  = True
        self.RESETUBOOT_EN      = True
        self.DATAVERIFY_EN      = False

    def stop_uboot(self):
        self.pexp.expect_action(60, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_action(30, self.bootloader_prompt, "")

    def set_mac(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setmac")
        expect_list = [
            "Unknown command",
            "Currently programmed:"
        ]
        index = self.pexp.expect_get_index(timeout=60, exptxt=expect_list)
        if index == 0:
            log_debug("U-Boot is formal FW U-Boot, MAC set command is different")
            comma_mac = self.mac_format_str2comma(self.mac)
            cmd = "go ${{ubntaddr}} usetmac -a {}".format(comma_mac)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            time.sleep(0.5)
            expect_list = [
                "Writing EEPROM",
                "Done"
            ]
            index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
            if index < 0:
                error_critical("Can't find expected message after usetmac ... ")

            self.uboot_w_app = True
        elif index == 1:
            log_debug("Old setmac found")

    def update_uboot(self):
        log_debug("Unlocking flash ... ")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "protect off all")
        self.pexp.expect_only(5, "Un-Protect Flash Bank")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "setenv ubntctrl enabled")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "ubnt_hwp SPM off")

        if self.uboot_w_app is True:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "go ${ubntaddr} usetprotect spm off")

        cmd = "tftp 81000000 {}".format(self.uboot_img)

        retry = 3
        for i in range(0, retry):
            time.sleep(3)
            self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
            try:
                self.pexp.expect_only(5, self.uboot_img)
                self.pexp.expect_only(5, "Bytes transferred =")
            except Exception as e:
                print("uboot transfer fail..." + str(i))
                continue
            break
        else:
            print("uboot transfer retry fail")
            raise NameError('uboot transfer retry fail')

        if self.board_id in self.is_wasp:
            cmd = "erase 9f000000 +0x50000; cp.b 0x81000000 0x9f000000 0x40000"
        else:
            cmd = "erase 9f000000 +0x50000; cp.b $fileaddr 0x9f000000 $filesize"

        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        time.sleep(2)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "reset")

        self.stop_uboot()
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} uclearcfg")
        msg(95, "Configuration erased")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetenv NORESET")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetenv serverip 192.168.1.254")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetenv ipaddr 192.168.1.20")
        cmd = "go ${ubntaddr} usetenv bootargs console=ttyS0,115200 rootfstype=squashfs init=/init"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usaveenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetmac")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

        retry = 3
        for i in range(0, retry):
            self.stop_uboot()
            self.set_mac()
            time.sleep(5)
            self.set_ub_net(dutaddr=self.dutip, srvaddr=self.tftp_server)
            try:
                self.is_network_alive_in_uboot(timeout=5, retry=3, arp_logging_en=True)
            except Exception as e:
                self.pexp.expect_ubcmd(5, self.bootloader_prompt, "reset")
                print("uboot ping fcd host fail..." + str(i))
                continue
            break
        else:
            print("uboot 2nd init network fail")
            raise NameError('DUT network setup retry fail')

    def load_cfg(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv NORESET 1")
        log_debug("Uploading configuration...")
        cmd = "tftp 0x83000000 {}".format(self.cfg_part)

        retry = 3
        for j in range(0, retry):
            for i in range(0, retry):
                time.sleep(3)
                self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)
                try:
                    self.pexp.expect_only(20, os.path.basename(self.cfg_part))
                    self.pexp.expect_only(20, "Bytes transferred")
                except Exception as e:
                    print("tftp cfg_part fail..." + str(i))
                    continue
                break
            else:
                print("tftp cfg_part fail, try reset")
                self.pexp.expect_ubcmd(5, self.bootloader_prompt, "reset")
                self.stop_uboot()
                self.set_mac()
                time.sleep(5)
                self.set_ub_net(dutaddr=self.dutip, srvaddr=self.tftp_server)
                continue
            break
        else:
            print("tftp cfg_part + reset fail")
            raise NameError('tftp cfg_part + reset retry fail')

        cmd = "go ${ubntaddr} uclearcfg 0x83000000 0x40000"
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd, "Writing EEPROM")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw 0x18000014 0x404e")
        time.sleep(1)

    def update_firmware(self):
        log_debug("do_urescue !!!")
        
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "urescue -f -e", "Waiting for connection")

        fw_path = "{}/{}.bin".format(self.fwdir, self.board_id)
        cmd = "atftp --option \"mode octet\" -p -l {} {} 2>&1 > /dev/null".format(fw_path, self.dutip)
        log_debug("host cmd:" + cmd)

        retry = 3
        for i in range(0, retry):
            time.sleep(3)
            self.fcd.common.xcmd(cmd)
            try:
                self.pexp.expect_only(60, "Firmware Version:")
            except Exception as e:
                print("atftp put image fail..." + str(i))
                continue
            break
        else:
            print("atftp put image fail")
            raise NameError('atftp put image fail')
        
        msg(30, "Firmware loaded")
        self.pexp.expect_only(60, "Copying partition 'u-boot' to flash memory:")
        msg(35, "Flashing u-boot ...")
        self.pexp.expect_only(60, "Copying partition 'kernel' to flash memory:")
        msg(40, "Flashing kernel ...")
        self.pexp.expect_only(60, "Copying partition 'rootfs' to flash memory:")
        msg(45, "Flashing rootfs ...")
        self.pexp.expect_only(200, "Firmware update complete.")
        msg(50, "Flashing Completed")
        time.sleep(1)

    def fix_idrsa_permission(self):
        host_idrsa_path = os.path.join(self.fcd_toolsdir, "uap", "id_rsa")
        cmdset = [
            "chmod 600 {}".format(host_idrsa_path)
        ]
        cmd = " ".join(cmdset)
        print("cmd: " + cmd)
        self.cnapi.xcmd(cmd)

    '''
        scp_put() from Host to DUT
    '''
    def scp_put(self, hostpath, dutpath):
        host_idrsa_path = os.path.join(self.fcd_toolsdir, "uap", "id_rsa")
        cmdset = [
            "scp -i {} -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no".format(host_idrsa_path),
            "{} fcd@{}:{}".format(hostpath, self.dutip, dutpath)
        ]
        cmd = " ".join(cmdset)
        print("cmd: " + cmd)
        self.cnapi.xcmd(cmd)

    ''' Remove local implementation
    def prepare_server_need_files(self):
        rmsg = "Starting to do {} ...".format(self.helperexe)
        log_debug(rmsg)

        dut_helper_path = os.path.join(self.dut_tmpdir, self.helperexe)
        host_helper_path = os.path.join(self.fcd_toolsdir, "uap", self.helperexe)
        self.scp_put(host_helper_path, dut_helper_path)
        log_debug("Writing HW revision helper ... ")

        host_idrsa_path = os.path.join(self.fcd_toolsdir, "uap", "id_rsa")
        cmd = "ssh -i {} -4 -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no fcd@{}".format(host_idrsa_path, self.dutip)
        print("cmd: " + cmd)
        self.ssh_DUT = ExpttyProcess(self.row_id, cmd, "\n")

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            dut_helper_path,
            "-q",
            "-c product_class=" + self.product_class,
            "-o field=flash_eeprom,format=binary,pathname=" + eebin_dut_path,
            ">",
            eetxt_dut_path
        ]
        sstr = ' '.join(sstr)
        log_debug(sstr)
        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt)
        time.sleep(1)

        files = [self.eetxt, self.eebin]
        for fh in files:
            srcp = os.path.join(self.tftpdir, fh)
            dstp = "/tmp/{0}".format(fh)
            if os.path.isfile(srcp) is False:
                os.mknod(srcp)
            else:
                log_debug(srcp + " is existed")

            os.chmod(srcp, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            time.sleep(2)

            cmd = "tftp -p -r {} -l {} {}".format(os.path.basename(srcp), dstp, self.host_ip)
            self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        log_debug("Send helper output files from DUT to host ...")
    '''
        

    def get_zeroconfig_ip(self, mac):
        mac.replace(":", "")
        zeroip = "169.254."
        b1 = str(int(mac[8:10], 16))
        b2 = str(int(mac[10:12], 16))
        # ubnt specific translation

        if b1 == "0" and b2 == "0":
            b2 = "128"
        elif b1 == "255" and b2 == "255":
            b2 = "127"

        zeroip = zeroip + b1 + "." + b2
        print("zeroip:" + zeroip)
        return zeroip

    def check_write_uboot_eeprom(self):
        log_debug("Checking calibration")
        self.pexp.expect_action(5, self.bootloader_prompt, "md.b 0xbfff5000 2")
        exp_list = ["bfff5000: 44 08"]
        index = self.pexp.expect_get_index(5, exp_list)
        if index == self.pexp.TIMEOUT:
            error_critical("Unable to check the calibrated data ... ")
        elif not index == 0:
            error_critical("No calibrated data, Board is not callibrated")

        log_debug("Checking calibration MAC")
        self.pexp.expect_action(5, self.bootloader_prompt, "md.b 0xbfff5006 3")
        exp_list = ["bfff5006: 00 03 7f"]
        index = self.pexp.expect_get_index(5, exp_list)
        if index == 0:
            error_critical("No calibrated MAC, Board is not callibrated")

        ''' Disable 2.4G WIFI Caldata check in e801
        log_debug("Checking second G2 calibration")
        self.pexp.expect_action(5, self.bootloader_prompt, "md.b 0xbfff1000 2")
        exp_list = ["bfff1000: 02 02"]
        index = self.pexp.expect_get_index(5, exp_list)
        if index == 0:
            self.second_wifi_found = True
            log_debug("Find second WiFi Calibration data")
        else:
            self.second_wifi_found = False
            log_debug("Doesn't find second WiFi Calibration data")
        '''
            
        log_debug("Writing Sytem ID")
        cmd = "go ${{ubntaddr}} usetbid {}".format(self.board_id)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(0.5)
        expect_list = [
            "Board ID is programmed as {} already!".format(self.board_id),
            "Writing EEPROM"
        ]
        index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
        if index < 0:
            error_critical("Can't find expected message after usetbid ... ")

        log_debug("Writing BOM revision")
        bomrev = "13-{}".format(self.bom_rev)
        cmd = "go ${{ubntaddr}} usetbrev {}".format(bomrev)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(1)
        expect_list = [
            "Writing EEPROM",
            "Done"
        ]
        index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
        if index < 0:
            error_critical("Can't find expected message after usetbrev ... ")

        self.lock_dfs = True
        log_debug("Forcing UNII unlock for all AC devices")
        if self.lock_dfs is True:
            cmd = "go ${{ubntaddr}} usetdfs {}".format(self.unlock_mark)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            time.sleep(0.5)
            expect_list = [
                "Writing EEPROM",
                "Done"
            ]
            index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
            if index < 0:
                error_critical("Can't find expected message after usetrd ... ")

        log_debug("Writing country code")
        if self.region == "002a": # mapping to UniFi region code: USA/Canada
            log_debug("Will set FCC lock")
            self.country_lock = 10752
        elif self.region == "8168":
            '''
                0x8000 (lock flag) + 0x168 (Indonesia country code (Decimal)360 = (HEX)0x168)
		        Then, swap, so 0x8168 => 0x6881 => (Decimal) 26753
            ''' 
            log_debug("Will set Indonesia lock")
            self.country_lock = 26753
        else: # mapping to UniFi region code: World
            log_debug("Will unset FCC lock")

        '''
            Lock country code
        '''
        country_lock_hex = hex(self.country_lock).replace("0x", "")
        rmsg = "Country code in hex: {:0>4}".format(country_lock_hex)
        log_debug(rmsg)
        log_debug("Checking ccode LOCK mark")

        cmd = "go ${{ubntaddr}} usetrd 0x{:0>4} 1 1".format(country_lock_hex)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(0.5)
        expect_list = [
            "Writing EEPROM",
            "Done"
        ]
        index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
        if index < 0:
            error_critical("Can't find expected message after usetrd ... ")
        '''
            PBE-5AC(e3d6) requires this 0.5s
        '''
        time.sleep(0.5)

        '''
        if self.second_wifi_found is True:
            log_debug("wifi num: " + self.wifinum[self.board_id])

        if self.second_wifi_found is True and self.wifinum[self.board_id] == "2":
            log_debug("Write region code to 2nd WiFi interface")
            cmd = "go ${{ubntaddr}} usetrd 0x{:0>4} 1 0".format(country_lock_hex)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            time.sleep(0.5)
            expect_list = [
                "Writing EEPROM",
                "Done"
            ]
            index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
            if index < 0:
                error_critical("Can't find expected message after usetrd ... ")
        elif self.second_wifi_found is False and self.wifinum[self.board_id] == "2":
            error_critical("Unable to get the second calibration data")
        elif self.second_wifi_found is True and self.wifinum[self.board_id] == "1":
            error_critical("Found only two WiFi interface but spec is one")
        else:
            log_debug("Found only one WiFi interface")
        '''
            
        # Check SSID
        cmd = "go ${ubntaddr} usetbid"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        # Check BOM revision
        #cmd = "go ${ubntaddr} usetbrev"
        #self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, self.bom_rev)

        # Check region domain
        rmsg = "Correct country code: {:0>4}".format(country_lock_hex)
        log_debug(rmsg)

        cmd = "go ${ubntaddr} usetrd"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        if self.second_wifi_found is True:
            rmsg = "WIFI0: {:0>4}".format(country_lock_hex)
            self.pexp.expect_only(10, rmsg)
            rmsg = "WIFI1: {:0>4}".format(country_lock_hex)
            self.pexp.expect_only(10, rmsg)
        else:
            rmsg = "WIFI1: {:0>4}".format(country_lock_hex)
            self.pexp.expect_only(10, rmsg)

        # Check MAC address
        cmd = "go ${ubntaddr} usetmac"
        int_mac = int(self.mac, 16)
        int_mac0_offset = int_mac + 1
        int_mac1_offset = int_mac + int("0x20000000000", 16)
        '''
            format defintion:
                0:  # first parameter
                #   # use "0x" prefix
                0   # fill with zeroes
                {1} # to a length of n characters (including 0x), defined by the second parameter
                x   # hexadecimal number, using lowercase letters for a-f

            Example: 0418D6A24EA9, will padding "0" in the first character
        '''
        mac0 = "{0:0{1}x}".format(int_mac0_offset, 12)
        mac1 = "{0:0{1}x}".format(int_mac1_offset, 12)
        mac0_comma = "MAC0: {}".format(self.mac_format_str2comma(mac0))
        mac1_comma = "MAC1: {}".format(self.mac_format_str2comma(mac1))
        wifi1_comma = "WIFI1: {}".format(self.mac_format_str2comma(self.mac))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, mac0_comma.upper())
        #self.pexp.expect_only(10, mac1_comma.upper())
        self.pexp.expect_only(10, wifi1_comma.upper())

    def detect_dut(self, ipaddr, retry):
        cmd = "ping -c 2 {}".format(ipaddr)
        expmsg = "2 packets transmitted, 2 received, 0% packet loss"
        for i in range(0, retry+1):
            try:
                [sto, rtc] = self.cnapi.xcmd(cmd, 5)
                m_packet = re.findall(expmsg, sto)
                if m_packet:
                    log_debug("Find the packets")
                    break
                else:
                    continue
            except Exception as e:
                if i < retry:
                    print("Retry {}".format(i+1))
                    continue
                else:
                    print("Exceeded maximum retry times {}".format(i))
                    raise e

    def access_chips_id(self):
        int_mask_16bit = int("ffff", 16)

        cmd = 'cat {} | sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\" | grep -v \"eeprom\"'.format(self.eetxt_path)
        log_debug(cmd)
        [regsubparams, rtc] = self.cnapi.xcmd(cmd)
        regsubparams = regsubparams.split("\n")

        cmd = "grep cpu_rev_id {} | cut -d \"=\" -f4".format(self.eetxt_path)
        [cpu_rev_id, rtc] = self.cnapi.xcmd(cmd)
        int_cpu_rev_id = int(cpu_rev_id, 16)
        cpu_rev_id_msk = hex(int_cpu_rev_id & int_mask_16bit)
        new_cpu_rev_id = "-i field=cpu_rev_id,format=hex,value={:0>8}".format(cpu_rev_id_msk.replace("0x", ""))
        regsubparams[3] = new_cpu_rev_id

        '''
        cmd = "grep radio1_rev_id {} | cut -d \"=\" -f4".format(self.eetxt_path)
        [radio1_rev_id, rtc] = self.cnapi.xcmd(cmd)
        int_radio1_rev_id = int(radio1_rev_id, 16)
        radio1_rev_id_msk = hex(int_radio1_rev_id& int_mask_16bit)
        new_radio1_rev_id = "-i field=ARxxxx_radio1_rev_id,format=hex,value={:0>8}".format(radio1_rev_id_msk.replace("0x", ""))
        regsubparams[2] = new_radio1_rev_id
        '''
        
        regsubparams = " ".join(regsubparams)

        log_debug(regsubparams)

        return regsubparams

    ''' Remove local implementation
    def registration(self):
        log_debug("Starting to do registration ...")
        int_mask_16bit = int("ffff", 16)

        cmd = [
            "cat {} |".format(self.eetxt_path),
            'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\" |',
            'grep -v \"eeprom\"'
        ]
        cmd = ' '.join(cmd)
        [regsubparams, rtc] = self.cnapi.xcmd(cmd)
        regsubparams = regsubparams.split("\n")

        if self.board_id in self.is_wasp:
            cmd = "grep cpu_rev_id {} | cut -d \"=\" -f4".format(self.eetxt_path)
            [cpu_rev_id, rtc] = self.cnapi.xcmd(cmd)
            int_cpu_rev_id = int(cpu_rev_id, 16)
            cpu_rev_id_msk = hex(int_cpu_rev_id & int_mask_16bit)
            new_cpu_rev_id = "-i field=ARxxxx_cpu_rev_id,format=hex,value={:0>8}".format(cpu_rev_id_msk.replace("0x", ""))
            regsubparams[1] = new_cpu_rev_id

            cmd = "grep radio1_rev_id {} | cut -d \"=\" -f4".format(self.eetxt_path)
            [radio1_rev_id, rtc] = self.cnapi.xcmd(cmd)
            int_radio1_rev_id = int(radio1_rev_id, 16)
            radio1_rev_id_msk = hex(int_radio1_rev_id& int_mask_16bit)
            new_radio1_rev_id = "-i field=ARxxxx_radio1_rev_id,format=hex,value={:0>8}".format(radio1_rev_id_msk.replace("0x", ""))
            regsubparams[2] = new_radio1_rev_id

        regsubparams = " ".join(regsubparams)

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        cmd = "uname -a"
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("Get linux information failed!!")
        else:
            log_debug("Get linux information successfully")
            match = re.findall("armv7l", sto)
            if match:
                clientbin = "/usr/local/sbin/client_rpi4_release"
            else:
                clientbin = "/usr/local/sbin/client_x86_release_20190507"

        regparam = [
            "-h prod.udrs.io",
            "-k " + self.pass_phrase,
            regsubparams,
            reg_qr_field,
            "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
            "-i field=fcd_id,format=hex,value=" + self.fcd_id,
            "-i field=fcd_version,format=hex,value=" + self.sem_ver,
            "-i field=sw_id,format=hex,value=" + self.sw_id,
            "-i field=sw_version,format=hex,value=" + self.fw_ver,
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

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")
        clit.close()

        self.pass_devreg_client = True

        log_debug("Excuting client_x86 registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()
    '''
            
    def check_eeprom_mac(self):
        int_mask_24bit = int("ffffff", 16)
        cmd = "hexdump -C -s 0 -n 6 {}".format(self.eesigndate_path)
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if rtc >= 0:
            m_mac = re.findall("00000000  (.*) (.*) (.*) (.*) (.*) (.*)", sto)
            if m_mac:
                t_mac = m_mac[0][0].replace(" ", "")
                int_t_mac = int(t_mac, 16)
                read_mac_msk = hex((int_t_mac - int("0x10000", 16)) & int_mask_24bit)
                real_mac_msk = hex(int(self.mac, 16) & int_mask_24bit)
                if read_mac_msk in real_mac_msk:
                    rmsg = "Read MAC: {}, check PASS".format(t_mac)
                    log_debug(rmsg)
                else:
                    rmsg = "Read MAC: {}, expected: {}, check Failed".format(t_mac, self.mac)
                    error_critical(rmsg)
            else:
                error_critical("Can't get MAC from EEPROM")


    def add_unifi_eeprom(self, netmeta, post_en=True, rsa_en=True):
        log_debug("Adding UniFi EEPROM Extension to {}".format(self.eebin))

        if rsa_en is True:
            self.gen_rsa_key()

        post_exp = None
        if post_en is True:
            post_exp = self.linux_prompt

        otmsg = "Starting to do {0} ...".format(self.eepmexe)
        log_debug(otmsg)
        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe)
        sstr = [
            flasheditor,
            "-F",
            "-f {}".format(self.eegenbin_path),
            "-r 113-{}".format(self.bom_rev),
            "-s 0x{}".format(self.board_id),
            "-m {}".format(self.mac),
            "-c 0x{}".format(self.region),
            "-e {}".format(netmeta['ethnum'][self.board_id]),
            "-w {}".format(netmeta['wifinum'][self.board_id]),
            "-b {}".format(netmeta['btnum'][self.board_id])
        ]
        log_debug("Top level BOM:" + self.tlb_rev)
        if self.tlb_rev != "":
            sstr.append("-t {}".format(self.tlb_rev))

        log_debug("ME BOM:" + self.meb_rev)
        if self.meb_rev != "":
            sstr.append("-M {}".format(self.meb_rev))

        if rsa_en is True:
            cmd_option = "-k {}".format(self.rsakey_path)
            sstr.append(cmd_option)

        sstr = ' '.join(sstr)
        log_debug("flash editor cmd: " + sstr)
        [sto, rtc] = self.cnapi.xcmd(sstr)
        time.sleep(0.5)
        if int(rtc) > 0:
            otmsg = "Flash editor filling out {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Flash editor filling out {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        log_debug("Writing the information from e.gen.{0} to e.b.{0}".format(self.row_id))

        f1 = open(self.eebin_path, "rb")
        bin_tres = list(f1.read())
        f1.close()

        f2 = open(self.eegenbin_path, "rb")
        gen_tres = list(f2.read())
        f2.close()

        f3 = open(self.eebin_path, "wb")
        
        ''' Disable this work around, use uboot default MAC
        # Write MAC0/1, use flasheditor generated MAC address to overwrite original MAC
        content_sz = 12
        for idx in range(0, content_sz):
            bin_tres[idx] = gen_tres[idx]
        '''
            
        # Write Unifi Extend content start from 0x8000 ~ 0x8100
        content_sz = 256 # 0x100
        offset = 32768  # 0x8000
        for idx in range(0, content_sz):
            bin_tres[idx + offset] = gen_tres[idx + offset]

        # Write RSA Key from 0xe000 ~ 0xe400
        content_sz = 1024 # 0x400
        offset = 57344  # 0xe000
        for idx in range(0, content_sz):
            bin_tres[idx + offset] = gen_tres[idx + offset]

        arr = bytearray(bin_tres)
        f3.write(arr)
        f3.close()

        self.print_eeprom_content(self.eebin_path)

    def unlock_flash(self):
        log_debug("Starting to do " + self.unlockexe + "...")
        servpath = os.path.join(self.tools, self.helper_path, self.unlockexe)
        dutpath = os.path.join(self.dut_tmpdir, self.unlockexe)

        self.tftp_get(remote=servpath, local=dutpath, timeout=60)

        cmd = "chmod 777 {0}".format(dutpath)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        cmd = "/tmp/fl_lock_11ac_re -l 0 -g 0"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)


    ''' Remove local implementation
    def check_devreg_data(self):
        log_debug("Uploading EEPROM ...")
        host_esd_path = "{}/{}".format(self.tftpdir, self.eesigndate)
        dut_esd_path = "{}/{}".format(self.dut_tmpdir, self.eesigndate)
        self.scp_put(host_esd_path, dut_esd_path)

        host_fllock_path = os.path.join(self.fcd_toolsdir, "am", "fl_lock_11ac_re")
        dut_fllock_path = "{}/{}".format(self.dut_tmpdir, "fl_lock_11ac_re")
        self.scp_put(host_fllock_path, dut_fllock_path)

        cmd = "/tmp/fl_lock_11ac_re -l 0 -g 0"
        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        dut_helper_path = os.path.join(self.dut_tmpdir, self.helperexe)
        cmd = "{} -q -i field=flash_eeprom,format=binary,pathname={}".format(dut_helper_path, dut_esd_path)
        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        cmd = "dd if={} of=/tmp/{}".format(self.devregpart, self.eechk)
        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        log_debug("Checking EEPROM ...")
        dstp = os.path.join(self.dut_tmpdir, self.eechk)

        if os.path.isfile(self.eechk_path) is False:
            os.mknod(self.eechk_path)
        else:
            log_debug(self.eechk_path + " is existed")

        os.chmod(self.eechk_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        time.sleep(2)
        cmd = "tftp -p -r {} -l {} {}".format(self.eechk, dstp, self.host_ip)
        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        cmd = "cmp {} {}".format(self.eesigndate_path, self.eechk_path)
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if rtc > 0:
            if sto == "":
                msg(90, "EEPROM check successfully ...")
            else:
                error_critical("EEPROM check failed ...")

        cmd = "hexdump -C -n 40 {}".format(self.eesigndate_path)
        [sto, rtc] = self.cnapi.xcmd(cmd)

        self.check_eeprom_mac()
        self.check_eeprom_bomrev()

        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action="reboot")
        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action="reboot")
        self.ssh_DUT.close()

        self.stop_uboot()
    '''

    def check_info(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)


    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.cnapi.config_stty(self.dev)

        '''
        Connect into DU and set pexpect helper for class using picocom
        '''
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        #self.fix_idrsa_permission()

        retry = 3
        for i in range(0, retry):
            self.stop_uboot()
            self.set_mac()
            time.sleep(5)
            self.set_ub_net(dutaddr=self.dutip, srvaddr=self.tftp_server)
            try:
                self.is_network_alive_in_uboot(timeout=5, retry=3, arp_logging_en=True)
            except Exception as e:
                self.pexp.expect_ubcmd(5, self.bootloader_prompt, "reset")
                print("uboot ping fcd host fail..." + str(i))
                continue
            break
        else:
            print("uboot 1st init network fail")
            raise NameError('DUT network setup retry fail')

        if self.UPDATE_UBOOT_EN is True:
            msg(10, "Update U-boot ...")
            self.update_uboot()

        if self.PROVISION_EN is True:
            msg(20, "Data provisioning ...")
            self.check_write_uboot_eeprom()

        if self.LOADCFG_EN is True:
            msg(25, "Load CFG ...")
            self.load_cfg()

        if self.FWUPDATE_EN is True:
            self.update_firmware()

        if self.DOHELPER_EN is True:
            #self.detect_dut(self.dutip, retry=60)
            msg(55, "Prepare Registration ...")
            self.login(timeout=240, press_enter=True)
            self.set_lnx_net("eth0")
            self.chk_lnxcmd_valid()
            self.is_network_alive_in_linux(ipaddr=self.tftp_server)
            self.erase_eefiles()
            self.prepare_server_need_files()

        if self.REGISTER_EN is True:
            msg(60, "Run Registration ...")
            if self.ADDUNIFIEEPROM_EN is True:
                self.add_unifi_eeprom(self.devnetmeta)

            self.registration()
            self.unlock_flash()
            self.check_devreg_data()

        if self.RESETUBOOT_EN is True:
            msg(80, "Reset Uboot ...")

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
            self.stop_uboot()

            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} uclearcfg")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetenv NORESET")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetenv serverip 192.168.1.254")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetenv ipaddr 192.168.1.20")
            cmd = "go ${ubntaddr} usetenv bootargs console=ttyS0,115200 rootfstype=squashfs init=/init"
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usaveenv")
            msg(85, "Uboot Configuration erased")
            
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "go ${ubntaddr} usetmac")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
            self.pexp.expect_only(10, "Booting")

        if self.DATAVERIFY_EN is True:
            msg(85, "Check Device Info ...")
            self.login(timeout=240, press_enter=True)
            self.check_info()

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    factory = AMAR9342Factory()
    factory.run()

if __name__ == "__main__":
    main()
