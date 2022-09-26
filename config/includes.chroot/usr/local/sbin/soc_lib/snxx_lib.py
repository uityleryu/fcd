#!/usr/bin/python3

import serial
import time
from os.path import exists as file_exists
from os.path import basename
import sys
import os
import re
import zlib
import argparse
from script_base import ScriptBase
import data.constant as CONST


class SnxxLib(ScriptBase):
    _serial_port = None
    _last_read_timeout = None
    _board_greeting = "SONIX "
    # use this size due to the limitation on the board
    _write_block_size = 1024

    # all timeouts are in sec
    CMD_TOUT_DEFAULT = 3
    CMD_TOUT_PREPARE = 0.5
    CMD_TOUT_FLASH_CRC32 = 10
    CMD_TOUT_FLASH_ERASE = 10
    CMD_TOUT_TABLE_READ = 20
    CMD_TOUT_CHECK_SEC = 15

    def __init__(self):
        super(SnxxLib, self).__init__()

    def __del__(self):
        super(SnxxLib, self).__del__()
        self.close_port()

    @property
    def board_greeting(self):
        return self._board_greeting

    @board_greeting.setter
    def board_greeting(self, greeting_str: str):
        self._board_greeting = greeting_str

    def open_serial_port(self, uart_file: str, uart_baud=115200):
        try:
            self._serial_port = serial.Serial(port=uart_file, baudrate=uart_baud, parity=serial.PARITY_NONE,
                                              stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
        except BaseException as err:
            return "open_serial_port: {0}".format(err)

        return ""

    def close_port(self):
        if not self._serial_port is None:
            self._serial_port.close

    def prepare_cmd(self, cmd="\rback\rsetlvl 0\rsetuilvl 0", timeout=CMD_TOUT_PREPARE):
        if self._serial_port is None:
            return "Serial port is not opened"

        try:
            if cmd:
                self._serial_port.flushInput()
                self._serial_port.write("{}{}".format(cmd, "\r").encode())
                self._serial_port.flush()

            end_ts = time.time() + timeout
            while time.time() < end_ts:
                if self._serial_port.inWaiting() > 0:
                    self._serial_port.read(self._serial_port.in_waiting)

        except BaseException as err:
            return "prepare_cmd: {0}".format(err)

        return ""

    def send_cmd(self, menu_level: str, cmd: str, answer_lines_cnts=[], timeout=CMD_TOUT_DEFAULT):
        return self.__send_cmd_helper(menu_level, cmd, answer_lines_cnts, timeout)

    def enter_sublevel(self, menu_sublevel: str, timeout=CMD_TOUT_DEFAULT):
        empty_lines_cnt = []
        return self.__send_cmd_helper(menu_sublevel, menu_sublevel, empty_lines_cnt, timeout)

    def exit_sublevel(self, timeout=CMD_TOUT_DEFAULT):
        menu_level = "main"
        empty_lines_cnt = []
        return self.__send_cmd_helper(menu_level, "back", empty_lines_cnt, timeout)

    def send_cmd_sublevel(self, menu_sublevel: str, cmd: str, answer_lines_cnts=[], timeout=CMD_TOUT_DEFAULT):
        menu_level = "main"
        empty_lines_cnt = []
        if menu_sublevel:
            # go to sublevel
            menu_level = menu_sublevel
            [err, res] = self.__send_cmd_helper(menu_level, menu_sublevel, empty_lines_cnt, timeout)
            if err:
                return [err, res]

        # send command
        cmd_result = self.__send_cmd_helper(menu_level, cmd, answer_lines_cnts, timeout)

        if menu_sublevel:
            # go to main level
            menu_level = "main"
            [err, res] = self.__send_cmd_helper(menu_level, "back", empty_lines_cnt, timeout)
            if err:
                return [err, res]

        return cmd_result

    def __send_cmd_helper(self, menu_level: str, cmd: str, answer_lines_cnts, timeout):
        if self._serial_port is None:
            return ["__send_cmd_helper: serial port is not opened", []]

        if not cmd:
            return ["__send_cmd_helper: command is empty", []]

        if not menu_level:
            return ["__send_cmd_helper: menu level is empty", []]

        if not self._last_read_timeout == timeout:
            try:
                self._last_read_timeout = timeout
                self._serial_port.timeout = self._last_read_timeout
            except BaseException as err:
                return ["__send_cmd_helper: {0}".format(err), []]

        menu_level_main = "main"
        cmd_send = "{0}{1}".format(cmd, "\r")
        greeting = "{0}({1})>:".format(self._board_greeting, menu_level)
        greeting_main = "{0}({1})>:".format(self._board_greeting, menu_level_main)

        try:
            self._serial_port.flushInput()
            self._serial_port.write(cmd_send.encode())
            self._serial_port.flush()
        except BaseException as err:
            return ["__send_cmd_helper: {0}".format(err), []]

        wait_echo = 1
        skip_first_empty = 0
        lines_list = []

        start_ts = time.time()
        end_ts = start_ts + self._last_read_timeout * 0.9
        while True:
            try:
                line = self._serial_port.readline()
            except BaseException as err:
                return ["__send_cmd_helper: {0}".format(err), []]

            if len(line) == 0:
                return ["__send_cmd_helper: read data timeout", []]

            bytearr_line = bytearray(line)

            err_check_str = ""
            for pos in range(len(bytearr_line)):
                ch = bytearr_line[pos]
                if not (ch == 9 or ch == 10 or ch == 13 or (ch >= 32 and ch <= 126)):
                    if not err_check_str:
                        err_check_str = "received wrong char 0x{0:02x} in pos {1}".format(ch, pos)

                    bytearr_line[pos] = 46;

            err_decode_str = ""
            try:
                line = bytearr_line.decode("utf-8")

                # remove all Carriage Return ('\r') and New line symbols ('\n') from line
                line = line.strip("\r\n")
            except BaseException as err:
                err_decode_str = err

            if err_check_str:
                if err_decode_str or not line:
                    return ["__send_cmd_helper: {0}".format(err_check_str), []]
                else:
                    return ["__send_cmd_helper: {0} (corrected line '{1}')".format(err_check_str, line), []]

            if err_decode_str:
                return ["__send_cmd_helper: {0}".format(err_decode_str), []]

            if line:
                if wait_echo == 1:
                    if not line == cmd:
                        return ["__send_cmd_helper: wrong echo responce '{0}', expected '{1}'".format(line, cmd), []]

                    wait_echo = 0
                    skip_first_empty = 1
                    continue

                if skip_first_empty:
                        return ["__send_cmd_helper: wrong echo responce '{0}', expected first empty line".format(line), []]

                if line == greeting:
                    break

                if line == greeting_main:
                    if not greeting == greeting_main:
                        return [
                            "__send_cmd_helper: menu '{0}' is absent (received response menu level '{1}', requested '{0}')".format(
                                menu_level, menu_level_main), []]

                    break

                lines_list.append(line)
            else:
                if skip_first_empty:
                    skip_first_empty = 0
                else:
                    lines_list.append(line)

            if time.time() > end_ts:
                return ["__send_cmd_helper: too much data is read from the serial port during {:0.0f} ms".format(
                    (time.time() - start_ts) * 1000), []]

        found = 0
        lines_count = len(lines_list)
        if lines_count == 0:
            return ["__send_cmd_helper: error: absent any line before board greeting", []]

        last_line = lines_list.pop()
        if last_line:
            return ["__send_cmd_helper: error: wrong line before board greeting {0}, expected first empty line".format(last_line), []]

        lines_count = lines_count - 1

        for cur_count in answer_lines_cnts:
            if lines_count == cur_count:
                found = 1
                break

        if not len(answer_lines_cnts) == 0 and found == 0:
            error_str = ""
            if lines_count > 0:
                error_str = lines_list[0]

            return ["__send_cmd_helper: answer lines count {0} is not in range {1}: {2}".format(lines_count,
                                                                                                str(answer_lines_cnts),
                                                                                                error_str), []]

        return ["", lines_list]

    def __hex_str_to_byte_arr(self, inp_str: str):
        try:
            byte_str = inp_str.encode()
        except BaseException as err:
            return ["__hex_str_to_byte_arr: {0}".format(err), []]

        inp_len = len(byte_str)

        if inp_len == 0:
            return ["__hex_str_to_byte_arr: input hex string should not be empty", bytearray()]

        if not inp_len % 2 == 0:
            return ["__hex_str_to_byte_arr: input hex string length '{0}' is not even".format(inp_len), bytearray()]

        if re.fullmatch(r"^[0-9a-fA-F]+$", inp_str) == None:
            return ["__hex_str_to_byte_arr: input hex string contains invalid symbol(s)", bytearray()]

        hex_table = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 0, 0, 0, 0, 0, 0, 10, 11, 12, 13, 14, 15, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 10, 11, 12, 13, 14, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]

        out_len = inp_len >> 1
        out_arr = bytearray(out_len)

        inp_idx = 0
        for i in range(out_len):
            out_arr[i] = hex_table[byte_str[inp_idx]] << 4
            inp_idx += 1
            out_arr[i] |= hex_table[byte_str[inp_idx]]
            inp_idx += 1

        return ["", out_arr]

    def __byte_arr_to_hex_str(self, inp_arr):
        inp_len = len(inp_arr)
        if inp_len == 0:
            return ["__byte_arr_to_hex_str: input byte  array should not be empty", ""]

        out_len = inp_len << 1
        out_str = " " * out_len

        hex_chars = [*range(ord('0'), ord('9') + 1), *range(ord('a'), ord('f') + 1)]

        out_arr = bytearray(out_len)

        out_idx = 0
        for i in range(inp_len):
            ch = inp_arr[i]
            out_arr[out_idx] = hex_chars[ch >> 4]
            out_idx += 1
            out_arr[out_idx] = hex_chars[ch & 0x0f]
            out_idx += 1

        return ["", out_arr.decode()]

    def __address_to_hex(self, address: int):
        try:
            address_hex = hex(address)
        except BaseException as err:
            return ["__address_to_hex: {0}".format(err), ""]

        if len(address_hex) > 10:
            return ["__address_to_hex: address is out of range: {0}".format(address), ""]

        return ["", address_hex]

    def __send_cmd_regex_helper(self, menu_level: str, command: str, pattern: str, timeout: int):
        try:
            pat = re.compile(pattern)
        except re.error as err:
            return ["__send_cmd_regex_helper: {0}".format(err), ""]

        responce_data = []
        [error_str, responce_data] = self.send_cmd(menu_level, command, [1], timeout)
        if error_str:
            return [error_str, ""]

        res = re.search(pat, responce_data[0])
        if not res:
            return ["'{0}': wrong responce: '{1}'".format(command, responce_data[0]), ""]

        if len(res.groups()) >= 2:
            return ["", res.group(2)]

        return ["", ""]

    def __get_devreg_flash_crc32_hex_helper(self, address: int, length: int):
        [error_str, address_hex] = self.__address_to_hex(address)
        if error_str:
            return ["__get_devreg_flash_write_helper: {0}".format(error_str), ""]

        command = "flash crc32 {0} {1}".format(address_hex, length)
        pattern = "(^Devreg flash crc32: addr=0x[0-9a-fA-F]+, length=\d+: )(0x[0-9a-fA-F]+$)"
        [error_str, mem_crc_str] = self.__send_cmd_regex_helper("devreg", command, pattern, self.CMD_TOUT_FLASH_CRC32)
        return [error_str, mem_crc_str.lower()]

    def __get_devreg_table_size_int_helper(self):
        pattern = "(^Devreg data table size: )(\d+$)"
        [error_str, table_cnt_str] = self.__send_cmd_regex_helper("devreg", "table size", pattern,
                                                                  self.CMD_TOUT_DEFAULT)
        if error_str:
            return [error_str, ""]

        try:
            table_cnt = int(table_cnt_str)
        except BaseException as err:
            return ["__get_devreg_table_size_int_helper: {0}".format(err), 0]

        return ["", table_cnt]

    def __get_devreg_flash_size_int_helper(self):
        pattern = "(^Devreg flash size: )(\d+$)"
        [error_str, flash_size_str] = self.__send_cmd_regex_helper("devreg", "flash size", pattern,
                                                                   self.CMD_TOUT_DEFAULT)
        if error_str:
            return [error_str, ""]

        try:
            flash_size = int(flash_size_str)
        except BaseException as err:
            return ["__get_devreg_flash_size_int_helper: {0}".format(err), 0]

        return ["", flash_size]

    def __get_devreg_flash_write_helper(self, address: int, size: int, hex_str: str):
        [error_str, address_hex] = self.__address_to_hex(address)
        if error_str:
            return "__get_devreg_flash_write_helper: {0}".format(error_str)

        command = "flash write {0} {1} {2}".format(address_hex, size, hex_str)
        pattern = "^Devreg flash write: addr=0x[0-9a-fA-F]+, length=\d+: done$"
        [error_str, tmp_str] = self.__send_cmd_regex_helper("devreg", command, pattern, self.CMD_TOUT_DEFAULT)
        return error_str

    def __get_devreg_flash_erase_helper(self, address: int, size: int):
        [error_str, address_hex] = self.__address_to_hex(address)
        if error_str:
            return "__get_devreg_flash_erase_helper: {0}".format(error_str)

        command = "flash erase {0} {1}".format(address, size)
        pattern = "^Devreg flash erase: "
        [error_str, tmp_str] = self.__send_cmd_regex_helper("devreg", command, pattern, self.CMD_TOUT_FLASH_ERASE)
        return error_str

    def __devreg_check_sec_helper(self):
        pattern = "(^Devreg check sec: )([a-zA-Z]+$)"
        [error_str, check_sec_str] = self.__send_cmd_regex_helper("devreg", "check", pattern, self.CMD_TOUT_CHECK_SEC)
        return [error_str, check_sec_str]

    def read_devreg_helper_and_flash_data(self, helper_text_file: str, flash_binary_file: str):
        if not helper_text_file and not flash_binary_file:
            return "read_devreg_helper_and_flash_data: at least one file name (helper / flash) should not be empty"

        error_str = ""

        [error_str, ret] = self.enter_sublevel("devreg")

        while True:
            if error_str:
                break

            [error_str, table_cnt] = self.__get_devreg_table_size_int_helper()
            if error_str:
                break

            [error_str, table_data] = self.send_cmd("devreg", "table read", [table_cnt], self.CMD_TOUT_TABLE_READ)
            if error_str:
                break

            bin_data = bytearray()
            found = False
            for line in table_data:
                res = re.search(r"(^field=flash_eeprom,format=hex,value=)([0-9a-fA-F]+$)", line)
                if res:
                    found = True
                    [error_str, bin_data] = self.__hex_str_to_byte_arr(res.group(2))
                    break

            if error_str:
                break

            if not found:
                error_str = "read_devreg_helper_and_flash_data: could not found flash_eeprom field"
                break

            file_crc = "".join("0x{0:08x}".format(zlib.crc32(bin_data) & 0xffffffff))

            [error_str, mem_crc] = self.__get_devreg_flash_crc32_hex_helper(0, len(bin_data))
            if error_str:
                break

            if not file_crc == mem_crc:
                error_str = "read_devreg_helper_and_flash_data: calculated crc ({0}) and requested crc ({1}) are not the same".format(
                    file_crc, mem_crc)
                break

            if helper_text_file:
                try:
                    with open(helper_text_file, 'w') as f:
                        for line in table_data:
                            f.write(line)
                            f.write('\n')
                        f.close()
                except BaseException as err:
                    error_str = "read_devreg_helper_and_flash_data: {0}".format(err)
                    break

            if flash_binary_file:
                try:
                    with open(flash_binary_file, 'wb') as f:
                        f.write(bin_data)
                        f.close()
                except BaseException as err:
                    error_str = "read_devreg_helper_and_flash_data: {0}".format(err)
                    break

            break

        [err, ret] = self.exit_sublevel()

        if error_str:
            return error_str

        return err

    def read_devreg_flash_data(self, flash_binary_file: str):
        if not flash_binary_file:
            return "read_devreg_flash_data: flash file name should not be empty"

        return self.read_devreg_helper_and_flash_data("", flash_binary_file)

    def write_devreg_flash_data(self, flash_binary_file: str):
        if not flash_binary_file:
            return "write_defreg_flash_data: flash file name should not be empty"

        if not file_exists(flash_binary_file):
            return "write_defreg_flash_data: file '{0}' does not exists".format(basename(flash_binary_file))

        file_stats = os.stat(flash_binary_file)
        file_size = file_stats.st_size

        if file_size == 0:
            return "write_defreg_flash_data: write_defreg_flash_data: file '{0}' is empty".format(
                basename(flash_binary_file))

        error_str = ""

        [error_str, ret] = self.enter_sublevel("devreg")

        while True:
            if error_str:
                break

            [error_str, flash_size] = self.__get_devreg_flash_size_int_helper()
            if error_str:
                break

            if file_size > flash_size:
                error_str = "write_defreg_flash_data: wile size ({0}) is greater than flash size ({1})".format(
                    file_size, flash_size)
                break

            error_str = self.__get_devreg_flash_erase_helper(0, file_size)
            if error_str:
                break

            prev_crc = 0
            try:
                with open(flash_binary_file, "rb") as f:
                    address = 0
                    while address < file_size:
                        write_len = file_size - address
                        if write_len > self._write_block_size:
                            write_len = self._write_block_size

                        read_data = f.read(write_len)
                        prev_crc = zlib.crc32(read_data, prev_crc)

                        all_ff = True
                        for b in read_data:
                            if not int(b) == 255:
                                all_ff = False
                                break

                        if not all_ff:
                            [error_str, hex_str] = self.__byte_arr_to_hex_str(read_data)
                            if error_str:
                                break

                            error_str = self.__get_devreg_flash_write_helper(address, write_len, hex_str)
                            if error_str:
                                break

                        address += write_len

                    f.close()

            except BaseException as err:
                error_str = "write_defreg_flash_data: {0}".format(err)
                break

            if error_str:
                break

            file_crc = "".join("0x{:08x}".format(prev_crc & 0xffffffff))

            [error_str, mem_crc] = self.__get_devreg_flash_crc32_hex_helper(0, file_size)
            if error_str:
                break

            if not file_crc == mem_crc:
                error_str = "write_defreg_flash_data: calculated crc ({0}) and requested crc ({1}) are not the same".format(
                    file_crc, mem_crc)
                break

            break

        [err, ret] = self.exit_sublevel()

        if error_str:
            return error_str

        return err

    def devreg_check_sec(self):
        [error_str, ret] = self.enter_sublevel("devreg")

        check_status = ""

        while True:
            if error_str:
                break

            [error_str, check_status] = self.__devreg_check_sec_helper()
            if error_str:
                break

            break

        [err, ret] = self.exit_sublevel()
        if err:
            return [err, ""]

        if error_str:
            return [error_str, ""]

        return ["", check_status]

    def read_mac(self):
        pattern = "(^MAC: )([0-9A-F]{12}$)"
        [error_str, serial_str] = self.__send_cmd_regex_helper("main", "showmac", pattern, self.CMD_TOUT_DEFAULT)
        return [error_str, serial_str]

    def read_serial(self):
        pattern = "(^Serial: )([0-9A-Z]{13}$)"
        [error_str, serial_str] = self.__send_cmd_regex_helper("main", "serial read", pattern, self.CMD_TOUT_DEFAULT)
        return [error_str, serial_str]

    def write_serial(self, serial: str):
        pattern = "(^Serial is programmed!$)"
        command = "serial write {0}".format(serial)
        [error_str, tmp_str] = self.__send_cmd_regex_helper("main", command, pattern, self.CMD_TOUT_DEFAULT)
        return error_str

    def close_fcd(self):
        # If do back to T1, self.key_dir should be None and do not check blacklist
        if self.key_dir:
            self.check_blacklist()

        self.test_result = 'Pass'
        time.sleep(2)
        exit(0)
