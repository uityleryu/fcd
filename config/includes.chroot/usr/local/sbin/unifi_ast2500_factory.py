#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True


class UNIFIBMCFactory(ScriptBase):
    def __init__(self):
        super(UNIFIBMCFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.helperexe = "helper_AST2500_release"
        self.helper_path = "usrv"
        self.devregpart = "/tmp/eeprom0"
        self.cpuid = ""
        self.flash_jedecid = ""
        self.flash_uuid = ""

        # number of mac
        self.macnum = {
            '1200': "2"
        }

        # number of WiFi
        self.wifinum = {
            '1200': "0"
        }

        # number of Bluetooth
        self.btnum = {
            '1200': "1"
        }

        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.PROVISION_EN       = True
        self.DOHELPER_EN        = True
        self.REGISTER_EN        = True

    def prepare_server_need_files(self):
        # Ex: tools/uvp/helper_DVF99_release_ata_max
        srcp = os.path.join(self.tools, self.helper_path, self.helperexe)

        # Ex: /tmp/helper_DVF99_release_ata_max
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)
        self.tftp_get(remote=srcp, local=helperexe_path, timeout=60)

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
            # Ex: /tftpboot/e.t.0
            srcp = os.path.join(self.tftpdir, fh)

            # Ex: /tmp/e.t.0
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        # Ex: tools/uvp/helper_DVF99_release_ata_max
        srcp = os.path.join(self.tools, "usrv", "ui-getuuid")
        # Ex: /tmp/helper_DVF99_release_ata_max
        dstp = os.path.join(self.dut_tmpdir, "ui-getuuid")
        self.tftp_get(remote=srcp, local=dstp, timeout=60)

        cmd = "chmod 777 {0}".format(dstp)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        cmd = "cat /proc/cpumidr"
        rtb = self.pexp.expect_get_output(cmd, self.linux_prompt)
        self.cpuid = rtb.split("\n")[1].strip()
        log_debug("cpuid: " + self.cpuid)

        cmd = "cat /sys/class/mtd/mtd0/jedec_id"
        rtb = self.pexp.expect_get_output(cmd, self.linux_prompt)
        self.flash_jedecid = rtb.split("\n")[1].strip().zfill(8)
        log_debug("jedecid: " + self.flash_jedecid)

        cmd = "/tmp/ui-getuuid"
        rtb = self.pexp.expect_get_output(cmd, self.linux_prompt)
        self.flash_uuid = rtb.split("\n")[1].strip()
        log_debug("uuid: " + self.flash_uuid)

        log_debug("Send helper output files from DUT to host ...")

    def registration(self, regsubparams = None):
        log_debug("Starting to do registration ...")
        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        clientbin = "/usr/local/sbin/client_rpi4_release"
        regparam = [
            "-h prod.udrs.io",
            "-k {}".format(self.pass_phrase),
            "-i field=product_class_id,format=hex,value=0014",
            "-i field=cpu_rev_id,format=hex,value={}".format(self.cpuid),
            "-i field=flash_jedec_id,format=hex,value={}".format(self.flash_jedecid),
            "-i field=flash_uid,format=hex,value={}".format(self.flash_uuid),
            reg_qr_field,
            "-i field=flash_eeprom,format=binary,pathname={}".format(self.eebin_path),
            "-i field=fcd_version,format=hex,value={}".format(self.sem_ver),
            "-i field=sw_id,format=hex,value={}".format(self.sw_id),
            "-i field=sw_version,format=hex,value={}".format(self.fw_ver),
            "-o field=flash_eeprom,format=binary,pathname={}".format(self.eesign_path),
            "-o field=registration_id",
            "-o field=result",
            "-o field=device_id",
            "-o field=registration_status_id",
            "-o field=registration_status_msg",
            "-o field=error_message",
            "-x {}ca.pem".format(self.key_dir),
            "-y {}key.pem".format(self.key_dir),
            "-z {}crt.pem".format(self.key_dir)
        ]

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Security Service Device Registration Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        self.pass_devreg_client = True

        log_debug("Excuting client registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()

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

        self.login(timeout=300, username="root", password="0penBmc")
        # Workaround: To sleep until network stable, the network intialization is divided into several parts
        #             It's hard to check if network initialization completes or not via ping.
        time.sleep(60)
        cmd = "dmesg -n1"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        cmd = "dd if=/dev/zero bs=1k count=64 | tr '\\000' '\\377' > {0}".format(self.devregpart)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            self.erase_eefiles()
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_EN is True:
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
            ============ Registration End ============
        '''

        cmd = "write_eeprom 6-0050 {0}".format(self.devregpart)
        self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, "Write EEPROM Done")
        msg(60, "Finish writing EEPROM ...")

        eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)
        cmd = "read_eeprom 6-0050 {0}".format(eechk_dut_path)
        self.pexp.expect_lnxcmd(120, self.linux_prompt, cmd, "Read EEPROM Done")

        self.tftp_put(remote=self.eechk_path, local=eechk_dut_path, timeout=30)
        rtc = filecmp.cmp(self.eechk_path, self.eesigndate_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")
        msg(70, "Finish comparing EEPROM ...")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm -rf /run/initramfs/rw/cow/etc/systemd/network",
                                self.linux_prompt)

        remote_path = "{}/{}-dfu.bin".format(self.fwdir, self.board_id)
        local_path = "{}/{}-dfu.bin".format(self.dut_tmpdir, self.board_id)
        self.tftp_get(remote=remote_path, local=local_path, timeout=30)

        remote_path = "{}/{}-lcmfw.bin".format(self.fwdir, self.board_id)
        local_path = "{}/{}-lcmfw.bin".format(self.dut_tmpdir, self.board_id)
        self.tftp_get(remote=remote_path, local=local_path, timeout=30)

        cmd = "cd {0}; update_lcm {1}-dfu.bin {1}-lcmfw.bin".format(self.dut_tmpdir, self.board_id)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

        expect_msg = "UI LCM bootloader and firmware downloaded successfully"
        self.pexp.expect_only(120, expect_msg)

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    factory = UNIFIBMCFactory()
    factory.run()

if __name__ == "__main__":
    main()
