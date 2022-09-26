#!/usr/bin/python3
import sys
import time
import os
import stat
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class Retry():
    def __init__(self, _function, max_retry_count=0, delay_time=0):
        self.retry(_function,max_retry_count, delay_time)
    
    def retry(self, _function, max_retry_count, delay_time):
        for i in range(max_retry_count + 1):
            try:
                _function()
                return 
            except Exception as e:
                log_debug('Catch expection "{}" at {}'.format(e, _function.__name__))
            log_debug('Sleep {} seconds'.format(delay_time))
            time.sleep(delay_time)
            log_debug('Retry {}, {} time(s)'.format(_function.__name__, i + 1))
        log_error('Exceed max retry count {}'.format(max_retry_count))
        error_critical('Failed at {}'.format(_function.__name__))


class UNASALPINEFactory(ScriptBase):
    def __init__(self):
        super(UNASALPINEFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # override the base vars
        self.user = "root"
        self.ubpmt = ">"
        self.linux_prompt = ["#"]
        self.wait_LCM_upgrade_en = {'ea20', 'ea21', 'ea51'}
        # script specific vars

        '''
        ea1a: UNVR
        ea20: UNVR-Pro
        ea51: UNAS-Pro
        ea21: UNVR-AI
        ea30: UNVR-HD
        ea50: UNAS
        '''
        self.devregparts = {
            '0000': "/dev/mtdblock9",
            'ea1a': "/dev/mtdblock4",
            'ea20': "/dev/mtdblock4",
            'ea51': "/dev/mtdblock4",
            'ea21': "/dev/mtdblock4",
            'ea30': "/dev/mtdblock4",
            'ea50': "/dev/mtdblock4",
        }
        self.devregpart = self.devregparts[self.board_id]
        self.bomrev = "113-" + self.bom_rev
        self.helperexe = "helper_UNVR-AL324"
        self.dut_nasdir = os.path.join(self.dut_tmpdir, "unas")
        self.helper_path = os.path.join(self.dut_nasdir, self.helperexe)
        self.eepmexe_path = os.path.join(self.dut_nasdir, self.eepmexe)

        # EEPROM related files path on DUT
        self.eesign_dut_path = os.path.join(self.dut_nasdir, self.eesign)
        self.eetgz_dut_path = os.path.join(self.dut_nasdir, self.eetgz)
        self.eechk_dut_path = os.path.join(self.dut_nasdir, self.eechk)
        self.eebin_dut_path = os.path.join(self.dut_nasdir, self.eebin)
        self.eetxt_dut_path = os.path.join(self.dut_nasdir, self.eetxt)

        self.fcd_unasdir = os.path.join(self.tftpdir, "tmp", "unas")

        # number of Ethernet
        self.ethnum = {
            'ea1a': "2",
            'ea20': "2",
            'ea51': "2",
            'ea21': "3",
            'ea30': "2",
            'ea50': "1",
        }

        # number of WiFi
        self.wifinum = {
            'ea1a': "0",
            'ea20': "0",
            'ea51': "0",
            'ea21': "0",
            'ea30': "0",
            'ea50': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ea1a': "1",
            'ea20': "1",
            'ea51': "1",
            'ea21': "1",
            'ea30': "1",
            'ea50': "1",
        }

        self.netif = {
            'ea1a': "ifconfig enp0s1 ",
            'ea20': "ifconfig enp0s1 ",
            'ea51': "ifconfig enp0s1 ",
            'ea21': "ifconfig enp0s1 ",
            'ea30': "ifconfig enp0s1 ",
            'ea50': "ifconfig enp0s2 ",
        }

        self.pkg_name = {
            'ea1a': "",
            'ea20': "factory-test-tools*",
            'ea51': "nvr-lcm-tools*",
            'ea21': "",
            'ea30': "",
            'ea50': "nvr-lcm-tools*",
        }



        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def install_uboot_on_spi(self):
        fcd_spifwpath = os.path.join(self.tftpdir, "unas", "spi.image")
        spi_fw_path = os.path.join(self.tftpdir, "spi.image")
        if not os.path.isfile(spi_fw_path):
            sstr = [
                "cp",
                "-p",
                fcd_spifwpath,
                spi_fw_path
            ]
            sstrj = ' '.join(sstr)
            [sto, rtc] = self.fcd.common.xcmd(sstrj)
            time.sleep(1)
            if int(rtc) > 0:
                error_critical("Copying spi flash to tftp server failed")
            else:
                time.sleep(5)
                log_debug("Copying spi flash to tftp server successfully")
        else:
            log_debug("spi.image is already existed under /tftpboot")

        self.pexp.expect_action(30, self.ubpmt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.ubpmt, "setenv serverip  " + self.tftp_server)
        self.pexp.expect_action(30, self.ubpmt, "ping  " + self.tftp_server)
        self.pexp.expect_only(30, self.tftp_server + " is alive", err_msg="Tftp server is not alive!")

        uboot_fun = 'setenv offset 0x10000000;sf probe;tftpboot ${offset} ${tftpdir}spi.image;if test $? -ne 0; then run fail; exit;fi;if test ${filesize} -ne 2000000;  then echo "Wrong image size";  exit;fi;echo "Wrapping spi flash, DO NOT reboot now!";sf erase 0 0x2000000;echo "Writing spi flash, DO NOT reboot now!";sf write ${offset} 0 ${filesize};echo "SPI flash updated, reset";'
        set_uboot_fun = "setenv spiupd '" + uboot_fun + "'"
        self.pexp.expect_action(30, self.ubpmt, set_uboot_fun)
        self.pexp.expect_action(10, self.ubpmt, "run spiupd")
        msg(15, "Installing fw on spi")
        self.pexp.expect_only(300, "Bytes transferred =", err_msg="Failed get spi.image from tftp server")
        self.pexp.expect_only(60, "Wrapping spi flash", err_msg="No msg of process of installation")
        self.pexp.expect_action(600, "SPI flash updated", "reset", err_msg="No msg of installation completed")

    def install_nand_fw(self):
        fcd_fwpath = os.path.join(self.fwdir, self.board_id + "-fw.bin")
        nand_path_for_dut = os.path.join(self.tftpdir, "fw-image.bin")
        cmd = "cp -p {} {}".format(fcd_fwpath, nand_path_for_dut)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Copying nand flash to tftp server failed")

        self.pexp.expect_action(30, self.ubpmt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.ubpmt, "setenv serverip  " + self.tftp_server)
        self.is_network_alive_in_uboot(retry=9, timeout=5)

        # clean up config block
        self.pexp.expect_action(30, self.ubpmt, "sf probe; sf erase 0x01200000 0x1000")
        self.pexp.expect_only(60, "Erased: OK", err_msg="Erase config failed")

        self.pexp.expect_action(30, self.ubpmt, "setenv bootargsextra 'factory server={} client={}'".format(self.tftp_server, self.dutip))
        self.pexp.expect_action(10, self.ubpmt, "run bootcmdspi")
        msg(15, "Installing fw on nand")
        self.pexp.expect_only(10, "bootargs=", err_msg="Cannot see reboot msg after enter boot cmd in uboot")
        self.pexp.expect_only(10, "Starting kernel", err_msg="No msg of process of installation")

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")
        sstr = [
            self.helper_path,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname=" + self.eebin_dut_path,
            ">",
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "cf",
            self.eetgz_dut_path,
            self.eebin_dut_path,
            self.eetxt_dut_path
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        os.mknod(self.eetgz_path)
        os.chmod(self.eetgz_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        log_debug("Send helper output tgz file from DUT to host ...")
        sstr = [
            "tftp",
            "-p",
            "-r " + self.eetgz,
            "-l " + self.eetgz_dut_path,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)
        self.pexp.expect_only(10, self.linux_prompt)
        time.sleep(1)

        sstr = [
            "tar",
            "xvf " + self.eetgz_path,
            "-C " + self.tftpdir
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Decompressing " + self.eetgz_path + " file failed!!")
        else:
            log_debug("Decompressing " + self.eetgz_path + " files successfully")
        eetxt = os.path.join(self.fcd_unasdir, self.eetxt)
        eebin = os.path.join(self.fcd_unasdir, self.eebin)
        sstr = [
            "mv",
            eetxt,
            self.eetxt_path
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        sstr = [
            "mv",
            eebin,
            self.eebin_path
        ]
        sstrj = ' '.join(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)

    def fwupdate(self):
        fcd_fwpath = os.path.join(self.image, self.board_id + "-fw.bin")
        fwpath = os.path.join(self.dut_tmpdir, "firmware.bin")
        sstr = [
            "tftp",
            "-g",
            "-r " + fcd_fwpath,
            "-l " + fwpath,
            self.tftp_server
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, sstrj)

        log_debug("Starting to do fwupdate ... ")
        sstr = [
            "ubntnas",
            "system",
            "upgrade",
            fwpath
        ]
        sstrj = ' '.join(sstr)
        self.pexp.expect_action(300, self.linux_prompt, sstrj)
        self.pexp.expect_only(60, "Restarting system")

    def check_info(self):
        """under developing
        """
        self.pexp.expect_action(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno error")

    def wait_lcm_upgrade(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "/usr/share/lcm-firmware/lcm-fw-info /dev/ttyACM0", post_exp="md5", retry=24)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "")

    def copy_rename_uImage_to_tftpboot(self):
        uImage = 'uImage'
        fcd_spifwpath = os.path.join(self.tftpdir, self.board_id, uImage)
        spi_fw_path = os.path.join(self.tftpdir, uImage)
        if not os.path.isfile(spi_fw_path):
            sstr = [
                "cp",
                "-p",
                fcd_spifwpath,
                spi_fw_path
            ]
            sstrj = ' '.join(sstr)
            [sto, rtc] = self.fcd.common.xcmd(sstrj)
            time.sleep(1)
            if int(rtc) > 0:
                error_critical("Copying {} to tftp server failed".format(uImage))
            else:
                time.sleep(5)
                log_debug("Copying {} to tftp server successfully".format(uImage))
        else:
            log_debug("{} is already existed under /tftpboot".format(uImage))

    def set_tftp_at_uboot(self):
        self.pexp.expect_action(30, self.ubpmt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.ubpmt, "setenv serverip  " + self.tftp_server)
        self.is_network_alive_in_uboot(retry=9, timeout=5)
    
    def pull_uImage_from_fcd_server(self, dut_nc_ip):
        cmd = 'setenv ipaddr {}; setenv serverip {}; setenv bootargsextra \'client={} server={} factory nc_transfer\'; run bootcmdtftp'.format(self.dutip, self.tftp_server, self.dutip, self.tftp_server)
        self.pexp.expect_action(30, self.ubpmt, cmd)
        self.pexp.expect_only(300, "Bytes transferred =", err_msg="Failed get uImage from tftp server")

    def fcd_host_shell(self, cmd):
        log_debug('FCD host shell: "{}"'.format(cmd))
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("{} failed".format(cmd))
        else:
            time.sleep(5)
            log_debug("{} successfully".format(cmd))

    def fcd_server_send_firmware_by_nc(self, cmd):
        self.fcd_host_shell(cmd)
    
    def pull_firmware_by_nc(self, firmware_file_name, dut_nc_ip, dut_nc_port='5566'):
        cmd = 'nc -N {} {} < {}'.format(dut_nc_ip, dut_nc_port, firmware_file_name)
        nc_ready_message = 'Wait for nc client to push firmware to {}:{} ...'.format(dut_nc_ip, dut_nc_port)
        self.pexp.expect_only(300, nc_ready_message, err_msg="Failed at {}".format(nc_ready_message))
        self.fcd_server_send_firmware_by_nc(cmd)

    def install_firmware_on_emmc(self):
        self.copy_rename_uImage_to_tftpboot()
        self.set_tftp_at_uboot()
        self.pull_uImage_from_fcd_server(dut_nc_ip=self.dutip)
        fcd_fwpath = os.path.join(self.fwdir, self.board_id + "-fw.bin")
        self.pull_firmware_by_nc(firmware_file_name=fcd_fwpath, dut_nc_ip=self.dutip)

    def clear_shell(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "")

    def reboot(self):
        self.clear_shell()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
    
    def sleep_with_message(self, sleep_time, message=None):
        if message: log_debug('Sleep {} seconds for {}'.format(message))
        time.sleep(sleep_time)

    def set_fake_sysid(self):
        self.pexp.expect_action(300, "Autobooting in 2 seconds, press", "\x1b\x1b")
        self.pexp.expect_ubcmd(10, self.ubpmt, "sf probe")
        self.pexp.expect_ubcmd(10, self.ubpmt, "mw.l 0x08000000 544e4255")

        if self.board_id == "ea50":
            self.pexp.expect_ubcmd(10, self.ubpmt, "mw.l 0x0800000c 770750ea")
            self.pexp.expect_ubcmd(10, self.ubpmt, "mw.l 0x08000010 50ea7707")
        else:
            self.pexp.expect_ubcmd(10, self.ubpmt, "mw.l 0x0800000c 770751ea")
            self.pexp.expect_ubcmd(10, self.ubpmt, "mw.l 0x08000010 51ea7707")
        self.pexp.expect_ubcmd(10, self.ubpmt, "sf erase 0x1f0000 0x9000")
        self.pexp.expect_only(30, "Erased: OK")
        self.pexp.expect_ubcmd(10, self.ubpmt, "sf write 0x08000000 0x1f0000 0x20")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.ubpmt, "sf write 0x08000000 0x1f8000 0x20")
        self.pexp.expect_only(30, "Written: OK")
        self.pexp.expect_ubcmd(10, self.ubpmt, "reset")

    def set_network_in_kernel(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip)
        time.sleep(2)

        cmd = "ping -c 5 {}".format(self.tftp_server)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, ["64 bytes from"])

    def load_pkg_tool(self):
        self.set_network_in_kernel()
        src_file = os.path.join(self.fcd_toolsdir, self.board_id, self.pkg_name[self.board_id])
        self.scp_get(dut_user=self.user, dut_pass=self.password, dut_ip=self.dutip, src_file=src_file, dst_file=self.dut_tmpdir)
        cmd = "dpkg -i /tmp/"+ self.pkg_name[self.board_id]
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

    def run(self):
        """main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        INSTALL_SPI_FLASH = False  # this is temp solution, will remove after next build
        INSTALL_NAND_FW_ENABLE = True
        PROVISION_ENABLE = True
        DOHELPER_ENABLE = True
        REGISTER_ENABLE = True
        FWUPDATE_ENABLE = False
        DATAVERIFY_ENABLE = True
        if self.board_id == 'ea1a' or self.board_id == 'ea50':
            WAIT_LCMUPGRADE_ENABLE = False
        else:
            WAIT_LCMUPGRADE_ENABLE = True

        if self.board_id == 'ea51' or self.board_id == 'ea50':
            msg(3, 'Set fake sysid in uboot')
            self.set_fake_sysid()
        
        if INSTALL_SPI_FLASH is True:
            msg(5, "Boot to u-boot console and install spi flash...")
            self.pexp.expect_action(300, "Autobooting in 2 seconds, press", "\x1b\x1b")  # \x1b is esc key
            self.install_uboot_on_spi()  # will be rebooting after installation

        if INSTALL_NAND_FW_ENABLE is True:
            msg(10, "Boot to u-boot console and install nand flash...")
            self.pexp.expect_action(300, "Autobooting in 2 seconds, press", "\x1b\x1b")  # \x1b is esc key
            if self.board_id == 'ea51'or self.board_id == 'ea50':
                self.install_firmware_on_emmc()
            else:
                self.install_nand_fw()  # will be rebooting after installation

        msg(30, "Waiting boot to linux console...")
        if self.board_id == 'ea51' or self.board_id == 'ea50':
            self.login(timeout=300)
        else:
            self.pexp.expect_only(300, "Welcome to UniFi NVR!")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, self.netif[self.board_id] + self.dutip)
        time.sleep(2)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, ["64 bytes from"])
        msg(35, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(40, "Send tools to DUT and data provision ...")
            self.copy_and_unzipping_tools_to_dut(timeout=30)
            self.data_provision_64k(netmeta=self.devnetmeta)

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(45, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(60, "Finish doing registration ...")
            self.check_devreg_data(dut_tmp_subdir="unas")
            msg(70, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            self.pexp.expect_action(300, "login:", self.user)
            self.pexp.expect_action(15, "Password:", self.password)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n 1")
            msg(80, "Succeeding in downloading the fw file ...")
        else:
            self.pexp.expect_action(30, self.linux_prompt, "reboot")
            msg(85, "Waiting boot to linux console...")
            if self.board_id == 'ea51' or self.board_id == 'ea50':
                self.login(timeout=300)
            else:
                self.pexp.expect_only(300, "Welcome to UniFi NVR!")

        if DATAVERIFY_ENABLE is True:
            if self.board_id == 'ea51' or self.board_id == 'ea50':
                self.clear_shell()

            Retry(self.check_info, max_retry_count=3, delay_time=1)
            msg(90, "Succeeding in checking the devreg information ...")

        if WAIT_LCMUPGRADE_ENABLE is True:
            if self.board_id == 'ea50' or self.board_id == 'ea51':
                self.load_pkg_tool()
            if self.board_id in self.wait_LCM_upgrade_en:
                msg(95, "Waiting LCM upgrading ...")
                self.wait_lcm_upgrade()

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()

def main():
    unas_alpine_factory = UNASALPINEFactory()
    unas_alpine_factory.run()

if __name__ == "__main__":
    main()
