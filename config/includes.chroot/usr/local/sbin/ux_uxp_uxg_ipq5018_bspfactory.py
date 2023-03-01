#!/usr/bin/python3
import time
import re
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a667: UEX
    a674: UEXP
    a677: UXG
'''


class UX_UXP_UXG_IPQ5018_BspFactory(ScriptBase):
    def __init__(self):
        super(UX_UXP_UXG_IPQ5018_BspFactory, self).__init__()
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

        if self.board_id in ["a667", "a674"]:
            self.log_upload_failed_alert_en = True

        self.prod_shortname ={
            'a667': "UX",
            'a674': "UXP",
            "a677": "UXG"

        }

        self.ethnum = {
            'a667': "2",
            'a674': "2",
            "a677": "2"
        }

        self.wifinum = {
            'a667': "2",
            'a674': "2",
            'a677': "0"
        }

        self.btnum = {
            'a667': "1",
            'a674': "1",
            'a677': "1"
        }

        self.bootm_addr = {
            'a667': "",
            'a674': "",
            'a677': ""
        }

        self.bootm_cmd = {
            'a667': "",
            'a674': "",
            'a677': ""
        }

        self.linux_prompt_select = {
            'a667': "#",
            'a674': "#",
            'a677': "#"
        }

        self.uboot_eth_port = {
            'a667': "eth0",
            'a674': "eth0",
            'a677': "eth0"
        }

        self.lnx_eth_port = {
            'a667': "br-lan",
            'a674': "br-lan",
            'a677': "br-lan"
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
        cmd = "mmc write 0x50000000 0x20800 0xffff; saveenv"
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

    def registration_uex(self, regsubparams = None):
        log_debug("Starting to do registration ...")
        self.devreg_hostname = "stage.udrs.io"
        if regsubparams is None:
            regsubparams = self.access_chips_id()

        code_type = "01"

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value={}".format(self.qrhex)

        # The HEX of the activate code
        if self.activate_code is None or not self.activate_code:
            reg_activate_code = ""
        else:
            reg_activate_code = "-i field=code,format=hex,value={}".format(self.activate_code_hex)

        clientbin = "/usr/local/sbin/client_rpi4_release"
        regparam = [
            "-h {}".format(self.devreg_hostname),
            "-k {}".format(self.pass_phrase),
            regsubparams,
            "-i field=code_type,format=hex,value={}".format(code_type),
            reg_qr_field,
            reg_activate_code,
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

    def check_info(self):

        self.pexp.expect_lnxcmd(5, self.linux_prompt, "info", "Version", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "shortname=" + self.prod_shortname[self.board_id])
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

    def chk_caldata_uex(self):
        cmd = "hexdump -s 0x1000 -n 10 /dev/mtdblock8"
        post_exp = "0001000 0001 0404 0000 0000 8000"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

        time.sleep(1)
        cmd = "hexdump -s 0x26800 -n 10 /dev/mtdblock8"
        post_exp = "0026800 0001 0404 0000 0000 8000"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

    def run(self):
        """
            Main procedure of factory
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
            if self.board_id == "a667" or self.board_id == "a674":
                self.chk_caldata_uex()
                self.registration_uex()
            else:
                self.registration()

            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            if self.board_id == "a667" or self.board_id == "a674" or self.board_id == "a677":
                self.fwupdate_uex()
            else:
                self.fwupdate()

            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        if self.board_id in ["a667", "a674"]:
            self.__del__()
        cmd = "systemctl is-system-running"
        ct = 0
        retry_max = 120
        while ct < retry_max:
            output = self.pexp.expect_get_output(action=cmd, prompt="", timeout=3)
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
    ux_uxp_uxg_ipq5018_bspfactory = UX_UXP_UXG_IPQ5018_BspFactory()
    ux_uxp_uxg_ipq5018_bspfactory.run()

if __name__ == "__main__":
    main()
