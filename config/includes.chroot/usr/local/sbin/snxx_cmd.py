#!/usr/bin/python3

from soc_lib.snxx_lib import SnxxLib
import sys
import os
import argparse
from argparse import RawTextHelpFormatter
from os.path import exists as file_exists
from os.path import basename as file_basename

def parse_range(numbers: str):
    ids = []

    if not numbers:
        return ids

    for x in numbers.split(','):
        x = x.strip()
        if x.isdigit():
            ids.append(int(x))
        elif x[0] == '<':
            ids.extend(range(1,int(x[1:])))
        elif '-' in x:
            xr = x.split('-')
            ids.extend(range(int(xr[0].strip()), int(xr[1].strip())+1))
        else:
            raise ValueError(f"Unknown range specified: {x}")

    return ids

def TradArg():
    ap = argparse.ArgumentParser(description='[Sonix simple cmd wrapper]\n'
                                'SonixBridge module allows to do more than this wrapper like send command in the selected menu level\n'
                                'This allows to save some time in case if a lot of small commands should be sent on the menu sublevel\n'
                                'Also prepare_cmd() method (takes more than 0.5 sec) should be called once before communicating with a board\n\n'
                                'This wrapper does next things before running commands by calling prepare_cmd() method:\n'
                                ' a. set loglevel to 0\n'
                                ' b. try to back from the menu sublevel 0\n'
                                ' a. try to read all chars from the serial port\n\n'
                                '--greeting used for all commands, --sublevel, --level, --answer_lines and --timeout used only for --command\n'
                                'Script may send unwrapped command using --command, navigate in menu using --sublevel or --back\n'
                                'or call a function (command without short form)\n'.format(os.path.basename(__file__)),formatter_class=RawTextHelpFormatter)
    ap.add_argument('-u', '--uart_dev', metavar="DEV", help="[Uart dev] eg, /dev/ttyUSB0", required=True)
    ap.add_argument('-k', '--skip_prepare', help="[Skip prepare] skip prepare command", default=False, action='store_true')
    ap.add_argument('-s', '--sublevel', metavar="LVL", help="[Menu sublevel], select menu sublevel, will do next if --command is present:\nsend command and return from the sublevel to the main menu level", default="")
    ap.add_argument('-l', '--level', metavar="LVL", help="[Menu level], send command in this menu level, should not be used with --sublevel", default="")
    ap.add_argument('-b', '--back', help="[Back], back to the 'main' menu level, should not be used with --sublevel and --command", default=False, action='store_true')
    ap.add_argument('-c', '--command', metavar="CMD", help="[Command] eg, \"serial read\", use \"main\" level if --sublevel and --level are not set")
    ap.add_argument('-a', '--answer_lines', metavar="LINES", help="[Answer lines range] eg, \"<2,4-6,8\" (will be expanded to [1,4,5,6,8]), will be checked if present", default="")
    ap.add_argument('-g', '--greeting', metavar="GRT", help="[Board greeting] eg, \"SONIX \"", default="SONIX ")
    ap.add_argument('-t', '--timeout', metavar="TOUT", help="[Command timeout] in sec, default 3, some commands required longer timeout", type=int, default=3)
    ap.add_argument('--read_d_table', metavar="FNAME", help="[Read devreg data table] devred data table to file", default="")
    ap.add_argument('--read_d_mem', metavar="FNAME", help="[Read devreg memory to binary file] reads entire devreg memory to file", default="")
    ap.add_argument('--write_d_mem', metavar="FNAME", help="[Write binary file to devreg memory] reads entire devreg memory to file", default="")
    ap.add_argument('--check_sec', help="[run check sec] run security check", default=False, action='store_true')
    ap.add_argument('--read_mac', help="[Read MAC] read device MAC address", default=False, action='store_true')
    ap.add_argument('--read_serial', help="[Read serial] read device serial number", default=False, action='store_true')
    ap.add_argument('--write_serial', metavar="SERIAL", help="[Write serial] write device serial number", default="")
    return ap

