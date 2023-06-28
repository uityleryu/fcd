#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os
import re

'''
    ea3d: UDM-Enterprise
    ea3e: UXG-Enterprise
'''


class UDM_CN96XX_FACTORY(ScriptBase):
    def __init__(self):
        super(UDM_CN96XX_FACTORY, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fw_img = self.board_id + "-fw.bin"
        self.recovery_img = self.board_id + "-recovery"
        self.bootloader_img = self.board_id + "-boot.img"
        self.bootloader_prompt = ">"
        self.linux_prompt = "#"
        self.devregpart = "/dev/mtdblock6"

        self.helperexe = ""
        self.helper_path = "udm"
        self.username = "ui"
        self.password = "ui"

        # CPU flash Path
        self.node_info = ["/proc/cpumidr",
                          "/sys/class/mtd/mtd0/jedec_id",
                          "/sys/class/mtd/mtd0/flash_uid"]
        # Base Path
        tool_name = {
            'ea3d': "udm_ent",
            'ea3e': "uxg_ent"
        }

        self.toool_folder = os.path.join(self.fcd_toolsdir, tool_name[self.board_id])

        self.eeprom_offset = {
            'ea3d': "0x00a60000",
            'ea3e': "0x00a60000"
        }

        self.eeprom_offset_2 = {
            'ea3d': "0x00a68000",
            'ea3e': "0x00a68000"
        }

        # Vendor ID + Sys ID
        self.vdr_sysid = {
            'ea3d': "77073dea",
            'ea3e': "77073eea",
        }

        # Sys ID + Vendor ID
        self.sysid_vdr = {
            'ea3d': "3dea7707",
            'ea3e': "3eea7707",
        }

        # active port
        self.activeport = {
            'ea3d': "rvu_pf#3",
            'ea3e': "al_eth3",
        }

        # number of Ethernet
        self.ethnum = {
            'ea3d': "6",
            'ea3e': "6",
        }

        # number of Wi-Fi
        self.wifinum = {
            'ea3d': "0",
            'ea3e': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ea3d': "1",
            'ea3e': "1",
        }

        # ethernet interface
        self.netif = {
            'ea3d': "eth3",
            'ea3e': "br0",
        }

        # LCM
        self.lcm = {
            'ea3d': True,
            'ea3e': True,
        }

        # Wifi cal data setting
        self.wifical = {
            'ea3d': False,
            'ea3e': False,
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

    def set_fake_eeprom(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf erase {} 0x10000".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(60, "Erased: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + "a3d61804")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800000c " + self.vdr_sysid[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000010 " + "4c710000")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf write 0x08000000 {} 0x20".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")
        #
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + "544e4255")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000010 " + self.sysid_vdr[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000014 " + "4c710000")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf write 0x08000000 {} 0x20".format(self.eeprom_offset_2[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def set_fake_eeprom_uxg(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf erase {} 0x10000".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(60, "Erased: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + "a3d61804")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000004 " + "1806ee97")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000008 " + "ee97a3d6")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800000c " + self.vdr_sysid[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000010 " + "050c0000")
        #
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08008000 " + "544e4255")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000010 " + self.sysid_vdr[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "sf write 0x08000000 {} 0x10000".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def config_board_model_nbumer(self):
        self.pexp.expect_action(60, "Press 'B' within 2 seconds for boot menu", "B")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "S", "Choice: B")
        self.pexp.expect_action(60, "S) Enter Setup", )
        self.pexp.expect_action(60, "B) Board Manufacturing Data", "B")
        self.pexp.expect_only(30, "(INS)Board Model Number [uxg-enterprise]:")
        self.pexp.expect_action(60, "B) Board Model Number", "uxg-enterprise")
        self.pexp.expect_only(30, "XXXXXXXXXXXXXXXXXXXXX")

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)

        if self.board_id in ["ea3d"]:
            self.pexp.expect_action(40,action="ping {}".format(self.tftp_server))
            self.pexp.expect_action(40, self.bootloader_prompt,"setenv ethact {}".format(self.activeport[self.board_id]))
        self.is_network_alive_in_uboot(retry=9, timeout=10)
        self.copy_file(
            source=os.path.join(self.fwdir, self.bootloader_img),
            dest=os.path.join(self.tftpdir, "boot.img")
        )

        self.pexp.expect_action(150, self.bootloader_prompt, "tftpboot boot.img")
        self.pexp.expect_action(150, self.bootloader_prompt, "bootimgup spi 0 $loadaddr $filesize")
        self.pexp.expect_action(150, self.bootloader_prompt, "reset")

    def update_recovery(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)
        if self.board_id in ["ea3d"]:
            self.pexp.expect_action(40,action="ping {}".format(self.tftp_server))
            self.pexp.expect_action(40, self.bootloader_prompt,"setenv ethact {}".format(self.activeport[self.board_id]))
        self.is_network_alive_in_uboot(retry=9, timeout=10)
        # copy recovery image
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-recovery"),
            dest=os.path.join(self.tftpdir, "uImage")
        )

        # copy FW image
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-fw.bin"),
            dest=os.path.join(self.tftpdir, "fw-image.bin")
        )

        self.pexp.expect_ubcmd(10, self.bootloader_prompt,
                               "setenv bootargs console=ttyAMA0,115200n8 earlycon=pl011,0x87e028000000 net.ifnames=0 maxcpus=24 rootwait rw root= coherent_pool=16M client={} server={} sysid={}".format(
                                   self.dutip,
                                   self.tftp_server,
                                   self.board_id))
        self.pexp.expect_action(60, self.bootloader_prompt,
                                "setenv bootcmd 'ext4load mmc 0:1 $loadaddr uImage;bootm $loadaddr'")
        self.pexp.expect_action(60, self.bootloader_prompt, "saveenv")
        self.pexp.expect_action(60, self.bootloader_prompt,
                                "setenv bootargs console=ttyAMA0,115200n8 earlycon=pl011,0x87e028000000 net.ifnames=0 maxcpus=24 rootwait rw root= coherent_pool=16M client={} server={} sysid={} factory".format(
                                    self.dutip,
                                    self.tftp_server,
                                    self.board_id))
        self.pexp.expect_action(60, self.bootloader_prompt, "tftpboot uImage")
        self.pexp.expect_action(60, self.bootloader_prompt, "bootm $loadaddr")

        time.sleep(2)

    def update_fw(self):
        time.sleep(2)

    def set_boot_net(self):
        # import pdb; pdb.set_trace()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv sysid")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv model")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def set_kernel_net(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip))
        self.is_network_alive_in_linux(ipaddr=self.dutip)

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
            nodes = ["/proc/cpumidr",
                     "/sys/class/mtd/mtd0/jedec_id",
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
            # self.config_board_model_nbumer()
            self.update_uboot()
            if self.board_id == "ea3d":
                self.set_fake_eeprom()
            elif self.board_id == "ea3e":
                self.set_fake_eeprom_uxg()
            msg(10, "Boot up to linux console and network is good ...")

        if self.BOOT_RECOVERY_IMAGE:
            self.update_recovery()
            msg(15, "Boot up to linux console and network is good ...")

        if self.INIT_RECOVERY_IMAGE:
            self.login(self.username, self.password, timeout=360, log_level_emerg=True)
            # time.sleep(15)  # for stable eth
            self.set_kernel_net()
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "echo 140 >> /sys/class/hwmon/hwmon0/pwm1")
            self.unlock_eeprom_permission()
            time.sleep(1)
            msg(20, "Boot up to linux console and network is good ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if self.PROVISION_ENABLE:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_by_cmd(nodes=self.node_info)

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

        if not self.LCM_FW_Check_ENABLE:
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
            if len(m_run) == 2:
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
    udm_cn96xx_factory = UDM_CN96XX_FACTORY()
    udm_cn96xx_factory.run()


if __name__ == "__main__":
    main()
