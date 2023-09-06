#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_info, log_debug, log_error, msg, error_critical
from datetime import datetime

'''
This FCD script is for
    e614: ULTE-FLEX-EU
    e615: ULTE-FLEX-US
    e618: UMR-EU-AC
    e619: UMR-US-AC
    e620: UMR-Ultra
    dca6: UMR-PRO-US
    dca7: UMR-PRO-EU
'''


class UAPQCA956xFactory2(ScriptBase):
    def __init__(self):
        super(UAPQCA956xFactory2, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.devregpart = "/dev/mtdblock2"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "ath>"
        self.linux_prompt = "# "
        self.cmd_prefix = "go 0x80200020 "
        self.product_class = "radio"  # For this product using radio

        # helper path
        helppth = {
            'e614': "ulte_flex",
            'e615': "ulte_flex",
            'e618': "ulte_flex",
            'e619': "ulte_flex",
            'e620': "ulte_flex",
            'dca6': "ulte_flex",
            'dca7': "ulte_flex"
        }

        self.helperexe = "helper_ARxxxx_release"
        self.helper_path = helppth[self.board_id]

        self.UPDATE_UBOOT = True
        self.FWUPDATE_ENABLE = True
        self.BOOT_RECOVERY_IMAGE = True
        self.INIT_RECOVERY_IMAGE = False
        self.PROVISION_ENABLE = True
        self.DOHELPER_ENABLE = True
        self.REGISTER_ENABLE = True
        self.DATAVERIFY_ENABLE = True
        self.SSH_ENABLE = True

    def enter_uboot(self, init_uapp=False):
        self.pexp.expect_action(90, "Hit any key to stop autoboot", "\033")
        time.sleep(2)

        if init_uapp is True:
            log_debug(msg="Init uapp")
            # Init uapp. DUT will reset after init
            self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uappinit")

        self.set_ub_net()
        self.is_network_alive_in_uboot(arp_logging_en=True, del_dutip_en=True)

    def update_uboot(self):
        uboot_path = os.path.join(self.fwdir, self.board_id + "-uboot.bin")
        log_debug(msg="uboot bin path:" + uboot_path)

        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootfile {}".format(uboot_path))
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "tftpboot 0x81000000", "Bytes transferred")

        # erase and write flash
        self.pexp.expect_action(30, self.bootloader_prompt, 'erase_ext 0 80000')
        self.pexp.expect_action(60, self.bootloader_prompt, 'write_ext 0x81000000 0 80000')
        self.pexp.expect_action(60, self.bootloader_prompt, 'erase_ext 80000 10000')

    def boot_recovery(self):
        recovery_path = os.path.join(self.fwdir, self.board_id + "-recovery.bin")
        log_debug(msg="recovery bin path:" + recovery_path)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootfile {}".format(recovery_path))
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "tftpboot 0x81000000", "Bytes transferred")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootm")

    def fwupdate(self):
        fw_path = os.path.join(self.fwdir, self.board_id + ".bin")
        log_debug(msg="firmware path:" + fw_path)

        if self.board_id in ["dca6", "dca7", "e618", "e619", "e620"]:
            self.user = "ui"
            self.password = "ui"

        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip,
                     src_file=fw_path, dst_file=self.dut_tmpdir)

        self.pexp.expect_action(30, "", "md5sum /tmp/{}.bin".format(self.board_id))
        # self.pexp.expect_action(30, self.linux_prompt, "afiupgrade /tmp/{}.bin".format(self.board_id))
        self.pexp.expect_action(240, self.linux_prompt, "uh-fw-tool -f /tmp/{}.bin".format(self.board_id))
        self.pexp.expect_only(30, 'Message Digest successfully verfied')
        self.pexp.expect_only(180, 'fw_inactive')
        self.pexp.expect_only(180, 'ltefw')
        self.pexp.expect_only(180, 'recovery')
        self.pexp.expect_only(180, 'Updating boot select partitions')
        self.pexp.expect_action(180, self.linux_prompt, "reboot")
        # self.pexp.expect_only(540, 'Starting kernel')

    def _fwupdate(self):
        # TFTP bin from TestServer
        fw_path = os.path.join(self.fwdir, self.board_id + ".bin")
        log_debug(msg="firmware path:" + fw_path)

        self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootfile {}".format(fw_path))
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "tftpboot 0x81000000", "Bytes transferred")

        # FIXME: replace flash w/r with initramfs for safe update
        # erase and write flash
        self.pexp.expect_action(90, self.bootloader_prompt, 'erase_ext 26a0000 CB0000')
        self.pexp.expect_action(90, self.bootloader_prompt, 'write_ext 0x81000000 26a0000 CB0000')
        self.pexp.expect_action(90, self.bootloader_prompt, '\033')

    def set_eeprom_info(self):
        log_debug(msg="Set Board ID:" + self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid -f " + self.board_id)
        self.pexp.expect_only(10, 'Done')

        log_debug(msg="Set BOM rev:" + self.bom_rev)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev " + self.bom_rev)
        self.pexp.expect_only(10, 'Done')

        # DUT must have been calibrated otherwise usetrd be failed
        log_debug(msg="Set Regulatory Domain:" + self.region)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd " + self.region)
        self.pexp.expect_only(10, 'Done')

        log_debug(msg="Set MAC:" + self.mac)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac " + self.mac)
        self.pexp.expect_only(10, 'Done')

        log_debug(msg="Clear uboot env")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearenv")
        self.pexp.expect_only(30, 'done')
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearcfg")
        self.pexp.expect_only(30, 'done')

        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uprintenv")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usaveenv")

    def check_eeprom_info(self):
        log_debug(msg="Check eeprom info")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid")
        self.pexp.expect_only(15, self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev")
        self.pexp.expect_only(15, self.bom_rev)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd")
        self.pexp.expect_only(15, self.region)

        # FIXME: check mac or not
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac")

    def login_kernel(self):
        log_debug(msg="Login kernel")
        # self.pexp.expect_action(120, "Please press Enter to activate this console", "")
        time.sleep(60)
        self.pexp.expect_action(30, "", "\n")

        time.sleep(15)  # for stable system

        if self.board_id in ["e618", "e619", "e620"]:
            log_debug(msg="Add IP Addr")
            cmd = "ifconfig"
            exp = "br-lan"
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=exp, retry=60)
            time.sleep(15)
            self.pexp.expect_action(30, "", "\n")
            self.pexp.expect_action(5, self.linux_prompt, "ip addr add {}/24 dev br-lan".format(self.dutip))
            time.sleep(3)
            cmd = "ip addr"
            exp = self.dutip
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=exp, retry=5)
        elif self.board_id in ["dca6", "dca7"]:
            cmd = "/etc/init.d/network start"
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, retry=60)

        self.is_network_alive_in_linux(retry=60, arp_logging_en=True, del_dutip_en=True)
        self.pexp.expect_action(30, self.linux_prompt, "ifconfig br-lan {}".format(self.dutip))
        time.sleep(3)  # for stable eth
        self.is_network_alive_in_linux(retry=10, arp_logging_en=True, del_dutip_en=True)

    def enable_ssh(self):
        self.pexp.expect_action(30, self.linux_prompt, "echo ssh | prst_tool -w misc; /etc/init.d/dropbear start")
        self.pexp.expect_action(60, self.linux_prompt, "")
        log_debug(msg="Enabled SSH")

    def gen_and_upload_ssh_key(self):
        self.gen_rsa_key()
        self.gen_dss_key()

        # Upload the RSA key
        cmd = [
            "tftpboot",
            "80800000",
            self.rsakey
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = [
            self.cmd_prefix,
            "usetsshkey",
            "$fileaddr",
            "$filesize"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)

        # Upload the DSS key
        cmd = [
            "tftpboot",
            "80800000",
            self.dsskey
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        self.pexp.expect_only(15, "Bytes transferred =")

        cmd = [
            self.cmd_prefix,
            "usetsshkey",
            "$fileaddr",
            "$filesize"
        ]
        cmd = ' '.join(cmd)
        self.pexp.expect_action(5, self.bootloader_prompt, cmd)
        log_debug(msg="ssh keys uploaded successfully")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, "", "")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())

    def registration(self, regsubparams=None):
        log_debug("Starting to do registration ...")
        self.devreg_hostname = "stage.udrs.io"
        if regsubparams is None:
            regsubparams = self.access_chips_id()

        clientbin = "/usr/local/sbin/client_rpi4_release"
        regparam = [
            "-h {}".format(self.devreg_hostname),
            "-k {}".format(self.pass_phrase),
            regsubparams,
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

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=code,format=hex,value={}".format(self.qrhex)
            regparam.append(reg_qr_field)

        # The HEX of the activate code
        if self.activate_code is None or not self.activate_code:
            reg_activate_code = ""
        else:
            code_type = "01"
            reg_code_type = "-i field=code_type,format=hex,value={}".format(code_type)
            regparam.append(reg_code_type)
            reg_activate_code = "-i field=code,format=hex,value={}".format(self.activate_code_hex)
            regparam.append(reg_activate_code)

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

    def check_boot_complete(self):
        log_debug("Starting to check DUT boot to complete ...")
        status = False
        t_secs = 90
        dt_last = datetime.now()
        ts = datetime.now() - dt_last
        while ts.seconds <= t_secs:
            output = self.pexp.expect_get_output2("brctl show | grep wlan0", self.linux_prompt, self.linux_prompt, timeout=5)
            log_info('rsp = {}'.format(output))
            if 'br-lan' in output and 'wlan0' in output:
                status = True
                break
            time.sleep(1)
            ts = datetime.now() - dt_last
        if not status:
            otmsg = "Check DUT boot to complete failed!!"
            error_critical(otmsg)

        log_debug("Check DUT boot to complete passed!!")

    def check_wireless_config(self):
        log_debug("Starting to check wireless config ...")
        status = False
        t_secs = 180
        dt_last = datetime.now()
        ts = datetime.now() - dt_last
        while ts.seconds <= t_secs:
            output = self.pexp.expect_get_output2("ls /etc/config/wireless", self.linux_prompt, self.linux_prompt,
                                                  timeout=5)
            if '/etc/config/wireless' in output:
                output = self.pexp.expect_get_output2("tail /etc/config/wireless", self.linux_prompt, self.linux_prompt,
                                                      timeout=5)
                if 'option ubnt_role \'initial_setup\'' in output:
                    status = True
                    break
            time.sleep(1)
            ts = datetime.now() - dt_last
        if not status:
            otmsg = "Check wireless config failed!!"
            error_critical(otmsg)

        log_debug("Check wireless config passed!!")

    def enable_burn_in_mode(self):
        log_debug("Starting to enable burn in mode ...")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "/etc/init.d/ajconf stop")
        time.sleep(1)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "uci set uictld.@uictld[0].lcd_test=1")
        time.sleep(0.5)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "uci commit")
        time.sleep(0.5)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cfg.sh write")
        time.sleep(1)
        for _ in range(3):
            output = self.pexp.expect_get_output2("grep lcd_test /etc/config/uictld", self.linux_prompt,
                                                  self.linux_prompt,
                                                  timeout=5)
            output = str(output).strip()
            if "lcd_test" in output:
                break
            time.sleep(3)
        if "lcd_test" not in output:
            otmsg = "Enable burn in mode failed!!"
            error_critical(otmsg)

        log_debug("Enable burn in mode passed!!")

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        msg(5, "Open serial port successfully ...")

        if self.UPDATE_UBOOT is True:
            msg(20, "Updating uboot ...")
            self.enter_uboot()
            self.update_uboot()
            self.pexp.expect_action(60, self.bootloader_prompt, 'reset')

        if self.PROVISION_ENABLE is True:
            msg(30, "Setting EEPROM ...")
            self.enter_uboot(init_uapp=True)
            self.set_eeprom_info()
            self.pexp.expect_action(30, self.bootloader_prompt, "reset")

            # FIXME: bom-rev goes wrong
            msg(35, "Checking EEPROM ...")
            self.enter_uboot(init_uapp=True)
            self.check_eeprom_info()

            msg(40, "Uploading ssh keys ...")
            self.gen_and_upload_ssh_key()

            self.pexp.expect_action(30, self.bootloader_prompt, "reset")

        if self.BOOT_RECOVERY_IMAGE is True:
            msg(50, "Booting into recovery images...")
            self.enter_uboot()
            self.boot_recovery()

            self.login_kernel()
            self.enable_ssh()

        if self.DOHELPER_ENABLE is True:
            msg(55, "Do helper to get the output file to devreg server ...")
            self.erase_eefiles()
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:
            msg(60, "Doing registration ...")
            self.registration()
            msg(65, "Checking signed file and EEPROM ...")
            self.check_devreg_data()

        if self.FWUPDATE_ENABLE is True:
            msg(80, "Updating firmware ...")
            self.fwupdate()
            self.login_kernel()

            if self.board_id in ["e618", "e619", "e620"]:
                self.check_boot_complete()
                time.sleep(10)

        if self.DATAVERIFY_ENABLE is True:
            msg(90, "Checking the devrenformation ...")
            self.check_info()

        if self.board_id in ["e618", "e619", "e620"]:
            self.check_wireless_config()

            time.sleep(5)

            self.enable_burn_in_mode()

            self.__del__()

        msg(100, "Completed FCD process ...")

        self.close_fcd()


def main():
    uap_qca956x_factory2 = UAPQCA956xFactory2()
    uap_qca956x_factory2.run()


if __name__ == "__main__":
    main()
