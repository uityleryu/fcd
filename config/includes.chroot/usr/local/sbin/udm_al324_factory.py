#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import time
import os
import re

'''
    ea2a: UDW
    ea2b: UDW-PRO
    ea2c: UDM-SE
    ea11: UDM
'''


class UDM_AL324_FACTORY(ScriptBase):
    def __init__(self):
        super(UDM_AL324_FACTORY, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = ">"
        self.devregpart = "/dev/mtdblock4"
        self.helperexe = "helper_AL324_release"
        self.helper_path = "udm"
        self.bomrev = "113-" + self.bom_rev
        self.username = "ubnt"
        self.password = "ubnt"
        self.linux_prompt = "#"

        # Base path
        tool_name = {
            'ea2a': "udw",  # udw
            'ea2b': "udw",  # udw_pro, but tools same as udw
            'ea2c': "udm_se",  # udm_se
            'ea15': "udm_pro",
            'ea11': "udm"
        }

        self.tool_folder = os.path.join(self.fcd_toolsdir, tool_name[self.board_id])

        self.eeprom_offset = {
            'ea2a': "0x220000",
            'ea2b': "0x220000",
            'ea2c': "0x1f0000",
            'ea15': "0x1f0000",
            'ea11': "0x1f0000"
        }
        
        self.eeprom_offset_2 = {
            'ea2a': "0x228000",
            'ea2b': "0x228000",
            'ea2c': "0x1f8000",
            'ea15': "0x1f8000",
            'ea11': "0x1f8000"
        }

        self.wsysid = {
            'ea2a': "77072aea",
            'ea2b': "77072bea",
            'ea2c': "77072cea",
            'ea15': "770715ea",
            'ea11': "770711ea",
        }

        # active port
        self.activeport = {
            'ea2a': "al_eth3",
            'ea2b': "al_eth3",
            'ea2c': "al_eth2",  # set sfp 0 or 2 for SPF+
            'ea15': "al_eth2",
            'ea2c': "al_eth2",  # set sfp 0 or 2 for SPF+
            'ea11': "al_eth3"
        }

        # number of Ethernet
        self.ethnum = {
            'ea2a': "20",
            'ea2b': "23",
            'ea2c': "11",
            'ea15': "11",
            'ea11': "5"
        }

        # number of WiFi
        self.wifinum = {
            'ea2a': "2",
            'ea2b': "3",
            'ea2c': "0",
            'ea15': "0",
            'ea11': "2"
        }

        # number of Bluetooth
        self.btnum = {
            'ea2c': "1",
            'ea2a': "1",
            'ea2b': "1",
            'ea15': "1",
            'ea11': "1"
        }

        # ethernet interface
        self.netif = {
            'ea2a': "br0",
            'ea2b': "psu0",
            'ea2c': "eth10",
            'ea15': "eth10",
            'ea11': "br0 "
        }

        # LCM update
        self.lcmupdate = {
            'ea2a': True,
            'ea2b': False,
            'ea2c': False,
            'ea15': False,
            'ea11': False
        }

        # Wifi cal data setting
        self.wifical = {
            'ea2a': True,
            'ea2b': True,
            'ea2c': False,
            'ea15': False,
            'ea11': False,
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        '''
            2022/11/4
            This is a special event for changing the BOM revision on the UDM-SE
        '''
        self.SPECIAL_RECALL_EVENT = False

        self.INIT_RECOVERY_IMAGE = True

        if self.SPECIAL_RECALL_EVENT is True:
            self.UPDATE_UBOOT = False
            self.BOOT_RECOVERY_IMAGE = False
        else:
            self.UPDATE_UBOOT = True
            self.BOOT_RECOVERY_IMAGE = True

        self.NEED_DROPBEAR = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True

        if self.SPECIAL_RECALL_EVENT is True:
            self.DATAVERIFY_ENABLE = False
            self.LCM_CHECK_ENABLE = False
        else:
            self.DATAVERIFY_ENABLE = True
            self.LCM_CHECK_ENABLE = True

    def set_boot_net(self):
        # import pdb; pdb.set_trace()
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv sysid")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "printenv model")
        
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ethact {}".format(self.activeport[self.board_id]))

    def set_fake_EEPROM(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf probe")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000000 " + "544e4255")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800000c " + self.wsysid[self.board_id])
        # reverse 77072aea to 2aea7707
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000010 " + self.wsysid[self.board_id][4:] + self.wsysid[self.board_id][:4])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x08000018 " + str(self.row_id).zfill(2) + "01ac74")  # fake mac
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "mw.l 0x0800001c " + "00032cbd")

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf erase {} 0x9000".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 {} 0x20".format(self.eeprom_offset[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "sf write 0x08000000 {} 0x20".format(self.eeprom_offset_2[self.board_id]))
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

    def set_kernel_net(self):
        if self.board_id == "ea2c" or self.board_id == "ea15":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "systemctl mask network-init udapi-server")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "systemctl stop network-init udapi-server")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "brctl delif br0 {}".format(self.netif[self.board_id]))
        elif self.board_id == "ea11":
            cmd = "swconfig dev switch0 vlan 99 set ports '0 1 2 3 4'"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
            cmd = "swconfig dev switch0 set apply"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig {} {}".format(self.netif[self.board_id], self.dutip))
        self.is_network_alive_in_linux(ipaddr=self.tftp_server)

    def update_uboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.set_boot_net()

        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)

        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-uboot.bin"),
            dest=os.path.join(self.tftpdir, "boot.img")
        )

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server, self.dutip))
        self.pexp.expect_action(10, self.bootloader_prompt, "run bootupd")  # tranfer img and update
        self.pexp.expect_only(30, "Bytes transferred")
        self.pexp.expect_action(60, self.bootloader_prompt, "run delenv")

    def boot_recovery_image(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)

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

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server, self.dutip))

        self.pexp.expect_action(10, self.bootloader_prompt, "run bootcmdtftp")
        self.pexp.expect_only(30, "Bytes transferred")

        self.pexp.expect_only(360, "Reboot system safely")

    def init_recovery_image(self):
        self.set_kernel_net()

    def fwupdate(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.set_boot_net()
        time.sleep(2)

        self.is_network_alive_in_uboot(retry=9, timeout=10)

        log_debug("Updating FW image ...")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv bootargsextra 'factory server={} client={} nc_transfer'".format(self.tftp_server, self.dutip))

        # copy recovery image to tftp server
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-recovery"),
            dest=os.path.join(self.tftpdir, "uImage")  # fixed name
        )

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "run bootcmdtftp")
        log_debug(msg="Enter factory install mode ...")
        self.pexp.expect_only(120, "Wait for nc client to push firmware")

        time.sleep(5)  # for stable

        nc_cmd = "nc -q 1 {} 5566 < {}".format(self.dutip, os.path.join(self.fwdir, self.board_id + "-fw.bin"))
        log_debug(msg=nc_cmd)

        [buf, rtc] = self.fcd.common.xcmd(nc_cmd)
        if (int(rtc) > 0):
            error_critical("cmd: \"{}\" fails, return value: {}".format(nc_cmd, rtc))

        log_debug(msg="Upgrading FW ...")
        self.pexp.expect_only(240, "Reboot system safely")
        log_debug(msg="FW update done ...")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def lcm_fw_ver_check(self):
        self.scp_get(
            dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
            src_file=os.path.join(self.tool_folder, "factory-test-tools*"),
            dst_file=self.dut_tmpdir
        )
        self.scp_get(
            dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
            src_file=os.path.join(self.tool_folder, "bc_*"),
            dst_file=self.dut_tmpdir
        )
        self.scp_get(
            dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
            src_file=os.path.join(self.tool_folder, "memtester_*"),
            dst_file=self.dut_tmpdir
        )
        self.scp_get(
            dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
            src_file=os.path.join(self.tool_folder, "mt-wifi-ated_*"),
            dst_file=self.dut_tmpdir
        )

        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dpkg -i /tmp/bc_*")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dpkg -i /tmp/memtester_*")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dpkg -i /tmp/factory-test-tools*")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "dpkg -i /tmp/mt-wifi-ated_*")

        try:
            cmd = "cat /usr/share/firmware/udw-lcm-fw.version"
            cmd_reply = self.pexp.expect_get_output(cmd, self.linux_prompt)
            log_debug("Get LCM FW version from shipping FW(raw data): " + cmd_reply)
            pattern = r"v([\d].[\d].[\d])-"
            m_prod_lcm_fw = re.findall(pattern, cmd_reply)
            if m_prod_lcm_fw:
                log_debug("Get LCM FW version from shipping FW(extracted): " + m_prod_lcm_fw[0])
                cmd = "/usr/share/lcm-firmware/lcm-fw-info /dev/ttyACM0"
                self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, post_exp=m_prod_lcm_fw[0], retry=20)
            else:
                error_critical("Can't the LCM FW from the shipping FW, FAIL!!")
        except Exception as e:
            self.pexp.expect_lnxcmd(30, "", "cat /var/log/ulcmd.log")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "")
            raise e

    def unlock_eeprom_permission(self):
        log_debug(msg="Unlock eeprom permission")
        self.pexp.expect_lnxcmd(30, self.linux_prompt, "echo 5edfacbf > /proc/ubnthal/.uf")

    def check_refuse_data(self):
        # expected efuse data provided by RF Julie lin
        # reg_dict format is {reg: expected_val}

        log_debug(msg="Check efuse register")
        reg_dict = {
            '49': '0x0020',
            '4D': '0x0040',
        }

        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ifconfig ra0 up")
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ifconfig rai0 up")
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "iwpriv ra0 set bufferLoadFromEfuse=1")
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "iwpriv rai0 set bufferLoadFromEfuse=1")

        try:
            for reg, expect_val in reg_dict.items():
                self.pexp.expect_lnxcmd(15, self.linux_prompt, "iwpriv rai0 e2p {}".format(reg), expect_val, retry=1)
        except Exception as e:
            log_error("Efuse data is incorrect")
            raise e

    def check_flash_data(self):
        # offset_dict format is {offset: expected_val}
        k_part = "/dev/mtd3"

        # 5G cal data
        log_debug(msg="Checking 5G cal data in flash")

        offset_dict = {
            '0x20049': '20 00',  # little endian of 49
            '0x2004d': '40 00',  # little endian of 4D
        }

        try:
            for offset, expect_val in offset_dict.items():
                self.pexp.expect_lnxcmd(
                    15,
                    self.linux_prompt,
                    "busybox hexdump -s {} -n 2 -C {} | head -n 1".format(offset, k_part),
                    expect_val,
                    retry=1
                )
        except Exception as e:
            log_error("Calibration data in flash is incorrect")
            raise e

    def del_anonymous_file(self):
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "rm /persistent/system/anonymous_device_id")

    def write_caldata_to_flash(self):
        log_debug(msg="Writing efuse data to flash")
        self.check_refuse_data()
        self.unlock_eeprom_permission()

        self.pexp.expect_lnxcmd(30, self.linux_prompt, 'ated -i ra0 -c "sync eeprom all"')
        self.pexp.expect_lnxcmd(30, self.linux_prompt, 'ated -i rai0 -c "sync eeprom all"')

        self.check_flash_data()
        
    def show_info(self):
        retry_time = 15
        while retry_time >= 0:
            output = self.pexp.expect_get_output(action="info", prompt= "" ,timeout=3)
            if output.find("Version") >= 0:
                break
            retry_time -= 1
            time.sleep(1)

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT is True:
            self.set_fake_EEPROM()
            self.update_uboot()
            self.pexp.expect_action(10, self.bootloader_prompt, "reset")
            msg(10, "Finish boot updating")

        if self.BOOT_RECOVERY_IMAGE is True:
            msg(15, "Updating FW")
            self.fwupdate()

        if self.INIT_RECOVERY_IMAGE is True:
            self.login(self.username, self.password, timeout=240, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            msg(15, "Boot up to linux console and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.unlock_eeprom_permission()
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.DATAVERIFY_ENABLE is True:
            self.pexp.expect_action(10, self.linux_prompt, "reboot -f")  # for correct ubnthal
            self.login(self.username, self.password, timeout=180, log_level_emerg=True)
            time.sleep(15)  # for stable eth
            self.set_kernel_net()
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.board_id == "ea11" or self.board_id == "ea15" or self.board_id == "ea2c":
            # copy factory and memtester deb
            pkg_sets = [
                "{}-memtester.deb".format(self.board_id),
                "{}-factory.deb".format(self.board_id)
            ]
            for pkg in pkg_sets:
                src_path = os.path.join(self.fcd_toolsdir, pkg)
                dst_path = os.path.join(self.dut_tmpdir, pkg)
                self.tftp_get(remote=src_path, local=dst_path,timeout=20)
                cmd = "dpkg -i {}".format(dst_path)
                self.pexp.expect_lnxcmd(15, self.linux_prompt, cmd)
        if self.LCM_CHECK_ENABLE is True:
            if self.lcmupdate[self.board_id] is True:
                msg(85, "Check LCM FW version ...")
                self.lcm_fw_ver_check()

        if self.wifical[self.board_id] is True:
            msg(95, "Write and check calibration data")
            self.check_refuse_data()
            self.write_caldata_to_flash()

        if self.board_id != "ea11":
            self.del_anonymous_file()

        if self.board_id == "ea2b":
            # below one of two function will cause the data of flash(MTD3) was removed so do not use it
            # self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig psu0 169.254.1.1 netmask 255.255.0.0")
            # self.show_info()
            output = self.pexp.expect_get_output(action="cat /usr/lib/version", prompt="", timeout=3)
            log_debug(output)
        else:
            # self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /usr/lib/version")
            output = self.pexp.expect_get_output(action="cat /usr/lib/version", prompt="", timeout=3)
            log_debug(output)
        if self.board_id == "ea15":
            cmd = "ulcmd --command dump --sender fcd_team"
            ct = 0
            retry_max = 240
            while ct < retry_max:
                cmd_reply = self.pexp.expect_get_output(cmd, self.linux_prompt)
                log_debug("Get LCM FW version from shipping FW(raw data): " + cmd_reply)
                pattern = r"v([\d].[\d].[\d])-"
                m_prod_lcm_fw = re.findall(pattern, cmd_reply)
                if m_prod_lcm_fw:
                    break # 若成功找到符合的 pattern，則跳出迴圈
                time.sleep(1)
                ct += 1
            else:
                rmsg = "Get LCM FW Version Fail!!!"
                error_critical(rmsg)

        if self.board_id == "ea15" or self.board_id =="ea2c":
            self.pexp.expect_action(30, self.linux_prompt, "systemctl unmask network-init udapi-server")
            self.pexp.expect_action(30, self.linux_prompt, "systemctl start network-init udapi-server")
            self.pexp.expect_action(30, self.linux_prompt, "systemctl daemon-reload")

        cmd = "systemctl is-system-running"
        ct = 0
        retry_max = 120
        while ct < retry_max:
            output = self.pexp.expect_get_output(action=cmd, prompt="" ,timeout=3)
            m_run = re.findall("running", output)
            m_degraded = re.findall("degraded", output)
            if len(m_run) == 2 or len(m_degraded) == 1:
                rmsg = "The system is running good"
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
    udm_al324_factory = UDM_AL324_FACTORY()
    udm_al324_factory.run()


if __name__ == "__main__":
    main()
