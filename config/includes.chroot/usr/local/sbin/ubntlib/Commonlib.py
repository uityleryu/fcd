#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import time
import sys
import subprocess
import pexpect


class ExpttyProcess():
    def __init__(self, id, tty):
        self.id = id
        cmd = ["sudo picocom",
               tty,
               "-b 115200"]
        cmdstr = " ".join(str(x) for x in cmd)
        self.proc = pexpect.spawn(cmdstr, encoding='utf-8', codec_errors='replace')
        self.proc.logfile = sys.stdout
        self.proc.timeout = None

    def expect2act(self, tmo, exptxt, action):
        if (exptxt != ""):
#             self.proc.timeout = tmo
            rt = self.proc.expect(exptxt)
            time.sleep(0.2)
        else:
            rt = 1

        if (action != "") and (rt >= 0):
            self.proc.sendline(action)

        time.sleep(1)

#     def tftpgetfromhost(self, srfile, dstfile):
#         log_debug("Get"+srfile+"command from host to DUT ...")
#         sstr = ["tftp -g -r", srfile, "-l", dstfile, svip]
#         sstrj = ' '.join(sstr)
#         p.expect2act(30, lnxpmt, sstrj)

    def close(self):
        self.proc.close()


# class ExpttyProcess():
#     def __init__(self, id, tty):
#         self.id = id
#         cmd = ["sudo cu -l",
#                tty,
#                "-s 115200"]
#         cmdstr = " ".join(str(x) for x in cmd)
#         self.proc = pexpect.spawn(cmdstr, encoding='utf-8', codec_errors='replace' ,timeout=1200)
#         self.proc.logfile = sys.stdout
#   
#     def expect2act(self, timeout, exptxt, action):
#         rt = self.proc.expect(exptxt, timeout)
#         if (action != "") and (rt >= 0):
#             self.proc.sendline(action)
#   
#         time.sleep(0.1)
#   
#     def close(self):
#         self.proc.close()


# class ExpttyProcess():
#     def __init__(self, id, tty):
#         self.id = id
#         cmd = ["sudo screen",
#                tty,
#                "115200"]
#         cmdstr = " ".join(str(x) for x in cmd)
#         self.proc = pexpect.spawn(cmdstr, encoding='utf-8', timeout=1200)
#         self.proc.logfile = sys.stdout
#   
#     def expect2act(self, timeout, exptxt, action):
#         rt = self.proc.expect(exptxt, timeout)
#         if (action != "") and (rt >= 0):
#             self.proc.sendline(action)
#   
#         time.sleep(0.1)
#   
#     def close(self):
#         self.proc.close()


def msg(no, out):
    pstr = ""
    if (no != ""):
        pstr = "\n=== "+str(no)+" ===";

    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S] ", time.gmtime())
    print("\n"+pstr+"\n"+nowtime+out+"\n\n\n")


def log_error(msg):
    erstr = "\n* * * ERROR: * * *"
    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S] ", time.gmtime())
    print("\n"+erstr+"\n"+nowtime+msg+"\n\n")


def log_debug(msg):
    pstr = "\nDEBUG:"
    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S] ", time.gmtime())
    print("\n"+pstr+"\n"+nowtime+msg+"\n\n")


def error_critical(msg):
    log_error(msg)
    time.sleep(1)
    sys.exit(2)



def msgerrror(parent, msg):
    mgdimsg = Gtk.MessageDialog(parent,
                                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                Gtk.MessageType.ERROR,
                                Gtk.ButtonsType.CLOSE,
                                "")
    mgdimsg.format_secondary_text(msg)
    mgdimsg.run()
    mgdimsg.destroy()

def msginfo(parent, msg):
    mgdimsg = Gtk.MessageDialog(parent,
                                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                Gtk.MessageType.INFO,
                                Gtk.ButtonsType.NONE,
                                "")
    mgdimsg.format_secondary_text(msg)
    x = mgdimsg.run()
    print('The return x:'+str(x))
    z = mgdimsg.response(Gtk.ResponseType.OK)
    print('The return z:'+str(z))
    y = mgdimsg.destroy()
    print('The return y:'+str(y))


def pcmd(cmd):
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


def xcmd(cmd):
    output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    output.wait()
    [stdout, stderr] = output.communicate()
    stdoutd = stdout.decode()
    print(stdoutd)
    return [stdout, output.returncode]


def main():
    cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
    [sto, rtc] = xcmd(cmd)
    if (int(sto.decode()) > 0):
        error_critical("Caps Lock is on")
    else:
        log_debug("Caps Lock is off")

    cmd = "sudo chmod 777 /dev/ttyUSB0"
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("Can't set tty to 777 failed!!")
    else:
        log_debug("Configure tty to 777 successfully")

    time.sleep(0.5)

    cmd = "stty -F /dev/ttyUSB0 sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("stty configuration failed!!")
    else:
        log_debug("Configure stty successfully")

    time.sleep(0.5)
    p = ExpttyProcess(0, "/dev/ttyUSB0")
    rrt = p.proc.isatty()
    if rrt == True:
        print("Joe: is tty")
    p.expect2act(10, "", "\n")

#     p.expect2act(30, "Hit any key to stop autoboot:", "\n")

    sstr = ["tftp",
            "-g",
            "-r upgrade.tar",
            "-l /tmp/upgrade.tar",
            "192.168.1.19"]
    sstrj = ' '.join(sstr)
    p.expect2act(30, "#", sstrj)
    time.sleep(200)
    p.expect2act(200, "#", "\n")
    print("Joe: complete")


if __name__ == "__main__":
    main()
