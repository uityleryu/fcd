#!/usr/bin/python3
import time
import re

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a681: U7-Enterprise
    a682: U7-Pro
    a685: U7-Enterprise-IW
'''
class U7IPQ5322BspFactory(ScriptBase):
    def __init__(self):
        super(U7IPQ5322BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = "images/{}-fw.bin".format(self.board_id)
        self.initramfs = "images/{}-initramfs.bin".format(self.board_id)
        self.gpt = "images/{}-gpt.bin".format(self.board_id)
        self.devregpart = "/dev/mtdblock10"
        self.bomrev = "113-{}".format(self.bom_rev)
        self.bootloader_prompt = "IPQ5332#"
        self.linux_prompt = "root@OpenWrt:/#"

        self.ethnum = {
            'a681': "1",
            'a682': "1",
            'a685': "4",
        }

        self.wifinum = {
            'a681': "3",
            'a682': "3",
            'a685': "3",
        }

        self.btnum = {
            'a681': "1",
            'a682': "1",
            'a685': "1",
        }

        self.bootm_addr = {
            'a681': "0x50000000",
            'a682': "0x50000000",
            'a685': "0x50000000",
        }

        # 650 U6-Pro, 651 U6-Mesh, 652 U6-IW, 653 U6-Extender, 656 U6-Enterprise-IW
        self.bootm_cmd = {
            'a681': "bootm $fileaddr#config@a681",
            'a682': "bootm $fileaddr#config@a682",
            'a685': "bootm $fileaddr#config@a685",
        }

        self.linux_prompt_select = {
            'a681': "#",
            'a682': "#",
            'a685': "#",
        }

        self.uboot_eth_port = {
            'a681': "eth0",
            'a682': "eth0",
            'a685': "eth0",
        }

        self.lnx_eth_port = {
            'a681': "br-lan",
            'a682': "br-lan",
            'a685': "br-lan",
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
        self.CHKCALDATA_ENABLE = True
        self.REGISTER_ENABLE = True
        self.FANI2C_CHECK_ENABLE = True
        self.FUSE_ENABLE = True
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
            "tftpboot 0x44000000 {} && mmc write 0x44000000 0 34 && mmc rescan && mmc part".format(self.gpt),
            "setenv imgaddr {} && tftpboot {} {}".format(self.bootm_addr[self.board_id], self.bootm_addr[self.board_id], self.initramfs),
            self.bootm_cmd[self.board_id]
        ]
        for cmd in cmdset:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.linux_prompt = self.linux_prompt_select[self.board_id]
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)
        time.sleep(30)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "mtd erase /dev/mtd7", self.linux_prompt)
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "ifconfig br0", "inet addr", retry=20)
        cmd = "ifconfig br0 {}".format(self.dutip)
        self.disable_udhcpc()
        time.sleep(3)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)
        self.is_network_alive_in_linux()

        src = "{}/{}-fw.bin".format(self.fwdir, self.board_id)
        dst = "{}/fwupdate.bin".format(self.dut_tmpdir)
        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip, src_file=src, dst_file=dst)

        if self.board_id in ['a681', 'a682', 'a683', 'a685', 'a686']:
            time.sleep(2)  # because do not wait to run "syswrapper.sh upgrade2" could be fail, the system ae still startup
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "fwupdate.real -m /{}".format(dst))

        # self.pexp.expect_lnxcmd(10, self.linux_prompt, "syswrapper.sh upgrade2")
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

        cmd = "tftpb 0x50000000 images/{}-uboot.mbn".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(60, "Bytes transferred", "sf probe")
        cmd = "sf erase 0x110000 0xb0000"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        cmd = "sf write 0x50000000 0x120000 $filesize"
        self.pexp.expect_ubcmd(60, "Erased: OK", cmd)
        self.pexp.expect_ubcmd(60, "Written: OK", "reset")

        self.pexp.expect_action(60, "to stop", "\033\033")
        self.del_arp_table(self.dutip)
        comma_mac = self.mac_format_str2comma(self.mac)
        self.set_ub_net(comma_mac)
        self.is_network_alive_in_uboot()
        self.display_arp_table()

        cmd = "setenv bootargs 'console=ttyMSM0,115200 factory server={} nc_transfer client={}'".format(
            self.tftp_server, self.dutip)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)

        '''
            The recovery image == image loader
            which is "uImage"
        '''
        cmd = "tftpb 0x50000000 images/{}-loader.img".format(self.board_id)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        self.pexp.expect_only(60, "Bytes transferred")
        cmd = "mmc write 0x50000000 0x20800 0xffff"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(60, "written: OK", "bootm")

        self.pexp.expect_only(120, "enter factory install mode")
        log_debug(msg="Enter factory install mode ...")
        self.pexp.expect_only(120, "Wait for nc client")
        log_debug(msg="nc ready ...")

        ct = 0
        retry = 5
        while ct < retry:
            ct += 1
            cmd = "ping -c 3 {}".format(self.dutip)
            [buf, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                rmsg = "ping IP: {}, FAILED, Retry: {}".format(self.dutip, ct)
                log_debug(rmsg)
            else:
                log_debug("ping IP: {} successfully".format(self.dutip))
                break
        else:
            rmsg = "ping IP: {}, FAILED".format(self.dutip)
            error_critical(rmsg)

        cmd = "nc -N {} 5566 < {}/{}-fw.bin".format(self.dutip, self.fwdir, self.board_id)
        log_debug("cmd: " + cmd)
        ct = 0
        retry = 4
        while ct < retry:
            ct += 1
            [buf, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                rmsg = "\nCommand output:\n{}".format(buf)
                rmsg += "Retry: {}".format(ct)
                log_debug(rmsg)
                time.sleep(1)
            else:
                break
        else:
            rmsg = "\nCommand output:\n{}".format(buf)
            rmsg += "Uploading FW FAIL!!!"
            error_critical(rmsg)

        log_debug(msg="Upgrading FW ...")
        self.pexp.expect_only(120, "Reboot system safely")
        log_debug(msg="FW update done ...")

        self.linux_prompt = "root"
        self.login("ui", "ui", timeout=300, log_level_emerg=True, press_enter=False, retry=3)

    def check_info(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def chk_caldata_ipq5322(self):
        cmd = "hexdump -s 0x1000 -n 10 /dev/mtdblock9"
        post_exp = "0001000 0001 0378 0000 0000 f800"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

        time.sleep(1)
        cmd = "hexdump -s 0x58800 -n 10 /dev/mtdblock9"
        post_exp = "0058800 0001 0404 0000 0000 7800"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

    def i2c_check(self, item):
        if item == "fan":
            cmd = "i2cdetect -y -r 0 0x4c 0x4c"
            post_exp = "UU"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

    def fuse(self):
        cmd = "hexdump -C /dev/mtd5 | grep 00002350"
        post_exp = "Ubiquiti"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)
        log_debug(msg="Check TME-L image is OEM-Signed ... PASS")

        cmd = "echo 1 > /sys/devices/system/qfprom/qfprom0/list_ipq5322_fuse"
        post_exp = "TME_AUTH_EN\t0x000A00D0"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

        cmd = "echo 1 > /sys/devices/system/qfprom/qfprom0/list_ipq5322_fuse"
        post_exp = "TME_OEM_ID\t0x000A00D0"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)
        log_debug(msg="Check the board fuse table ... PASS")

        cmd = "md5sum /lib/firmware/sec.dat"
        post_exp = "e3ddf61f6867b9fbee40b45a7a52e811"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)
        log_debug(msg="Check the md5sum of fuse blower sec.dat ... PASS")

        cmd = "echo -n \"/lib/firmware/sec.dat\" > /sys/devices/system/qfprom/qfprom0/sec_dat"
        post_exp = "Fuse Blow Success"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)
        log_debug(msg="Blow Miami fuse ... PASS")

        cmd = "echo 1 > /sys/devices/system/qfprom/qfprom0/list_ipq5322_fuse"
        post_exp = "TME_AUTH_EN\t0x000A00D0\t0x00000041"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

        cmd = "echo 1 > /sys/devices/system/qfprom/qfprom0/list_ipq5322_fuse"
        post_exp = "TME_OEM_ID\t0x000A00D0\t0x02180000"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)
        log_debug(msg="Check Miami Fuse register ... PASS")

    def run(self):
        """
            Main procedure of factory
        """

        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)


        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")

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

        if self.CHKCALDATA_ENABLE is True:
            if self.board_id in ["a681", "a682", "a683", "a685", "a686"]:
                self.chk_caldata_ipq5322()
                msg(35, "Finish check wifi cal_data ...")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FANI2C_CHECK_ENABLE is True:
            self.i2c_check(item="fan")
            msg(62, "Succeeding in checking FAN i2c value ...")

        if self.FUSE_ENABLE is True:
            self.fuse()
            msg(65, "Succeeding in fuse Qualcomm auth data ...")

        if self.FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        if self.ps_state is True:
            time.sleep(2)
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    u7ipq5322_bspfactory = U7IPQ5322BspFactory()
    u7ipq5322_bspfactory.run()


if __name__ == "__main__":
    main()
