#!/usr/bin/python3


import time
import os
import re
import json

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class UCMT7628Factory(ScriptBase):
    def __init__(self):
        super(UCMT7628Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        
        self.fwimg = "images/" + self.board_id + "-fw.bin"
        self.initramfs = "images/" + self.board_id + "-initramfs.bin"
        self.ubootimg = "images/" + self.board_id + "-uboot.bin"
        
        self.devregpart = "/dev/mtdblock3"
        self.helperexe = "helper_MT7628_release"
        self.bootloader_prompt = ">"
        
        if self.board_id == "ea2e":
            self.helper_path = "udw_pro_pu"
        elif self.board_id == "ed15":
            self.helper_path = "usp_pro_pdu_hd"
        else:
            self.helper_path = "afi_ups"

        # number of mac
        self.macnum =  {
            'ed14': "0",
            'ea2e': "1",
            'ed15': "1"
        }
        # number of WiFi
        self.wifinum = {
            'ed14': "1",
            'ea2e': "0",
            'ed15': "0"
        }
        # number of Bluetooth
        self.btnum =   {
            'ed14': "1",
            'ea2e': "0",
            'ed15': "0",
        }
        # flash size map
        self.flash_size = {
            'ed14': "33554432",
            'ea2e': "16777216",
            'ed15': "16777216"
        }
        # firmware image
        self.fwimg = self.board_id + "-fw.bin"
        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
        }

        self.UPDATE_UBOOT_ENABLE    = True
        self.BOOT_RAMFS_IMAGE       = True
        self.PROVISION_ENABLE       = True
        self.DOHELPER_ENABLE        = True
        self.REGISTER_ENABLE        = True
        self.FWUPDATE_ENABLE        = True
        self.DATAVERIFY_ENABLE      = True

        self.SOC_FW_CHECK_ENABLE = {
            'ed14': False,
            'ea2e': False,
            'ed15': True,
        }
        self.SOC_FW_VERSION = {
            'ed14': '',
            'ea2e': '',
            'ed15': 'US.mt7628_6.5.68+14839.230815.1558',
        }

        self.LCM_FW_CHECK_ENABLE    = False

        self.MCU_FW_CHECK_ENABLE = {
            'ed14': False,
            'ea2e': False,
            'ed15': True,
        }
        self.MCU_FW_VERSION = {
            'ed14': '',
            'ea2e': '',
            'ed15': '1.2.7',
        }
        self.MCU_FW_LOADER = {
            'ed14': '',
            'ea2e': '',
            'ed15': 'v1.0.1',
        }

        self.OFF_POWER_UNIT_ENABLE  = {
            'ed14': False,
            'ea2e': True,
            'ed15': False,
        }

    def enter_uboot(self):
        self.pexp.expect_action(60, "Hit any key to stop autoboot", "")
        self.set_boot_net()
        
    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv loadaddr 0x81000000")
        self.is_network_alive_in_uboot()
        
    def update_uboot_image(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot ${{loadaddr}} {}".format(self.ubootimg))
        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf probe; sf erase 0x0 0x60000; sf write ${loadaddr} 0x0 ${filesize}")
        ## Uboot of BSP, AFi-UPS
        # SF: Detected mx25l25635e with page size 256 Bytes, erase size 64 KiB, total 32 MiB
        # SF: 393216 bytes @ 0x0 Erased: OK
        # device 0 offset 0x0, size 0x2c3f0
        # SF: 181232 bytes @ 0x0 Written: OK
        # =>

        ## Uboot of FW, AFi-UPS
        # SF: Detected mx25l25635e with page size 256 Bytes, erase size 64 KiB, total 32 MiB
        # SF: 16777216 bytes @ 0x0 Erased: OK
        # uboot>
        
        self.pexp.expect_only(120, "Erased: OK")
        # self.pexp.expect_only(120, "Written: OK")  #BSP uboot, have "Written", FW Uboot have no Written
        # Uboot, if you enter the "Enter", uboot will run previous command so "^c" is to avoid to re-run re-program flash again
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "^c")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")
        
    def init_ramfs_and_erease_devreg(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot ${{loadaddr}} {}".format(self.initramfs))
        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm")
        
        self.pexp.expect_only(30, "Loading kernel")
        self.login(press_enter=True, log_level_emerg=True, timeout=60)
        
        # #  remove DEVREG data
        # if self.board_id == 'ea2e':
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo EEPROM,388caeadd99840d391301bec20531fcef05400f4 > " +
        #                                                "/sys/module/mtd/parameters/write_perm", self.linux_prompt)
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "cfgmtd -no Factory -c", self.linux_prompt)
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "sync;sync;sync", self.linux_prompt)
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", self.linux_prompt)
        # else:
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo \"EEPROM,388caeadd99840d391301bec20531fcef05400f4\" > " +
        #                                                "/sys/module/mtd/parameters/write_perm", self.linux_prompt)
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, 'dd if=/dev/zero ibs=1 count=64K | tr "\000" "\377" > /tmp/ff.bin', self.linux_prompt)
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if=/tmp/ff.bin of=/dev/mtdblock3 bs=1k count=64", self.linux_prompt)
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "sync;sync;sync", self.linux_prompt)
        #     self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", self.linux_prompt)
            
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo \"EEPROM,388caeadd99840d391301bec20531fcef05400f4\" > " +
                                                       "/sys/module/mtd/parameters/write_perm", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, 'dd if=/dev/zero ibs=1 count=64K | tr "\000" "\377" > /tmp/ff.bin', self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dd if=/tmp/ff.bin of=/dev/mtdblock3 bs=1k count=64", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "sync;sync;sync", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", self.linux_prompt)

        
    def init_ramfs_image(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "tftpboot ${{loadaddr}} {}".format(self.initramfs))
        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "bootm")
        
        self.pexp.expect_only(30, "Loading kernel")
        self.login(press_enter=True, log_level_emerg=True, timeout=60)
        
        if self.board_id == "ed14":
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "hexdump -C -n 512 /dev/mtdblock3", self.linux_prompt)
            try:
                self.disable_udhcpc()
            except Exception as e:
                log_debug("ERROR:{}".format(e))
            
            try:
                self.disable_wpa_supplicant()
            except Exception as e:
                log_debug("ERROR:{}".format(e))
        else:
            pass
        
        if self.board_id == "ed14":
            # AFi-UPS
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "init -q", self.linux_prompt)
            # time.sleep(45)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig wlan0 down", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "swconfig dev switch0 set reset", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ps", self.linux_prompt)

        elif self.board_id == "ea2e":
            
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0", self.linux_prompt)
            print("Wait 2mins for DUT setup up IP(169.254.1.2) for eth0 then FCD will change the IP 192.168.1.x instead")
            time.sleep(120)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0", self.linux_prompt)
            #UDM-Pro-PU will set eth port as 169.254.x.x as default
            retry_time = 20
            while retry_time >=0:
                ret_msg = self.pexp.expect_get_output("ifconfig eth0",self.linux_prompt)
                if ret_msg.find("169.254.1.2") >= 0:
                    print("IP of Interface is set up done")
                    break
                time.sleep(1)
            else:
                print("IP of Interface is not sey up done")
                self.pexp.expect_action(3, "169.254.1.2", "ifconfig eth0")

            self.pexp.expect_lnxcmd(10, self.linux_prompt, "swconfig dev switch0 set reset", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, r"sed -i 's/netconf.1.ip=169.254.1.2/netconf.1.ip={}/g' /tmp/system.cfg".format(self.dutip), self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "syswrapper.sh apply-config 2>&1 &", self.linux_prompt)
            time.sleep(10)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 up", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, r"ifconfig eth0 {} netmask 255.255.255.0".format(self.dutip), self.linux_prompt)

        elif self.board_id == "ed12":
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "ifconfig eth0 "+self.dutip, self.linux_prompt)
        else:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "swconfig dev switch0 set reset", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 up", self.linux_prompt)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, r"ifconfig eth0 {} netmask 255.255.255.0".format(self.dutip), self.linux_prompt)
        
        self.is_network_alive_in_linux()
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo \"EEPROM,388caeadd99840d391301bec20531fcef05400f4\" > " +
                                                       "/sys/module/mtd/parameters/write_perm", self.linux_prompt)

    def fwupdate(self, image, reboot_en):
        if reboot_en is True:
            self.pexp.expect_action(30, self.linux_prompt, "reboot -f")
        self.enter_uboot()
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearcfg TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv ubnt_clearenv TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "setenv do_urescue TRUE")
        self.pexp.expect_action(30, self.bootloader_prompt, "bootubnt -f")
        self.pexp.expect_action(30, "Listening for TFTP transfer on", "")

        # to use Desktop atftp to transfer image to DUT
        # atftp -p -l /tftpboot/images/ea2e-fw.bin 192.168.1.20
        cmd = ["atftp",
               "-p",
               "-l",
               self.fwdir+"/"+image,
               self.dutip]
        cmdj = ' '.join(cmd)

        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Failed to upload firmware image")
        else:
            log_debug("Uploading firmware image successfully")

        self.pexp.expect_only(30, "Bytes transferred = ")
        self.pexp.expect_only(30, "Firmware Version:")
        self.pexp.expect_only(30, "Firmware Signature Verfied, Success.")
        self.pexp.expect_only(60, "Updating kernel0 partition \(and skip identical blocks\)")
        self.pexp.expect_only(240, "done")

    def check_info(self):
        self.pexp.expect_action(30, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(30, "flashSize="+self.flash_size[self.board_id])
        self.pexp.expect_only(30, "systemid="+self.board_id)
        self.pexp.expect_only(30, "serialno="+self.mac.lower())
        self.pexp.expect_only(30, "qrid="+self.qrcode)
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/build.properties")
        self.pexp.expect_action(30, self.linux_prompt, "cat /usr/lib/version")
        
        retry_time = 15
        while retry_time >= 0:
            output = self.pexp.expect_get_output(action="info", prompt="", timeout=3)
            if output.find("Version") >= 0:
                break
            retry_time -= 1
            time.sleep(1)
            
    def soc_fw_check(self):
        version = self.pexp.expect_get_output("cat /usr/lib/version", self.linux_prompt)

        if self.SOC_FW_VERSION[self.board_id] not in version:
            err_msg = f"SOC FW version mismatch, got {version} but expect {self.SOC_FW_VERSION[self.board_id]}"
            error_critical(err_msg)
        else:
            log_debug("SOC FW version matched!")

    def lcm_fw_check(self):
        self.pexp.expect_lnxcmd(5, self.linux_prompt, 'lcm-ctrl -t dump', 'version', retry=48)

    def mcu_fw_check(self):
        if self.board_id == "ed15":
            mcu_num = 2
            global loader, mode, version

            # pre-action before set loader true
            self.stop_mcu_status_poll(mcu_num)

            for i in range(1, mcu_num+1):
                try:
                    params = {"loader": True}
                    mcu_info = self.mcu_info(i, params)
                    loader = re.search(r'"loader":(.*),', mcu_info).group(1).strip()
                    mode = re.search(r'"mode":(.*),', mcu_info).group(1).strip()
                    version = re.search(r'"version":(.*),', mcu_info).group(1).strip()
                    log_debug(f"Loader: {loader}, mode: {mode}, version: {version}")

                except Exception as e:
                    log_error(e)
                    err_msg = f"MCU {i} unable to get info"
                    self.mcu_error_handler(err_msg)

                if "normal" not in mode:
                    err_msg = f"MCU {i} wrong mode, expect normal mode! Not allow to proceed test!"
                    self.mcu_error_handler(err_msg)

                if self.MCU_FW_LOADER[self.board_id] in loader and self.MCU_FW_VERSION[self.board_id] in version:
                    log_debug(f"MCU {i} FW version & loader version matched.")

                if self.MCU_FW_LOADER[self.board_id] not in loader:
                    err_msg = f"MCU {i} loader version mismatch, got {loader} but expect {self.MCU_FW_LOADER[self.board_id]}"  # noqa: E501
                    self.mcu_error_handler(err_msg)

                if self.MCU_FW_VERSION[self.board_id] not in version:
                    err_msg = f"MCU {i} FW version mismatch, got {version} but expect {self.MCU_FW_LOADER[self.board_id]}"  # noqa: E501
                    self.mcu_error_handler(err_msg)

            # post-action after set loader true & before end test
            self.start_mcu_status_poll(mcu_num)

    def mcu_error_handler(self, err_msg):
        mcu_num = 2
        # post-action after set loader true & before end test
        self.start_mcu_status_poll(mcu_num)
        error_critical(err_msg)

    def mcu_status_poll(self, mcu_id, enable):
        cmd = f"ubus call power.outlet.meter_mcu.{mcu_id} status_poll '" + json.dumps({"set": "start" if enable else "stop"}) + "'"  # noqa: E501
        try:
            ret_msg = self.pexp.expect_get_output(cmd, self.linux_prompt)
        except Exception:
            raise Exception(f"MCU {mcu_id} status_poll error")
        return ret_msg

    def mcu_info(self, mcu_id, params=None):
        ret_msg = None
        if params is None:
            params = {}
        cmd = f"ubus call power.outlet.meter_mcu.{mcu_id} info " + (f" '{json.dumps(params)}'" if params != {} else "")

        for retry in range(3):
            try:
                log_debug(f"Retrieve mcu info, attempt {retry+1}")
                ret_msg = self.pexp.expect_get_output(cmd, self.linux_prompt, timeout=20)
                if ret_msg is None or "result" not in ret_msg:
                    log_debug("Unable to get mcu info, try again...")
                    if retry == 2:
                        err_msg = f"MCU {mcu_id} get mcu_info error after max retries"
                        self.mcu_error_handler(err_msg)
                    continue
                else:
                    break
            except Exception as e:
                log_error(e)
                err_msg = f"MCU {mcu_id} get mcu_info error"
                self.mcu_error_handler(err_msg)
        return ret_msg

    def start_mcu_status_poll(self, mcu_num):
        for mcu_id in range(1, mcu_num + 1):
            self.mcu_status_poll(mcu_id, enable=True)

    def stop_mcu_status_poll(self, mcu_num):
        for mcu_id in range(1, mcu_num + 1):
            self.mcu_status_poll(mcu_id, enable=False)

    def off_power_unit_power(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "i2ctransfer -y 4 w4@0xb 0x00 0x10 0x00 0x44", self.linux_prompt)
        time.sleep(1)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "i2ctransfer -y 4 w4@0xb 0x00 0x10 0x00 0x44", self.linux_prompt)
        time.sleep(1)

    def run(self):
        if self.ps_state is True:
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        self.fcd.common.config_stty(self.dev)
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(5)

        if self.ps_state is True:
            self.set_ps_port_relay_on()
        else:
            log_debug("No need power supply control")

        msg(5, "Open serial port successfully ...")
        if self.UPDATE_UBOOT_ENABLE is True:
            self.enter_uboot()
            self.update_uboot_image()
            msg(10, "Update Uboot image successfully ...")

        if self.BOOT_RAMFS_IMAGE is True:
            msg(15, "Boot into initRamfs image for registration ...")
            self.enter_uboot()
            self.init_ramfs_and_erease_devreg()

            self.enter_uboot()
            self.init_ramfs_image()

        if self.PROVISION_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(self.devnetmeta)

        if self.DOHELPER_ENABLE is True:
            self.prepare_server_need_files()
            msg(30, "Do helper to get the output file to devreg server ...")

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            msg(60, "Updating released firmware ...")
            self.fwupdate(self.fwimg, reboot_en=True)
            msg(70, "Updating released firmware done...")
        else:
            self.pexp.expect_lnxcmd(30, self.linux_prompt, "reboot", self.linux_prompt)

        if self.DATAVERIFY_ENABLE is True:
            self.login(press_enter=True, log_level_emerg=True, timeout=60)
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        if self.SOC_FW_CHECK_ENABLE[self.board_id] is True:
            self.soc_fw_check()
            msg(85, "Succeeding in checking the SOC FW information ...")

        if self.LCM_FW_CHECK_ENABLE is True:
            self.lcm_fw_check()
            msg(90, "Succeeding in checking the LCM FW information ...")

        if self.MCU_FW_CHECK_ENABLE[self.board_id] is True:
            self.mcu_fw_check()
            msg(95, "Succeeding in checking the MCU FW information ...")

        if self.OFF_POWER_UNIT_ENABLE[self.board_id] is True:
            self.off_power_unit_power()

        if self.ps_state is True:
            time.sleep(2)
            self.set_ps_port_relay_off()
        else:
            log_debug("No need power supply control")

        msg(100, "Complete FCD process ...")
        self.close_fcd()

def main():
    uc_mt7628_factory = UCMT7628Factory()
    uc_mt7628_factory.run()

if __name__ == "__main__":
    main()
