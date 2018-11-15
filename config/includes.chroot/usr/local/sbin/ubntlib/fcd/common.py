#!/usr/bin/python3
import subprocess
import time
import os
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical
from ubntlib.variable.common import CommonVariable

class Common(object):
    def __init__(self):
        self.__variable = CommonVariable()

    def print_current_fcd_version(self, file=None):
        out_log = "Using default file "+ self.__variable.fcd_version_info_file_path if file is None else \
                "Using file " + file
        file = self.__variable.fcd_version_info_file_path if file is None else file
        msg(no="", out=out_log)
        f = open(file, "r")
        line = f.readline()
        msg(no="", out="FCD version: " + line)
        f.close()

    def config_stty(self, dev=None):
        """
        config stty to 777 and set output to /dev/{dev}
        """
        if dev is None:
            error_critical(msg="dev is not assigned")
        else:
            cmd = "sudo chmod 777 /dev/" + dev
            [_, returncode] = self.xcmd(cmd)
            if (int(returncode) > 0):
                error_critical("Can't set tty to 777 failed!!")
            else:
                log_debug("Configure tty to 777 successfully")

            time.sleep(0.5)

            cmd = "stty -F /dev/" + dev +" sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
            [_, returncode] = self.xcmd(cmd)
            if (int(returncode) > 0):
                error_critical("stty configuration failed!!")
            else:
                log_debug("Configure stty successfully")

            time.sleep(0.5)

    def pcmd(self, cmd):
        output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output.wait()
        [stdout, stderr] = output.communicate()
        """
        Linux shell script return code:
            pass: 0
            failed: 1
        """
        if (output.returncode == 1):
            print("pcmd returncode: " + str(output.returncode))
            return False
        else:
            return True

    def xcmd(self, cmd):
        output = subprocess.Popen([cmd], shell=True, stderr=None, stdout=subprocess.PIPE)
        output.wait()
        [stdout, stderr] = output.communicate()
        stdoutd = stdout.decode()
        print(stdoutd)
        return [stdout, output.returncode]
