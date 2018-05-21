#!/usr/bin/python3.6

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import time
import sys
import subprocess

def msg(no, out):
    pstr = ""
    if (no != ""):
        pstr = "\n=== "+str(no)+" ===";

    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S] ", time.gmtime())
    print("\n"+pstr+"\n"+nowtime+out+"\n\n\n")

def log_error(msg):
    erstr = "\n* * * ERROR: * * *"
    nowtime = time.strftime("[FCD %Y-%m-%d %H:%M:%S]", time.gmtime())
    print("\n"+erstr+"\n"+nowtime+msg+"\n\n")

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
    print("Joe: in pcmd, cmd: "+cmd)
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