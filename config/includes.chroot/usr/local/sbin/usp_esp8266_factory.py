#!/usr/bin/python3
import sys
import time
import os
import stat
import filecmp
from script_base import ScriptBase
from ubntlib.fcd.esptool_helper import ESPTool
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


FLASH_HELPER = True
DO_SECURITY = True
FLASH_FW = True
DATAVERIFY_ENABLE = False


class USPESP8266Factory(ScriptBase):
    def __init__(self):
        super(USPESP8266Factory, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.bomrev = "113-" + self.bom_rev
        self.helperexe = "helper_esp8266"

        self.fcd_uhtools = os.path.join(self.tftpdir, "usp", "plug")
        self.helper_path = os.path.join(self.fcd_toolsdir, "usp", self.helperexe)

        self.fwbin_1 = os.path.join(self.fwdir, "ee73_user1.bin")
        self.fwbin_2 = os.path.join(self.fwdir, "ee73_user2.bin")
        self.recovery_bin = os.path.join(self.fwdir, "ee73_recovery.bin")

        self.boot_bin = os.path.join(self.fcd_uhtools, "rboot.bin")
        self.helper_bin_1 = os.path.join(self.fcd_uhtools, "helper.bin")
        self.blank_bin = os.path.join(self.fcd_uhtools, "blank.bin")
        self.esp_init_data_default_bin = os.path.join(self.fcd_uhtools, "esp_init_data_default.bin")
        self.mac_with_colon = ":".join(self.mac[i:i+2] for i in range(0, len(self.mac), 2))

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
        self.ser.set_baudrate("460800")
        self.ser.set_flash_size(self.ser._16M)
        self.ser.set_flash_mode(self.ser.DOUT)

        msg(10, "Initializing flash")

        self.ser.add_arg(option="0x00000", value=self.boot_bin)
        self.ser.add_arg(option="0x01000", value=self.helper_bin_1)
        self.ser.add_arg(option="0x76000", value=self.blank_bin)
        self.ser.add_arg(option="0x77000", value=self.blank_bin)
        self.ser.add_arg(option="0x78000", value=self.blank_bin)
        self.ser.add_arg(option="0xF6000", value=self.blank_bin)
        self.ser.add_arg(option="0xFB000", value=self.blank_bin)
        self.ser.add_arg(option="0xFD000", value=self.blank_bin)
        self.ser.add_arg(option="0xFE000", value=self.blank_bin)
        self.ser.add_arg(option="0xFF000", value=self.blank_bin)
        self.ser.add_arg(option="0x1FC000", value=self.esp_init_data_default_bin)

        stdout, rtc = self.ser.write_flash()
        log_debug(stdout)
        if rtc != 0:
            error_critical("Init flash failed")
        self.ser.clear_cur_args()

    def do_helper(self):
        # bom => 00645-01
        base_revision = 0x28500  # 00645
        board_revision = int(self.bom_rev[-2:], 16)  # 01
        hw_revision = base_revision + board_revision  # hex value
        # [1 byte unused ] [ 2 bytes BOM ID ] [ 1 byte BOM rev ]
        # 00645-01 is: 0x285 + 01 = 0x28501 = 165121
        msg(10, "Running helper")
        log_debug("hw revision:" + str(hw_revision))
        cmd = [
            self.helper_path,
            "/dev/" + self.dev,
            self.row_id,
            self.board_id,
            str(hw_revision),
            self.mac_with_colon
        ]
        cmdj = ' '.join(cmd)
        log_debug(cmdj)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        log_debug(sto.decode('UTF-8'))
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
        time.sleep(1)
        print(sto)
        sstr = [
            "mv",
            eebin,
            self.eebin_path
        ]
        sstrj = ' '.join(sstr)
        [sto, _] = self.fcd.common.xcmd(sstrj)
        print(sto)
        time.sleep(1)

    def flash_eeprom_and_fw(self):
        msg(60, "Prepare eefiles for dut")
        ee_79 = os.path.join(self.tftpdir, self.eesign + "_79")
        ee_f7 = os.path.join(self.tftpdir, self.eesign + "_f7")
        sstr = [
            "dd",
            "if=" + self.eesign_path,
            "of=" + ee_79,
            "bs=1k",
            "count=32"
        ]
        sstrj = ' '.join(sstr)
        [sto, _] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        print(sto)
        sstr = [
            "dd",
            "if=" + self.eesign_path,
            "of=" + ee_f7,
            "bs=1k",
            "skip=32",
            "count=16"
        ]
        sstrj = ' '.join(sstr)
        [sto, _] = self.fcd.common.xcmd(sstrj)
        time.sleep(1)
        print(sto)

        msg(70, "Flashing firmware and eeprom files")
        self.ser.set_baudrate("460800")
        self.ser.set_flash_size(self.ser._16M)
        self.ser.set_flash_mode(self.ser.DOUT)

        self.ser.add_arg(option="0x00000", value=self.boot_bin)
        self.ser.add_arg(option="0x01000", value=self.fwbin_1)
        self.ser.add_arg(option="0x81000", value=self.fwbin_2)
        self.ser.add_arg(option="0x76000", value=self.blank_bin)
        self.ser.add_arg(option="0x77000", value=self.blank_bin)
        self.ser.add_arg(option="0x78000", value=self.blank_bin)
        self.ser.add_arg(option="0x79000", value=ee_79)
        self.ser.add_arg(option="0xF7000", value=ee_f7)
        self.ser.add_arg(option="0xF6000", value=self.blank_bin)
        self.ser.add_arg(option="0xFB000", value=self.blank_bin)
        self.ser.add_arg(option="0xFD000", value=self.blank_bin)
        self.ser.add_arg(option="0xFE000", value=self.blank_bin)
        self.ser.add_arg(option="0xFF000", value=self.blank_bin)
        self.ser.add_arg(option="0x1FC000", value=self.esp_init_data_default_bin)
        self.ser.add_arg(option="0x101000", value=self.recovery_bin)

        stdout, rtc = self.ser.write_flash()
        log_debug(stdout)
        if rtc != 0:
            error_critical("Flashing firmware and eeprom files failed")
        self.ser.clear_cur_args()
        msg(80, "Flashing firmware and eeprom files success")

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

        if FLASH_HELPER is True:
            self.flash_helper()
            time.sleep(5)

        if DO_SECURITY is True:
            self.do_helper()
            self.erase_eefiles()
            self.copy_eefiles_from_tmp()
            msg(40, "Registering device")
            self.registration(registration_only=True)

        if FLASH_FW is True:
            self.flash_eeprom_and_fw()

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(95, "Succeeding in checking thregistrationmation ...")

        msg(100, "Completing FCD process ...")


def main():
    usp_8266_factory = USPESP8266Factory()
    usp_8266_factory.run()

if __name__ == "__main__":
    main()
