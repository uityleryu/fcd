#!/usr/bin/python3
import sys
import time


def msg(no, out):
    pstr = ""
    if (no != ""):
        pstr = "\n=== " + str(no) + " ==="
    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S] ", time.gmtime())
    print("\n" + pstr + "\n" + nowtime + out + "\n\n\n")


def log_error(msg):
    erstr = "\n* * * ERROR: * * *"
    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S] ", time.gmtime())
    print("\n" + erstr + "\n" + nowtime + msg + "\n\n")


def log_debug(msg):
    pstr = "\nDEBUG:"
    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S] ", time.gmtime())
    print("\n" + pstr + "\n" + nowtime + msg + "\n\n")


def error_critical(msg):
    log_error(msg)
    time.sleep(1)
    sys.exit(2)
