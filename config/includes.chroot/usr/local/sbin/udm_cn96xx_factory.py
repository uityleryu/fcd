#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os
import re
import pexpect
import sys

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
            'ea3e': "rvu_pf#3",
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

        self.boarad_model = {
            'ea3d': "udm-enterprise",
            'ea3e': "uxg-enterprise"
        }

        self.board_rev = {
            'ea3d': "r9",
            'ea3e': "r3"
        }

        self.MAC_Num = {
            'ea3d': "12",
            'ea3e': "12"
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

        self.proc = None
        self.pexpect_cmd = str("sudo picocom /dev/" + self.dev + " -b 115200")
        self.newline = "\n"
        self.board_config = False
        self.fuse_config = False
        self.DEV_REG_ENABLE=True

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

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        # if self.ps_state is True:
        #     self.set_ps_port_relay_off()
        #     time.sleep(3)
        #     self.set_ps_port_relay_on()

    def set_fake_eeprom_uxg(self):
        self.pexp.expect_action(90, "to stop", "\033\033")
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
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        # if self.ps_state is True:
        #     self.set_ps_port_relay_off()
        #     time.sleep(3)
        #     self.set_ps_port_relay_on()

    def send_cmd_by_char(self, cmd):
        for s in cmd:
            self.proc.send(s)
            time.sleep(0.1)
        self.proc.send(cmd)
        # self.proc.send(self.newline)

    def send_cmd_by_line(self, cmd):
        self.proc.send(cmd)

    def send_wo_extra_newline(self, pre_exp, cmd, post_exp=None, timout=10):
        if post_exp is None:
            self.proc.expect([pre_exp, pexpect.EOF, pexpect.TIMEOUT], timout)
            self.send_cmd_by_line(cmd)
        else:
            self.proc.expect([pre_exp, pexpect.EOF, pexpect.TIMEOUT], timout)
            self.send_cmd_by_char(cmd)
            self.proc.expect([post_exp, pexpect.EOF, pexpect.TIMEOUT], timout)

    def config_fuse_setting(self):
        # # idx = self.pexp.expect_get_index(10, "Press 'B' within 2 seconds for boot menu")
        # # if idx != 0:
        # #     return 0
        # # self.pexp.close()
        # self.proc = pexpect.spawn(self.pexpect_cmd, encoding='utf-8', codec_errors='replace', timeout=2000)
        # self.proc.logfile_read = sys.stdout
        # self.proc.send("b")
        # self.proc.send("b")
        # self.proc.send("b")
        # self.proc.send("b")
        # self.proc.send("b")
        self.send_wo_extra_newline("Choice:", "s")
        self.send_wo_extra_newline("Choice:", "t")
        self.send_wo_extra_newline("(INS)Menu choice", "13\n")
        self.send_wo_extra_newline("(INS)Menu choice", "6\n")
        for i in range(0, 12):
            # for i in range(0,11):
            self.send_wo_extra_newline("]:", "\n")
        time.sleep(2)
        self.send_wo_extra_newline("SPI_SAFEMODE", "1\n")
        # self.send_wo_extra_newline("Secure NV counter", "0\n")
        self.proc.send(self.newline)
        self.send_wo_extra_newline("(INS)Menu choice", "7\n")
        self.send_wo_extra_newline("(INS)Menu choice", "15\n")
        time.sleep(2)
        self.send_wo_extra_newline("Choice:", "s", timout=15)
        # idx = self.pexp.expect_get_index(10, "Press 'B' within 2 seconds for boot menu")

    def config_board_model_nbumer(self):
        # idx = self.pexp.expect_get_index(10, "Press 'B' within 2 seconds for boot menu")
        # log_debug("idx={}".format(idx))
        # if idx == 0:
        #     return 0
        # # if idx !=0 and idx !=1:
        # #     for i in range(3):
        # #         if self.ps_state is True:
        # #             self.set_ps_port_relay_off()
        # #             time.sleep(3)
        # #             self.set_ps_port_relay_on()
        # #         idx = self.pexp.expect_get_index(10, "OcteonTX SOC")
        # #         if idx ==0:
        # #             break
        # idx = self.pexp.expect_get_index(10, "Choice:")
        # if idx != 0:
        #     return 1
        # log_debug("idx={}".format(idx))
        # self.pexp.close()
        # time.sleep(1)
        # self.proc = pexpect.spawn(self.pexpect_cmd, encoding='utf-8', codec_errors='replace', timeout=2000)
        # self.proc.logfile_read = sys.stdout
        self.proc.send(self.newline)
        self.send_wo_extra_newline("Choice:", "s")
        time.sleep(1)
        self.send_wo_extra_newline("Choice:", "b")
        time.sleep(1)
        self.send_wo_extra_newline("]:", "{}\n".format(self.boarad_model[self.board_id]))
        self.send_wo_extra_newline("Choice:", "b")
        time.sleep(1)
        self.send_wo_extra_newline("]:", "{}\n".format(self.boarad_model[self.board_id]))
        self.send_wo_extra_newline("Choice:", "r")
        self.send_wo_extra_newline("]:", "{}\n".format(self.board_rev[self.board_id]))
        self.send_wo_extra_newline("Choice:", "n")
        self.send_wo_extra_newline("]:", "{}\n".format(self.MAC_Num[self.board_id]))
        self.send_wo_extra_newline("Choice:", "w")
        self.send_wo_extra_newline("Choice:", "q")
        # self.send_wo_extra_newline("Choice:", "f")
        # self.proc.close()
        # return 1

    def update_uboot(self):
        self.pexp.expect_action(30, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)
        self.pexp.expect_action(40, self.bootloader_prompt, "ping {}".format(self.tftp_server))
        self.pexp.expect_action(40, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))
        self.pexp.expect_action(10, self.bootloader_prompt, "ping {}".format(self.tftp_server))
        self.pexp.expect_action(40, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))

        self.is_network_alive_in_uboot(retry=9, timeout=10)
        self.copy_file(
            source=os.path.join(self.fwdir, self.bootloader_img),
            dest=os.path.join(self.tftpdir, "boot.img")
        )

        self.pexp.expect_action(150, self.bootloader_prompt, "tftpboot boot.img")
        self.pexp.expect_action(150, self.bootloader_prompt, "bootimgup spi 0 $loadaddr $filesize")
        self.pexp.expect_action(150, self.bootloader_prompt, "reset")
        # if self.ps_state is True:
        #     self.set_ps_port_relay_off()
        #     time.sleep(3)
        #     self.set_ps_port_relay_on()

    def update_recovery(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)
        self.pexp.expect_action(40, self.bootloader_prompt, "ping {}".format(self.tftp_server))
        self.pexp.expect_action(40, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))
        self.pexp.expect_action(10, self.bootloader_prompt, "ping {}".format(self.tftp_server))
        self.pexp.expect_action(40, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))
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
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "brctl delif br0 {}".format(self.netif[self.board_id], self.dutip))
        self.is_network_alive_in_linux(ipaddr=self.dutip)

    def unlock_eeprom_permission(self):
        log_debug(msg="Unlock eeprom permission")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "echo 5edfacbf > /proc/ubnthal/.uf",valid_chk=True)

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
        cmd = "ulcmd --command dump --sender fcd_team"
        self.pexp.expect_lnxcmd(5, self.linux_prompt, cmd, '"lcm.fw.version":"v', retry=48)

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
        # pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        # log_debug(msg=pexpect_cmd)
        # pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        # pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
        # self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        self.proc = pexpect.spawn(self.pexpect_cmd, encoding='utf-8', timeout=10)
        # self.proc.sendline("123456")  # For Local test
        self.proc.logfile_read = sys.stdout
        msg(5, "Open serial port successfully ...")
        if self.ps_state is True:
            self.set_ps_port_relay_on()
        for i in range(3):
            try:
                index = self.proc.expect(
                    [pexpect.EOF, pexpect.TIMEOUT, 'Choice:', "Press 'B' within 1 seconds for boot menu"], timeout=15)
                if index in [2] and not self.board_config:
                    output = self.proc.before  # Get the previous data
                    log_debug(output)
                    self.config_board_model_nbumer()
                    self.board_config = True
                    continue
                elif index in [3] and not self.fuse_config:
                    output = self.proc.before  # Get the previous data
                    log_debug(output)
                    if self.board_id == "ea3d":
                        if "06 Oct" in output:
                            self.fuse_config = True
                        else:
                            self.proc.send("b")
                            self.proc.send("b")
                            self.config_fuse_setting()
                            self.fuse_config = True
                    else:
                        if "01 Aug" in output:
                            self.fuse_config = True
                        else:
                            self.proc.send("b")
                            self.proc.send("b")
                            self.config_fuse_setting()
                            self.fuse_config = True
                else:
                    if self.ps_state is True:
                        self.set_ps_port_relay_off()
                        time.sleep(2)
                        self.set_ps_port_relay_on()
                if self.fuse_config:
                    self.proc.close(True)
                    # self.proc.close(True)
                    break
            except Exception as e:
                log_debug(str(e))
        else:
            raise Warning("Set Board Info Failed....")
        if self.UPDATE_UBOOT:
            log_debug(msg=self.pexpect_cmd)
            pexpect_obj = ExpttyProcess(self.row_id, self.pexpect_cmd, "\n")
            self.set_pexpect_helper(pexpect_obj=pexpect_obj)
            time.sleep(2)
            # self.pexp.expect_action(10, "", "123456")  # For Local test
            if self.board_id == "ea3d":
                self.set_fake_eeprom()
            elif self.board_id == "ea3e":
                self.set_fake_eeprom_uxg()
            self.update_uboot()

            msg(10, "Boot up to linux console and network is good ...")

        if self.BOOT_RECOVERY_IMAGE:
            self.update_recovery()
            idx = self.pexp.expect_get_index(timeout=300, exptxt="reboot: Restarting system")
            # if self.ps_state and idx == 0:
            #     self.set_ps_port_relay_off()
            #     time.sleep(3)
            #     self.set_ps_port_relay_on()
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
            # if self.ps_state and idx == 0:
            #     self.set_ps_port_relay_off()
            #     time.sleep(3)
            #     self.set_ps_port_relay_on()
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.wifical[self.board_id]:
            msg(85, "Write and check calibration data")
            self.check_refuse_data()
            self.write_caldata_to_flash()

        if self.LCM_FW_Check_ENABLE:
            if self.lcm[self.board_id]:
                msg(90, "Check LCM FW version ...")
                self.lcm_fw_ver_check()
        if self.DEV_REG_ENABLE:
            try:
                time.sleep(2)
                pkg_sets = [
                    "{}-devreg.deb".format(self.board_id)
                ]
                for pkg in pkg_sets:
                    src_path = os.path.join(self.fcd_toolsdir, pkg)
                    dst_path = os.path.join(self.dut_tmpdir, pkg)
                    self.tftp_get(remote=src_path, local=dst_path, timeout=30)
                cmd = "dpkg -i {}".format(dst_path)
                self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd)
                output = self.pexp.expect_get_output(action="devreg_CN9670 | grep Result", prompt="", timeout=25)
                if "PASS" not in output:
                    raise NameError('Check Registration FAIL')
            except Exception as e:
                log_debug(str(e))
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
        if self.ps_state is True:
            time.sleep(2)
            # self.set_ps_port_relay_off()
        self.close_fcd()


def main():
    udm_cn96xx_factory = UDM_CN96XX_FACTORY()
    udm_cn96xx_factory.run()


if __name__ == "__main__":
    main()
