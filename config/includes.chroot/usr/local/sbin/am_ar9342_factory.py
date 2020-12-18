#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import subprocess

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.common import Common
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

'''
    e7f9: LBE-5AC
'''


class AMAR9342Factory(ScriptBase):
    def __init__(self):
        super(AMAR9342Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.product_class = "radio"
        self.devregpart = "/dev/mtdblock5"
        self.helperexe = "helper_ARxxxx_11ac"
        self.bootloader_prompt = "ar7240>"
        self.uboot_img = "{}/{}-uboot.bin".format(self.image, self.board_id)
        self.cfg_part = os.path.join(self.tools, "am", "cfg_part_ar9342.bin")
        self.helper_path = "am"
        self.uboot_w_app = False
        self.lock_dfs = False
        self.unlock_mark = "52ff"
        self.clear_mark = "ffff"
        self.host_ip = "169.254.1.19"
        self.ssh_DUT = None

        # Country Lock is a value
        self.country_lock = 0
        self.second_radio = False

        self.is_wasp = ["e7f9"]
        self.dfs_lock_list = [
            "e7e5", "e1f5", "e3f5", "e3f5", "e3d5", "e3d5", "e5f5", "e6f5",
            "e6f5", "e6f5", "e6f5", "e4f5", "e9f5", "e8f5", "e9f5", "e7f7",
            "e7f9", "e3d6", "e3d7", "e3d8", "e7e6", "e7e7"
        ]

        # number of mac
        self.macnum = {
            'e7f9': "2"
        }

        # number of WiFi
        self.wifinum = {
            'e7f9': "2"
        }

        # number of Bluetooth
        self.btnum = {
            'e7f9': "0"
        }

        # vlan port mapping
        # self.vlanport_idx = {
        #     'e7f9': "'6 0'"
        # }

        # flash size map
        # self.flash_size = {
        #     'e7f9': "33554432"
        # }

        # firmware image
        self.fwimg = {
            'e7f9': self.board_id + ".bin"
        }

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        self.zero_ip = self.cnapi.get_zeroconfig_ip(self.mac)

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
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
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
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(5, self.uboot_img)
        self.pexp.expect_only(5, "Bytes transferred =")

        if self.board_id in self.is_wasp:
            cmd = "erase 9f000000 +0x50000; cp.b 0x81000000 0x9f000000 0x40000"
        else:
            cmd = "erase 9f000000 +0x50000; cp.b \$fileaddr 0x9f000000 \$filesize"

        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, "reset")
        self.stop_uboot()
        self.set_mac()
        self.set_ub_net()
        self.is_network_alive_in_uboot()

    def update_firmware(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv NORESET 1")
        log_debug("Uploading configuration...")
        cmd = "tftp 0x83000000 {}".format(self.cfg_part)
        self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)
        self.pexp.expect_only(20, os.path.basename(self.cfg_part))

        cmd = "go ${ubntaddr} uclearcfg 0x83000000 0x40000"
        self.pexp.expect_ubcmd(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(5, "Writing EEPROM")

        log_debug("do_urescue !!!")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "urescue -f -e")
        self.pexp.expect_only(20, "Waiting for connection")
        fw_path = "{}/{}.bin".format(self.fwdir, self.board_id)
        cmd = "atftp --option \"mode octet\" -p -l {} {} 2>&1 > /dev/null".format(fw_path, self.dutip)
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

    '''
        scp_put() from Host to DUT
    '''
    def scp_put(self, hostpath, dutpath):
        host_idrsa_path = os.path.join(self.fcd_toolsdir, "am", "id_rsa")
        cmdset = [
            "scp -i {} -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no".format(host_idrsa_path),
            "{} fcd@{}:{}".format(hostpath, self.zero_ip, dutpath)
        ]
        cmd = " ".join(cmdset)
        print("cmd: " + cmd)
        self.cnapi.xcmd(cmd)

    def prepare_server_need_files(self):
        rmsg = "Starting to do {} ...".format(self.helperexe)
        log_debug(rmsg)

        dut_helper_path = os.path.join(self.dut_tmpdir, self.helperexe)
        host_helper_path = os.path.join(self.fcd_toolsdir, "am", self.helperexe)
        self.scp_put(host_helper_path, dut_helper_path)
        log_debug("Writing HW revision helper ... ")

        host_idrsa_path = os.path.join(self.fcd_toolsdir, "am", "id_rsa")
        cmd = "ssh -i {} -4 -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no fcd@{}".format(host_idrsa_path, self.zero_ip)
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

            cmd = "tftp -p -r {} -l {} {}".format(srcp, dstp, self.host_ip)
            self.ssh_DUT.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        log_debug("Send helper output files from DUT to host ...")

    def data_provision_64k(self):
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

        log_debug("Checking second G2 calibration")
        self.pexp.expect_action(5, self.bootloader_prompt, "md.b 0xbfff1000 2")
        exp_list = ["bfff1000: 02 02"]
        index = self.pexp.expect_get_index(5, exp_list)
        if index == self.pexp.TIMEOUT:
            if self.board_id == "e2f3":
                error_critical("Unable to get the second calibration data")
        elif index == 0:
            log_debug("Second radio found")
            self.second_radio = True

        log_debug("Writing Sytem ID")
        cmd = "go ${{ubntaddr}} usetbid {}".format(self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
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
        self.pexp.expect_only(10, "Writing EEPROM")

        self.lock_dfs = True
        log_debug("Forcing UNII unlock for all AC devices")
        if self.lock_dfs is True:
            cmd = "go ${{ubntaddr}} usetdfs {}".format(self.unlock_mark)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        log_debug("Writing country code")
        if self.region == "002a":
            log_debug("Will set FCC lock")
            self.country_lock = 10752
        elif self.region == "8168":
            '''
                0x8000 (lock flag) + 0x168 (Indonesia country code (Decimal)360 = (HEX)0x168)
		        Then, swap, so 0x8168 => 0x6881 => (Decimal) 26753
            ''' 
            log_debug("Will set Indonesia lock")
            self.country_lock = 26753
        else:
            log_debug("Will unset FCC lock")

        country_lock_hex = hex(self.country_lock).replace("0x", "")
        rmsg = "Country code in hex: {:0>4}".format(country_lock_hex)
        log_debug(rmsg)
        log_debug("Checking ccode LOCK mark")

        cmd = "go ${{ubntaddr}} usetrd {:0>4} 1 1".format(country_lock_hex)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "Writing EEPROM")
        if self.second_radio is True:
            cmd = "go ${{ubntaddr}} usetrd {:0>4} 1 0".format(country_lock_hex)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            self.pexp.expect_only(10, "Writing EEPROM")

        # Check SSID
        cmd = "go ${ubntaddr} usetbid"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        # Check BOM revision
        cmd = "go ${ubntaddr} usetbrev"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, self.bom_rev)

        # Check region domain
        cmd = "go ${ubntaddr} usetrd"
        rmsg = "WIFI0: {}".format(country_lock_hex)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd, rmsg)
        rmsg = "Correct country code: {}".format(country_lock_hex)
        log_debug(rmsg)

        # Check MAC address
        cmd = "go ${ubntaddr} usetmac"
        int_mac = int(self.mac, 16)
        mac0 = hex(int_mac + int("0x10000", 16)).replace("0x", "")
        mac0_comma = "MAC0: {}".format(self.mac_format_str2comma(mac0))
        wifi0_comma = "WIFI1: {}".format(self.mac_format_str2comma(self.mac))
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
                    print("Retry {}".format(i+1))
                    continue
                else:
                    print("Exceeded maximum retry times {}".format(i))
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
            "-h devreg-prod.ubnt.com",
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
        clit.expect_only(10, "Ubiquiti Device Security Client")
        clit.expect_only(10, "Hostname")
        clit.expect_only(10, "field=result,format=u_int,value=1")
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

        self.stop_uboot()
        self.set_mac()
        self.set_ub_net()
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
            self.pexp.expect_only(10, "Booting")


        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    factory = AMAR9342Factory()
    factory.run()

if __name__ == "__main__":
    main()
