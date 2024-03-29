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
    ed10: USW-Flex
    ec20: UAP-nanoHD
    ec22: UAP-IW-HD
    ec25: UAP-BeaconHD (UDM-Beacon)
    ec26: UAP-FLEXHD
    ec2a: UAP nanoHD industrial
    ed11: USP-RPS
    ed13: USP-RPS-PRO
'''


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

        helper_path = {
            'ed11': 'usp_rps',  # ed11 only support old helper
            'ed13': 'usp_rps_pro',
        }
        self.helper_path = helper_path.get(self.board_id, 'common')

        # customize variable for different products
        self.radio_check = {'ec25': ('0x8052', '/dev/mtd2', '0x02')}
        self.zeroip_en = {'ed10'}
        self.wait_LCM_upgrade_en = {'ed11', 'ed13'}
        self.uboot_upgrade_en = {'ed11', 'ec2a', 'ec20', 'ec22', 'ec25', 'ec26'}

        # number of mac
        self.macnum = {
            'ed10': "3",
            'ec20': "1",
            'ec22': "1",
            'ec25': "1",
            'ec26': "1",
            'ec2a': "1",
            'ed11': "2",
            'ed13': "2"
        }
        # number of WiFi
        self.wifinum = {
            'ed10': "0",
            'ec20': "2",
            'ec22': "2",
            'ec25': "2",
            'ec26': "2",
            'ec2a': "2",
            'ed11': "0",
            'ed13': "0",
        }
        # number of Bluetooth
        self.btnum = {
            'ed10': "0",
            'ec20': "1",
            'ec22': "1",
            'ec25': "1",
            'ec26': "1",
            'ec2a': "0",
            'ed11': "0",
            'ed13': "1",
        }
        # vlan port mapping
        self.vlanport_idx = {
            'ed10': "'6 4'",
            'ec20': "'6 0'",
            'ec22': "'6 0'",
            'ec25': "'6 0'",
            'ec26': "'6 0'",
            'ec2a': "'6 0'",
            'ed11': "'6 0'",
            'ed13': "'6 0'"
        }
        # flash size map
        self.flash_size = {
            'ed10': "",
            'ec20': "33554432",
            'ec22': "33554432",
            'ec25': "33554432",
            'ec26': "33554432",
            'ec2a': "33554432",
            'ed11': "16777216",
            'ed13': "33554432",
        }
        # firmware image
        self.fwimg = {
            'ed10': self.board_id + "-diag.bin",
            'ec20': self.board_id + ".bin",
            'ec22': self.board_id + ".bin",
            'ec25': self.board_id + ".bin",
            'ec26': self.board_id + ".bin",
            'ec2a': self.board_id + ".bin",
            'ed11': self.board_id + "-fw.bin",
            'ed13': self.board_id + "-fw.bin",
        }

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
        self.login(timeout=120, press_enter=True)

    def init_recovery_image(self):
        self.pexp.expect_action(30, self.linux_prompt, "dmesg -n 1")
        #self.SetnCheckEEPROM()
        self.CheckRadioStat()
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 set enable_vlan 1")
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 vlan 1 set vid 1")
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 vlan 1 set ports " + self.vlanport_idx[self.board_id])
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 port 0 set disable 0")
        self.pexp.expect_action(30, self.linux_prompt, "swconfig dev switch0 set apply")
        self.pexp.expect_action(30, self.linux_prompt, "[ $(ifconfig | grep -c eth0) -gt 0 ] || ifconfig eth0 up")
        self.pexp.expect_action(30, self.linux_prompt, "ifconfig eth0 "+self.dutip)
        self.is_network_alive_in_linux()

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
        try:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "lcm-ctrl -t dump", post_exp="version", retry=24)
        except Exception as e:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /tmp/.lcm_fwupdate.log")
            raise e

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
        self.is_network_alive_in_uboot()

    def reboot_f(self):
        self.pexp.expect_action(30, "", "reboot -f")

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
        self.login(timeout=120, press_enter=True)
        time.sleep(15)
        self.pexp.expect_action(30, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(30, "flashSize="+self.flash_size[self.board_id])
        self.pexp.expect_only(30, "systemid="+self.board_id)
        self.pexp.expect_only(30, "serialno="+self.mac.lower())
        self.pexp.expect_only(30, "qrid="+self.qrcode)
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/build.properties")
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/version")
    
    def prepare_server_need_files_ed10(self, method="tftp"):
        log_debug("Starting to do " + self.helperexe + "...")
        helperexe_path = os.path.join('/sbin/', self.helperexe)
        md5sum_helper = 'md5sum {}'.format(helperexe_path)
        self.pexp.expect_lnxcmd(30, pre_exp=self.linux_prompt, action=md5sum_helper)

        cmd = "chmod 777 {0}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class=" + self.product_class,
            "-o field=flash_eeprom,format=binary,pathname=" + eebin_dut_path,
            ">",
            eetxt_dut_path
        ]
        sstr = ' '.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)
        time.sleep(1)

        files = [self.eetxt, self.eebin]
        for fh in files:
            srcp = os.path.join(self.tftpdir, fh)
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send helper output files from DUT to host ...")

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

        if self.DOHELPER_ENABLE is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            if self.board_id == 'ed10':
                self.prepare_server_need_files_ed10()
            else:
                self.prepare_server_need_files()

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

if __name__ == "__main__":
    main()
