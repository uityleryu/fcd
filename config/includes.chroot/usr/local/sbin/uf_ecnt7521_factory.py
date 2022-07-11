#!/usr/bin/python3

from binascii import unhexlify
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil

class UFECNT7521Factory(ScriptBase):
    def __init__(self):
        super(UFECNT7521Factory, self).__init__()
        self.ver_extract()
        self.init_vars()
        self.hw_revision = (int(self.bom_rev[0:5]) << 8) + int(self.bom_rev[6:8])
        self.hw_pref = 13

    def init_vars(self):
        self.ubpmt = {
            'eec5': "",
            'eec8': ""
        }

        self.lnxpmt = {
            'eec5': "#",
            'eec8': "#"
        }

        self.lnxpmt_fcdfw = {
            'eec5': "#",
            'eec8': "#"
        }

        self.bootloader = {
            'eec5': "eec5-uboot.bin",
            'eec8': "eec8-uboot.bin"
        }

        self.product_class_table = {
            'eec5': "basic",
            'eec8': "basic"
        }

        self.devregmtd = {
            'eec5': "/dev/mtdblock9",
            'eec8': "/dev/mtdblock9"
        }

        self.helpername = {
            'eec5': "helper_ECNT7528_debug",
            'eec8': "helper_ECNT7528_debug"
        }

        self.pd_dir_table = {
            'eec5': "uf_wifi6",
            'eec8': "uf_wifi6"
        }

        self.ethnum = {
            'eec5': "1",
            'eec8': "1",
        }

        self.wifinum = {
            'eec5': "1",
            'eec8': "0"
        }

        self.btnum = {
            'eec5': "1",
            'eec8': "0"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.region_dict = {
            "World": '1',
            "USA/Canada": '2'
        }

        self.region_code = self.region_dict[self.region_name]

        self.devregpart = self.devregmtd[self.board_id]
        self.product_class = self.product_class_table[self.board_id]

        self.linux_prompt = self.lnxpmt[self.board_id]
        self.linux_prompt_fcdfw = self.lnxpmt_fcdfw[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]

        self.tftpdir = self.tftpdir + "/"

        # EX: /tftpboot/tools/af_af60
        self.pd_dir = self.pd_dir_table[self.board_id]
        self.tools_full_dir = os.path.join(self.fcd_toolsdir, self.pd_dir)

        # EX: /tftpboot/tools/af_af60/id_rsa
        self.id_rsa = os.path.join(self.tools_full_dir, "id_rsa")
        self.bomrev = "13-{0}".format(self.bom_rev)

        # EX: helper in FCD host: /tftpboot/tools/af_af60/helper_IPQ40xx
        self.helperexe = self.helpername[self.board_id]
        self.helper_path = self.pd_dir

        # EX: /tftpboot/tools/commmon/x86-64k-ee
        self.eetool = os.path.join(self.fcd_commondir, self.eepmexe)
        self.dropbear_key = "/tmp/dropbear_key.rsa.{0}".format(self.row_id)

    def stop_uboot(self):
        print('stop_uboot')
        self.pexp.expect_ubcmd(30, "Press any key to enter boot command mode.", "\n")
       
    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ipaddr " + self.dutip)
        
    def lnx_netcheck(self, netifen=False):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()

    def check_info(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        cmd = 'cat /proc/bsp_helper/cpu_rev_id'
        self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd)

    def check_onu(self):
        cmd = "cat /sys/class/net/pon/address"
        mac_with_colon = self.get_mac_with_colon()
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd, post_exp=mac_with_colon.lower())

        time.sleep(2)
        cmd = "cat /proc/ubnthal/*"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd, post_exp='~')

    def get_mac_with_colon(self):
        ans = ''
        for i in range(len(self.mac)):
            ans += self.mac[i]
            if i & 1 and i != len(self.mac) - 1:
                ans += ':'
        return ans.strip()
        
    def set_show_mac(self):
        mac_with_colon = self.get_mac_with_colon()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "macaddr {}".format(mac_with_colon))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'macaddr')

    def update_fw(self, where):
        time.sleep(1)
        self.set_uboot_network()

        image_name = {
            'uboot':  ['--tc'  , 'tcboot.bin' , '{}-uboot.bin'.format(self.board_id)],
            'kernel': ['--boot', 'tclinux.bin', '{}-fw.bin'.format(self.board_id)]
        }

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue {}".format(image_name[where][0]))
        if self.cnapi.ip_is_alive("{}".format(self.dutip), retry=120) is False:
            error_critical("Can't ping to DUT {}".format(self.dutip))

        cmd = "atftp -p -l {0}/{1} -r {3} {2}".format(self.fwdir, image_name[where][2], self.dutip, image_name[where][1])

        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload image")
        else:
            log_debug("Uploading image successfully")

        self.pexp.expect_only(120, "ubnt_process_image")
        if image_name[where][0] == '--boot':
            self.pexp.expect_only(120, "Upgrade image check ok.")

        self.pexp.expect_only(120, "done")
        self.pexp.expect_only(120, "resetting")
    
    def eth1_mac_new_rule(self, mac_list):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000006 {}'.format(mac_list[0]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000007 {}'.format(mac_list[1]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000008 {}'.format(mac_list[2]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000009 {}'.format(mac_list[3]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000a {}'.format(mac_list[4]))
        
        eth1_mac_last_two = (hex(int(mac_list[5], 16) + 1))[2:]
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000b {}'.format(eth1_mac_last_two))
        
    def write_hw_info(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'erase 01f60000 10000')

        time.sleep(5)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'flash_read 80000000 01f60000 10000')

        mac_list = []
        for i in range(0, len(self.mac), 2):
            mac_list.append(self.mac[i:i + 2])
            op = int('2', 16)

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000000 {}'.format(mac_list[0]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000001 {}'.format(mac_list[1]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000002 {}'.format(mac_list[2]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000003 {}'.format(mac_list[3]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000004 {}'.format(mac_list[4]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000005 {}'.format(mac_list[5]))

        self.eth1_mac_old_rule(mac_list, op)

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a022 {}'.format(mac_list[0]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a023 {}'.format(mac_list[1]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a024 {}'.format(mac_list[2]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a025 {}'.format(mac_list[3]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a026 {}'.format(mac_list[4]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a027 {}'.format(mac_list[5]))

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000c {}'.format(self.board_id[0:2]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000d {}'.format(self.board_id[2:]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000e 07')
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000f 77')

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000010 {}'.format(hex((self.hw_revision >> 24) & 0xff)[2:]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000011 {}'.format(hex((self.hw_revision >> 16) & 0xff)[2:]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000012 {}'.format(hex((self.hw_revision >> 8) & 0xff)[2:]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000013 {}'.format(hex((self.hw_revision) & 0xff)[2:]))

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000016 {}'.format(hex((self.hw_pref >> 8) & 0xff)[2:]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000017 {}'.format(hex((self.hw_pref) & 0xff)[2:]))

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a020 07')
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000a021 77')

        log_debug('Region name = {}.'.format(self.region_name))
        log_debug('Region code = {}.'.format(self.region_code))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80001000 {}'.format(self.region_code))

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'dump 80000000 30')

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'flash 01f60000 80000000 10000 0')

    def erase_setting(self, only_cfg=False):
        time.sleep(5)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'erase_cfg')
        
        if not only_cfg:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'mtd')
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'erase 01f70000 90000')
        
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'reset')

    def set_board_gpon_mode(self):
        cmds = ['echo set_flash_register 0x07050701 0x94 > /proc/pon_phy/debug',
            'echo save_flash_matrix > /proc/pon_phy/debug',
            'mtd bob save']
        for cmd in cmds:
            time.sleep(2)
            self.pexp.expect_lnxcmd(5, self.linux_prompt, cmd, post_exp=self.linux_prompt)

    def eth1_mac_old_rule(self, mac_list, op):
        
        mac0_or_02 = hex(int(mac_list[0], 16) | op)[2:]
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000006 {}'.format(mac0_or_02))

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000007 {}'.format(mac_list[1]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000008 {}'.format(mac_list[2]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 80000009 {}'.format(mac_list[3]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000a {}'.format(mac_list[4]))
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, 'memwb 8000000b {}'.format(mac_list[5]))

    def run(self):
        UPDATE_UBOOT_EN = True
        PROVISION_EN = True
        DOHELPER_EN = True
        REGISTER_EN = True
        UPDATE_FCDFW_EN = True
        DATAVERIFY_EN = True

        """
        Main procedure of factory
        """
        
        msg(1, "Start Procedure")
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\r")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        self.mac = self.mac.upper()

        if UPDATE_UBOOT_EN is True:
            msg(5, "Configure bootloader...")
            self.stop_uboot()
            self.set_show_mac()
            msg(10, 'Configure bootloader... done.')

            self.update_fw('uboot')
            msg(15, "Upgrade uboot... done.")   
            
            msg(16, "Write devreg data...")
            self.stop_uboot()
            self.write_hw_info()
            msg(20, "Write devreg data... done.")

            msg(21, "Erase settings...")
            self.erase_setting()
            msg(25, "Erase settings... done.")

        if UPDATE_FCDFW_EN is True:
            msg(30, "update firmware...")
            self.stop_uboot()
            self.set_show_mac()
            self.update_fw('kernel')
            msg(40, "Upgrade fw... done")

        self.login(timeout=30, retry=5)

        if PROVISION_EN is True:    
            msg(50, "Sendtools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=60)
        
        if DOHELPER_EN is True:
            msg(60, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.FCD_TLV_data = False
            self.registration()
            msg(70, "Finish doing registration ...")
            self.check_devreg_data()
            msg(80, "Finish doing signed file and EEPROM checking ...")

        self.pexp.expect_ubcmd(10, self.linux_prompt, "reboot")
        self.stop_uboot()
        self.erase_setting(only_cfg=True)

        time.sleep(40)
        self.login(retry=5)

        if DATAVERIFY_EN is True:
            self.check_onu()
            msg(90, "Succeeding in checking the MAC information ...")


        msg(95, "Set DUT to GPON mode ...")
        self.set_board_gpon_mode()

        msg(100, "Complete FCD process ...")
        self.close_fcd()
        
def main():
    uf_ecnt7521_factory = UFECNT7521Factory()
    uf_ecnt7521_factory.run()

if __name__ == "__main__":
    main()