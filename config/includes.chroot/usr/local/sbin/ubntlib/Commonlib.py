#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import time
import sys
import subprocess
import pexpect


class ExpttyProcess():
    def __init__(self, id, cmd, newline):
        self.id = id
        self.proc = pexpect.spawn(cmd, encoding='utf-8', codec_errors='replace', timeout=2000)
        self.proc.logfile_read = sys.stdout
        self.newline = newline

    '''return negative means error, return 0 means success'''
    def expect2act(self, timeout, exptxt, action):
        index = self.proc.expect([exptxt, pexpect.EOF, pexpect.TIMEOUT], timeout)
        if(index == 1):
            print("[ERROR:EOF]: Expect \"" + exptxt + "\"")
            return -1
        if(index == 2):
            print("[ERROR:Timeout]: Expect \"" + exptxt + "\" more than " + str(timeout) + " seconds")
            return -1
            
        self.proc.send(action + self.newline)
        return 0

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

    ''' This example is outdated 
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
    '''

    ''' telnet connection example of EOT450
    # Assign command of connection and newline character, 
      some machine newline is "\n" EX: UAP NANO HD
    conn = Commonlib.ExpttyProcess(0, "telnet 10.2.128.209", "\r")
    conn.expect2act(5, 'Username', "admin")
    conn.expect2act(5, 'Password', "")
    ...do someting...
    conn.expect2act(5, '#', "") #flush buffer(expect the last command and force output)
    '''    

    ''' UART connection example of EOT450
    conn = Commonlib.ExpttyProcess(0, "picocom /dev/ttyUSB0 -b 115200", "\r")
    conn.expect2act(5, '', "")
    conn.expect2act(5, 'Username', "admin")
    conn.expect2act(5, 'Password', "")
    ...do someting...
    conn.expect2act(5, '#', "")
    '''
    pass

if __name__ == "__main__":
    main()
