#!/usr/bin/python3
import os


class CommonVariable(object):

    def __init__(self):

        #prompt related
        self.bootloader_prompt = "u-boot>"
        self.linux_prompt = "#"
        self.cmd_prefix = r"go $ubntaddr "
     
        #DU log-in info
        self.user = "ubnt"
        self.password = "ubnt"

        #fcd related
        self.fcd_user = "user"
        self.fcd_version_info_file = "version.txt"
        self.fcd_version_info_file_path = os.path.join("/home", self.fcd_user, "Desktop", self.fcd_version_info_file)

        #images is saved at /tftpboot/images, tftp server searches files start from /tftpboot
        self.firmware_dir = "images"
        self.tftp_server_dir = "/tftpboot"

    def print_variables(self):
        print("user:" + str(self.user))
        print("password:" + str(self.password))
        print("tftp_server:" + str(self.tftp_server))

    def set_bootloader_prompt(self, prompt=None):
        if prompt != None:
            self.bootloader_prompt = prompt
        else:
            print("Nothing changed. Please assign promt!")

    def set_cmd_prefix(self, prefix=None):
        if prefix != None:
            self.cmd_prefix = prefix
        else:
            print("Nothing changed. Please assign prefix!")

    def set_linux_prompt(self, prompt=None):
        if prompt != None:
            self.linux_prompt = prompt
        else:
            print("Nothing changed. Please assign prompt!")
