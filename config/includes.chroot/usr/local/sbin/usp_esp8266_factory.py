#!/usr/bin/python3
import sys
import time
import os
import stat
import filecmp
from script_base import ScriptBase
from ubntlib.fcd.esptool_helper import ESPTool
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

class USPESP8266Factory(ScriptBase):
    def __init__(self):
        super(USPESP8266Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.bomrev = "113-" + self.bom_rev
        self.helperexe = "helper_esp8266"
        self.FCD_TLV_data = False

        # image folder path
        self.image_path = {
            'ee73': "plug",
            'ee74': "strip"
        }
 
        self.fcd_uhtools = os.path.join(self.tftpdir, "usp", self.image_path[self.board_id])
        self.helper_path = os.path.join(self.fcd_toolsdir, "usp", self.helperexe)
        self.gen_key_sh_path = os.path.join(self.fcd_toolsdir, "usp", "gen-cert.sh")
        self.private_key_path = os.path.join(self.fcd_toolsdir, "usp", "private_" + self.row_id + ".pem")
        self.public_key_path = os.path.join(self.fcd_toolsdir, "usp", "public_" + self.row_id + ".pem")

        self.fwbin_1 = os.path.join(self.fwdir, self.board_id + "_user1.bin")
        self.fwbin_2 = os.path.join(self.fwdir, self.board_id+ "_user2.bin")
        self.recovery_bin = os.path.join(self.fwdir, self.board_id + "_recovery.bin")

        self.rboot_bin = os.path.join(self.fcd_uhtools, "rboot.bin")
        self.helper_bin_1 = os.path.join(self.fcd_uhtools, "helper.bin")
        self.blank_bin = os.path.join(self.fcd_uhtools, "blank.bin")
        self.esp_init_data_default_bin = os.path.join(self.fcd_uhtools, "esp_init_data_default.bin")
        self.mac_with_colon = ":".join(self.mac[i:i+2] for i in range(0, len(self.mac), 2))

        self.FLASH_HELPER = True 
        self.DO_SECURITY  = True
        self.GEN_CA_KEY   = True if self.board_id == 'ea74' else False
        self.FLASH_FW     = True

    def check_info(self):
        """under developing
        """
        self.pexp.expect_action(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno error")

    def wait_device(self, timeout=120):
        while timeout > 0:
            output = self.ser.chip_id()
            log_debug(str(output))
            if "Chip" in str(output):
                return True
            else:
                log_debug("Waiting device")
            time.sleep(1)
            timeout -= 1
        return False

    def flash_helper(self):
        self.ser.set_baudrate("921600")
        self.ser.set_after_action("soft_reset")
        self.ser.set_flash_size(self.ser._DETECT)
        self.ser.set_flash_mode(self.ser.DOUT)

        msg(10, "Initializing flash")

        if self.board_id == 'ee73':
            self.ser.add_arg(option="0x000000", value=self.rboot_bin)
            self.ser.add_arg(option="0x001000", value=self.helper_bin_1)
            self.ser.add_arg(option="0x076000", value=self.blank_bin)
            self.ser.add_arg(option="0x077000", value=self.blank_bin)
            self.ser.add_arg(option="0x078000", value=self.blank_bin)
            self.ser.add_arg(option="0x0F6000", value=self.blank_bin)
            self.ser.add_arg(option="0x0FB000", value=self.blank_bin)
            self.ser.add_arg(option="0x0FD000", value=self.blank_bin)
            self.ser.add_arg(option="0x0FE000", value=self.blank_bin)
            self.ser.add_arg(option="0x0FF000", value=self.blank_bin)
            self.ser.add_arg(option="0x1FC000", value=self.esp_init_data_default_bin)
        elif self.board_id == 'ee74':
            self.ser.add_arg(option="0x000000", value=self.rboot_bin)
            self.ser.add_arg(option="0x001000", value=self.helper_bin_1)
            self.ser.add_arg(option="0x3FC000", value=self.esp_init_data_default_bin)

        self.ser.set_stub(True)
        stdout, rtc = self.ser.write_flash()
        log_debug(stdout)
        if rtc != 0:
            error_critical("Init flash failed")
        self.ser.clear_cur_args()

    def do_helper(self):
        # bom       : 00645-01
        # bom_number: 0x28500 (00645 => 0x285 + '00' = 0x28500)
        # bom_rev   : 0x1 (01 => 0x1)
        # [1 byte unused ] [ 2 bytes BOM ID ] [ 1 byte BOM rev ]
        # 00645-01 is: 0x285 + 01 = 0x28501 = 165121
        bom_number = hex(int(self.bom_rev[:-3], 10)) + '00'
        bom_rev = hex(int(self.bom_rev[-2:], 10))
        bom = str(int(bom_number, 16) + int(bom_rev, 16))
        msg(10, "Running helper")
        log_debug("BOM:" + bom)
        cmd = [
            self.helper_path,
            "/dev/" + self.dev,
            self.row_id,
            self.board_id,
            bom,
            self.mac_with_colon
        ]
        cmdj = ' '.join(cmd)
        log_debug("cmdj = " + cmdj)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        log_debug(sto)
        if int(rtc) > 0:
            error_critical("Running helper failed")

    def copy_eefiles_from_tmp(self):
        msg(30, "Copying ee files generated from helper from /tmp")
        eetxt = os.path.join("/tmp", "e.t" + self.row_id)
        eebin = os.path.join("/tmp", "e.b" + self.row_id)
        sstr = [
            "mv",
            eetxt,
            self.eetxt_path
        ]
        sstrj = ' '.join(sstr)
        [sto, _] = self.fcd.common.xcmd(sstrj)
        print(sto)
        sstr = [
            "mv",
            eebin,
            self.eebin_path
        ]
        sstrj = ' '.join(sstr)
        [sto, _] = self.fcd.common.xcmd(sstrj)
        print(sto)

    def flash_eeprom_and_fw(self):
        msg(60, "Flashing firmware and eeprom files")
        self.ser.set_baudrate("921600")
        self.ser.set_after_action("soft_reset")
        self.ser.set_flash_size(self.ser._DETECT)
        self.ser.set_flash_mode(self.ser.DOUT)

        if self.board_id == 'ee73':
            devreg_part1 = os.path.join(self.eesign_path + "_79")
            devreg_part2 = os.path.join(self.eesign_path + "_F7")
            sstr = [
                "dd",
                "if=" + self.eesign_path,
                "of=" + devreg_part1,
                "bs=1k",
                "count=32"
            ]
            sstrj = ' '.join(sstr)
            [sto, _] = self.fcd.common.xcmd(sstrj)
            print(sto)
            sstr = [
                "dd",
                "if=" + self.eesign_path,
                "of=" + devreg_part2,
                "bs=1k",
                "skip=32",
                "count=32"
            ]
            sstrj = ' '.join(sstr)
            [sto, _] = self.fcd.common.xcmd(sstrj)
            print(sto)

            self.ser.add_arg(option="0x000000", value=self.rboot_bin)
            self.ser.add_arg(option="0x001000", value=self.fwbin_1)
            self.ser.add_arg(option="0x076000", value=self.blank_bin)
            self.ser.add_arg(option="0x077000", value=self.blank_bin)
            self.ser.add_arg(option="0x078000", value=self.blank_bin)
            self.ser.add_arg(option="0x079000", value=devreg_part1)
            self.ser.add_arg(option="0x081000", value=self.fwbin_2)
            self.ser.add_arg(option="0x0F6000", value=self.blank_bin)
            self.ser.add_arg(option="0x0F7000", value=devreg_part2)
            self.ser.add_arg(option="0x101000", value=self.recovery_bin)
            self.ser.add_arg(option="0x1FC000", value=self.esp_init_data_default_bin)
            self.ser.add_arg(option="0x1FD000", value=self.blank_bin)
            self.ser.add_arg(option="0x1FE000", value=self.blank_bin)
        elif self.board_id == 'ee74':
            self.ser.add_arg(option="0x000000", value=self.rboot_bin)
            self.ser.add_arg(option="0x001000", value=self.fwbin_1)
            self.ser.add_arg(option="0x101000", value=self.fwbin_2)
            self.ser.add_arg(option="0x201000", value=self.recovery_bin)
            self.ser.add_arg(option="0x38A000", value=self.eesign_path)
            self.ser.add_arg(option="0x3F5000", value=self.public_key_path)
            self.ser.add_arg(option="0x3F6000", value=self.private_key_path)
            self.ser.add_arg(option="0x3FC000", value=self.esp_init_data_default_bin)

        stdout, rtc = self.ser.write_flash()
        log_debug(stdout)
        if rtc != 0:
            error_critical("Flashing firmware and eeprom files failed")
        self.ser.clear_cur_args()
        msg(80, "Flashing firmware and eeprom files success")
    
    def gen_CA_key(self):
        cmd = [
            "bash",
            self.gen_key_sh_path,
            self.mac,
            self.qrcode,
            self.row_id
        ]
        cmdj = ' '.join(cmd)
        log_debug("cmdj = " + cmdj)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        log_debug(sto)
        if int(rtc) > 0:
            error_critical("Gen key failed")

    def run(self):
        """main procedure of factory
        """
        self.ver_extract()
        seriel_object = ESPTool(port="/dev/" + self.dev, baudrate="115200")
        self.set_serial_helper(serial_obj=seriel_object)
        time.sleep(1)

        if not self.wait_device():
            error_critical("Device not found!")
        log_debug("Device is connected")

        if self.FLASH_HELPER is True:
            self.flash_helper()
            time.sleep(3)

        if self.DO_SECURITY is True:
            self.do_helper()
            self.erase_eefiles()
            self.copy_eefiles_from_tmp()
            msg(40, "Registering device")
            self.registration()

        if self.GEN_CA_KEY is True:
            msg(50, "Generate certification key")
            self.gen_CA_key()

        if self.FLASH_FW is True:
            self.flash_eeprom_and_fw()

        msg(100, "Completing FCD process ...")
        self.close_fcd()

def main():
    usp_8266_factory = USPESP8266Factory()
    usp_8266_factory.run()

if __name__ == "__main__":
    main()
