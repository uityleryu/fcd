#!/usr/bin/python3
import time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a650: U6-PRO
    a651: U6-Mesh
    a652: U6-IW
    a653: U6-Extender
    a654: U6-Enterprise
    a655: U6-Infinity
    a656: U6-Exterprise-IW
    a665: AFi-6-R
    a666: AFi-6-Ext
    a667: UniFi-Express
    a674: UniFi-Express Mesh
    a675: UniFi6 Pro outdoor
'''


class U6IPQ5018BspFactory(ScriptBase):
    def __init__(self):
        super(U6IPQ5018BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = "images/{}-fw.bin".format(self.board_id)
        self.initramfs = "images/{}-initramfs.bin".format(self.board_id)
        self.gpt = "images/{}-gpt.bin".format(self.board_id)
        self.devregpart = "/dev/mtdblock9"
        self.bomrev = "113-{}".format(self.bom_rev)
        self.bootloader_prompt = "IPQ5018#"
        self.linux_prompt = "root@OpenWrt:/#"

        self.ethnum = {
            'a650': "1",
            'a651': "1",
            'a652': "1",
            'a653': "0",
            'a654': "1",
            'a655': "1",
            'a656': "1",
            'a665': "2",
            'a666': "0",
            'a667': "2",
            'a674': "2",
            'a675': "4"
        }

        self.wifinum = {
            'a650': "2",
            'a651': "2",
            'a652': "2",
            'a653': "2",
            'a654': "3",
            'a655': "3",
            'a656': "3",
            'a665': "2",
            'a666': "2",
            'a667': "2",
            'a674': "2",
            'a675': "0"
        }

        self.btnum = {
            'a650': "1",
            'a651': "1",
            'a652': "1",
            'a653': "1",
            'a654': "1",
            'a655': "1",
            'a656': "1",
            'a665': "1",
            'a666': "1",
            'a667': "1",
            'a674': "1",
            'a675': "1"
        }

        self.bootm_addr = {
            'a650': "0x50000000",
            'a651': "0x50000000",
            'a652': "0x50000000",
            'a653': "0x50000000",
            'a654': "0x50000000",
            'a655': "0x50000000",
            'a656': "0x50000000",
            'a665': "1",
            'a666': "1",
            'a667': "",
            'a674': "",
            'a675': "0x50000000"
        }

        # 650 U6-Pro, 651 U6-Mesh, 652 U6-IW, 653 U6-Extender, 656 U6-Enterprise-IW
        self.bootm_cmd = {
            'a650': "bootm $fileaddr#config@a650",
            'a651': "bootm $fileaddr#config@a651",
            'a652': "bootm $fileaddr#config@a652",
            'a653': "bootm $fileaddr#config@a653",
            'a654': "bootm $fileaddr#config@a654",
            'a655': "bootm $fileaddr#config@a655",
            'a656': 'bootm $fileaddr#config@a656',
            'a665': "1",
            'a666': "1",
            'a667': "",
            'a674': "",
            'a675': "bootm $fileaddr#config@a675"
        }

        self.linux_prompt_select = {
            'a650': "#",    #prompt will be like "UBNT-BZ.5.65.0#"
            'a651': "#",    #prompt will be like "UBNT-BZ.5.65.0#"
            'a652': "#",
            'a653': "#",
            'a654': "#",    #prompt will be like "UBNT-BZ.5.65.0#"
            'a655': "#",    #prompt will be like "UBNT-BZ.5.65.0#"
            'a656': "#",
            'a665': "#",
            'a666': "#",
            'a667': "#",
            'a674': "#",
            'a675': "#"
        }

        self.uboot_eth_port = {
            'a650': "eth0",
            'a651': "eth0",
            'a652': "eth1",
            'a653': "eth0",
            'a654': "eth0",
            'a655': "eth0",
            'a656': "eth1",
            'a665': "eth0",
            'a666': "eth0",
            'a667': "eth0",
            'a674': "eth0",
            'a675': "eth0"
        }

        self.lnx_eth_port = {
            'a650': "br-lan",
            'a651': "br-lan",
            'a652': "br-lan",
            'a653': "br-lan",
            'a654': "br-lan",
            'a655': "br-lan",
            'a656': "br-lan",
            'a665': "br-lan",
            'a666': "br-lan",
            'a667': "br-lan",
            'a674': "br-lan",
            'a675': "br-lan"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        '''
            This is a special case for the U6-Pro recall event.
        '''
        self.BOOT_INITRAM_IMAGE = False

        self.BOOT_BSP_IMAGE = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        if self.board_id == "a666" or self.board_id == "a665" or self.board_id == "a674" or self.board_id == "a675":
            self.FWUPDATE_ENABLE = False
            self.DATAVERIFY_ENABLE = False
        else:
            self.FWUPDATE_ENABLE = True
            self.DATAVERIFY_ENABLE = True

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0)
        self.set_lnx_net(self.lnx_eth_port[self.board_id])
        self.is_network_alive_in_linux()

    '''
        This is a special case for the U6-Pro recall event.
    '''
    def run_initram_bootup(self):
        self.pexp.expect_action(20, "to stop", "\033\033")
        self.set_ub_net(self.premac, ethact=self.uboot_eth_port[self.board_id])
        self.is_network_alive_in_uboot()
        cmd = "tftpboot 0x50000000 images/{}.itb".format(self.board_id)
        self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)
        cmd = self.bootm_cmd[self.board_id]
        self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)

        self.linux_prompt = "#"
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)
        cmd = "ifconfig br0"
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, "Link encap:Ethernet", retry=10)

        self.set_lnx_net("br0")
        self.is_network_alive_in_linux()
        cmd = "echo 5edfacbf > /proc/ubnthal/.uf"
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd)

    def _ramboot_uap_fwupdate(self):
        self.pexp.expect_action(40, "to stop", "\033\033")
        self.set_ub_net(self.premac, ethact=self.uboot_eth_port[self.board_id])
        self.is_network_alive_in_uboot()

        cmdset = [
            "tftpboot 0x50000000 {} && mmc erase 0x00000000 22 && mmc write 0x50000000 0x00000000 22".format(self.gpt),
            "setenv bootcmd \"mmc read {0} 0x00000022 0x00020022; bootm {0}\"".format(self.bootm_addr[self.board_id]),
            "setenv imgaddr 0x44000000",
            "saveenv",
            "tftpboot {} {}".format(self.bootm_addr[self.board_id] ,self.initramfs),
            self.bootm_cmd[self.board_id]
        ]
        for cmd in cmdset:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.linux_prompt = self.linux_prompt_select[self.board_id]
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)
        self.disable_udhcpc()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "mtd erase /dev/mtd6", self.linux_prompt)
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "ifconfig br0", "inet addr", retry=12)
        cmd = "ifconfig br0 {}".format(self.dutip)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        self.is_network_alive_in_linux()

        src = "{}/{}-fw.bin".format(self.fwdir, self.board_id)
        dst = "{}/fwupdate.bin".format(self.dut_tmpdir)
        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip, src_file=src, dst_file=dst)

        if self.board_id == 'a650' or self.board_id == 'a651':
            time.sleep(10)  # because do not wait to run "syswrapper.sh upgrade2" could be fail, the system ae still startup

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "syswrapper.sh upgrade2")
        self.linux_prompt = "#"

    def fwupdate(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
        self._ramboot_uap_fwupdate()
        # U6-IW, the upgrade fw process ever have more than 150sec, to increase 150 -> 300 sec to check if it still fail
        #sometimes DUT will fail log to interrupt the login in process so add below try process for it
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)

    def fwupdate_uex(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
        self.pexp.expect_action(60, "to stop", "\033\033")
        self.del_arp_table(self.dutip)
        comma_mac = self.mac_format_str2comma(self.mac)
        self.set_ub_net(comma_mac)
        self.is_network_alive_in_uboot()
        self.display_arp_table()

        cmdset = [
            "tftpb 0x50000000 images/{}-uboot.mbn".format(self.board_id),
            "sf probe",
            "sf erase 0x110000 0xb0000",
            "sf write 0x50000000 0x120000 $filesize",
            "reset"
        ]
        for cmd in cmdset:
            self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)

        self.pexp.expect_action(60, "to stop", "\033\033")
        self.del_arp_table(self.dutip)
        comma_mac = self.mac_format_str2comma(self.mac)
        self.set_ub_net(comma_mac)
        self.is_network_alive_in_uboot()
        self.display_arp_table()

        cmdset = [
            "setenv bootargs 'console=ttyMSM0,115200 factory server={} nc_transfer client={}'".format(
            self.tftp_server, self.dutip),
            "tftpb 0x50000000 images/{}-loader.img".format(self.board_id),
            "bootm"
        ]
        for cmd in cmdset:
            self.pexp.expect_ubcmd(20, self.bootloader_prompt, cmd)

        self.pexp.expect_only(120, "enter factory install mode")
        log_debug(msg="Enter factory install mode ...")
        self.pexp.expect_only(120, "Wait for nc client")
        log_debug(msg="nc ready ...")
        nc_cmd = "nc -N {} 5566 < {}/{}-fw.bin".format(self.dutip, self.fwdir, self.board_id)
        [buf, rtc] = self.fcd.common.xcmd(nc_cmd)
        if (int(rtc) > 0):
            error_critical("cmd: \"{}\" fails, return value: {}".format(nc_cmd, rtc))

        log_debug(msg="Upgrading FW ...")
        self.pexp.expect_only(120, "Reboot system safely")
        log_debug(msg="FW update done ...")

        # the linux prompt is different to other products
        self.linux_prompt = "root@UEX"
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=False, retry=3)

    def check_info(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if self.BOOT_BSP_IMAGE is True:
            self.init_bsp_image()

        '''
            This is a special case for the U6-Pro recall event. 
        '''
        if self.BOOT_INITRAM_IMAGE is True:
            self.run_initram_bootup()

        msg(10, "Boot up to linux console by initram and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            if self.board_id == "a667":
                self.fwupdate_uex()
            else:
                self.fwupdate()

            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    u6ipq5018_bspfactory = U6IPQ5018BspFactory()
    u6ipq5018_bspfactory.run()

if __name__ == "__main__":
    main()
