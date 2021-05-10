#!/usr/bin/python3
import time
import os
import stat
from script_base import ScriptBase
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical

UBOOTUPDATE_ENABLE = True
UBOOTWRITEINFO_ENABLE = True
WRITESSHKEY_ENABLE = False
PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True
UPLOADLOG_ENABLE = False  # When uploadlog test stable, will merge this feature into script_base

class UNMSQCA9563Factory(ScriptBase):
    def __init__(self):
        super(UNMSQCA9563Factory, self).__init__()
        self.init_vars()

    def init_vars(self):

        self.ubpmt = {
            '0000': "ath>",
            'dca2': "ath>",
            'dca3': "ath>"
        }

        self.bootloader_img = {
            '0000': "dca3-bootloader.bin",
            'dca2': "dca2-bootloader.bin",
            'dca3': "dca3-bootloader.bin"
        }

        self.ubaddr = {
            '0000': "0x9f000000",
            'dca2': "0x9f000000",
            'dca3': "0x9f000000"
        }

        self.eepromaddr = {
            '0000': "0x9f090000",
            'dca2': "0x9f090000",
            'dca3': "0x9f090000"
        }

        self.eepromsize = {
            '0000': "+10000",
            'dca2': "+10000",
            'dca3': "+10000"
        }

        self.cfgaddr = {
            '0000': "0x9f0c0000",
            'dca2': "0x9f0c0000",
            'dca3': "0x9f0c0000"
        }

        self.cfgsize = {
            '0000': "+340000",
            'dca2': "+340000",
            'dca3': "+340000"
        }

        # number of mac
        self.macnum = {
            'dca2': "2",
            'dca3': "2"
        }

        # number of WiFi
        self.wifinum = {
            'dca2': "0",
            'dca3': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'dca2': "1",
            'dca3': "1"
        }

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

        # script specific vars
        self.bomrev = "113-" + self.bom_rev

        self.cmd_prefix = "go 0x80200020 "
        self.bootloader_prompt = self.ubpmt[self.board_id]
        self.bootloader = self.bootloader_img[self.board_id]
        self.uboot_address = self.ubaddr[self.board_id]
        self.bootenv_address = "0x9f080000"
        self.bootenv_size = "+10000"
        self.eeprom_address = self.eepromaddr[self.board_id]
        self.eeprom_size = self.eepromsize[self.board_id]
        self.cfg_address = self.cfgaddr[self.board_id]
        self.cfg_size = self.cfgsize[self.board_id]

        self.helper_path = "unms-lte"
        self.helperexe = "helper_ARxxxx_debug"
        self.devregpart = "/dev/mtdblock2"
        self.user = "root"

        self.linux_prompt = "# "
        
        self.product_class = "basic"  # For this product using radio

        #self.FCD_TLV_data = False

    def enter_uboot(self):
        self.pexp.expect_action(300, "Hit any key to", "")
        time.sleep(2)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix+ "uappinit" )
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_lnxcmd(10, self.bootloader_prompt,  "ping " + self.tftp_server, "host " + self.tftp_server + " is alive",  retry=5 )

    def fromOS_retest(self):
        self.pexp.expect_action(5, " ", "")
        self.pexp.expect_action(30, self.linux_prompt, "reboot" )

    def ubootupdate(self):
        self.pexp.expect_action(50, self.bootloader_prompt, "tftp 0x80800000 images/{}".format(self.bootloader))
        self.pexp.expect_action(50, self.bootloader_prompt, "protect off all")
        self.pexp.expect_action(50, self.bootloader_prompt, "erase {} +$filesize".format(self.uboot_address))
        self.pexp.expect_action(50, self.bootloader_prompt, "cp.b $fileaddr {} $filesize".format(self.uboot_address))
        self.pexp.expect_action(50, self.bootloader_prompt, "erase {} {}".format(self.bootenv_address, self.bootenv_size))
        self.pexp.expect_action(50, self.bootloader_prompt, "erase {} {}".format(self.cfg_address, self.cfg_size))
        self.pexp.expect_action(50, self.bootloader_prompt, "reset")

    def ubootwriteinfo(self):
        self.pexp.expect_action(50, self.bootloader_prompt, "protect off all")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearenv")
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "uclearcfg")
        self.pexp.expect_action(50, self.bootloader_prompt, "erase {} {}".format(self.eeprom_address, self.eeprom_size))
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid -f " + self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev " + self.bom_rev)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd " + self.region)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac " + self.mac)
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")
        
        # Check Info
        self.enter_uboot()

        if WRITESSHKEY_ENABLE is True:
            self.gen_and_upload_ssh_key()

        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbid")
        self.pexp.expect_only(15, self.board_id)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetbrev")
        self.pexp.expect_only(15, self.bom_rev)
        #self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetrd")
        #self.pexp.expect_only(15, self.region)
        self.pexp.expect_action(30, self.bootloader_prompt, self.cmd_prefix + "usetmac " + self.mac)
        self.pexp.expect_only(15, self.mac)
        self.pexp.expect_action(30, self.bootloader_prompt, "reset")

    def fwupdate(self):
        #self.pexp.expect_action(50, self.bootloader_prompt, "protect off all")
        #self.pexp.expect_action(50, self.bootloader_prompt, "setenv do_urescue TRUE; urescue -u -e")
        #time.sleep(2)

        # TFTP bin from TestServer
        #fw_path = self.tftpdir + "/images/" + self.board_id + ".bin"
        #log_debug(msg="firmware path:" + fw_path)
        #atftp_cmd = 'exec atftp --option "mode octet" -p -l {} {}'.format(fw_path, self.dutip)
        #log_debug(msg="Run cmd on host:" + atftp_cmd)
        #self.fcd.common.xcmd(cmd=atftp_cmd)

        # Check Bin from DUT
        #self.pexp.expect_only(120, "Bytes transferred")
        #self.pexp.expect_action(100, self.bootloader_prompt, self.cmd_prefix+ "uwrite -f" )
        #log_debug(msg="TFTP Finished")
        self.pexp.expect_action(50, self.bootloader_prompt, "setenv bootargs console=ttyS0,115200 panic=3 recovery")
        self.pexp.expect_action(50, self.bootloader_prompt, "tftp 0x81000000 images/{}.bin".format(self.board_id))
        self.pexp.expect_ubcmd(180, "Bytes transferred", "bootm 0x81000000")

    def boot_image(self):
        # Boot into OS and enable console
        # self.pexp.expect_action(30, self.bootloader_prompt, "setenv bootargs 'quiet console=ttyS0,115200 init=/init nowifi'" )
        # self.pexp.expect_action(30, self.bootloader_prompt, "boot" )
        #self.pexp.expect_action(200, "Please press Enter to activate this console.", "" )
        self.pexp.expect_action(360, "Welcome to UbiOS", "" )
        time.sleep(20)
        self.pexp.expect_action(30, "", "")
        #self.pexp.expect_action(30, "UBNT login:", "ubnt")
        self.pexp.expect_action(30, "login:", "ubnt")
        self.pexp.expect_action(30, "Password: ", "ubnt")
        time.sleep(3)

        # Disable Console NotExpected output
        #self.pexp.expect_action(30, self.linux_prompt ,'#')
        #self.pexp.expect_action(60, self.linux_prompt, "while true; do grep -q 'hostapd' /etc/inittab; if \[ $? -eq 0 \]; then echo 'hostapd exists in /etc/inittab'; break; else echo \"hostapd doesn't exist in /etc/inittab\"; sleep 1; fi; done")
        #self.pexp.expect_action(60, self.linux_prompt, "sed -i 's/null::respawn:\\/usr\\/sbin\\/hostapd/#null::respawn:\\/usr\\/sbin\\/hostapd/g' /etc/inittab")
        #self.pexp.expect_action(60, self.linux_prompt, "init -q; sleep 15")
        time.sleep(5)
        self.pexp.expect_action(60, self.linux_prompt, "dmesg -n 1")
        time.sleep(5)
        cmd = "ifconfig eth0 {0} up".format(self.dutip)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.chk_lnxcmd_valid()
        
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()

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
        #self.pexp.expect_only(15, "Done")

        # Upload the DSS key
        cmd = [
            "tftpboot",
            "0x01000000",
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
        #self.pexp.expect_only(15, "Done")
        log_debug(msg="ssh keys uploaded successfully")


    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot")
        
        self.boot_image()

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=")
        self.pexp.expect_only(10, "systemid=" + self.board_id)
        self.pexp.expect_only(10, "serialno=" + self.mac.lower())

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        # For development reboot to retest
        # self.fromOS_retest()

        if UBOOTUPDATE_ENABLE is True:
            self.enter_uboot()
            self.ubootupdate()
            msg(20, "Succeeding in update uboot ...")

        if UBOOTWRITEINFO_ENABLE is True:
            self.enter_uboot()
            self.ubootwriteinfo()
            msg(30, "Succeeding in write board into ...")

        if FWUPDATE_ENABLE is True:
            self.enter_uboot()
            self.fwupdate()
            msg(40, "Succeeding in update bin file ...")
            self.boot_image()

        if PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(50, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if DOHELPER_ENABLE is True:
            msg(60, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(70, "Finish doing registration ...")
            self.check_devreg_data()
            msg(75, "Finish doing signed file and EEPROM checking ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing firmware upgrading ...")

        if UPLOADLOG_ENABLE is True:
            self.uploadlog()

        self.close_fcd()

def main():
    Factory = UNMSQCA9563Factory()
    Factory.run()

if __name__ == "__main__":
    main()
