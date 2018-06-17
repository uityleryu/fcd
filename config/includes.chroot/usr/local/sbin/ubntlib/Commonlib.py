#!/usr/bin/python3.6

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
        self.proc = pexpect.spawn(cmdstr, encoding='utf-8', codec_errors='replace', timeout=1200)
        self.proc.setecho(False)
        self.proc.logfile = sys.stdout

    def expect2act(self, timeout, exptxt, action):
        if (exptxt != ""):
            rt = self.proc.expect(exptxt, timeout)
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
    return [stdout, output.returncode]


def main():
    cmd = "stty -F /dev/ttyUSB0 sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
    [sto, rtc] = xcmd(cmd)
    t = ExpttyProcess(0, "/dev/ttyUSB0")
    t.expect2act(30, 'Hit any key to', "\n")
    t.expect2act(30, 'uboot>', "setenv ipaddr 192.168.1.31")
    t.expect2act(30, 'uboot>', "setenv serverip 192.168.1.11")
    t.expect2act(30, 'uboot>', "ping 192.168.1.11")
    t.expect2act(30, 'host 192.168.1.11 is alive', "")
    t.expect2act(30, 'uboot>', "printenv")
    t.expect2act(30, 'uboot>', "reset")
    t.expect2act(60, 'Please press Enter to activate', "\n")
    t.expect2act(30, 'UBNT login:', "ubnt")
    t.expect2act(30, 'Password:', "ubnt")
    t.expect2act(30, 'US.pcb-mscc', "\n")
    t.expect2act(30, 'US.pcb-mscc', "cat /proc/ubnthal/system.info")
    t.expect2act(30, 'US.pcb-mscc#', "info")


if __name__ == "__main__":
    main()