def main(argv):
    ap = TradArg()
    args = ap.parse_args()

    uart_dev = args.uart_dev
    skip_prepare = args.skip_prepare
    menu_sublevel = args.sublevel
    menu_level = args.level
    menu_back = args.back
    command = args.command
    answer_lines_arg = args.answer_lines
    answer_lines_cnts = []
    board_greeting = args.greeting
    timeout = args.timeout
    read_d_table_file = args.read_d_table
    read_d_mem_file = args.read_d_mem
    write_d_mem_file = args.write_d_mem
    check_sec = args.check_sec
    read_mac = args.read_mac
    read_serial = args.read_serial
    write_serial = args.write_serial

    try:
        answer_lines_cnts = parse_range(answer_lines_arg)
    except BaseException as err:
        sys.exit("Error: {0}".format(err))

    if write_d_mem_file and not file_exists(write_d_mem_file):
        sys.exit("Error: File '{0}' does not exists".format(write_d_mem_file))

    result = []

    dev = SnxxLib()

    err = dev.open_serial_port(uart_dev)
    if err:
        sys.exit("Error: {0}".format(err))

    dev.board_greeting = board_greeting

    if not skip_prepare:
        # try to go back and then disable log
        err = dev.prepare_cmd()
        if err:
            sys.exit("Error: {0}".format(err))

    if menu_level:
        if menu_sublevel:
            sys.exit("Error: --level could not be used with --sublevel")

    if menu_back:
        if menu_sublevel:
            sys.exit("Error: --back could not be used with --sublevel")
        if command:
            sys.exit("Error: --back could not be used with --command")

    if not (menu_sublevel or menu_back or command or read_d_table_file or read_d_mem_file or write_d_mem_file or check_sec or read_mac or read_serial or write_serial):
        skip_prepare_info = "exit"
        if not skip_prepare:
            skip_prepare_info = "just do prepare cmd and exit"
        sys.exit("Nothing to do, {0}".format(skip_prepare_info))

    if menu_sublevel and not command:
        [err, result] = dev.enter_sublevel(menu_sublevel)
        if err:
            sys.exit("Error: {0}".format(err))

    if menu_back:
        [err, result] = dev.exit_sublevel()
        if err:
            sys.exit("Error: {0}".format(err))

    if command:
        if menu_level:
            [err, result] = dev.send_cmd(menu_level, command, answer_lines_cnts, timeout)
        else:
            # if menu_sublevel is empty - "main" level will be used
            [err, result] = dev.send_cmd_sublevel(menu_sublevel, command, answer_lines_cnts, timeout)
        if err:
            sys.exit("Error: {0}".format(err))

        print(*result, sep = "\n")

    if read_d_table_file or read_d_mem_file:
        err = dev.read_devreg_helper_and_flash_data(read_d_table_file, read_d_mem_file)
        if err:
            sys.exit("Error: {0}".format(err))

        if read_d_table_file:
            print("Read devreg table to '{0}' done".format(file_basename(read_d_table_file)))

        if read_d_mem_file:
            print("Read devreg memory to '{0}' done".format(file_basename(read_d_mem_file)))

    if write_d_mem_file:
        err = dev.write_devreg_flash_data(write_d_mem_file)
        if err:
            sys.exit("Error: {0}".format(err))

        print("File '{0}' is written to the devreg memory".format(file_basename(write_d_mem_file)))

    if check_sec:
        [err, status] = dev.devreg_check_sec()

        if err:
            sys.exit("Error: {0}".format(err))

        print("Check security status: {0}".format(status))

    if read_mac:
        [err, serial] = dev.read_mac()

        if err:
            sys.exit("Error: {0}".format(err))

        print("Read MAC: {0}".format(serial))

    if read_serial:
        [err, serial] = dev.read_serial()

        if err:
            sys.exit("Error: {0}".format(err))

        print("Read serial number: {0}".format(serial))

    if write_serial:
        err = dev.write_serial(write_serial)

        if err:
            sys.exit("Error: {0}".format(err))

        print("Serial number is programmed!")

if __name__ == '__main__':
    main(sys.argv[1:])
