#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical
import time

class UISPAR933XFactory(ScriptBase):
    def __init__(self):
        super(UISPAR933XFactory, self).__init__()

        self.ver_extract()
        self.fwimg = self.board_id + "-fw.bin"
        self.bootloader_prompt = "ar7240>"
        self.devregpart = "/dev/mtdblock5"
        self.helperexe = "helper_ARxxxx_release"
        self.helper_path = "uisp-p-lite"
        self.hw_revision = str((int(self.bom_rev[0:5]) << 8) + int(self.bom_rev[6:8]))
        self.hw_pref = '13'
        self.uboot_file = "eefa-uboot.bin"
        self.fwimg = "eefa.bin"
        self.uboot_addr = '0x9f000000'
        self.eeprom_address = '0x9fff0000'
        self.eeprom_size = '0x10000'
        self.cfg_address = '0x9ffb0000'
        self.cfg_size = '0x40000'
        self.device_type = 'eefa'
        self.images_path = 'images'
        self.mac2 = self.get_mac2()

        # number of Ethernet
        ethnum = {
            'eefa': '1',
        }

        # number of WiFi
        wifinum = {
            'eefa': '0',
        }

        # number of Bluetooth
        btnum = {
            'eefa': '1',
        }

        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
        }
       
        self.UPDATE_UBOOT_ENABLE    = False
        self.PROGRAM_FW_ENABLE      = True
        self.INIT_FW_ENABLE         = True
        self.PROVISION_ENABLE       = True
        self.GET_CAL_DATA_ENABLE    = True
        self.DOHELPER_ENABLE        = True
        self.REGISTER_ENABLE        = True
        self.FWUPDATE_ENABLE        = False
        self.DATAVERIFY_ENABLE      = True

    def get_mac2(self):
        mac_ret = ''
        for i in range(len(self.mac)):
            mac_ret += self.mac[i]
            if i % 2 == 1 and i != len(self.mac) - 1:
                mac_ret += ':'
        return mac_ret

    def wait_for_promt_uboot(self):
        self.pexp.expect_only(15, self.bootloader_prompt, err_msg="Command promt not found")


    def stop_uboot(self):
        log_debug("Stoping U-boot")
        self.pexp.expect_action(30, "Hit any key to stop autoboot:", "\x1b", err_msg="Device not found!")

        self.wait_for_promt_uboot()

    def update_u_boot(self):
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "usetmac {}".format(self.mac2))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setmac {}".format(self.mac2))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv serverip {}".format(self.tftp_server))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv ipaddr {}".format(self.dutip))

        time.sleep(10)

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "tftp 81000000 {}/{}".format(self.images_path, self.uboot_file))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, 'md.b 81000000 10')
        
        self.pexp.expect_only(15, "81000000: 10 00 00 ff 00 00 00 00 10 00 00 fd 00 00 00 00", err_msg="U-boot download failure")

        self.wait_for_promt_uboot()

        self.pexp.expect_ubcmd(15, self.bootloader_prompt, "erase 1:0-3; cp.b 81000000 {} 0x40000".format(self.uboot_addr))

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, 'reset')

        self.stop_uboot() 

    def setmac(self):
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setmac -e {}".format(self.mac2))

    def get_hex(self, input):
        ans = str("0x{:08x}".format(int(input)))
        ans = ans[2:-1] + 'b'
        return ans 

    def get_hex_pref(self, input):
        ans = str("0x{:04x}".format(int(input)))
        ans = ans[2:-1] + 'd'
        return str(ans)

    def write_hw_rev(self):
        log_debug("Seting HW rev. {}:".format(self.hw_revision))
        log_debug("Copying EEPROM to RAM...")

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "cp.b 0x9fff0000 0x81000000 0x10000")

        self.hw_rev_hex = self.get_hex(self.hw_revision) 
        self.hw_rev_hex_pref = self.get_hex_pref(self.hw_pref)

        log_debug("Seting HW rev.: <0x{}>-<0x{}>".format(self.hw_rev_hex_pref, self.hw_rev_hex))

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "mw.l 0x81000010 {}".format(self.hw_rev_hex))
        
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "md.l 0x81000010 1")
        self.pexp.expect_only(15, "81000010: {}".format(self.hw_rev_hex), err_msg="HW rev. setting failure.")

        self.wait_for_promt_uboot()

        log_debug("Seting board ID.: <0x{}>".format(self.device_type))
        log_debug("Current board ID.: <0x{}>".format(self.device_type))

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "md.l 0x8100000C 1")
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "mw.l 0x8100000C {}0777".format(self.device_type))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "md.l 0x8100000C 1")
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "mw.w 0x81000016 {}".format(self.hw_rev_hex_pref))

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "md.w 0x81000016 1")
        self.pexp.expect_only(15, "81000016: {}".format(self.hw_rev_hex_pref), err_msg="HW rev. setting failure.")

        self.wait_for_promt_uboot()

        log_debug("Erasing EEPROM...")

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "erase 1:255")

        log_debug("Copying RAM to EEPROM...") 
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "cp.b 0x81000000 0x9fff0000 0x10000")

        log_debug("Checking HW rev...") 

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "md.l 0x9fff0010 1")

        self.pexp.expect_only(15, "9fff0010: {}".format(self.hw_rev_hex), err_msg="HW rev. setting failure.")

        self.wait_for_promt_uboot()

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "md.w 0x9fff0016 1")

        self.pexp.expect_only(15, "9fff0016: {}".format(self.hw_rev_hex_pref), err_msg="HW rev. setting failure.")

        self.wait_for_promt_uboot()

    def login_kernel(self):
        self.login(timeout=240, press_enter=True)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /lib/build.properties", post_exp=self.linux_prompt)


    def handle_uboot(self):
        self.stop_uboot()
        msg(10, "Got INTO U-boot")

        time.sleep(1)
        self.update_u_boot()

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv serverip {}".format(self.tftp_server))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv ipaddr {}".format(self.dutip))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "printenv")
        self.setmac()

        time.sleep(1)

        self.write_hw_rev()
        self.setmac()

        msg(20, "MAC set")

    def fwupdate(self):
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv serverip {}".format(self.tftp_server))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv ipaddr {}".format(self.dutip))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "printenv")

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "erase {} +{}".format(self.cfg_address, self.cfg_size))

        log_debug("Uploading configuration...") 

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "tftp 81000000 {}/eefa_epx_cfg.bin".format(self.images_path))

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "cp.b 0x81000000 {} {}".format(self.cfg_address, self.cfg_size))

        log_debug("Firmware {}".format(self.fwimg))

        self.fcd.common.xcmd(cmd='ip addr')

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "urescue -f -e")

        self.pexp.expect_only(10, "Waiting for connection", err_msg="Failed to start urescue")


        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir + "/" + self.fwimg,
               self.dutip]
        cmdj = ' '.join(cmd)

        self.fcd.common.xcmd(cmdj)
                                                 
        self.pexp.expect_only(30, "Firmware Version:", err_msg="Failed to download firmware !")
        msg(30, "Firmware loaded")

        self.pexp.expect_only(30, "Copying partition 'u-boot' to flash memory:", err_msg="Failed to flash firmware !")

        msg(35, "Flashing firmware...")

        self.pexp.expect_only(15, "Copying partition 'kernel' to flash memory:", err_msg="Failed to flash firmware !")

        msg(40, "Flashing firmware...")

        self.pexp.expect_only(30, "Copying partition 'rootfs' to flash memory:", err_msg="Failed to flash firmware !")

        msg(45, "Flashing firmware...")

        self.pexp.expect_only(180, "Firmware update complete.", err_msg="Failed to flash firmware !")

        self.fcd.common.xcmd(cmd='ip addr')

        msg(50, "Firmware flashed")

    

    

    def run(self):
        """main procedure of factory
        """
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Open serial port successfully ...")
        
        msg(6, "Waiting - PLUG in the device...")

        self.handle_uboot()

        self.fwupdate()

        self.login_kernel()

        self.is_network_alive_in_linux()
        
        if self.PROVISION_ENABLE is True:
            msg(60, "Send tools to DUT and data provision ...")

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "hexdump -n48 /dev/mtdblock5")

            self.copy_and_unzipping_tools_to_dut(timeout=60)
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            msg(70, "Do helper to get the output file to devreg server ...")

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "hexdump -n48 /dev/mtdblock5")

            self.erase_eefiles()
            self.prepare_server_need_files()

        if self.REGISTER_ENABLE is True:

            self.FCD_TLV_data = False
            self.registration()
            msg(80, "Finish doing registration ...")

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "hexdump -n48 /dev/mtdblock5")
  
            self.check_devreg_data()
            msg(90, "Finish doing signed file and EEPROM checking ...")

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "hexdump -n48 /dev/mtdblock5")
        
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot -f")

        self.stop_uboot()

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "erase {} +{}".format(self.cfg_address, self.cfg_size))
        msg(95, "Configuration erased")

        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv serverip {}".format(self.tftp_server))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "setenv ipaddr {}".format(self.dutip))
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "saveenv")

        mac_str = self.pexp.expect_get_output('setmac', self.bootloader_prompt)

        self.wait_for_promt_uboot()
        self.pexp.expect_ubcmd(2, self.bootloader_prompt, "re")
        self.pexp.expect_only(180, "Booting", err_msg="Kernel boot failure !")
        
        msg(99,"Completed with {}".format(mac_str))
        msg(100, "Completing FCD process ...")
        self.close_fcd()

def main():
    uisp_ar933x_factory = UISPAR933XFactory()
    uisp_ar933x_factory.run()

if __name__ == "__main__":
    main()
