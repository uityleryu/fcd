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
    E1F5: 113-00348 Rocket 5AC Lite
    E865: 113-00372 LBE-M5-23
'''

class AMAR9342Factory(ScriptBase):
    def __init__(self):
        super(AMAR9342Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.fcd_id = "0x000b"
        self.product_class = "radio"
        self.devregpart = "/dev/mtdblock5"
        self.helperexe = "helper_ARxxxx_wasp"
        self.fl_lock = "fl_lock63"
        self.bootloader_prompt = ">"
        self.uboot_img = "{}/{}-uboot.bin".format(self.image, self.board_id)
        self.cfg_part = os.path.join(self.tools, "am_m", "cfg_part_m_series.bin")
        self.helper_path = "am_m"
        self.dut_helper_path = os.path.join(self.dut_tmpdir, self.helperexe)
        self.host_helper_path = os.path.join(self.fcd_toolsdir, "am_m", self.helperexe)
        self.host_idrsa_path = os.path.join(self.fcd_toolsdir, "am_m", "id_rsa")
        self.uboot_w_app = False
        self.lock_dfs = False
        self.unlock_mark = "52ff"
        self.clear_mark = "ffff"
        self.host_ip = "169.254.1.19"
        self.ssh_DUT = None

        # Country Lock is a value
        self.country_lock = 0

        self.second_wifi_found = False

        self.is_wasp = [
            "e865"
        ]

        '''
        self.dfs_lock_list = [
            "e1f5", "e2c5", "e2c7", "e2f3", "e3d5", "e3d6", "e3d8", "e3f5", "e4f3", "e4f5", "e5f5", "e6f5",
            "e7e5", "e7e6", "e7e7", "e7e8", "e7e9", "e7f5", "e7f7", "e7f9", "e8f5", "e9f5", "e7ff", "e7fe",
            "e7fb", "e8e5"
        ]
        '''

        # number of WiFi
        self.wifinum = {
            'e865': "1"
        }

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.zero_ip = self.get_zeroconfig_ip(self.mac)

        self.UPDATE_UBOOT_EN    = True
        self.PROVISION_EN       = True
        self.FWUPDATE_EN        = True
        self.DOHELPER_EN        = True
        self.REGISTER_EN        = True
        self.DATAVERIFY_EN      = True

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
            comma_mac = self.mac_format_str2comma(self.mac)
            cmd = "setmac -a {}".format(comma_mac)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            time.sleep(0.5)
            expect_list = [
                "Writing EEPROM",
                "Done"
            ]
            index = self.pexp.expect_get_index(timeout=10, exptxt=expect_list)
            if index < 0:
                error_critical("Can't find expected message after setmac ... ")

    def update_uboot(self):
        log_debug("Unlocking flash ... ")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "protect off all")
        self.pexp.expect_only(5, "Un-Protect Flash Bank")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "setenv ubntctrl enabled")
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "ubnt_hwp SPM off")

        if self.uboot_w_app is True:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "go ${ubntaddr} usetprotect spm off")

        cmd = "tftp 81000000 {}".format(self.uboot_img)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(5, self.uboot_img)
        self.pexp.expect_only(5, "Bytes transferred =")

        if self.board_id in self.is_wasp:
            cmd = "erase 9f000000 +0x50000; cp.b 0x81000000 0x9f000000 0x40000"
        else:
            cmd = "erase 9f000000 +0x50000; cp.b $fileaddr 0x9f000000 $filesize"

        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        time.sleep(2)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "reset")
        self.stop_uboot()
        self.set_mac()
        time.sleep(1)
        self.set_ub_net(dutaddr=self.zero_ip, srvaddr="169.254.1.19")
        self.is_network_alive_in_uboot()

    def update_firmware(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv NORESET 1")
        log_debug("Uploading configuration...")
        cmd = "tftp 0x83000000 {}".format(self.cfg_part)
        self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)
        self.pexp.expect_only(20, os.path.basename(self.cfg_part))
        self.pexp.expect_only(20, "Bytes transferred")

        cmd = "go ${ubntaddr} uclearcfg 0x83000000 0x40000"
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd, "Writing EEPROM")
        time.sleep(1)

        log_debug("do_urescue !!!")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "urescue -f -e", "Waiting for connection")

        fw_path = "{}/{}.bin".format(self.fwdir, self.board_id)
        cmd = "atftp --option \"mode octet\" -p -l {} {} 2>&1 > /dev/null".format(fw_path, self.zero_ip)
        log_debug("host cmd:" + cmd)
        self.fcd.common.xcmd(cmd)
        self.pexp.expect_only(60, "Firmware Version:")
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
        self.pexp.close()

    def fix_idrsa_permission(self):
        cmdset = [
            "chmod 600 {}".format(self.host_idrsa_path)
        ]
        cmd = " ".join(cmdset)
        log_debug("cmd: " + cmd)
        self.cnapi.xcmd(cmd)

    '''
        scp_put() from Host to DUT
    '''
    def scp_put(self, hostpath, dutpath, retry=12):
        
        cmdset = [
            "scp -i {} -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no".format(self.host_idrsa_path),
            "{} fcd@{}:{}".format(hostpath, self.zero_ip, dutpath)
        ]
        cmd = " ".join(cmdset)
        log_debug("cmd: " + cmd)

        for i in range(0, retry):
            [msg, ret] = self.cnapi.xcmd(cmd)
            log_debug("scp_put ret: " + str(ret) + " msg: " + msg)
            if "Connection refused" in msg:
                log_debug("scp_put failed, retry..." + str(i))
                time.sleep(5)
            else:
                return

        error_critical("scp_put:" + hostpath + " failed")

    def prepare_server_need_files(self):
        rmsg = "Starting to do {} ...".format(self.helperexe)
        log_debug(rmsg)

        self.scp_put(self.host_helper_path, self.dut_helper_path)
        log_debug("Writing HW revision helper ... ")

        cmd = "ssh -i {} -4 -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no fcd@{}".format(self.host_idrsa_path, self.zero_ip)
        log_debug("cmd: " + cmd)
        self.ssh_DUT = ExpttyProcess(self.row_id, cmd, "\n")

        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action="chmod 700 " + self.dut_helper_path, post_exp=self.linux_prompt)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            self.dut_helper_path,
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
        log_debug("zeroip:" + zeroip)
        return zeroip

    def data_provision_64k(self):
        log_debug("Checking calibration")
        self.pexp.expect_action(5, self.bootloader_prompt, "md.b 0xbfff1000 2")
        exp_list = ["bfff1000: 02 02"]
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

        '''
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
        time.sleep(3)
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
            self.country_lock = 42
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

        cmd = "go ${{ubntaddr}} usetrd 0x{:0>4}".format(country_lock_hex)
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
        cmd = "go ${ubntaddr} usetbrev"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, self.bom_rev)

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
            rmsg = "RegulatoryDomain: {:0>4}".format(country_lock_hex)
            self.pexp.expect_only(10, rmsg)

        # Check MAC address
        cmd = "go ${ubntaddr} usetmac"
        int_mac = int(self.mac, 16)
        int_mac_offset = int_mac + int("0x10000", 16)
        '''
            format defintion:
                0:  # first parameter
                #   # use "0x" prefix
                0   # fill with zeroes
                {1} # to a length of n characters (including 0x), defined by the second parameter
                x   # hexadecimal number, using lowercase letters for a-f

            Example: 0418D6A24EA9, will padding "0" in the first character
        '''
        mac0 = "{0:0{1}x}".format(int_mac_offset, 12)
        mac0_comma = "MAC0: {}".format(self.mac_format_str2comma(mac0))
        wifi0_comma = "WIFI: {}".format(self.mac_format_str2comma(self.mac))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, mac0_comma.upper())
        self.pexp.expect_only(10, wifi0_comma.upper())

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
                    log_debug("Retry {}".format(i+1))
                    continue
                else:
                    log_debug("Exceeded maximum retry times {}".format(i))
                    raise e

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
        log_debug("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")
        clit.close()

        self.pass_devreg_client = True

        log_debug("Excuting client_x86 registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()

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

    def check_devreg_data(self):
        log_debug("Uploading EEPROM ...")
        host_esd_path = "{}/{}".format(self.tftpdir, self.eesigndate)
        dut_esd_path = "{}/{}".format(self.dut_tmpdir, self.eesigndate)
        self.scp_put(host_esd_path, dut_esd_path)

        host_fllock_path = os.path.join(self.fcd_toolsdir, "am_m", self.fl_lock)
        dut_fllock_path = "{}/{}".format(self.dut_tmpdir, self.fl_lock)
        self.scp_put(host_fllock_path, dut_fllock_path)

        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action="chmod 700 " + dut_fllock_path, post_exp=self.linux_prompt)

        cmd = dut_fllock_path + " -l 0"
        self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        cmd = "{} -q -i field=flash_eeprom,format=binary,pathname={}".format(self.dut_helper_path, dut_esd_path)
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

        self.fix_idrsa_permission()

        self.stop_uboot()
        self.set_mac()
        time.sleep(1)
        self.set_ub_net(dutaddr=self.zero_ip, srvaddr="169.254.1.19")
        self.is_network_alive_in_uboot()

        if self.UPDATE_UBOOT_EN is True:
            msg(10, "Update U-boot ...")
            self.update_uboot()

        if self.PROVISION_EN is True:
            msg(20, "Data provisioning ...")
            self.data_provision_64k()

        if self.FWUPDATE_EN is True:
            self.update_firmware()

        if self.DOHELPER_EN is True:
            self.detect_dut(self.zero_ip, retry=60)
            self.erase_eefiles()
            time.sleep(5)
            self.prepare_server_need_files()

        if self.REGISTER_EN is True:
            self.registration()
            self.check_devreg_data()

        if self.DATAVERIFY_EN is True:
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
            self.pexp.expect_only(10, "Resetting...")


        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    factory = AMAR9342Factory()
    factory.run()

if __name__ == "__main__":
    main()
