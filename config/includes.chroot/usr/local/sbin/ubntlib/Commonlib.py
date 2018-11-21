#!/usr/bin/python3
from gi.repository import Gtk
from io import StringIO

import time
import sys
import subprocess
import pexpect
import logging
import gi
gi.require_version('Gtk', '3.0')


class ExpttyProcess():
    def __init__(self, id, cmd, newline, logger_name=None):
        self.id = id
        self.proc = pexpect.spawn(cmd, encoding='utf-8', codec_errors='replace', timeout=2000)
        self.proc.logfile_read = sys.stdout
        self.newline = newline
        # Using default logger shows message to stdout
        if(logger_name == None):
            self.log = logging.getLogger()
            self.log.setLevel(logging.DEBUG)
            log_stream = logging.StreamHandler(sys.stdout)
            log_stream.setLevel(logging.DEBUG)
            self.log.addHandler(log_stream)
        # Using customized logger shows message
        else:
            self.log = logging.getLogger(logger_name)

    '''return negative means error, return 0 means success'''
    def expect2actu1(self, timeout, exptxt, action):
        index = self.proc.expect([exptxt, pexpect.EOF, pexpect.TIMEOUT], timeout)
        if(index == 1):
            print("[ERROR:EOF]: Expect \"" + exptxt + "\"")
            exit(1)
        if(index == 2):
            print("[ERROR:Timeout]: Expect \"" + exptxt + "\" more than " + str(timeout) + " seconds")
            exit(1)

        if (action != ""):
            if (action == "enter"):
                self.proc.send(self.newline)
            else:
                self.proc.send(action + self.newline)

            time.sleep(0.05)
            self.proc.readline(1)

        return 0

    def expect2act(self, timeout, exptxt, action, rt_buf=None):
        sys.stdout = mystdout = StringIO()
        self.proc.logfile_read = sys.stdout

        # expect last time command buffer
        index = self.proc.expect([exptxt, pexpect.EOF, pexpect.TIMEOUT], timeout)
        if(index == 1):
            self.log.error("[ERROR:EOF]: Expect \"" + exptxt + "\"")
            return -1
        if(index == 2):
            self.log.error("[ERROR:Timeout]: Expect \"" + exptxt + "\" more than " + str(timeout) + " seconds")
            return -1

        sys.stdout = sys.__stdout__
        self.log.debug(mystdout.getvalue())

        # send action
        self.proc.send(action + self.newline)

        # re-init
        sys.stdout = mystdout = StringIO()
        self.proc.logfile_read = sys.stdout

        # capture action output message, if you pass not None rt_buf
        if(rt_buf != None):
            # read action output
            index = self.proc.expect([exptxt, pexpect.EOF, pexpect.TIMEOUT], timeout)
            if(index == 1):
                self.log.error("[ERROR:EOF]: Expect \"" + exptxt + "\"")
                return -1
            if(index == 2):
                self.log.error("[ERROR:Timeout]: Expect \"" + exptxt + "\" more than " + str(timeout) + " seconds")
                return -1

            sys.stdout = sys.__stdout__
            rt_buf.insert(0, mystdout.getvalue())
            self.log.debug(rt_buf[0])

            # only senf newline for getting hint
            self.proc.send(self.newline)

        sys.stdout = sys.__stdout__
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

