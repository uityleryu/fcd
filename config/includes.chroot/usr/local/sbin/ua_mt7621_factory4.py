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


class UAMT7621Factory(ScriptBase):
    def __init__(self):
        super(UAMT7621Factory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        '''
            ec55: Hub-Enterprise
            ec46: Hub-Gate
        '''

        self.ubpmt = {
            'ec55': "=>",
            'ec46': "=>"
        }

        self.ubpmt_fcdfw = {
            'ec55': "MT7621 #",
            'ec46': "MT7621 #"
        }

        # linux console prompt
        self.lnxpmt = {
            'ec55': "root@LEDE:",
            'ec46': "root@LEDE:/#"
        }

        self.lnxpmt_fcdfw = {
            'ec55': "#",
            'ec46': "#"
        }

        self.cacheaddr = {
            'ec55': "0x80010000",
            'ec46': "0x80010000"
        }

        self.ubaddr = {
            'ec55': "0x0",
            'ec46': "0x0"
        }

        self.ubsz = {
            'ec55': "0x2000000",
            'ec46': "0x2000000"
        }

        self.ubmtd = {
            'ec55': "/dev/mtd0",
            'ec46': "/dev/mtd0"
        }

        self.product_class_table = {
            'ec55': "basic",
            'ec46': "basic"
        }

        self.devregmtd = {
            'ec55': "/dev/mtdblock3",
            'ec46': "/dev/mtdblock3"
        }

        self.pd_dir_table = {
            'ec55': "",
            'ec46': ""
        }

        self.ethnum = {
            'ec55': "1",
            'ec46': "1"
        }

        self.wifinum = {
            'ec55': "0",
            'ec46': "1"
        }

        self.btnum = {
            'ec55': "0",
            'ec46': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.devregpart = self.devregmtd[self.board_id]
        self.product_class = self.product_class_table[self.board_id]

        self.linux_prompt = self.lnxpmt[self.board_id]
        self.linux_prompt_fcdfw = self.lnxpmt_fcdfw[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]
        self.bootloader_prompt_fcdfw = self.ubpmt_fcdfw[self.board_id]
        self.bootloader_prompt_combine = [self.bootloader_prompt, self.bootloader_prompt_fcdfw]

        self.cache_address = self.cacheaddr[self.board_id]
        self.uboot_address = self.ubaddr[self.board_id]
        self.uboot_size = self.ubsz[self.board_id]
        self.ubootpart = self.ubmtd[self.board_id]

        self.tftpdir = self.tftpdir + "/"

        # EX: /tftpboot/tools/af_af60
        self.pd_dir = self.pd_dir_table[self.board_id]
        self.tools_full_dir = os.path.join(self.fcd_toolsdir, self.pd_dir)

        # EX: /tftpboot/tools/af_af60/id_rsa
        self.id_rsa = os.path.join(self.tools_full_dir, "id_rsa")
        self.bomrev = "13-{0}".format(self.bom_rev)

    def stop_uboot(self, timeout=30):
        self.pexp.expect_ubcmd(timeout, "Hit any key to stop autoboot", "\033")

    def enter_console(self):
        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        if self.board_id in ['ec55']:
            self.pexp.expect_ubcmd(10, "login:", "ui")
            self.pexp.expect_ubcmd(10, "Password:", "ui")
        else:
            self.pexp.expect_ubcmd(10, "login:", "ubnt")
            self.pexp.expect_ubcmd(10, "Password:", "ubnt")

    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt_combine, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt_combine, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt_combine, "ping " + self.tftp_server)

    def turn_on_console(self):
        self.stop_uboot(240)
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt_fcdfw, "setenv bootargs console=ttyS0,115200")
        time.sleep(3)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt_fcdfw, "saveenv", "OK")
        time.sleep(3)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt_fcdfw, "reset")

    def boot_to_T1(self):
        self.stop_uboot()
        time.sleep(1)
        self.set_uboot_network()

        log_debug("Starting doing U-Boot update")
        cmd = "tftpboot {0} images/{1}".format(self.cache_address, "{}-t1-fw.bin".format(self.board_id))
        log_debug(cmd)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt_combine, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "usetprotect spm off")

        cmd = "sf probe;sf erase {0} {1};sf write {2} {0} {1}".format(self.uboot_address, self.uboot_size,
                                                                      self.cache_address)
        log_debug(cmd)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt_combine, cmd)
        time.sleep(1)

        self.pexp.expect_ubcmd(200, self.bootloader_prompt_combine, "reset")
        self.pexp.expect_ubcmd(240, "drop_caches", "")
        self.pexp.expect_ubcmd(10, self.linux_prompt, "")

    def update_fcd_uboot(self):
        source = os.path.join(self.fwdir, "{}-uboot.bin".format(self.board_id))
        target = os.path.join(self.dut_tmpdir, "uboot.bin")
        # get length of uboot image
        cmd = "stat -Lc %s {}".format(source)
        log_debug("host cmd: " + cmd)
        [uboot_img_sz, rtc] = self.fcd.common.xcmd(cmd)
        log_debug("uboot_img_sz: " + uboot_img_sz)

        log_debug("Send uboot image from host to DUT ...")
        self.tftp_get(remote=source, local=target, timeout=10, post_en=self.linux_prompt)

        pattern = r"[A-Fa-f0-9]{32}"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "mtd erase {}".format(self.ubootpart))
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if={} of={}".format(target, self.ubootpart))
        rsp = self.pexp.expect_get_output("md5sum {}".format(target), self.linux_prompt)
        log_debug('rsp = {}'.format(rsp))
        try:
            match = re.findall(pattern, rsp)
            if match:
                uboot_img_md5 = match[0]
                log_debug('uboot md5sum from file is {}'.format(uboot_img_md5))
            else:
                error_critical("Parsing uboot md5sum from file failed!!!")
        except Exception as e:
            error_critical("Parsing uboot md5sum from file exception occurred!!!")

        cmd = "dd if={} of=/tmp/dump_uboot bs=1 count={}".format(self.ubootpart, uboot_img_sz)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        rsp = self.pexp.expect_get_output("md5sum /tmp/dump_uboot", self.linux_prompt)
        log_debug('rsp = {}'.format(rsp))
        try:
            match = re.findall(pattern, rsp)
            if match:
                uboot_dump_md5 = match[0]
                log_debug('uboot md5sum from flash is {}'.format(uboot_dump_md5))
            else:
                error_critical("Parsing uboot md5sum from flash failed!!!")
        except Exception as e:
            error_critical("Parsing uboot md5sum from flash exception occurred!!!")

        if uboot_img_md5 == uboot_dump_md5:
            log_debug("Upgrade FCD Uboot success !")
        else:
            error_critical("Upgrade FCD Uboot fail !")

    def update_fcd_fw(self):
        self.stop_uboot()
        time.sleep(1)
        self.set_uboot_network()

        self.pexp.expect_ubcmd(30, self.bootloader_prompt_fcdfw, "set do_urescue TRUE")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt_fcdfw, "bootubnt")
        self.pexp.expect_ubcmd(30, "Listening for TFTP transfer on", "")

        cmd = "atftp -p -l {0}/{1} {2}".format(self.fwdir, "{}-fw.bin".format(self.board_id), self.dutip)
        log_debug("host cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

    def check_info2(self):
        self.enter_console()

        time.sleep(3)

        cmd = "cat /usr/lib/version"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "info"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "cat /etc/board.info"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "cat /proc/ubnthal/board"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "cat /proc/ubnthal/system.info"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "cat /proc/meminfo  | head -n 3"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "cat /proc/cpuinfo  | grep processor"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "cat /proc/cmdline"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        cmd = "cat /proc/mtd"
        self.pexp.expect_lnxcmd(10, self.linux_prompt_fcdfw, cmd)

        self.pexp.expect_only(10, self.linux_prompt_fcdfw)

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

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        if UPDATE_UBOOT_EN is True:
            msg(10, "Booting the T1 image ...")
            self.boot_to_T1()

        if PROVISION_EN is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.erase_eefiles()
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
            msg(40, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if REGISTER_EN is True:
            self.registration()
            msg(50, "Finish doing registration ...")
            self.check_devreg_data()
            msg(60, "Finish doing signed file and EEPROM checking ...")

        # self.pexp.expect_ubcmd(10, self.linux_prompt, "reboot")

        if UPDATE_FCDFW_EN is True:
            msg(70, "update firmware...")
            self.update_fcd_uboot()
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
            self.update_fcd_fw()
            self.turn_on_console()

        if DATAVERIFY_EN is True:
            self.check_info2()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    ua_mt7621_factory = UAMT7621Factory()
    ua_mt7621_factory.run()


if __name__ == "__main__":
    main()
