#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

SIM_PCYL_LNX_EN = False
SIM_PCYL_UB_EN = False
UB_WR_DUMMY_EN = True
PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
SETBOARDNAME_EN = True
FWUPDATE_EN = True
DATAVERIFY_EN = True
VTSYCHECK_EN = False
AUTODIAG_EN = False

'''
    eed4: UISP-SPINE-100G
    eed5: UISP-LEAF-100G
'''


class UISPALPINE(ScriptBase):
    def __init__(self):
        super(UISPALPINE, self).__init__()

        self.ver_extract()
        self.devregpart = "/dev/mtd4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = self.board_id
        self.bootloader_prompt = "UBNT_UISP_ALL>"

        # number of Ethernet
        ethnum = {
            'eed4': "130",
            'eed5': "65",
        }

        # number of WiFi
        wifinum = {
            'eed4': "0",
            'eed5': "0",
        }

        # number of Bluetooth
        btnum = {
            'eed4': "1",
            'eed5': "1",
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }

    def login(self, username="ubnt", password="ubnt", timeout=10, press_enter=False, retry=3, log_level_emerg=False):
        """
        should be called at login console
        """
        for i in range(0, retry + 1):
            post = [
                "login:",
                "Error-A12 login"
            ]
            ridx = self.pexp.expect_get_index(timeout, post)
            if ridx >= 0:
                '''
                    To give twice in order to make sure of that the username has been keyed in
                '''
                self.pexp.expect_action(10, "", username)
                self.pexp.expect_action(10, "Password:", password)
                break
            else:
                self.pexp.expect_action(timeout, "", "\003")
                print("Retry login {}/{}".format(i + 1, retry))
                timeout = 10
                self.pexp.expect_action(10, "", "\n")
        else:
            raise Exception("Login exceeded maximum retry times {}".format(retry))

        if log_level_emerg is True:
            self.pexp.expect_action(10, self.linux_prompt, "dmesg -n1")

        return ridx

    def data_provision_64k(self, netmeta, post_en=True):
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
            "-f " + self.eegenbin_path,
            "-r 113-{0}".format(self.bom_rev),
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + netmeta['ethnum'][self.board_id],
            "-w " + netmeta['wifinum'][self.board_id],
            "-b " + netmeta['btnum'][self.board_id],
            "-k " + self.rsakey_path
        ]
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

        cmd = "dd if={0} of=/tmp/{1} bs=1k count=64".format(self.devregpart, self.eeorg)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(0.1)

        dstp = "/tmp/{0}".format(self.eeorg)
        self.tftp_put(remote=self.eeorg_path, local=dstp, timeout=20)


        log_debug("Writing the information from e.gen.{} to e.org.{}".format(self.row_id, self.row_id))
        '''
            Trying to access the initial information from the EEPROM of DUT and save to e.org.0
        '''
        f1 = open(self.eeorg_path, "rb")
        org_tres = list(f1.read())
        f1.close()

        '''
            Creating by the FCD host with the utiltiy eetool
        '''
        f2 = open(self.eegenbin_path, "rb")
        gen_tres = list(f2.read())
        f2.close()

        '''
            Writing the information from e.gen.0 to e.org.0
        '''
        f3 = open(self.eeorg_path, "wb")

        # Write 40K content to the first 40K section
        # 40 * 1024 = 40960 = 0xA000, 40K
        # the for loop will automatically count it from 0 ~ (content_sz - 1)
        # example:  0 ~ 40K = 0 ~ 40959
        content_sz = 40 * 1024
        for idx in range(0, content_sz):
            org_tres[idx] = gen_tres[idx]

        # Write 4K content start from 0xC000
        # 49152 = 0xC000 = 48K
        content_sz = 4 * 1024
        offset = 48 * 1024
        for idx in range(0, content_sz):
            org_tres[idx + offset] = gen_tres[idx + offset]

        # Write 8K content start from 0xE000
        # 57344 = 0xE000 = 56K
        content_sz = 8 * 1024
        offset = 56 * 1024
        for idx in range(0, content_sz):
            org_tres[idx + offset] = gen_tres[idx + offset]

        arr = bytearray(org_tres)
        f3.write(arr)
        f3.close()

        eeorg_dut_path = os.path.join(self.dut_tmpdir, self.eeorg)
        self.tftp_get(remote=self.eeorg, local=eeorg_dut_path, timeout=15)

    def check_devreg_data(self, dut_tmp_subdir=None, mtd_count=None, post_en=True, zmodem=False, timeout=10):
        """check devreg data
        in default we assume the datas under /tmp on dut
        but if there is sub dir in your tools.tar, you should set dut_subdir

        you MUST make sure there is eesign file under /tftpboot

        Keyword Arguments:
            dut_subdir {[str]} -- like udm, unas, afi_aln...etc, take refer to structure of fcd-script-tools repo
        """
        log_debug("Send signed eeprom file adding date code from host to DUT ...")
        post_txt = None

        # Determine what eeprom should be written into DUT finally
        if self.FCD_TLV_data is True:
            eewrite = self.eesigndate
        else:
            eewrite = self.eesign

        eewrite_path = os.path.join(self.tftpdir, eewrite)
        eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)

        if post_en is True:
            post_txt = self.linux_prompt

        if dut_tmp_subdir is not None:
            eewrite_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, eewrite)
        else:
            eewrite_dut_path = os.path.join(self.dut_tmpdir, eewrite)

        if zmodem is False:
            self.tftp_get(remote=eewrite, local=eewrite_dut_path, timeout=timeout, post_en=post_en)
        else:
            self.zmodem_send_to_dut(file=eewrite_path, dest_path=self.dut_tmpdir)

        log_debug("Change file permission - {0} ...".format(eewrite))
        cmd = "chmod 777 {0}".format(eewrite_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        cmd = "flash_erase {} 0 0".format(self.devregpart)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        log_debug("Starting to write signed info to SPI flash ...")
        cmd = "dd if={0} of={1} bs=1k count=64".format(eewrite_dut_path, self.devregpart)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        cmd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Send " + self.eechk + " from DUT to host ...")

        if zmodem is False:
            self.tftp_put(remote=self.eechk_path, local=eechk_dut_path, timeout=timeout, post_en=post_en)
        else:
            self.zmodem_recv_from_dut(file=eechk_dut_path, dest_path=self.tftpdir)

        otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, eewrite)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.eechk_path, eewrite_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")

    def registration(self, regsubparams=None):
        log_debug("Starting to do registration ...")
        if regsubparams is None:
            regsubparams = self.access_chips_id()

        clientbin = "/usr/local/sbin/client_rpi4_release"
        regparam = [
            "-h prod.udrs.io",
            "-k {}".format(self.pass_phrase),
            regsubparams,
            "-i field=qr_code,format=hex,value={}".format(self.qrhex),
            "-i field=flash_eeprom,format=binary,pathname={}".format(self.eeorg_path),
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
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Boot from SPI recovery image ...")
        self.pexp.expect_action(120, "Autobooting in 2 seconds, press", "\x1b\x1b")
        self.set_ub_net()
        cmd = "tftpboot $loadaddr images/{}-mfg.bin".format(self.board_id)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        cmd = "setenv bootargs $rootargs pci=pcie_bus_perf console=ttyS0,115200 $bootargsextra"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        cmd = "bootm ${loadaddr}"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.login(retry=100)

        cmd = "ifconfig eth0 down"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(3)
        self.set_lnx_net("eth1")
        self.is_network_alive_in_linux()

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

        cmd = "reboot"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.pexp.expect_action(60, "Autobooting in 2 seconds, press", "\x1b\x1b")

        cmd = "saveenv"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "setenv onie_boot_reason install"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "run bootcmd"
        self.pexp.expect_ubcmd(10, "", cmd)

        self.pexp.expect_lnxcmd(100, pre_exp="Please press Enter to activate this console", action="\n", post_exp=self.linux_prompt, retry=3)
        '''
            To stop continous requiring messages
        '''
        cmd = "onie-stop"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        cmd = "ifconfig eth0 down"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(3)
        self.set_lnx_net("eth1")
        self.is_network_alive_in_linux()

        '''
            To clean the EMMC
        '''
        cmd = "sgdisk -d 1 /dev/sda"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        cmd = "sgdisk -d 2 /dev/sda"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        cmd = "onie-nos-install http://{}/images/{}-fw.bin".format(self.tftp_server, self.board_id)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.pexp.expect_only(30, "Executing installer")
        self.pexp.expect_only(30, "Updating U-Boot")
        self.pexp.expect_only(30, "Post-initialize the rest of partitions")
        self.pexp.expect_only(30, "NOS install successful")
        self.pexp.expect_only(30, "Rebooting")
        self.pexp.expect_action(120, "Autobooting in 2 seconds, press", "\x1b\x1b")
        msg(60, "Finish doing formal image installation ...")

        cmd = "env default -a"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "setenv nos_bootcmd 'run bootemmcdual'"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "setenv onie_initargs 'setenv bootargs pci=pcie_bus_perf console=$consoledev,$baudrate DIAG'"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        cmd = "saveenv"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        msg(70, "Finish configuring to run DIAG as default ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()

def main():
    uisp_apline = UISPALPINE()
    uisp_apline.run()

if __name__ == "__main__":
    main()
