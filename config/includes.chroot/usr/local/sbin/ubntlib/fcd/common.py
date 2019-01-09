#!/usr/bin/python3
import subprocess
import time
import os
import sys

from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class Tee(object):
    """
    Tee class is kind of sys.stdout recorder
    in the __init__() of Tee class,
        sys.stdout = self

    If there is a snippet of code like
        Tee('/tmp/log.txt', 'w')
        sys.stdout.write("UBNT-test\n")

    it will regard the code as
        Tee('/tmp/log.txt', 'w')
        Tee.write("UBNT-test\n")

    Like C/C++ pointer
    """

    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        # sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def __enter__(self):
        pass

    def __exit__(self, _type, _value, _traceback):
        pass


class Common(object):
    def __init__(self):
        pass

    def print_current_fcd_version(self, file=None):
        if file is not None:
            out_log = "Version file " + file
            msg(no="", out=out_log)
            try:
                f = open(file, "r")
                line = f.readline()
                msg(no="", out="FCD version: " + line)
                f.close()
            except Exception as e:
                log_debug(str(e))
        else:
            log_debug("[print_current_fcd_version] No file path input")

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

            cmd = "stty -F /dev/" + dev + " sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
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

    @staticmethod
    def get_zeroconfig_ip(mac):
        mac.replace(":", "")

        b1 = str(int(mac[8:10], 16))
        b2 = str(int(mac[10:12], 16))

        if b2 == 0:
            b2 = 128
        elif b2 == 255:
            b2 = 127
        elif b2 == 19:
            b2 = 18

        print("zeroip: 169.254." + b1 + "." + b2)
        return "169.254." + b1 + "." + b2
