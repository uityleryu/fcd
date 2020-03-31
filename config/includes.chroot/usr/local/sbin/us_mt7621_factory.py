#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.common import Common
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class USFLEXFactory(ScriptBase):
    def __init__(self):
        super(USFLEXFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.devregpart = "/dev/mtdblock3"
        self.helperexe = "helper_UNIFI_MT7621_release"
        self.bootloader_prompt = "MT7621 #"
        self.fcdimg = self.board_id + "-fcd.bin"
        self.helper_path = "common"

        # customize variable for different products
        self.radio_check = {'ec25': ('0x8052', '/dev/mtd2', '0x02')}
        self.zeroip_en = {'ed10', 'ed11'}
        self.wait_LCM_upgrade_en = {'ed11'}
        self.uboot_upgrade_en = {'ed11', 'ec2a', 'ec20', 'ec22', 'ec25', 'ec26',
                                 'a610', 'a611', 'a612', 'a613', 'a614'}
        self.uap6_series = {'a610', 'a611', 'a612', 'a613', 'a614'}
        self.helperexe = "helper_UAP6_MT7621_release" if self.board_id in self.uap6_series else self.helperexe

        # number of mac
        self.macnum = {'ed10': "3",
                       'ec20': "1",
                       'ec22': "1",
                       'ec25': "1",
                       'ec26': "1",
                       'ec2a': "1",
                       'ed11': "2",
                       'a610': "1",
                       'a611': "1",
                       'a612': "1",
                       'a613': "1",
                       'a614': "1"}
        # number of WiFi
        self.wifinum = {'ed10': "0",
                        'ec20': "2",
                        'ec22': "2",
                        'ec25': "2",
                        'ec26': "2",
                        'ec2a': "2",
                        'ed11': "0",
                        'a610': "2",
                        'a611': "2",
                        'a611': "2",
                        'a612': "2",
                        'a613': "2",
                        'a614': "2"}
        # number of Bluetooth
        self.btnum = {'ed10': "0",
                      'ec20': "1",
                      'ec22': "1",
                      'ec25': "1",
                      'ec26': "1",
                      'ec2a': "0",
                      'ed11': "0",
                      'a610': "1",
                      'a611': "1",
                      'a612': "1",
                      'a613': "1",
                      'a614': "1"}
        # vlan port mapping
        self.vlanport_idx = {'ed10': "'6 4'",
                             'ec20': "'6 0'",
                             'ec22': "'6 0'",
                             'ec25': "'6 0'",
                             'ec26': "'6 0'",
                             'ec2a': "'6 0'",
                             'ed11': "'6 0'",
                             'a610': "'6 0'",
                             'a611': "'6 0'",
                             'a612': "'6 0'",
                             'a613': "'6 0'",
                             'a614': "'6 0'"}
        # flash size map
        self.flash_size = {'ed10': "33554432",
                           'ec20': "33554432",
                           'ec22': "33554432",
                           'ec25': "33554432",
                           'ec26': "33554432",
                           'ec2a': "33554432",
                           'ed11': "16777216",
                           'a610': "33554432",
                           'a611': "33554432",
                           'a612': "33554432",
                           'a613': "33554432",
                           'a614': "33554432"}
        # firmware image
        self.fwimg = {'ed10': self.board_id + "-diag.bin",
                      'ec20': self.board_id + ".bin",
                      'ec22': self.board_id + ".bin",
                      'ec25': self.board_id + ".bin",
                      'ec26': self.board_id + ".bin",
                      'ec2a': self.board_id + ".bin",
                      'ed11': self.board_id + "-diag.bin",
                      'a610': self.board_id + ".bin",
                      'a611': self.board_id + ".bin",
                      'a612': self.board_id + ".bin",
                      'a613': self.board_id + ".bin",
                      'a614': self.board_id + ".bin"}

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        self.UPDATE_UBOOT_ENABLE    = True
        self.BOOT_RECOVERY_IMAGE    = True
        self.PROVISION_ENABLE       = True
        self.DOHELPER_ENABLE        = True
        self.REGISTER_ENABLE        = True
        self.FWUPDATE_ENABLE        = True 
        self.DATAVERIFY_ENABLE      = True 
        self.CONF_ZEROIP_ENABLE     = True 
        self.WAIT_LCMUPGRADE_ENABLE = True 

    def boot_recovery_image(self, Img):
        self.pexp.expect_action(30, self.bootloader_prompt, "tftpboot 84000000 "+"images/"+Img)
        self.pexp.expect_only(30, "Bytes transferred = "+str(os.stat(self.fwdir+"/"+Img).st_size))
        self.pexp.expect_action(10, self.bootloader_prompt, "bootm")
        self.login_kernel()

    def init_recovery_image(self):
        self.pexp.expect_action(30, self.linux_prompt, "dmesg -n 1")
        #self.SetnCheckEEPROM()
        self.CheckRadioStat()
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 set enable_vlan 1")
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 vlan 1 set vid 1")
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 vlan 1 set ports " + self.vlanport_idx[self.board_id])
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 set apply")
        self.pexp.expect_action(30, self.linux_prompt, "[ $(ifconfig | grep -c eth0) -gt 0 ] || ifconfig eth0 up")
        self.pexp.expect_action(30, self.linux_prompt, "ifconfig eth0 "+self.dutip)
        for _ in range(3):
            is_network_alive = self.is_network_alive_in_linux()                                                                                                              
            if is_network_alive is True:
                break
            time.sleep(5)
        if is_network_alive is not True:
            error_critical("Network is not good")

    def login_kernel(self):
        rt = self.pexp.expect_action(120, "Please press Enter to activate this console","")
        if rt != 0:
            error_critical("Failed to boot manufacturing kernel")
        os.system("sleep 5")
        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(30, "UBNT login: ", "ubnt")
        self.pexp.expect_action(30, "Password: ", "ubnt")

    def SetBootNet(self):
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ethaddr " + self.premac)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

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
            index = self.pexp.expect_get_index(timeout=30, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def CheckRadioStat(self):
        if self.board_id in self.radio_check:
            log_debug('Checking radio calibration status...')
            ckaddr = self.radio_check[self.board_id][0]
            factorymtd = self.radio_check[self.board_id][1]
            checkrst = self.radio_check[self.board_id][2]

            cmd = ['hexdump', '-n 1 -s', ckaddr, '-e', ' \'\"0x%02x\\n\" \' ', factorymtd]
            cmd = ' '.join(cmd)

            ret = self.pexp.expect_get_output(cmd, self.bootloader_prompt)

            if checkrst in ret:
                log_debug('Radio was calibrated')
            else:
                error_critical("Radio was NOT calibrated, status result is {}".format(ret))
        else:
            print("Pass checking radio status")

    def wait_lcm_upgrade(self):                                                                                                     
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "lcm-ctrl -t dump", post_exp="version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "", post_exp=self.linux_prompt)

    def update_uboot(self):
        uboot_img = os.path.join(self.image, self.board_id+'-uboot.bin')
        uboot_size = os.stat(os.path.join(self.tftpdir, uboot_img)).st_size
        try:
            self.pexp.expect_action(30, self.bootloader_prompt, "setenv loadaddr 0x84000000")
            self.pexp.expect_lnxcmd(15, self.bootloader_prompt,
                                    "tftpboot ${loadaddr} "+uboot_img,
                                    post_exp="Bytes transferred = {}".format(uboot_size))
        except Exception as e:
            error_critical("Failed to transfer boot img")

        self.pexp.expect_action(30, self.bootloader_prompt, "sf probe; sf erase 0x0 0x60000; \
                                sf write ${loadaddr} 0x0 ${filesize}")

        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

    def enter_uboot(self):
        rt = self.pexp.expect_action(30, "Hit any key to stop autoboot", "")

        self.bootloader_prompt = "MT7621 #"
        retry = 2
        while retry > 0:
            if rt != 0:
                error_critical("Failed to detect device")
            try:
                self.pexp.expect_action(10, self.bootloader_prompt, "")
                break
            except Exception as e:
                self.bootloader_prompt = "=>"
                log_debug("Change prompt to {}".format(self.bootloader_prompt))
                retry -= 1

        self.SetBootNet()

        if self.is_network_alive_in_uboot(retry=3) is False:
            error_critical("Failed to ping tftp server in u-boot")

    def fwupdate(self):
        log_debug("Change to product firware...")
        self.pexp.expect_action(30, "", "")
        self.pexp.expect_action(30, self.linux_prompt, "reboot -f")
        self.enter_uboot()
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearcfg TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearenv TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv do_urescue TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
        self.pexp.expect_action(30, "Listening for TFTP transfer on", "")

        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir+"/"+self.fwimg[self.board_id],
               self.dutip]
        cmdj = ' '.join(cmd)

        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
        self.pexp.expect_only(60, "Updating u-boot partition \(and skip identical blocks\)")
        self.pexp.expect_only(60, "done")
        self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(120, "done")

    def configure_zeroip(self):
        comm_util = Common()
        zero_cfg_ip = comm_util.get_zeroconfig_ip(self.mac)
        log_debug("zero cfg ip is {}".format(zero_cfg_ip))
        self.pexp.expect_action(30, self.linux_prompt, "sed -i -e \'s/netconf.1.ip=192.168.1.20/netconf.1.ip={}/g\' /tmp/system.cfg".format(zero_cfg_ip))
        self.pexp.expect_action(30, self.linux_prompt, "sed -i -e \'s/netconf.1.netmask=255.255.255.0/netconf.1.netmask=255.255.0.0/g\' /tmp/system.cfg")
        self.pexp.expect_action(30, self.linux_prompt, "sed -i \'/dhcpc.1.status=enabled/d\' /tmp/system.cfg")
        self.pexp.expect_action(30, self.linux_prompt, "sed -i \'/dhcpc.1.devname=eth0/d\' /tmp/system.cfg")
        self.pexp.expect_action(30, self.linux_prompt, "sed -i \'/mgmt.is_default=true/d\' /tmp/system.cfg")
        self.pexp.expect_action(30, self.linux_prompt, "syswrapper.sh save-config")
        self.pexp.expect_only(30, r'Storing Active.+\[%100\]')

    def check_info(self):
        self.login_kernel()
        self.pexp.expect_action(30, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(30, "flashSize="+self.flash_size[self.board_id])
        self.pexp.expect_only(30, "systemid="+self.board_id)
        self.pexp.expect_only(30, "serialno="+self.mac.lower())
        self.pexp.expect_only(30, "qrid="+self.qrcode)
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/build.properties")
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/version")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT_ENABLE is True:
            if self.board_id in self.uboot_upgrade_en:
                self.enter_uboot()
                self.update_uboot()
                msg(10, "Update uboot successfully ...")

        if self.BOOT_RECOVERY_IMAGE is True:
            self.enter_uboot()
            self.boot_recovery_image(self.fcdimg)
            msg(15, "Boot into recovery image for registration ...")
            self.init_recovery_image()

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        # retry for unstable helper_UAP6
        retry = 3
        while retry >= 0:
            if self.DOHELPER_ENABLE is True:
                self.erase_eefiles()
                msg(30, "Do helper to get the output file to devreg server ...")
                self.prepare_server_need_files()

                eetxt_dut_path = os.path.join(self.tftpdir, self.eetxt)
                [uid_long, rtc] = self.fcd.common.xcmd("cat {}|grep uid".format(eetxt_dut_path))
                uid = re.search(r'value=(.*)', uid_long, re.S).group(1).strip()
                log_debug("Flash UID="+str(uid))
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
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.CONF_ZEROIP_ENABLE is True:
            if self.board_id in self.zeroip_en:
                self.configure_zeroip()
                msg(80, "Configure zeroip done ...")

        if self.WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id in self.wait_LCM_upgrade_en:
                msg(90, "Wait LCM upgrading ...")
                self.wait_lcm_upgrade()

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    us_flex_factory = USFLEXFactory()
    us_flex_factory.run()

main()
