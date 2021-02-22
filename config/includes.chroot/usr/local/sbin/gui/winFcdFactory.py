#!/usr/bin/python3

import sys
import time
import os
import re
import logging
import subprocess
import data.constant as CONST
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject, GLib
from gui.fraMonitorPanel import fraMonitorPanel
from gui.dlgUserInput import dlgUserInput
from ubntlib.fcd.common import Common
from ubntlib.gui.msgdialog import msgerrror

'''
    Prefix expression
        fra    : Gtk.Frame
        ety    : Gtk.Entry
        cmbb   : Gtk.ComboBox
        lbl    : Gtk.Lable
        btn    : Gtk.Button
        cbtn   : Gtk.CheckButton
        txv    : Gtk.TextView
        scl    : Gtk.ScrolledWindow
        epd    : Gtk.Expander
        mgdi   : Gtk.MessageDialog
        lsr    : Gtk.ListStore
        crt    : Gtk.CellRendererText
        dlg    : Gtk.Dialog
        ntb    : Gtk.Notebook
        txb    : Gtk.TextBuffer
        txi    : Gtk.TextIter
'''
log = logging.getLogger('uigui')


class winFcdFactory(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        self.xcmd = Common().xcmd

        # vboxdashboard used to show each DUT information
        self.vboxdashboard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.vboxdashboard2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.hboxdashboard = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.lblflavor = Gtk.Label("Flavor: ")
        self.lblprod = Gtk.Label('')

        # set the FCD host IP
        self.lblhostip = Gtk.Label("FCD host IP:")
        self.etyhostip = Gtk.Entry()
        self.etyhostip.set_text(CONST.fcdhostip)
        self.etyhostip.connect("changed", self.on_etyhostip_changed)

        # Enable to set the FCD host IP
        self.cbtnsethostip = Gtk.CheckButton("Enable-set-host-IP")
        if CONST.hostipsetenable is True:
            self.etyhostip.set_editable(True)
            self.etyhostip.set_sensitive(True)
            self.cbtnsethostip.set_active(True)
        else:
            self.etyhostip.set_editable(False)
            self.etyhostip.set_sensitive(False)
            self.cbtnsethostip.set_active(False)

        self.cbtnsethostip.connect("toggled", self.on_cbtnsethostip_toggled)

        self.hboxdashboard.pack_start(self.lblhostip, False, False, 0)
        self.hboxdashboard.pack_start(self.etyhostip, False, False, 0)
        self.hboxdashboard.pack_start(self.cbtnsethostip, False, False, 0)

        self.slot1 = fraMonitorPanel("0", "Slot 1")
        self.slot2 = fraMonitorPanel("1", "Slot 2")
        self.slot3 = fraMonitorPanel("2", "Slot 3")
        self.slot4 = fraMonitorPanel("3", "Slot 4")
        self.slot5 = fraMonitorPanel("4", "Slot 5")
        self.slot6 = fraMonitorPanel("5", "Slot 6")
        self.slot7 = fraMonitorPanel("6", "Slot 7")
        self.slot8 = fraMonitorPanel("7", "Slot 8")

        self.vboxdashboard.pack_start(self.lblflavor, False, False, 0)
        self.vboxdashboard.pack_start(self.lblprod, False, False, 0)
        self.vboxdashboard.pack_start(self.hboxdashboard, False, False, 0)
        self.vboxdashboard.pack_start(self.slot1, False, False, 0)
        self.vboxdashboard.pack_start(self.slot2, False, False, 0)
        self.vboxdashboard.pack_start(self.slot3, False, False, 0)
        self.vboxdashboard.pack_start(self.slot4, False, False, 0)
        self.vboxdashboard2.pack_start(self.slot5, False, False, 0)
        self.vboxdashboard2.pack_start(self.slot6, False, False, 0)
        self.vboxdashboard2.pack_start(self.slot7, False, False, 0)
        self.vboxdashboard2.pack_start(self.slot8, False, False, 0)

        self.epdslot = Gtk.Expander()
        self.epdslot.set_label('More Slots')
        self.epdslot.set_expanded(False)
        self.epdslot.add(self.vboxdashboard2)

        self.ntbmsg = Gtk.Notebook()
        self.ntbmsg.append_page(self.slot1.scllog, Gtk.Label("Slot 1"))
        self.ntbmsg.append_page(self.slot2.scllog, Gtk.Label("Slot 2"))
        self.ntbmsg.append_page(self.slot3.scllog, Gtk.Label("Slot 3"))
        self.ntbmsg.append_page(self.slot4.scllog, Gtk.Label("Slot 4"))
        self.ntbmsg.append_page(self.slot5.scllog, Gtk.Label("Slot 5"))
        self.ntbmsg.append_page(self.slot6.scllog, Gtk.Label("Slot 6"))
        self.ntbmsg.append_page(self.slot7.scllog, Gtk.Label("Slot 7"))
        self.ntbmsg.append_page(self.slot8.scllog, Gtk.Label("Slot 8"))

        # operation log
        self.epdoplog = Gtk.Expander()
        self.epdoplog.set_label('Output of production scripts')
        self.epdoplog.set_expanded(False)
        self.epdoplog.add(self.ntbmsg)

        # Main window
        self.vboxMainWindow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.vboxMainWindow.pack_start(self.vboxdashboard, False, False, 0)
        self.vboxMainWindow.pack_start(self.epdslot, False, False, 0)
        self.vboxMainWindow.pack_start(self.epdoplog, True, True, 0)
        self.set_title("UBNT FCD factory program")
        self.set_border_width(2)
        self.set_default_size(640, 480)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.add(self.vboxMainWindow)

    def on_etyhostip_changed(self, entry):
        __FUNC = sys._getframe().f_code.co_name
        fcdhostip = self.etyhostip.get_text()
        CONST.fcdhostip = fcdhostip.strip()
        rtmsg = "{0}: the FCD host IP: {1}".format(__FUNC, CONST.fcdhostip)
        log.info(rtmsg)

    def on_cbtnsethostip_toggled(self, button):
        __FUNC = sys._getframe().f_code.co_name
        CONST.hostipsetenable = not CONST.hostipsetenable
        if CONST.hostipsetenable is True:
            self.etyhostip.set_editable(True)
            self.etyhostip.set_sensitive(True)
        else:
            self.etyhostip.set_editable(False)
            self.etyhostip.set_sensitive(False)

        rtmsg = "{0}: CONST.hostipsetenable: {1}".format(__FUNC, CONST.hostipsetenable)
        log.info(rtmsg)

    def envinitial(self):
        if self.network_status_set() is False:
            msgerrror(self, "Network configure failed. Exiting...")
            return False

        if self.find_usb_storage() is False:
            msgerrror(self, "No USB storage found. Exiting...")
            return False

        if self.check_key_files() is False:
            msgerrror(self, "Security key files missing. Exiting...")
            return False

        if self.check_comport() is False:
            msgerrror(self, "Check host ttys failed. Exiting...")
            return False

        if self.call_input_dlg() is False:
            msgerrror(self, "Inputs information incorrect. Exiting...")
            return False

        return True

    def net_setting_inspect(self, fd, cond, proc):
        if (cond == GLib.IO_HUP):
            proc.poll()
            if (proc.returncode != 0):
                self.dialog.response(Gtk.ResponseType.NO)
            else:
                self.dialog.response(Gtk.ResponseType.YES)

            return False

    def network_status_set(self):
        self.dialog = Gtk.MessageDialog(
            self, 0,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.CANCEL,
            "Initializing environment, please wait.")

        self.dialog.format_secondary_text("Press cancel button to stop setting and close program")

        netpath = os.path.join(CONST.app_dir, "prod-network.sh")
        cmd = "sudo sh {0} {1}".format(netpath, CONST.fcdhostip)
        output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        GObject.io_add_watch(
            output.stdout,
            GLib.IO_HUP,
            self.net_setting_inspect,
            output)

        resp = self.dialog.run()
        self.dialog.destroy()
        if resp == Gtk.ResponseType.CANCEL:
            output.kill()
            exit(0)
        elif resp == Gtk.ResponseType.NO or output.returncode != 0:
            return False
        else:
            return True

    def find_usb_storage(self):
        __FUNC = sys._getframe().f_code.co_name
        cmd = "ls -ls /dev/disk/by-id | grep usb-"
        [stdout, rtc] = self.xcmd(cmd)
        """
        Linux shell script return code:
            pass: 0
            failed: 1
        """
        if (rtc == 1):
            rtmsg = "{0}: USB disk is not existed".format(__FUNC)
            log.info(rtmsg)
            return False

        stdoutarray = stdout.splitlines()
        for row in stdoutarray:
            device = row.split("/")[-1]
            rtmsg = "{0}: Device: {1}".format(__FUNC, device)
            log.info(rtmsg)

            fh = open("/proc/mounts", "r")
            line = fh.readline()
            while line:
                if re.search(device, line):
                    tmp = line.split(" ")
                    if (tmp[1] and tmp[1] != "/cdrom"):
                        CONST.usbrootdir = tmp[1]
                        # EX: /media/usbdisk/reg_logs
                        CONST.logdir = os.path.join(tmp[1], "reg_logs")
                        rtmsg = "{0}: found storage: {1}".format(__FUNC, CONST.logdir)
                        log.info(rtmsg)
                        fh.close()
                        return True

                line = fh.readline()

            fh.close()

        rtmsg = "{0}: No USB storage found".format(__FUNC)
        log.info(rtmsg)

        return False

    def check_key_files(self):
        __FUNC = sys._getframe().f_code.co_name
        CONST.keydir = "{0}/keys/".format(CONST.usbrootdir)
        log.info(CONST.keydir)

        for name in CONST.keyfilenames:
            rtmsg = "{0}: keyfile: {1}".format(__FUNC, name)
            log.info(rtmsg)
            tf = os.path.join(CONST.keydir, name)
            if os.path.isfile(tf) is False:
                rtmsg = "{0}: {1} doesn't exist!!".format(__FUNC, name)
                log.info(rtmsg)

                return False

        return True

    def check_comport(self):
        if (CONST.active_product_series != "UniFiVideo"):
            __FUNC = sys._getframe().f_code.co_name
            cmd = "ls /dev | grep 'ttyUSB\|ttyACM'"
            log.info("search tty cmd: " + cmd)
            [stdout, rtc] = self.xcmd(cmd)

            """
            Linux shell script return code:
                pass: 0
                failed: 1
            """
            if (rtc == 1):
                rtmsg = "{0}: serial port devices are not existed".format(__FUNC)
                log.info(rtmsg)
                return False

            exist_tty = stdout.splitlines()
            for itty in exist_tty:
                cmd = "stty -F /dev/{0} speed 115200 > /dev/null 2>/dev/null".format(itty)
                [stdout, rtc] = self.xcmd(cmd)
                if (rtc == 1):
                    rtmsg = "{0}: stty setting failed".format(__FUNC)
                    log.info(rtmsg)
                    return False

                CONST.active_tty.append(itty)
        else:
            CONST.active_tty.append("ttyUSB0")        

        num = len(CONST.active_tty)
        self.slot1.apply_comport_item(CONST.active_tty)
        self.slot2.apply_comport_item(CONST.active_tty)
        self.slot3.apply_comport_item(CONST.active_tty)
        self.slot4.apply_comport_item(CONST.active_tty)
        self.slot5.apply_comport_item(CONST.active_tty)
        self.slot6.apply_comport_item(CONST.active_tty)
        self.slot7.apply_comport_item(CONST.active_tty)
        self.slot8.apply_comport_item(CONST.active_tty)

        id = 0
        if id < num:
            self.slot1.cmbbcomport.set_active(id)
            id += +1

        if id < num:
            self.slot2.cmbbcomport.set_active(id)
            id += +1

        if id < num:
            self.slot3.cmbbcomport.set_active(id)
            id += +1

        if id < num:
            self.slot4.cmbbcomport.set_active(id)
            id += +1

        if id < num:
            self.slot5.cmbbcomport.set_active(id)
            id += +1

        if id < num:
            self.slot6.cmbbcomport.set_active(id)
            id += +1
        if id < num:
            self.slot7.cmbbcomport.set_active(id)
            id += +1
        if id < num:
            self.slot8.cmbbcomport.set_active(id)
            id += +1

        return True

    def call_input_dlg(self):
        __FUNC = sys._getframe().f_code.co_name
        dialog = dlgUserInput(self)

        rt = False
        while rt is False:
            response = dialog.run()
            if (response == Gtk.ResponseType.OK):
                rtmsg = "{0}: the OK button was clicked".format(__FUNC)
                log.info(rtmsg)
                if CONST.feature == "register":
                    result = dialog.check_inputs_reg()
                else:
                    result = dialog.check_inputs_bta()

                if result is False:
                    msgerrror(self, "Any one of inputs is not correct")
                    response = ""
                    rt = False
                else:
                    idx = CONST.active_productidx
                    title = "%s, %s" % (CONST.active_product_obj['DESC'], CONST.active_product_obj['BOMREV'])
                    self.lblprod.set_text(title)
                    self.slot1.set_bomrev(CONST.active_bomrev)
                    self.slot1.set_region(CONST.active_region)
                    self.slot1.set_product(CONST.active_product)
                    self.slot2.set_bomrev(CONST.active_bomrev)
                    self.slot2.set_region(CONST.active_region)
                    self.slot2.set_product(CONST.active_product)
                    self.slot3.set_bomrev(CONST.active_bomrev)
                    self.slot3.set_region(CONST.active_region)
                    self.slot3.set_product(CONST.active_product)
                    self.slot4.set_bomrev(CONST.active_bomrev)
                    self.slot4.set_region(CONST.active_region)
                    self.slot4.set_product(CONST.active_product)
                    self.slot5.set_bomrev(CONST.active_bomrev)
                    self.slot5.set_region(CONST.active_region)
                    self.slot5.set_product(CONST.active_product)
                    self.slot6.set_bomrev(CONST.active_bomrev)
                    self.slot6.set_region(CONST.active_region)
                    self.slot6.set_product(CONST.active_product)
                    self.slot7.set_bomrev(CONST.active_bomrev)
                    self.slot7.set_region(CONST.active_region)
                    self.slot7.set_product(CONST.active_product)
                    self.slot8.set_bomrev(CONST.active_bomrev)
                    self.slot8.set_region(CONST.active_region)
                    self.slot8.set_product(CONST.active_product)
                    rt = True
            else:
                rtmsg = "{0}: the Cancel button was clicked".format(__FUNC)
                log.info(rtmsg)
                rt = True

        dialog.destroy()

        return True
