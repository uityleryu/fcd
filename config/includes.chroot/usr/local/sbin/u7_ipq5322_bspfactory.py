#!/usr/bin/python3
import time
import re

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

'''
    a681: U7-Enterprise
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

        #if self.board_id in ["a667", "a674"]:
        #    self.log_upload_failed_alert_en = True

        self.ethnum = {
            'a681': "1",
        }

        self.wifinum = {
            'a681': "3",
        }

        self.btnum = {
            'a681': "1",
        }

        self.bootm_addr = {
            'a681': "0x50000000",
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
            'a681': "#",
        }

        self.uboot_eth_port = {
            'a681': "eth0",
        }

        self.lnx_eth_port = {
            'a681': "br-lan",
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
        self.FWUPDATE_ENABLE = False
        self.DATAVERIFY_ENABLE = False

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
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())
        self.pexp.expect_only(10, self.linux_prompt)

        if self.board_id in ["a667", "a674"]:
            cmd = "ifconfig | grep -C 2 br0"
            ct = 0
            retry_max = 300
            while ct < retry_max:
                output = self.pexp.expect_get_output(action=cmd, prompt="" ,timeout=3)
                pattern = r"192.168.1.[\d]+"
                m_run = re.findall(pattern, output)
                if len(m_run) == 1:
                    rmsg = "The system is running good"
                    log_debug(rmsg)
                    self.pexp.expect_lnxcmd(5, self.linux_prompt, "poweroff")
                    break

                time.sleep(1)
                ct += 1
            else:
                rmsg = "The system is not booting up successfully, FAIL!!"
                error_critical(rmsg)

        # Joseph: Just keep it for a period of time, if there is no problem to the upper method, then will remove it
        # if self.board_id in ["a667", "a674"]:
        #     cmd = "systemctl is-system-running"
        #     ct = 0
        #     retry_max = 300
        #     while ct < retry_max:
        #         output = self.pexp.expect_get_output(action=cmd, prompt="" ,timeout=3)
        #         m_run = re.findall("running", output)
        #         if len(m_run) == 2:
        #             rmsg = "The system is running good"
        #             log_debug(rmsg)
        #             break

        #         time.sleep(1)
        #         ct += 1
        #     else:
        #         rmsg = "The system is not booting up successfully, FAIL!!"
        #         error_critical(rmsg)

    def chk_caldata_ipq5322(self):
        cmd = "hexdump -s 0x1000 -n 10 /dev/mtdblock9"
        post_exp = "0001000 0001 0378 0000 0000 f800"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

        time.sleep(1)
        cmd = "hexdump -s 0x58800 -n 10 /dev/mtdblock9"
        post_exp = "0058800 0001 0404 0000 0000 7800"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, post_exp, retry=5)

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

        """
        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")
        """
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
            if self.board_id in ["a681"]:
                self.chk_caldata_ipq5322()
                msg(35, "Finish check wifi cal_data ...")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")
        """
        if self.ps_state is True:
            time.sleep(2)
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")
        """
        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    u7ipq5322_bspfactory = U7IPQ5322BspFactory()
    u7ipq5322_bspfactory.run()


if __name__ == "__main__":
    main()