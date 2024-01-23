#!/usr/bin/python3

import re
import sys
import os
import time
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical


'''
    f064: HyperSwitch
    f066: Enterprise Aggregation
'''


class HYPERSWITCHFactoryGeneral(ScriptBase):
    def __init__(self):
        super(HYPERSWITCHFactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        self.devregpart = "/sys/class/i2c-dev/i2c-0/device/0-0053/eeprom"
        self.helperexe = "helper_MRVL_HS_release"
        self.devregexe = "devreg_MRVL_HS_debug"
        self.bios_filename = "{}-bios.cab".format(self.board_id)
        self.ec_filename = "{}-ec.bin".format(self.board_id)
        self.bomrev = "113-{}".format(self.bom_rev)
        self.bootloader_prompt = "Shell>"
        self.linux_prompt = "#"

        self.BOOTUP_EN = True
        self.PROVISION_EN = True
        self.DOHELPER_EN = True
        self.REGISTER_EN = True
        self.WRITE_MAC_EN = True
        self.DATAVERIFY_EN = True
        self.UPDATE_BIOS_EN = True
        self.UPDATE_EC_EN = True

        self.ethnum = {
            'f064': "8",
            'f066': "8"
        }

        self.wifinum = {
            'f064': "0",
            'f066': "0",
        }

        self.btnum = {
            'f064': "0",
            'f066': "0",
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def login_net_config(self):
        self.login(timeout=120, retry=30)
        self.set_lnx_net("eth0")
        time.sleep(1)
        cmd = "config mgmt ip dhcp disable"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        cmd = "ssh-keygen -A"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        cmd = "ifconfig eth1 down"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.is_network_alive_in_linux()

    def data_provision_64k(self, netmeta, post_en=True, rsa_en=True, method="tftp"):
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
            sstr.append("-t 002-{}".format(self.tlb_rev))

        log_debug("ME BOM:" + self.meb_rev)
        if self.meb_rev != "":
            sstr.append("-M 300-{}".format(self.meb_rev))

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

        # Ex: dd if=/dev/mtdblock2 of=/tmp/e.org.0 bs=1k count=64
        cmd = "dd if={0} of={1}/{2} bs=1k count=64".format(self.devregpart, self.dut_tmpdir, self.eeorg)
        self.pexp.expect_lnxcmd(timeout=30, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(0.1)

        # Ex: /tmp/e.org.0
        dstp = "{0}/{1}".format(self.dut_tmpdir, self.eeorg)
        if method == "tftp":
            self.tftp_put(remote=self.eeorg_path, local=dstp, timeout=20)
        elif method == "scp":
            self.scp_put(self.user, self.password, self.dutip, self.eeorg_path, dstp)
        else:
            error_critical("Transferring interface not support !!!!")

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

        self.print_eeprom_content(self.eeorg_path)

        eeorg_dut_path = os.path.join(self.dut_tmpdir, self.eeorg)
        if method == "tftp":
            self.tftp_get(remote=self.eeorg, local=eeorg_dut_path, timeout=15)
        elif method == "scp":
            self.scp_get(self.user, self.password, self.dutip, self.eeorg_path, eeorg_dut_path)
        else:
            error_critical("Transferring interface not support !!!!")

        # Ex: dd if=/tmp/e.org.0 of=/dev/mtdblock2 bs=1k count=64
        cmd = "dd if={0}/{1} of={2} bs=32 count=2048".format(self.dut_tmpdir, self.eeorg, self.devregpart)
        self.pexp.expect_lnxcmd(timeout=30, pre_exp=self.linux_prompt, action=cmd, post_exp=post_exp)
        time.sleep(1)

    def prepare_server_need_files(self, method="tftp", helper_args_type="default"):
        log_debug("Starting to do " + self.helperexe + "...")
        # Ex: tools/uvp/helper_DVF99_release_ata_max
        srcp = os.path.join(self.tools, self.helper_path, self.helperexe)

        # Ex: /tmp/helper_DVF99_release_ata_max
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)

        if method == "tftp":
            self.tftp_get(remote=srcp, local=helperexe_path, timeout=60)
        elif method == "wget":
            self.dut_wget(srcp, helperexe_path, timeout=100)
        elif method == "scp":
            srcp = os.path.join(self.fcd_toolsdir, self.helperexe)
            self.scp_get(self.user, self.password, self.dutip, srcp, helperexe_path)
        else:
            error_critical("Transferring interface not support !!!!")

        cmd = "chmod 777 {0}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)

        HELPER_PROD_CLASS_ARG = {
            'default': "-c",
            'new': "--output-product-class-fields",
        }

        prod_class_arg = HELPER_PROD_CLASS_ARG.get(helper_args_type, HELPER_PROD_CLASS_ARG['default'])

        sstr = [
            helperexe_path,
            "-q",
            "{} product_class={}".format(prod_class_arg, self.product_class),
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
            if method == "tftp":
                self.tftp_put(remote=srcp, local=dstp, timeout=10)
            elif method == "scp":
                self.scp_put(self.user, self.password, self.dutip, srcp, dstp)
                time.sleep(1)
            else:
                error_critical("Transferring interface not support !!!!")

        log_debug("Send helper output files from DUT to host ...")

    def check_devreg_data(self, dut_tmp_subdir=None, mtd_count=None, post_en=True, method="tftp", timeout=10):
        """
            check devreg data
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

        if method == "zmodem":
            self.zmodem_send_to_dut(file=eewrite_path, dest_path=self.dut_tmpdir)
        elif method == "tftp":
            self.tftp_get(remote=eewrite, local=eewrite_dut_path, timeout=timeout, post_en=post_en)
        elif method == "scp":
            self.scp_get(self.user, self.password, self.dutip, eewrite_path, eewrite_dut_path)
            time.sleep(1)
        else:
            error_critical("Transferring interface not support !!!!")

        log_debug("Change file permission - {0} ...".format(eewrite))
        cmd = "chmod 777 {0}".format(eewrite_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Starting to write signed info to SPI flash ...")

        cmd = "dd if={0} of={1} bs=32 count=2048".format(eewrite_dut_path, self.devregpart)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        cmd = "dd if={} of={} bs=32 count=2048".format(self.devregpart, eechk_dut_path)
        self.pexp.expect_lnxcmd(timeout, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Send " + self.eechk + " from DUT to host ...")

        if method == "zmodem":
            self.zmodem_recv_from_dut(file=eechk_dut_path, dest_path=self.tftpdir)
        elif method == "tftp":
            self.tftp_put(remote=self.eechk_path, local=eechk_dut_path, timeout=timeout, post_en=post_en)
        elif method == "scp":
            self.scp_put(self.user, self.password, self.dutip, self.eechk_path, eechk_dut_path)
        else:
            error_critical("Transferring interface not support !!!!")

        self.print_eeprom_content(self.eechk_path)

        otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, eewrite)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.eechk_path, eewrite_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")

    def write_mac2cpu(self):
        fileset = [
            "DNV_LAN0_KR_KX_BP_noMNG_2p10_80000BDF.bin",
            "DNV_LAN1_KR_KX_BP_noMNG_2p10_80000BF9.bin",
            "fparts.txt",
            "spsFPT_v42649.efi",
            "eeupdate64e"
        ]

        cmd = "mount /dev/mmcblk0p1 /mnt"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        time.sleep(2)

        # Copying all tooling files in the /mnt
        for sf in fileset:
            src = os.path.join(self.fcd_toolsdir, sf)
            self.scp_get(self.user, self.password, self.dutip, src, "/mnt")

        cmd = "efibootmgr --bootnext $(efibootmgr | grep \"UEFI: Built-in EFI Shell\" | tr -d -c 0-9)"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        '''
            Loading several images in the DUT for enabling the MAC writing feature
        '''
        self.pexp.expect_lnxcmd(10, "UEFI: Built-in EFI Shell", "reboot")
        # self.pexp.expect_ubcmd(80, "UEFI", "\x1b\x1b")
        self.pexp.expect_ubcmd(80, "Shell>", "FS0:\r")
        cmd = "spsFPT_v42649.efi -F DNV_LAN0_KR_KX_BP_noMNG_2p10_80000BDF.bin -10GBEA\r"
        self.pexp.expect_ubcmd(20, "fs0:|FS0:", cmd)
        cmd = "spsFPT_v42649.efi -F DNV_LAN1_KR_KX_BP_noMNG_2p10_80000BF9.bin -10GBEB\r"
        self.pexp.expect_ubcmd(20, "fs0:|FS0:", cmd)
        self.pexp.expect_only(20, "spsFPT Operation Passed")

        '''
            Powering on/off the DUT
        '''
        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")
        time.sleep(6)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")
        time.sleep(6)

        '''
            configuring the networking setting
        '''
        self.login_net_config()

        cmd = "mount /dev/mmcblk0p1 /mnt"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        # Copying all tooling files in the /mnt
        for sf in fileset:
            src = os.path.join(self.fcd_toolsdir, sf)
            self.scp_get(self.user, self.password, self.dutip, src, "/mnt")

        '''
            Writing MAC addresses in the CPU
        '''
        base_mac_add_1 = self.mac_incr(self.mac, 1)
        cmdset = [
            "/mnt/eeupdate64e /NIC=1 /MAC={}".format(base_mac_add_1),
            "/mnt/eeupdate64e /NIC=2 /MAC={}".format(self.mac)
        ]
        for cmd in cmdset:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        time.sleep(1)
        cmdset = [
            "modprobe -r igb",
            "modprobe -r ixgbe",
            "modprobe igb",
            "modprobe ixgbe"
        ]
        for cmd in cmdset:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        time.sleep(1)

        # Deleting all tooling files
        for sf in fileset:
            cmd = "rm /mnt/{}".format(sf)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        cmd = "umount /mnt"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        time.sleep(1)

        '''
            Checking the MAC addresses in the CPU
        '''
        cmdset = [
            ["ip a show eth0 | grep ether", self.mac_format_str2comma(base_mac_add_1)],
            ["ip a show eth1 | grep ether", self.mac_format_str2comma(self.mac)]
        ]
        for cmd in cmdset:
            cmd_reply = self.pexp.expect_get_output(cmd[0], self.linux_prompt)
            if cmd[1] not in cmd_reply:
                error_critical("MAC comparison is incorrect, FAIL!!!")

        '''
            Powering on/off the DUT
        '''
        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")
        time.sleep(6)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")
        time.sleep(6)

    def check_board_signed(self):
        cmd = r"grep flashSize /proc/ubnthal/system.info"
        self.pexp.expect_action(10, "", "")
        output = self.pexp.expect_get_output(cmd, self.linux_prompt, 1.5)
        match = re.search(r'flashSize=', output)
        if not match:
            error_critical(msg="Device Registration check failed!")

        cmd = r"grep qrid /proc/ubnthal/system.info"
        output = self.pexp.expect_get_output(cmd, self.linux_prompt, 1.5)
        match = re.search(r'qrid=(.*)', output)
        if match:
            if match.group(1).strip() != self.qrcode:
                error_critical(msg="QR code doesn't match!")
        else:
            error_critical(msg="Unable to get qrid!, please checkout output by grep")

    def run(self):
        """
            Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")

        msg(1, "Waiting - PULG in the device...")
        if self.BOOTUP_EN is True:
            self.login_net_config()

        if self.PROVISION_EN is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False, method="scp")

        if self.DOHELPER_EN is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files(method="scp")

        if self.REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data(method="scp", timeout=30)
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.WRITE_MAC_EN is True:
            self.write_mac2cpu()

        if self.UPDATE_EC_EN is True:
            self.login_net_config()
            src = os.path.join(self.fcd_toolsdir, "ECUpdate")
            self.scp_get(self.user, self.password, self.dutip, src, self.dut_tmpdir)

            src_path = os.path.join(self.fwdir, self.ec_filename)
            self.scp_get(self.user, self.password, self.dutip, src_path, self.dut_tmpdir)

            cmd = "/tmp/ECUpdate /tmp/{}".format(self.ec_filename)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        if self.UPDATE_BIOS_EN is True:
            src_path = os.path.join(self.fwdir, self.bios_filename)
            self.scp_get(self.user, self.password, self.dutip, src_path, self.dut_tmpdir)

            cmd = "mkdir -p /boot/efi; mount /dev/mmcblk0p1 /boot/efi"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
            cmd = "/usr/lib/fwupd/fwupdtool install /tmp/{}".format(self.bios_filename)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp="An update requires a reboot to complete")

        '''
            Powering on/off the DUT
            After doing the BIOS and EC update, it requires the power cycle to reinitialize
        '''
        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")
        time.sleep(6)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")
        time.sleep(6)

        if self.DATAVERIFY_EN is True:
            msg(70, "Checking registration ...")
            self.login_net_config()
            self.check_board_signed()
            msg(no=80, out="Device Registration check OK...")

            src = os.path.join(self.fcd_toolsdir, self.devregexe)
            self.scp_get(self.user, self.password, self.dutip, src, self.dut_tmpdir)
            cmd = os.path.join(self.dut_tmpdir, self.devregexe)
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, "PASS")
            msg(no=90, out="devreg tool check OK...")

            cmd = "ls -la {} | grep {}".format(self.fwdir, self.bios_filename)
            [cmd_reply, rtc] = self.cnapi.xcmd(cmd)
            pattern = r"usw-fw/B701GT-UBQ_([\d]+_[\d]+_[\d]+).cab"
            m_bios = re.findall(pattern, cmd_reply)
            if m_bios:
                cmd = "dmidecode -s bios-version"
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, m_bios[0].replace("_", "."))
                log_debug("The BIOS version is correct")
            else:
                error_critical(msg="Can't find the BIOS version, FAIL!!!")

            cmd = "ls -la {} | grep {}".format(self.fwdir, self.ec_filename)
            [cmd_reply, rtc] = self.cnapi.xcmd(cmd)
            pattern = r"usw-fw/EC_PCOM-B701GT-UBQ_([\d]+_[\d]+_[\d]+).bin"
            m_ec = re.findall(pattern, cmd_reply)
            if m_ec:
                convert_m_ec = ""
                m_ec_split = m_ec[0].split("_")
                for i in m_ec_split:
                    convert_m_ec = "{}{}".format(convert_m_ec, i.zfill(2))

                cmd = "hexdump -s 0xe31d -n 3 -e '3/1 \"%02x\"' /dev/port"
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, convert_m_ec)
                log_debug("The EC version is correct")
            else:
                error_critical(msg="Can't find the EC version, FAIL!!!")

        self.pexp.expect_lnxcmd(30, self.linux_prompt, "lcm-ctrl -t dump", post_exp="\"rc\": \"ok\"", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "", post_exp=self.linux_prompt)

        if self.ps_state is True:
            time.sleep(2)
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        msg(no=100, out="Formal firmware completed with MAC0: " + self.mac)
        self.close_fcd()


def main():
    factory = HYPERSWITCHFactoryGeneral()
    factory.run()

if __name__ == "__main__":
    main()
