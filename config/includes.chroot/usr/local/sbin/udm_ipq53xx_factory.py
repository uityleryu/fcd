#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os
import re

'''
    a678: UCG-Ultra
    a679: UCG-Ultra-PoE
    a690: UXG
    a69a: UCG-Max
'''


class UDM_IPQ53XX_FACTORY(ScriptBase):
    def __init__(self):
        super(UDM_IPQ53XX_FACTORY, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fw_img = self.board_id + "-fw.bin"
        self.recovery_img = self.board_id + "-recovery"
        # if self.board_id == "a690":
        #     self.recovery_img = self.board_id + "-loader.img"
        self.bootloader_img = self.board_id + "-uboot.mbn"
        self.bootloader_prompt = "#"
        self.linux_prompt = "#"
        self.devregpart = "/dev/mtdblock3"
        self.helperexe = ""
        self.helper_path = "udm"
        self.username = "root"
        self.password = "ui"

        # CPU flash Path
        self.node_info = ["/proc/cpumidr",
                          "/sys/class/mtd/mtd0/jedec_id",
                          "/sys/class/mtd/mtd0/flash_uid"]
        # Base Path
        tool_name = {
            'a678': "udr_ultra",
            'a679': "udr_ultra_poe",
            'a690': "uxg",
            'a69a': "ucg_max"

        }

        self.toool_folder = os.path.join(self.fcd_toolsdir, tool_name[self.board_id])

        self.eeprom_offset = {
            'a678': "0x00410000",
            'a679': "0x00410000",
            'a690': "0x00410000",
            'a69a': "0x00410000"
        }

        self.eeprom_offset_2 = {
            'a678': "0x00418000",
            'a679': "0x00418000",
            'a690': "0x00418000",
            'a69a': "0x00418000"
        }

        # Vendor ID + Sys ID
        self.vdr_sysid = {
            'a678': "770778a6",
            'a679': "770779a6",
            'a690': "770790a6",
            'a69a': "77079aa6"
        }

        # Sys ID + Vendor ID
        self.sysid_vdr = {
            'a678': "78a67707",
            'a679': "79a67707",
            'a690': "90a67707",
            'a69a': "9aa67707"
        }

        # active port
        self.activeport = {
            'a678': "al_eth3",
            'a679': "al_eth3",
            'a690': "al_eth3",
            'a69a': "al_eth3"
        }

        # number of Ethernet
        self.ethnum = {
            'a678': "5",
            'a679': "8",
            'a690': "5",
            'a69a': "5",
        }

        # number of Wi-Fi
        self.wifinum = {
            'a678': "0",
            'a679': "0",
            'a690': "0",
            'a69a': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'a678': "1",
            'a679': "1",
            'a690': "1",
            'a69a': "1"
        }

        # ethernet interface
        self.netif = {
            'a678': "switch0",
            'a679': "switch0",
            'a690': "switch0",
            'a69a': "switch0"
        }

        # LCM
        self.lcm = {
            'a678': False,
            'a679': False,
            'a690': False,
            'a69a': False
        }

        # Wifi cal data setting
        self.wifical = {
            'a678': False,
            'a679': False,
            'a690': False,
            'a69a': False,
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.INIT_RECOVERY_IMAGE = True
        self.UPDATE_UBOOT = True
        self.BOOT_RECOVERY_IMAGE = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.DATAVERIFY_ENABLE = True
        self.LCM_FW_Check_ENABLE = True
        self.POWER_SUPPLY_EN = True
        self.DEV_REG_ENABLE = True

    def set_fake_eeprom(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x44000000 " + "544e4255")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x4400000c " + self.vdr_sysid[self.board_id])
        if self.board_id!="a690":
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x44000010 " + self.sysid_vdr[self.board_id])
        else:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x44000010 " + self.bom_rev.split('-')[1]+"5d2500")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf erase {} +0x9000".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf write 0x44000000 {} 0x20".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf write 0x44000000  {} 0x20".format(self.eeprom_offset_2[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def choose_boot_address(self, bom_value):
        ranges = [(0, 3, "uxg-v1"), (4, 8, "uxg-v2")]
        for start, end, version in ranges:
            if start <= bom_value <= end:
                return f"bootm 0x44000000#{version}"
        return "bootm 0x44000000#uxg-v3"

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)

        self.copy_file(
            source=os.path.join(self.fwdir, self.bootloader_img),
            dest=os.path.join(self.tftpdir, "u-boot.mbn")
        )

        self.pexp.expect_action(150, self.bootloader_prompt, "tftpboot u-boot.mbn")
        self.pexp.expect_only(60, "Bytes transferred =")
        self.pexp.expect_action(150, self.bootloader_prompt, "sf probe")
        self.pexp.expect_action(150, self.bootloader_prompt, "sf erase 0x00260000 +${filesize}")
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_action(150, self.bootloader_prompt, "sf write ${fileaddr} 0x00260000 ${filesize}")
        self.pexp.expect_only(60, "Written: OK")
        self.pexp.expect_action(150, self.bootloader_prompt, "reset")

    def update_recovery(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)
        self.is_network_alive_in_uboot(retry=9, timeout=10)
        # copy recovery image
        self.pexp.expect_ubcmd(30, self.bootloader_prompt,
                               "setenv bootargsextra factory nc_transfer client={}".format(self.dutip))

        # if self.board_id != "a690":
        # copy recovery image to tftp server
        self.copy_file(
            source=os.path.join(self.fwdir, self.recovery_img),
            dest=os.path.join(self.tftpdir, "uImage")  # fixed name
        )
        # else:
        #     # copy recovery image to tftp server
        #     self.copy_file(
        #         source=os.path.join(self.fwdir, self.recovery_img),
        #         dest=os.path.join(self.tftpdir, "loader.img")  # fixed name
        #     )
        time.sleep(2)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run load_bootargs")
        self.set_boot_net()
        self.is_network_alive_in_uboot(retry=9, timeout=10)
        # if self.board_id != "a690":
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot uImage")
        # else:
        #     self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot loader.img")

        self.pexp.expect_only(60, "Bytes transferred =")
        # self.pexp.expect_ubcmd(30, self.bootloader_prompt, "mw.l 0x1020000 0x2c1;sleep 2;mw.l 0x1020004 0x0;sleep 2")
        if self.board_id == "a679":
            self.pexp.expect_ubcmd(30, self.bootloader_prompt,
                                   "mw.l 0x1020000 0x2c1;sleep 2;mw.l 0x1020004 0x0;sleep 2")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm 0x44000000")
        elif self.board_id in ["a678","a69a"]:
            self.pexp.expect_ubcmd(30, self.bootloader_prompt,
                                   "mw.l 0x101A000 0x2c1;sleep 1;mw.l 0x101A004 0x0;sleep 1;mw.l 0x1020000 0x2c1;sleep 1;mw.l 0x1020004 0x0;")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm")
        else:
            log_debug("BOM REV:" + self.bom_rev.split('-')[1])
            bm = self.bom_rev.split('-')[1]
            cmd = self.choose_boot_address(int(bm))
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        log_debug(msg="Enter factory install mode ...")
        self.pexp.expect_only(120, "Wait for nc client to push firmware")

        time.sleep(5)  # for stable
        nc_cmd = "nc -v -q 1 {} 5566 < {}".format(self.dutip, os.path.join(self.fwdir, self.fw_img))
        log_debug(msg=nc_cmd)

        [buf, rtc] = self.fcd.common.xcmd(nc_cmd)
        if (int(rtc) > 0):
            error_critical("cmd: \"{}\" fails, return value: {}".format(nc_cmd, rtc))

        log_debug(msg="Upgrading FW ...")
        self.pexp.expect_only(240, "Reboot system safely")
        log_debug(msg="FW update done ...")

    def update_fw(self):
        time.sleep(2)

    def set_boot_net(self):
        # import pdb; pdb.set_trace()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv sysid")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv model")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def set_kernel_net(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip),
                                valid_chk=True)

        self.is_network_alive_in_linux(ipaddr=self.tftp_server)

    def unlock_eeprom_permission(self):
        log_debug(msg="Unlock eeprom permission")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "echo 5edfacbf > /proc/ubnthal/.uf")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def check_refuse_data(self):
        print('Wait Implement')

    def check_refuse_data(self):
        print('Wait Implement')

    def write_caldata_to_flash(self):
        print('Wait Implement')

    def lcm_fw_ver_check(self):
        print('Wait Implement')

    def prepare_server_need_files_by_cmd(self, nodes=None):
        log_debug("Starting to extract cpuid, flash_jedecid and flash_uuid from bsp node ...")
        # The sequencial has to be cpu id -> flash jedecid -> flash uuid
        if nodes is None:
            nodes = ["/proc/bsp_helper/cpu_rev_id",
                     "/proc/bsp_helper/flash_jedec_id",
                     "/sys/class/mtd/mtd0/flash_uid"]

        if self.product_class == 'basic':
            product_class_hexval = "0014"
        elif self.product_class == 'radio':
            product_class_hexval = "0001"
        else:
            error_critical("product class is '{}', FCD doesn't support \"{}\" class now".format(self.product_class))

        # Gen "e.t" from the nodes which were provided in BSP image
        for i in range(0, len(nodes)):
            sstr = [
                "fcd_reg_val{}=`".format(i + 1),
                "cat ",
                nodes[i],
                "`"
            ]
            sstr = ''.join(sstr)
            log_debug(sstr)
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                    valid_chk=True)
        # fcd_reg_val2="00${fcd_reg_val2}" Requirement is 4 bytes means 8 digits
        zero_padded_str = "fcd_reg_val2=\"00${fcd_reg_val2}\""
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=zero_padded_str,
                                post_exp=self.linux_prompt, valid_chk=True)
        sstr = [
            "echo -e \"field=product_class_id,format=hex,value={}\n".format(product_class_hexval),
            "field=cpu_rev_id,format=hex,value=$fcd_reg_val1\n",
            "field=flash_jedec_id,format=hex,value=$fcd_reg_val2\n",
            "field=flash_uid,format=hex,value=$fcd_reg_val3",
            "\" > /tmp/{}".format(self.eetxt)
        ]
        sstr = ''.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)

        # copy "e.org" as "e.b", cp -a /tmp/e.org.0 /tmp/e.b.0
        cmd = "cp -a {0}/{1} {0}/{2}".format(self.dut_tmpdir, self.eeorg, self.eebin)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        files = [self.eetxt, self.eebin]
        for fh in files:
            # Ex: /tftpboot/e.t.0
            srcp = os.path.join(self.tftpdir, fh)

            # Ex: /tmp/e.t.0
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send bspnode output files from DUT to host ...")

    def run(self):
        if self.ps_state is True:
            self.set_ps_port_relay_off()
            time.sleep(2)
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()
        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")
        if self.ps_state is True:
            self.set_ps_port_relay_on()
        if self.UPDATE_UBOOT:
            self.set_fake_eeprom()
            self.update_uboot()

            msg(10, "Boot up to linux console and network is good ...")

        if self.BOOT_RECOVERY_IMAGE:
            self.update_recovery()
            msg(15, "Boot up to linux console and network is good ...")

        if self.INIT_RECOVERY_IMAGE:
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            # time.sleep(15)  # for stable eth
            self.set_kernel_net()
            self.unlock_eeprom_permission()
            time.sleep(1)
            msg(20, "Boot up to linux console and network is good ...")
            # Create Soft link /bin/tftp from /bin/busybox due to FW team do not create the link already
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt,
                                    action="cp /usr/bin/tftp /usr/bin/tftp_backup")  # backup deb tftp
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action="mv /usr/bin/tftp /tmp")
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt,
                                    action="ln -s /bin/busybox /usr/bin/tftp")  # Create Soft link
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if self.PROVISION_ENABLE:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if self.REGISTER_ENABLE:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.DATAVERIFY_ENABLE:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")  # for correct ubnthal
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.wifical[self.board_id]:
            msg(85, "Write and check calibration data")
            self.check_refuse_data()
            self.write_caldata_to_flash()

        if self.DEV_REG_ENABLE:
            pkg_sets = [
                "{}-devreg.deb".format(self.board_id),
            ]
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt,
                                    action="cp /usr/bin/tftp /usr/bin/tftp_backup")  # backup deb tftp
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action="mv /usr/bin/tftp /tmp")
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt,
                                    action="ln -s /bin/busybox /usr/bin/tftp")  # Create Soft link
            for pkg in pkg_sets:
                src_path = os.path.join(self.fcd_toolsdir, pkg)
                dst_path = os.path.join(self.dut_tmpdir, pkg)
                self.tftp_get(remote=src_path, local=dst_path, timeout=20)
                cmd = "dpkg -i {}".format(dst_path)
                self.pexp.expect_lnxcmd(15, self.linux_prompt, cmd)
                output = self.pexp.expect_get_output(action="devreg_IPQ53xx | grep Result", prompt="", timeout=25)
                if "PASS" not in output:
                    raise NameError('Check Registration FAIL')
        if self.LCM_FW_Check_ENABLE:
            if self.lcm[self.board_id]:
                msg(90, "Check LCM FW version ...")
                self.lcm_fw_ver_check()
        output = self.pexp.expect_get_output(action="cat /usr/lib/version", prompt="", timeout=3)
        log_debug(output)
        cmd = "systemctl is-system-running"
        ct = 0
        retry_max = 150
        while ct < retry_max:
            output = self.pexp.expect_get_output(action=cmd, prompt="", timeout=3)
            m_run = re.findall("running", output)
            m_degraded = re.findall("degraded", output)
            if len(m_run) == 2 or len(m_degraded) == 1:
                rmsg = "The system is running good"
                log_debug(rmsg)
                break
            elif len(m_degraded) == 1:
                rmsg = "The system is degraded"
                log_debug(rmsg)
                break
            time.sleep(1)
            ct += 1
        else:
            rmsg = "The system is not booting up successfully, FAIL!!"
            error_critical(rmsg)
        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    udm_ipq53xx_factory = UDM_IPQ53XX_FACTORY()
    udm_ipq53xx_factory.run()


if __name__ == "__main__":
    main()