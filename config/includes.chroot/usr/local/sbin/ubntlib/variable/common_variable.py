#!/usr/bin/python3
import os

class CommonVariable(object):

    def __init__(self, args):

        #prompt related
        self.bootloader_prompt = "u-boot>"
        self.linux_prompt = "#"
        self.cmd_prefix = r"go $ubntaddr "

        self.tftp_server = "192.168.1.19"

        #DU log-in info
        self.user = "ubnt"
        self.password = "ubnt"

        #fcd related
        self.fcd_user = "user"
        self.fcd_version_info_file = "version.txt"
        self.fcd_version_info_file_path = os.path.join("/home", self.fcd_user, "Desktop", self.fcd_version_info_file)

    def print_variables(self):
        print("user:" + str(self.user))
        print("password:" + str(self.password))
        print("tftp_server:" + str(self.tftp_server))

