
#!/usr/bin/python3
"""
Base flash Editor class
"""
import sys
import time
import os
import stat
import filecmp
import argparse


class EditorBase(object):
    def __init__(self):
        self.input_args = self._init_parse_inputs()

    def _init_parse_inputs(self):
        parse = argparse.ArgumentParser(description="FCD tool args Parser")
        parse.add_argument('--fbin', '-fb', dest='file_bin', help='Binary file', default=None)
        parse.add_argument('--bom_rev', '-bom', dest='bom_rev', help='BOM revision', default=None)
        parse.add_argument('--sys_id', '-bid', dest='sys_id', help='System ID, ex:eb23, eb21', default=None)
        parse.add_argument('--mac', '-m', dest='mac', help='MAC address', default=None)
        parse.add_argument('--num_mac', '-mn', dest='num_mac', help='Number of MAC address', default=None)
        parse.add_argument('--num_wifi', '-wn', dest='num_wifi', help='Number of WiFi', default=None)
        parse.add_argument('--num_bt', '-bn', dest='num_bt', help='Number of Bluetooth', default=None)
        parse.add_argument('--region', '-r', dest='region', help='Region Code', default=None)
        parse.add_argument('--genkey', '-k', dest='genkey', help='Generate key', default=None)

        args, _ = parse.parse_known_args()
        self.file_bin = args.file_bin
        self.bom_rev = args.bom_rev
        self.sys_id = args.sys_id
        self.mac = args.mac.lower()
        self.num_mac = args.num_mac
        self.num_wifi = args.num_wifi
        self.num_bt = args.num_bt
        self.region = args.region
        self.genkey = self.genkey

        return args
