#!/usr/bin/python3
import re
import sys
import os
import time
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class USFactoryGeneral(ScriptBase):
    """
    command parameter description for security registration
    command: python3
    para0:   script
    para1:   slot ID
    para2:   UART device number
    para3:   FCD host IP
    para4:   system ID (board ID)
    para5:   MAC address
    para6:   passphrase
    para7:   key directory
    para8:   BOM revision
    para9:   QR code
    para10:  Region Code
    ex: ['1', 'ttyUSB1', 192.168.1.7', 'eb23', 'b4fbe451f2ba', '4w3IYmVMHKzj', '/media/chike/Ubuntu 18.04.1 LTS amd64/keys/',
    '02604-20', 'mYvJIK', '0000']
    """
    def __init__(self):
        super(USFactoryGeneral, self).__init__()

    def sf_erase(self, address, erase_size):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string}
        """
        log_debug(msg="Initializing sf => sf probe")
        self.pexp.expect_action(timeout=10, exptxt="", action="sf probe")
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)

        earse_cmd = "sf erase " + address + " " + erase_size
        log_debug(msg="run cmd " + earse_cmd)
        self.pexp.expect_action(timeout=10, exptxt="", action=earse_cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)

    def stop_uboot(self, timeout=30):
        if self.pexp is None:
            error_critical(msg="No pexpect obj exists!")
        else:
            log_debug(msg="Stopping U-boot")
            self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot", action="")
            self.pexp.expect_action(timeout=timeout, exptxt=self.bootloader_prompt, action="")

    def uclearcfg(self):
        """
        run cmd : uclearcfg
        clear linux config data
        """
        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uclearcfg")
        self.pexp.expect_only(timeout=20, exptxt="Done.")
        self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)
        log_debug(msg="Linux configuration erased")

    def cleanup_old_reg_related_files(self, files):
        """cleanup old files on both Host and DUT
        after cleanup files, change dir to /tftpboot on host; /tmp on du
        """
        for filekey in files:
            file_path_host = "/tftpboot/" + files[filekey]
            file_path_dut = "/tmp/" + files[filekey]
            if os.path.isfile(file_path_host):
                self.fcd.common.xcmd("rm -f " + file_path_host)
            cmd = r"[ ! -f " + file_path_dut + r" ] || rm " + file_path_dut
            self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
            self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
        os.chdir(path="/tftpboot")
        self.pexp.expect_action(timeout=10, exptxt="", action="cd /tmp")
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)

    def update_firmware_in_uboot(self):
        """
        use urescue to update firmwre,
        after flash firmware, DU will be resetting
        """
        self.pexp.expect_action(timeout=10, exptxt="", action="setenv do_urescue TRUE; urescue")
        extext_list = ["TFTPServer started. Wating for tftp connection...",
                       "Listening for TFTP transfer"]
        index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to start urescue")
        elif index == 0 or index == 1:
            log_debug(msg="TFTP is waiting for file")
        atftp_cmd = "atftp --option \"mode octet\" -p -l {0}/{1}/{2} {3}".format(
                                                                                self.tftpdir,
                                                                                "images",
                                                                                self.fwimg,
                                                                                self.var.us.ip)
        log_debug(msg="Run cmd on host:" + atftp_cmd)
        self.fcd.common.xcmd(cmd=atftp_cmd)
        self.pexp.expect_only(timeout=150, exptxt=self.bootloader_prompt)
        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uwrite -f")
        self.pexp.expect_only(timeout=20, exptxt="Firmware Version:")
        index = self.pexp.expect_get_index(timeout=300, exptxt="Copying to 'kernel0' partition. Please wait... :  done")
        msg(no=75, out="Firmware flashed on kernal0")
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to flash firmware.")
        index = self.pexp.expect_get_index(timeout=300, exptxt="Firmware update complete.")
        if index == self.pexp.TIMEOUT:
            error_critical(msg="Failed to flash firmware.")
        msg(no=90, out="Firmware update complete.")
        self.pexp.expect_only(timeout=150, exptxt="Starting kernel")

    def is_network_alive_in_uboot(self, retry=1):
        is_alive = False
        for _ in range(retry):
            time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="ping " + self.tftp_server)
            extext_list = ["host " + self.tftp_server + " is alive"]
            index = self.pexp.expect_get_index(timeout=60, exptxt=extext_list)
            if index == 0:
                is_alive = True
                break
            elif index == self.pexp.TIMEOUT:
                is_alive = False
        return is_alive

    def decide_uboot_env_mtd_memory(self):
        """
        decide by output of cmd [print mtdparts]
        Returns:
            [string, string] -- address, size
        """
        self.pexp.expect_action(timeout=10, exptxt="", action="print mtdparts")
        self.pexp.expect_only(timeout=10, exptxt=self.bootloader_prompt)
        output = self.pexp.proc.before
        if self.var.us.flash_mtdparts_64M in output:
            self.var.us.use_64mb_flash = 1
            return ("0x1e0000", "0x10000")  # use 64mb flash
        else:
            return ("0xc0000", "0x10000")

    def decide_bootargs(self, board_id=None):
        bootargs = None
        if board_id.lower() is self.var.us.USW_XG.lower():
            bootargs = "quiet console=ttyS0,115200 mem=496M " + self.var.us.flash_mtdparts_64M
        elif board_id.lower() in [
                                self.var.us.USW_24_PRO.lower(),
                                self.var.us.USW_48_PRO.lower(),
                                self.var.us.USW_6XG_150.lower()]:
            bootargs = "quiet console=ttyS0,115200 mem=1008M " + self.var.us.flash_mtdparts_64M
        elif self.var.us.use_64mb_flash is 1:
            bootargs = "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.var.us.flash_mtdparts_64M
        else:
            bootargs = "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.var.us.flash_mtdparts_32M
        if bootargs is not None:
            return bootargs
        else:
            error_critical(msg="Cannot decide bootargs")

    def set_bootargs_and_run_bootcmd(self):
        bootargs = self.decide_bootargs(board_id=self.board_id)
        self.pexp.expect_action(timeout=10, exptxt="", action="setenv bootargs '" + bootargs + "'")
        self.pexp.expect_only(timeout=15, exptxt=self.bootloader_prompt)
        self.pexp.expect_action(timeout=10, exptxt="", action="run bootcmd")
        self.pexp.expect_only(timeout=150, exptxt="Starting kernel")

    def set_board_info_in_uboot(self):
        cmd = "{0}usetbid {1}".format(self.cmd_prefix, self.board_id)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)

        cmd = "{0}usetbrev {1}".format(self.cmd_prefix, self.bom_rev)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)

        cmd = "{0}usetbrev".format(self.cmd_prefix)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)

    def check_board_info_in_uboot(self):
        """check board id/ bom revision/ mac address
        """
        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "usetbid")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        match = re.search(r"Board ID: (.{4})", self.pexp.proc.before)
        board_id = None
        if match:
            board_id = match.group(1)
        else:
            error_critical(msg="Found no Board ID info by regular expression. Please checkout output")
        if board_id != self.board_id:
            error_critical(msg="Board ID doesn't match!")

        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "usetbrev")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        match = re.search(r"BOM Rev: (\d+-\d+)", self.pexp.proc.before)
        bom_rev = None
        if match:
            bom_rev = match.group(1)
        else:
            error_critical(msg="Found no BOM Revision info by regular expression. Please checkout output")
        if bom_rev != self.bom_rev:
            error_critical(msg="BOM Revision  doesn't match!")

        self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "usetmac")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        match = re.search(
                        r"MAC0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*MAC1: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2})",
                        self.pexp.proc.before,
                        re.S)
        mac_0 = None
        mac_1 = None
        mac_input = self.mac
        mac_input_processed = mac_input
        if match:
            mac_0 = match.group(1).replace(":", "")
            mac_1 = match.group(2).replace(":", "")
            mac_input.replace(":", "")
            # take mac_input[1:2] to do OR with 0x2, then replace and generate processed string with new value at [1:2]
            final_hex = hex(int(mac_input[1:2], 16) | 0x2)
            mac_input_processed = mac_input_processed[:1] + str(final_hex[2:3]) + mac_input_processed[2:]
        else:
            error_critical(msg="Found no mac info by regular expression. Please checkout output")
        if mac_0 != mac_input or mac_1 != mac_input_processed:
            error_critical(msg="MAC address doesn't match!")

    def set_mac_info_in_uboot(self):
        cmd = "{0}usetmac {1}".format(self.cmd_prefix, self.mac)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=10, exptxt=self.bootloader_prompt)

        cmd = "{0}usetmac".format(self.cmd_prefix)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=10, exptxt=self.bootloader_prompt)
        output = self.pexp.proc.before
        match = re.search(r"MAC0: (.{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2}[-:].{2})", output)
        mac_str = None
        if match:
            mac_str = match.group(1)
        else:
            error_critical(msg="Found no mac info by regular expression. Please checkout output")
        cmd = "setenv ethaddr {0}; saveenv".format(mac_str)
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        log_debug(msg="MAC setting succeded")

    def set_network_env_in_uboot(self):
        is_network_alive = False
        for _ in range(3):
            if self.board_id in self.var.us.usw_group_1:
                self.pexp.expect_action(timeout=10, exptxt="", action="mdk_drv")
                self.pexp.expect_only(timeout=30, exptxt=self.bootloader_prompt)
                time.sleep(3)
            self.pexp.expect_action(timeout=10, exptxt="", action="setenv serverip " + self.tftp_server)
            self.pexp.expect_action(
                                    timeout=10, exptxt=self.bootloader_prompt, action="setenv ipaddr " +
                                    self.var.us.ip)
            is_network_alive = self.is_network_alive_in_uboot(retry=3)
            if is_network_alive is False:
                self.pexp.expect_action(timeout=10, exptxt="", action="re")
                self.stop_uboot(timeout=60)
            else:
                break
        if is_network_alive is False:
            error_critical(msg=self.tftp_server + " is not reachable.")
        self.pexp.expect_action(timeout=10, exptxt="", action="")
        self.pexp.expect_only(timeout=10, exptxt=self.bootloader_prompt)

    def setup_env(self):
        self.set_board_info_in_uboot()
        msg(no=10, out="Board ID/Revision set")
        (uboot_env_address, uboot_env_address_size) = self.decide_uboot_env_mtd_memory()
        log_debug(msg="Erasing uboot-env")
        self.sf_erase(address=uboot_env_address, erase_size=uboot_env_address_size)
        self.uclearcfg()
        msg(no=15, out="Configuration erased")
        self.set_mac_info_in_uboot()
        self.pexp.expect_action(timeout=10, exptxt="", action="re")
        self.stop_uboot()
        self.pexp.expect_action(timeout=10, exptxt="", action="printenv")
        self.pexp.expect_only(timeout=15, exptxt=self.bootloader_prompt)
        self.pexp.expect_action(timeout=10, exptxt="", action="saveenv")
        self.pexp.expect_only(timeout=15, exptxt=self.bootloader_prompt)
        msg(no=20, out="Environment Variables set")
        self.set_network_env_in_uboot()

    def gen_and_upload_ssh_key_on_board(self):
        full_path_rsa_key = "/tftpboot/" + self.var.us.rsa_key + self.row_id
        full_path_dss_key = "/tftpboot/" + self.var.us.dss_key + self.row_id

        self.fcd.common.xcmd(cmd="rm -f " + full_path_rsa_key)
        self.fcd.common.xcmd(cmd="rm -f " + full_path_dss_key)
        self.fcd.common.xcmd(cmd="dropbearkey -t rsa -f " + full_path_rsa_key)
        self.fcd.common.xcmd(cmd="dropbearkey -t dss -f " + full_path_dss_key)
        [_, return_code] = self.fcd.common.xcmd(cmd="sudo chmod +r " + full_path_rsa_key)
        if return_code != 0:
            error_critical(msg="Failing in rsa key generation.")
        self.fcd.common.xcmd(cmd="sudo chmod +r " + full_path_dss_key)
        [_, return_code] = self.fcd.common.xcmd(cmd="sudo chmod +r " + full_path_dss_key)
        if return_code != 0:
            error_critical(msg="Failing in dss key generation.")

        dl_addr = "0x01000000"
        rsa_key_on_board = self.var.us.rsa_key + self.row_id
        self.pexp.expect_action(timeout=5, exptxt="", action="tftpboot " + dl_addr + " " + rsa_key_on_board)
        self.pexp.expect_only(timeout=15, exptxt="Bytes transferred =")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        '''Currently, seems $fileaddr and $filesize are been hardcoded in ubnt apps tool.
        So, in the logs it will be showing blank for these two variables but we can use setenv in uboot to
        use our customed fileaddr and filesize if we wouldd like to in the future'''
        set_ssh_cmd = self.cmd_prefix + r"usetsshkey $fileaddr $filesize"
        self.pexp.expect_action(timeout=5, exptxt="", action=set_ssh_cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        dss_key_on_board = self.var.us.dss_key + self.row_id
        self.pexp.expect_action(timeout=15, exptxt="", action="tftpboot " + dl_addr + " " + dss_key_on_board)
        self.pexp.expect_only(timeout=15, exptxt="Bytes transferred =")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        set_ssh_cmd = self.cmd_prefix + r"usetsshkey $fileaddr $filesize"
        self.pexp.expect_action(timeout=5, exptxt="", action=set_ssh_cmd)
        self.pexp.expect_only(timeout=15, exptxt="Done.")
        self.pexp.expect_only(timeout=5, exptxt=self.bootloader_prompt)
        log_debug(msg="ssh keys uploaded successfully")

    """lrzsz helper functions"""
    def _host_send(self, filename):
        self.fcd.common.xcmd(
                            cmd="sz -e -v -b " + filename + " > /dev/" + self.dev + " < /dev/" +
                            self.dev)

    def _host_receive(self):
        self.fcd.common.xcmd(cmd="rz -v -b -y < /dev/" + self.dev + " > /dev/" + self.dev)

    def _check_host_file_exist(self, filepath):
        if not os.path.isfile(filepath):
            error_critical(msg="File: " + filepath + " is not exist!")

    def _dut_send(self, filename):
        self.pexp.expect_action(timeout=5, exptxt="", action="lsz -e -v -b " + filename)

    def _dut_receive(self):
        self.pexp.expect_action(timeout=5, exptxt="", action="lrz -v -b")
    """end region of lrzsz helper functions"""

    def run_client_x86(self, reg_files):
        """it's process which helps communicate and sign device
        """
        sign_cmd = r"/usr/local/sbin/client_x86_release $(cat /tftpboot/{0} | \
                    sed -r -e 's~^field=(.*)$~-i field=\1 ~g' | \
                    grep -v 'eeprom' | tr '\n' ' ') \
                    -h devreg-prod.ubnt.com \
                    -i field=qr_code,format=hex,value={1} \
                    -i field=flash_eeprom,format=binary,pathname=/tftpboot/{2} \
                    -o field=flash_eeprom,format=binary,pathname=/tftpboot/{3} \
                    -k {4} \
                    -o field=registration_id \
                    -o field=result \
                    -o field=device_id \
                    -o field=registration_status_id \
                    -o field=registration_status_msg \
                    -o field=error_message \
                    -x '{5}'/ca.pem \
                    -y '{5}'/key.pem \
                    -z '{5}'/crt.pem " \
                    .format(reg_files["eeprom_txt"],
                            self.var.us.qrcode_hex,
                            reg_files["eeprom_bin"],
                            reg_files["eeprom_signed"],
                            self.pass_phrase,
                            self.key_dir)
        [stdout, returncode] = self.fcd.common.xcmd(sign_cmd)
        if returncode != 0:
            error_critical(msg="Registration failure:" + str(stdout))

    def gen_eeprom_check_file(self, reg_files):
        cmd = None
        if self.var.us.use_64mb_flash == 1:
            cmd = r"dd of=/dev/`awk -F: '/EEPROM/{print $1}' /proc/mtd | \
                    sed 's~mtd~mtdblock~g'` if=/tmp/" + reg_files["eeprom_signed"]
        else:
            cmd = self.var.us.get_helper(self.board_id) + \
                    r" -q -i field=flash_eeprom,format=binary,pathname=" + \
                    reg_files["eeprom_signed"]
        self.pexp.expect_action(timeout=5, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)

        cmd = r"dd if=/dev/`awk -F: '/EEPROM/{print $1}' /proc/mtd  | \
                sed 's~mtd~mtdblock~g'` of=/tmp/" + reg_files["eeprom_check"]
        self.pexp.expect_action(timeout=5, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)

    def do_register_process(self):
        """after registeration process, board will be rebooting
        """
        reg_files = {
                    "eeprom_bin": "e.b." + self.row_id,
                    "eeprom_txt": "e.t." + self.row_id,
                    "eeprom_tgz": "e." + self.row_id + ".tgz",
                    "eeprom_signed": "e.s." + self.row_id,
                    "eeprom_check": "e.c." + self.row_id,
                    "e_s_gz": "e.s." + self.row_id + ".gz",
                    "e_c_gz": "e.c." + self.row_id + ".gz"}

        self.cleanup_old_reg_related_files(reg_files)
        eeprom_gen_cmd = "\
                        {0} -q -c product_class=bcmswitch -o field=flash_eeprom,format=binary,pathname={1} > {2}"\
                        .format(self.var.us.get_helper(self.board_id), reg_files["eeprom_bin"], reg_files["eeprom_txt"])
        self.pexp.expect_action(timeout=20, exptxt="", action=eeprom_gen_cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
        tar_cmd = "tar zcf {0} {1} {2}".format(reg_files["eeprom_tgz"], reg_files["eeprom_bin"], reg_files["eeprom_txt"])
        self.pexp.expect_action(timeout=20, exptxt="", action=tar_cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)

        log_debug(msg="Sending raw eeprom file to host")
        self._dut_send(filename=reg_files["eeprom_tgz"])
        self._host_receive()
        self.pexp.expect_only(timeout=200, exptxt=self.linux_prompt)
        self._check_host_file_exist(filepath="/tftpboot/" + reg_files["eeprom_tgz"])
        self.fcd.common.xcmd(cmd="tar zxf " + reg_files["eeprom_tgz"])
        self._check_host_file_exist(filepath="/tftpboot/" + reg_files["eeprom_bin"])
        self._check_host_file_exist(filepath="/tftpboot/" + reg_files["eeprom_txt"])

        self.run_client_x86(reg_files=reg_files)
        self.fcd.common.xcmd(cmd="gzip " + reg_files["eeprom_signed"])

        log_debug(msg="Sending eeprom signed file to board")
        self._dut_receive()
        self._host_send(filename=reg_files["e_s_gz"])
        self.pexp.expect_only(timeout=200, exptxt=self.linux_prompt)
        self.pexp.expect_action(timeout=5, exptxt="", action="gunzip " + reg_files["e_s_gz"])
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
        self.gen_eeprom_check_file(reg_files=reg_files)

        log_debug(msg="Sending eeprom check file to host")
        self.pexp.expect_action(timeout=5, exptxt="", action="gzip " + reg_files["eeprom_check"])
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
        self._dut_send(filename=reg_files["e_c_gz"])
        self._host_receive()
        self.pexp.expect_only(timeout=200, exptxt=self.linux_prompt)
        self._check_host_file_exist(filepath="/tftpboot/" + reg_files["e_c_gz"])
        self.fcd.common.xcmd(cmd="gunzip " + reg_files["e_c_gz"])
        self.fcd.common.xcmd(cmd="gunzip " + reg_files["e_s_gz"])
        self._check_host_file_exist(filepath="/tftpboot/" + reg_files["eeprom_check"])
        self._check_host_file_exist(filepath="/tftpboot/" + reg_files["eeprom_signed"])

        compare_cmd = "/usr/bin/cmp  /tftpboot/{0}  /tftpboot/{1}".format(reg_files["eeprom_signed"],
                                                                          reg_files["eeprom_check"])
        [_, returncode] = self.fcd.common.xcmd(cmd=compare_cmd)
        if returncode != 0:
            error_critical(msg="EEPROM check failed")
        self.pexp.expect_action(timeout=5, exptxt="", action="reboot")
        self.pexp.expect_only(timeout=10, exptxt=self.linux_prompt)
        self.pexp.expect_action(timeout=5, exptxt="", action="exit")
        log_debug(msg="EEPROM check OK...")

    def check_board_signed(self):
        cmd = r"grep -c flashSize /proc/ubnthal/system.info"
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
        output = self.pexp.proc.before
        match = re.search(r'(\d+)', output)
        if match:
            if int(match.group(1)) is not 1:
                error_critical(msg="Device Registration check failed!")
        else:
            error_critical(msg="Unable to get flashSize!, please checkout output by grep")

        cmd = r"grep qrid /proc/ubnthal/system.info"
        self.pexp.expect_action(timeout=10, exptxt="", action=cmd)
        self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
        output = self.pexp.proc.before
        match = re.search(r'qrid=(.*)', output)
        if match:
            if str(
                    match.group(1)).strip().strip("\n") != \
                    self.qrcode.strip().strip("\n"):
                error_critical(msg="QR code doesn't match!")
        else:
            error_critical(msg="Unable to get qrid!, please checkout output by grep")
        msg(no=95, out="Device Registration check OK...")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="qrcode_hex=" + self.var.us.qrcode_hex)
        cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
        [sto, _] = self.fcd.common.xcmd(cmd)
        if (int(sto) > 0):
            error_critical("Caps Lock is on")

        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(no=1, out="Waiting - PULG in the device...")
        index = self.pexp.expect_get_index(timeout=60, exptxt="U-Boot")
        if index == 0:
            self.stop_uboot()
            msg(no=5, out="Go into U-boot")
            self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uappinit")
            self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)
            log_debug(msg="Initialize ubnt app by uappinit")
            self.setup_env()
            self.gen_and_upload_ssh_key_on_board()
            msg(no=25, out="SSH keys uploaded")
            self.check_board_info_in_uboot()
            msg(no=30, out="Board ID/MAC address checked")
            self.set_bootargs_and_run_bootcmd()
            self.pexp.expect_action(timeout=120, exptxt="Please press Enter to activate this console.", action="")
            self.login()
            self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
            self.do_register_process()
            msg(no=60, out="Rebooting")
            self.stop_uboot()
            self.pexp.expect_action(timeout=10, exptxt="", action=self.cmd_prefix + "uappinit")
            self.pexp.expect_only(timeout=20, exptxt=self.bootloader_prompt)
            log_debug(msg="Initialize ubnt app by uappinit")
            self.set_network_env_in_uboot()
            self.update_firmware_in_uboot()
            self.pexp.expect_action(timeout=120, exptxt="Please press Enter to activate this console.", action="")
            self.login()
            self.pexp.expect_only(timeout=20, exptxt=self.linux_prompt)
            self.check_board_signed()
            msg(no=100, out="Formal firmware completed with MAC0: " + self.mac)

        elif index == self.pexp.TIMEOUT:
            error_critical(msg="Device not found!")


def main():
    us_factory_general = USFactoryGeneral()
    us_factory_general.run()

if __name__ == "__main__":
    main()
