#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a612:    U6-Lite Mt7621
    a614:    U6-LR Mt7621
    a620:    U6-LRv2 MT7622
'''


class U6MT762xFactory(ScriptBase):
    def __init__(self):
        super(U6MT762xFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        # self.devregpart = "/dev/mtdblock3"
        # self.helperexe = "helper_UAP6_MT7621_release"
        # self.bootloader_prompt = "MT7621 #"
        self.fcdimg = self.board_id + "-fcd.bin"
        self.uboot_img = os.path.join(self.image, self.board_id+'-uboot.bin')
        self.uboot_size = os.stat(os.path.join(self.tftpdir, self.uboot_img)).st_size

        self.helper_path = "common"

        # Devreg location
        self.devregpart_select = {
            "a612": "/dev/mtdblock3",
            "a614": "/dev/mtdblock3",
            "a620": "/dev/mtdblock5",
            "a640": "/dev/mtdblock3"
        }
        self.devregpart = self.devregpart_select[self.board_id]

        # helper by Project(platoform)
        self.helperexe_select = {
            "a612": "helper_UAP6_MT7621_release",
            "a614": "helper_UAP6_MT7621_release",
            "a620": "helper_UAP6_MT7622_release",
            "a640": "helper_UAP6_MT7621_release"
        }
        self.helperexe = self.helperexe_select[self.board_id]

        # bootloader prompt
        self.bootloader_prompt_select = {
            "a612": "MT7621 #",     # uboot of BSP is "=>"
            "a614": "MT7621 #",     # uboot of BSP is "=>"
            "a620": "MT7622>",
            "a640": "MT7621 #"     # uboot of BSP is "=>"
        }
        self.bootloader_prompt = self.bootloader_prompt_select[self.board_id]

        # number of mac
        self.macnum = {
            'a612': "1",
            'a614': "1",
            'a620': "1",
            'a640': "1",
        }

        # number of WiFi
        self.wifinum = {
            'a612': "2",
            'a614': "2",
            'a620': "2",
            'a640': "2",
        }

        # number of Bluetooth
        self.btnum = {
            'a612': "1",
            'a614': "1",
            'a620': "1",
            'a640': "1",
        }

        # vlan port mapping
        self.vlanport_idx = {
            'a612': "'6 0'",
            'a614': "'6 0'",
            'a620': "'6 0'",
            'a640': "'6 0'",
        }


        # flash size map
        self.flash_size = {
            'a612': "33554432",
            'a614': "33554432",
            'a620': "67108864",
            'a640': "33554432",
        }

        self.recovery_addr = {
            "a612": "0x84000000",
            "a614": "0x84000000",
            "a620": "0x5007ff28",
            "a640": "0x84000000",
        }

        # firmware image
        self.fwimg = {
            'a612': self.board_id + ".bin",
            'a614': self.board_id + ".bin",
            'a620': self.board_id + ".bin",
            'a640': self.board_id + ".bin",
        }

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        '''
            2022/11/4
            This is a special recall event for changing the BOM revision on the U6-LR
        '''
        self.SPECIAL_RECALL_EVENT = False
        # 20221202 for Gavin BLE reboot special case

        self.BOOT_RECOVERY_IMAGE = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True

        if self.SPECIAL_RECALL_EVENT is True:
            self.UPDATE_UBOOT_ENABLE = False
            self.FWUPDATE_ENABLE = False
            self.DATAVERIFY_ENABLE = False
        else:
            self.UPDATE_UBOOT_ENABLE = True
            self.FWUPDATE_ENABLE = True
            self.DATAVERIFY_ENABLE = True

    def boot_recovery_image(self, Img):
        cmd = "tftpboot {} images/{}".format(self.recovery_addr[self.board_id], Img)

        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            pass
        elif self.board_id == "a620":
            self.pexp.expect_action(15, self.bootloader_prompt, "nor init")

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Bytes transferred = "+str(os.stat(self.fwdir+"/"+Img).st_size))
        self.pexp.expect_action(10, self.bootloader_prompt, "bootm")
        self.login(timeout=240,press_enter=True)

    def init_recovery_image(self):
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dmesg -n 1", valid_chk=True)

        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            cmd = "swconfig dev switch0 set enable_vlan 1"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "swconfig dev switch0 vlan 1 set vid 1"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "swconfig dev switch0 vlan 1 set ports {}".format(self.vlanport_idx[self.board_id])
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "swconfig dev switch0 set apply"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            cmd = "[ $(ifconfig | grep -c eth0) -gt 0 ] || ifconfig eth0 up"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig br0", post_exp="inet addr:", retry=6, valid_chk=True)
            cmd = "ifconfig eth0 {}".format(self.dutip)
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)

        elif self.board_id == "a620":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig", "br0", retry=10)
            # To enable ethernet in 1G unit
            cmd = "sed -i '/udhcpc/d' /etc/inittab"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, retry=10)
            cmd = "init -q"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, retry=10)
            cmd = "ifconfig br0 {}".format(self.dutip)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, retry=10)

            comma_mac = self.mac_format_str2comma(self.mac)
            cmdset = [
                "ifconfig br0",
                "ifconfig br0 hw ether {}".format(comma_mac),
                "ifconfig br0",
                "ifconfig eth0",
                "ifconfig eth0 down",
                "ifconfig eth0 hw ether {}".format(comma_mac),
                "ifconfig eth0 up",
                "ifconfig eth0"
            ]
            for cmd in cmdset:
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

            time.sleep(10)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0")

        self.is_network_alive_in_linux(arp_logging_en=True, del_dutip_en=True, retry=10)

    def update_uboot(self):
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            log_debug("uboot_img: " + self.uboot_img)
            cmd = "tftpboot {} {}".format(self.recovery_addr[self.board_id], self.uboot_img)
            exp = "Bytes transferred = {}".format(self.uboot_size)
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, exp)
            cmd = "sf probe; sf erase 0x0 0x60000; sf write {} 0x0 ${{filesize}}".format(self.recovery_addr[self.board_id])
        elif self.board_id == "a620":
            self.pexp.expect_action(10, self.bootloader_prompt, "nor init")
            time.sleep(2)
            fake_eeprom_filename = "{}-fake_EEPROM.bin".format(self.board_id)
            fake_EEPROM_img = os.path.join(self.image, fake_eeprom_filename)
            log_debug("fake_EEPROM_img: " + fake_EEPROM_img)
            cmd = "tftpboot 0x4007ff28 {}".format(fake_EEPROM_img)
            self.pexp.expect_action(10, self.bootloader_prompt, cmd)
            time.sleep(1)

            cmd = "snor erase 0x110000 0x10000; snor write 0x4007ff28 0x110000 0x10000"
            self.pexp.expect_action(10, self.bootloader_prompt, cmd)
            time.sleep(2)
            self.pexp.expect_action(10, self.bootloader_prompt, "")
            time.sleep(2)

            log_debug("uboot_img: " + self.uboot_img)
            cmd = "tftpboot {}".format(self.uboot_img)
            exp = "Bytes transferred = {}".format(self.uboot_size)
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, cmd, exp)
            cmd = "snor erase 0x60000 0x60000; snor write ${loadaddr} 0x60000 ${filesize}"

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

    def enter_uboot(self, stp_enable=False):
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            rt = self.pexp.expect_action(30, "Hit any key to stop autoboot|Autobooting in 2 seconds, press", "\x1b\x1b")
            self.bootloader_prompt = "MT7621 #"  # here will need this because prompt could be changed with "=>" before on 1st uboot
            retry = 2
            while retry > 0:
                if rt != 0:
                    error_critical("Failed to detect device")
                try:
                    self.pexp.expect_action(10, self.bootloader_prompt, "\x1b\x1b")
                    break
                except Exception as e:
                    self.bootloader_prompt = "=>"
                    log_debug("Change prompt to {}".format(self.bootloader_prompt))
                    retry -= 1
                    
            if stp_enable is True:
                self.set_stp_env()

        elif self.board_id == "a620":
            rt = self.pexp.expect_action(30, "Hit any key to stop autoboot|Autobooting in 2 seconds, press|Autobooting in 3 seconds, press", "\x1b\x1b")
            retry = 2
            while retry > 0:
                if rt != 0:
                    error_critical("Failed to detect device")
                try:
                    self.pexp.expect_action(10, self.bootloader_prompt, "")
                    break
                except Exception as e:
                    self.bootloader_prompt = "#"
                    log_debug("Change prompt to {}".format(self.bootloader_prompt))
                    retry -= 1

            if stp_enable is True:
                self.set_stp_env()

    def set_uboot_network(self):
        self.set_ub_net(premac=self.mac)
        self.is_network_alive_in_uboot(arp_logging_en=True, del_dutip_en=True)

    def fwupdate(self):
        log_debug("Change to product firware...")
        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(30, self.linux_prompt, "reboot -f")
        self.enter_uboot()
        self.set_uboot_network()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubnt_clearcfg TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ubnt_clearenv TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv do_urescue TRUE")

        self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
        self.pexp.expect_action(30, "Listening for TFTP transfer on", "")

        ct = 0
        retry = 5
        while ct < retry:
            ct += 1
            cmd = "atftp -p -l {0}/{1} {2}".format(self.fwdir, self.fwimg[self.board_id], self.dutip)
            log_debug("host cmd: " + cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                rmsg = "Failed to upload firmware image.., retry: {}".format(ct)
                log_debug(rmsg)
                cmd = "sudo killall atftp"
                self.fcd.common.xcmd(cmd)
                time.sleep(2)
                cmd = "ping -c 3 {}".format(self.dutip)
                self.fcd.common.xcmd(cmd)
                time.sleep(1)
                continue
            else:
                log_debug("Uploading firmware image successfully")

            try:
                self.pexp.expect_only(30, "Bytes transferred = ")
                log_debug("DUT receives image successfully")
                break
            except self.pexp.ExceptionPexpect:
                rmsg = "Retry TFTP download ... retry: {}".format(ct)
                log_debug(rmsg)
                cmd = "ping -c 3 {}".format(self.dutip)
                self.fcd.common.xcmd(cmd)
                time.sleep(1)
        else:
            error_critical("FTFTP download, FAILED")

        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
        self.pexp.expect_only(60, "Updating u-boot partition \(and skip identical blocks\)")
        self.pexp.expect_only(60, "done")
        self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(240, "done")

    def set_stp_env(self):
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv is_ble_stp true;saveenv", "OK")
        elif self.board_id == "a620":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv is_ble_stp true; saveenv", "done")

    def check_wifi_eeprom(self):
        time.sleep(10)
        cmd = "ifconfig ra0 up"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        cmd = "ifconfig rai0 up"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        time.sleep(5)

        """
        # 2G TX0 power OFDM 54M
        self.eeprom_check(interface='ra0', address='58', check_value='22')
        # 2G TX1 power OFDM 54M
        self.eeprom_check(interface='ra0', address='5e', check_value='22')
        # 2G TX2 power OFDM 54M
        self.eeprom_check(interface='ra0', address='64', check_value='22')
        # 2G TX3 power OFDM 54M
        self.eeprom_check(interface='ra0', address='6a', check_value='22')
        # 2G MCS0 TX power by rate
        self.eeprom_check(interface='ra0', address='c5', check_value='C4C6')
        # 5G TX0 power OFDM 54M
        self.eeprom_check(interface='rai0', address='34c', check_value='2424')
        # 5G TX1 power OFDM 54M
        self.eeprom_check(interface='rai0', address='358', check_value='2424')
        # 5G TX2 power OFDM 54M
        self.eeprom_check(interface='rai0', address='364', check_value='2424')
        # 5G TX3 power OFDM 54M
        self.eeprom_check(interface='rai0', address='370', check_value='2424')
        # 5G MCS0 TX power by rate
        self.eeprom_check(interface='rai0', address='2a2', check_value='C4')
        """

        cmd = "hexdump -s 0x0 -n 131968 /dev/mtd4"
        self.pexp.expect_lnxcmd(120, self.linux_prompt, cmd, "0020380")

    def eeprom_check(self, interface, address, check_value):
        cmd = "iwpriv {} e2p {}".format(interface, address)
        buf = self.pexp.expect_get_output(action=cmd, prompt="", timeout=3)
        if check_value in buf.split(':')[2]:
            log_debug("eeprom value check PASS!!!")
        else:
            error_critical("eeprom value check FAIL!!!")

    def check_info(self):
        self.enter_uboot()
        log_debug("check DUT ip of Uboot, ipaddr=192.168.1.20(default) or not ?")
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, 'print', 'ipaddr=192.168.1.20')
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

        #Check BT FW is included or not
        bom = self.bom_rev.split("-")[0]
        rev_of_bomrev = int(self.bom_rev.split("-")[1])

        # U6-Lite, old bom is 113-00773-15 , if rev lower 15 , the uboot could be not "BT Power On result" message
        # U6-Lite, new bom is 113-01076
        if bom == "00773" and rev_of_bomrev < 15:
            pass
        else:   #for new bom U6-lIte and U6-LR
            self.pexp.expect_only(30, "\[BT Power On Result\] Success") 

        self.login(timeout=240,press_enter=True)
        cmd = "dmesg -n 1"
        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        elif self.board_id == "a620":
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)

        cmd = "cat /proc/ubnthal/system.info"
        exp = [
            "flashSize={0}".format(self.flash_size[self.board_id]),
            "systemid={0}".format(self.board_id),
            "serialno={0}".format(self.mac.lower()),
            "qrid={0}".format(self.qrcode)
        ]
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, post_exp=exp)
        cmd = "cat /usr/lib/build.properties"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)
        cmd = "cat /usr/lib/version"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, valid_chk=True)

        # BT FW will be checked by kernel, below info is for record
        ## BT "need" to be update will be like this
        # [   57.178542] [btmtk_info] btmtk_load_flash_init send
        # [   57.179347] [btmtk_info] btmtk_load_flash_chech_version send
        # [   57.180105] [btmtk_info] Get event result: NG
        # [   57.180105] 
        # [   57.180132] [btmtk_info] btmtk_cif_receive_evt, len = 22 Recv CMD:  Length(22):  E4 14 02 3F 10 00 05 00 32 30 32 31 30 32 32 34 31 30 32 35 32 39
        # [   57.180144] [btmtk_info] btmtk_cif_receive_evt, len = 22 Expect CMD:  Length(22):  E4 14 02 3F 10 00 05 00 32 30 32 31 30 32 30 34 32 30 31 32 34 33

        ## BT "no need" to be updated will be like this
        # [   42.418357] [btmtk_info] btmtk_load_flash_init send
        # [   42.419253] [btmtk_info] btmtk_load_flash_chech_version send
        # [   42.420077] [btmtk_err] ***btmtk_load_flash_programing: btmtk_load_flash_chech_version pass, no need update***
        # [   43.020197] mtk_soc_eth 1b100000.ethernet: path gmac1_sgmii in set_mux_gdm1_to_gmac1_esw updated = 1

        number_time = 0 # one loop is 5sec for 1 time
        while number_time < 14:  #14 * 5 = max 70 sec wait for dmesg key word for BT FW check, it will be around 43 sec 
            time.sleep(5)
            cmd = 'dmesg | grep -i "btmtk_load_flash_programing"'
            output = self.pexp.expect_get_output(action=cmd, prompt="", timeout=3)
            log_debug(output)
            if output.find("btmtk_load_flash_programing: btmtk_load_flash_chech_version pass, no need update") >= 0:
                log_debug("BT fw will 'not' need to be updated")
                break

            cmd = 'dmesg | grep -i "Get event result:"'
            output = self.pexp.expect_get_output(action=cmd, prompt="", timeout=3)
            log_debug(output)
            if output.find("Get event result: NG") >= 0:
                log_debug("BT fw will need to be updated, it will reboot system automatically")
                if bom == "00773" and rev_of_bomrev < 15:
                    pass
                else:   #for new bom U6-lIte and U6-LR
                    self.pexp.expect_only(120, "\[BT Power On Result\] Success")
                self.login(timeout=240,press_enter=True)
                break

            number_time = number_time + 1

        # RF Eric_Liao's request
        if self.board_id == "a620":
            self.check_wifi_eeprom()

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "fw_setenv is_ble_stp true")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "fw_printenv", "is_ble_stp=true")
        self.pexp.expect_action(10, self.linux_prompt, "reboot")

        if bom == "00773" and rev_of_bomrev < 15:
            pass
        else:   #for new bom U6-lIte and U6-LR
            self.pexp.expect_only(120, "\[BT Power On Result\] Success")

        if self.board_id == "a612" or self.board_id == "a614" or self.board_id == "a640":
            #to skip login action because fw update BT fw will take time , there is no this action in previous fw. 
            # factory said it take too much time
            # self.login(timeout=240,press_enter=True)
            pass
        elif self.board_id == "a620":
            self.pexp.expect_action(30, "Hit any key to stop autoboot|Autobooting in 2 seconds, press|Autobooting in 3 seconds, press", "")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE is True:
            self.enter_uboot()
            self.set_uboot_network()
            self.update_uboot()
            msg(10, "Update uboot successfully ...")

        if self.BOOT_RECOVERY_IMAGE is True:
            self.enter_uboot()
            self.set_uboot_network()
            self.boot_recovery_image(self.fcdimg)
            msg(15, "Boot into recovery image for registration ...")
            self.init_recovery_image()

# 20221202 Double add for recall sample's reboot issue (BLE FW update fail)
        if self.SPECIAL_RECALL_EVENT is True:
            cmd = "echo 5edfacbf > /proc/ubnthal/.uf"
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
            time.sleep(1)
            #self.cnapi.xcmd("ll")
            self.pexp.expect_lnxcmd(timeout=1, pre_exp=self.linux_prompt, action="ll", post_exp="abcd")
            #### echo 5edfacbf > /proc/ubnthal/.uf


        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        # retry for unstable helper_UAP6
        retry = 3
        while retry >= 0:
            if self.DOHELPER_ENABLE is True:
                self.erase_eefiles()
                msg(30, "Do helper to get the output file to devreg server ...")
                self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo 7 > /proc/sys/kernel/printk")
                self.prepare_server_need_files()

                eetxt_dut_path = os.path.join(self.tftpdir, self.eetxt)
                cmd = "cat {0} | grep uid".format(eetxt_dut_path)
                log_debug("host cmd: " + cmd)
                [uid_long, rtc] = self.fcd.common.xcmd(cmd)
                uid = re.search(r'value=(.*)', uid_long, re.S).group(1).strip()
                log_debug("Flash UID=" + str(uid))
                if uid is not '':
                    break
                else:
                    if retry == 0:
                        error_critical("Failed to gen files by helper")
                    log_debug("Retrying to run helper, remaining {}.".format(retry))
                    retry -= 1
                    time.sleep(2)

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            msg(60, "Updating released firmware ...")
            self.fwupdate()
            msg(70, "Updating released firmware done...")

        if self.DATAVERIFY_ENABLE is True:
            msg(80, "Save STP_ENV...")
            self.enter_uboot(stp_enable=True)
            # self.set_stp_env() will enable BLE and save other parameters in uboot
            # if changing parambeter before set_stp_enable, can save stp only, others can't save
            # self.set_stp_env()
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
            msg(85, "Save STP_ENV done...")
            self.check_info()
            msg(90, "Succeeding in checking the devreg information ...")

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    u6mt762xfactory = U6MT762xFactory()
    u6mt762xfactory.run()

if __name__ == "__main__":
    main()
