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
    a686: U7-Pro-IW
    a688: UK-Pro
    a691: U7-LR
    a696: U7-Pro-MAX
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
            'a686': "1",
            'a688': "1",
            'a691': "1",
            'a696': "1",
        }

        self.wifinum = {
            'a681': "3",
            'a682': "3",
            'a685': "3",
            'a686': "3",
            'a688': "2",
            'a691': "2",
            'a696': "3",
        }

        self.btnum = {
            'a681': "1",
            'a682': "1",
            'a685': "1",
            'a686': "1",
            'a688': "0",
            'a691': "1",
            'a696': "1",
        }

        self.bootm_addr = {
            'a681': "0x50400000",
            'a682': "0x50400000",
            'a685': "0x50400000",
            'a686': "0x50400000",
            'a688': "0x50000000",
            'a691': "0x50400000",
            'a696': "0x50400000",
        }

        self.bootm_cmd = {
            'a681': "bootm $fileaddr#config@a681",
            'a682': "bootm $fileaddr#config@a682",
            'a685': "bootm $fileaddr#config@a685",
            'a686': "bootm $fileaddr#config@a686",
            'a688': "bootm $fileaddr#config@a688",
            'a691': "bootm $fileaddr#config@a691",
            'a696': "bootm $fileaddr#config@a696",
        }

        self.linux_prompt_select = {
            'a681': "#",
            'a682': "#",
            'a685': "#",
            'a686': "#",
            'a688': "#",
            'a691': "#",
            'a696': "#",
        }

        self.uboot_eth_port = {
            'a681': "eth0",
            'a682': "eth0",
            'a685': "eth0",
            'a686': "eth0",
            'a688': "eth0",
            'a691': "eth0",
            'a696': "eth0",
        }

        self.lnx_eth_port = {
            'a681': "br-lan",
            'a682': "br-lan",
            'a685': "br-lan",
            'a686': "br-lan",
            'a688': "br-lan",
            'a691': "br-lan",
            'a696': "br-lan",
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.BOOT_BSP_IMAGE = True
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.CHKCALDATA_ENABLE = True
        self.REGISTER_ENABLE = True

        if self.board_id == "a688":
            self.FANI2C_CHECK_ENABLE = False
            self.FWUPDATE_ENABLE = True
            self.DATAVERIFY_ENABLE = True
        elif self.board_id in ["a681", "a685", "a696"]:
            self.FANI2C_CHECK_ENABLE = True
            self.FWUPDATE_ENABLE = False
            self.DATAVERIFY_ENABLE = False
        else:
            self.FANI2C_CHECK_ENABLE = True
            self.FWUPDATE_ENABLE = True
            self.DATAVERIFY_ENABLE = True

        self.FUSE_ENABLE = True
        # self.FWUPDATE_ENABLE = True
        # self.DATAVERIFY_ENABLE = True

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0)
        self.set_lnx_net(self.lnx_eth_port[self.board_id])
        self.is_network_alive_in_linux()

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

        time.sleep(2)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "fwupdate.real -m /{}".format(dst))

        # because do not wait to run "syswrapper.sh upgrade2" could be fail, the system ae still startup
        # self.pexp.expect_lnxcmd(10, self.linux_prompt, "syswrapper.sh upgrade2")
        self.linux_prompt = "#"

    def fwupdate(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")
        self._ramboot_uap_fwupdate()
        # U6-IW, the upgrade fw process ever have more than 150sec, to increase 150 -> 300 sec to check if it still fail
        #sometimes DUT will fail log to interrupt the login in process so add below try process for it
        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=True, retry=3)

    def check_info(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def chk_caldata_ipq5322(self):
        CHK_2G_CALDATA_EN = True
        CHK_5G_CALDATA_EN = True

        # 2G cal data
        if CHK_2G_CALDATA_EN is True:
            if self.board_id in ["a696"]:
                cmd = "hexdump -s 0x8A800 -n 10 /dev/mtdblock9"
                post_exp = "008a800 0001 0404 0000 0000 e800"
            else:
                cmd = "hexdump -s 0x1000 -n 10 /dev/mtdblock9"
                post_exp = "0001000 0001 0378 0000 0000 f800"

            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)
            time.sleep(1)

        # 5G cal data
        if CHK_5G_CALDATA_EN is True:
            cmd = "hexdump -s 0x58800 -n 10 /dev/mtdblock9"
            post_exp = "0058800 0001 0404 0000 0000"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)
            time.sleep(1)

    def chk_bdf_ipq5322(self):
        CHK_2G_BDF_EN = True
        CHK_5G_BDF_EN = True

        if self.board_id in ["a681", "a682", "a685", "a686" "a691", "a696"]:
            CHK_2G_BDF_EN = False
            CHK_5G_BDF_EN = False

        # 2G BDF
        if CHK_2G_BDF_EN is True:
            if self.board_id in ["a688"]:
                cmd = "md5sum /lib/firmware/IPQ5332/bdwlan.b16"
                post_exp = "06a6e5913e85b24d590fc499f881e954"
            else:
                pass

            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

        # 5G BDF
        if CHK_5G_BDF_EN is True:
            if self.board_id in ["a688"]:
                cmd = "md5sum /lib/firmware/qcn9224/bdwlan.b0002"
                post_exp = "bbfa01b814b9f13fbd412275870c2150"
            else:
                pass

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

        msg(10, "Boot up to linux console by initram and network is good ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if self.CHKCALDATA_ENABLE is True:
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
            self.chk_bdf_ipq5322()
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
