#!/usr/bin/python3

from gi.repository import Gtk, Gdk, GLib, GObject
from PAlib.Framework.gui.gui_variable import GPath, GCommon
from time import sleep
from PAlib.Framework.gui.msgdialog import msgerrror, msginfo
from PAlib.Framework.fcd.common import Common
from PAlib.ThirdParty.DHCPServer import dhcp

import gi
import re
import os
import subprocess
import time
import random
import threading
import shutil
import json
import sys

gi.require_version('Gtk', '3.0')

"""
    Prefix expression
        fra    : Gtk.Frame
        ety    : Gtk.Entry
        cmbb   : Gtk.ComboBox
        lbl    : Gtk.Lable
        btn    : Gtk.Button
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
"""


css = b"""
#pgrs_yellow {
    background-color: yellow;
}

#pgrs_green {
    background-color: #00FF00;
}

#pgrs_red {
    background-color: #FF0000;
}

#lbl_black {
    background-color: #D3D3D3;
    color: black;
    font-size: 15px;
}

#lbl_red {
    background-color: #D3D3D3;
    color: red;
    font-size: 15px;
}

#lbl_yellow {
    background-color: #D3D3D3;
    color: yellow;
    font-size: 15px;
}

#lbl_green {
    background-color: #D3D3D3;
    color: green;
    font-size: 15px;
}
"""


class fraMonitorPanel(Gtk.Frame):
    def __init__(self, id, frametitle):
        self.id = id
        Gtk.Frame.__init__(self, label=frametitle)
        self.xcmd = Common().xcmd
        self.devregready = False
        self.progressvalue = 0
        self.starttime = ""
        self.endtime = ""
        self.rtdevreg = 0
        self.x = False
        self.y = False
        self.z = False
        self.w = ""
        self.proc = ""

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.hbox.set_border_width(5)
        self.add(self.hbox)

        self.win = Gtk.Window()

        # Product
        self.etymac = Gtk.Entry()
        self.etymac.set_editable(False)
        self.etymac.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))

        self.etyip = Gtk.Entry()
        self.etyip.set_editable(False)
        self.etymac.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))

        # Progressing bar
        self.hboxpgrs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pgrbprogress = Gtk.ProgressBar()
        self.pgrbprogress.set_text("None")
        self.pgrbprogress.set_show_text(True)
        self.pgrbprogress.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))
        self.hboxpgrs.pack_start(self.pgrbprogress, True, True, 0)
        '''
        # start button
        self.btnstart = Gtk.Button()
        self.btnstart.set_label(" Start ")
        self.btnstart.set_focus_on_click(False)
        self.btnstart.connect("clicked", self.on_start_button_click)
        '''
        # Text view for showing log
        self.txvlog = Gtk.TextView()
        self.txvlog.set_editable(False)
        self.scllog = Gtk.ScrolledWindow()
        self.scllog.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scllog.set_size_request(100, 400)
        self.scllog.add(self.txvlog)
        self.txblog = self.txvlog.get_buffer()
        self.txilog = self.txblog.get_end_iter()
        self.endmark = self.txblog.create_mark("end", self.txilog, False)
        self.txblog.connect("insert-text", self.autoscroll)

        """
            A label to show the status: Idle, working, completed
        """
        self.lblresult = Gtk.Label('NONE')
        self.lblresult.set_size_request(100, 32)
        # self.lblresult.set_alignment(0.0, 0.0)
        self.lblresult.set_halign(Gtk.Align.CENTER)
        self.lblresult.set_valign(Gtk.Align.CENTER)
        lblresultcolorfont = '<span foreground="black" size="xx-large"><b>Idle....</b></span>'
        self.lblresult.set_markup(lblresultcolorfont)

        self.hbox.pack_start(self.etymac, False, False, 0)
        self.hbox.pack_start(self.etyip, False, False, 0)
        self.hbox.pack_start(self.hboxpgrs, True, True, 0)
        # self.hbox.pack_end(self.btnstart, False, False, 0)
        self.hbox.pack_end(self.lblresult, False, False, 0)

        GObject.timeout_add(700, self.panelstartconf, None)
        GObject.timeout_add(300, self.panelstepconf, None)
        GObject.timeout_add(700, self.panelendconf, None)

        # GObject.threads_init()
        Gdk.threads_init()

        self.templogfile = ""
        self.dev_mac = ""
        self.fwload_cnt = 0

        # self.loadr = fwloader()

    def on_cmbbcomport_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            GCommon.finaltty[int(self.id)] = model[tree_iter][0]

        print("The finaltty[%s]: %s " % (self.id, str(GCommon.finaltty[int(self.id)])))

    def autoscroll(self, iter, text, length, user_param1):
        self.txvlog.scroll_to_mark(self.endmark, 0.0, False, 1.0, 1.0)

    def apply_comport_item(self, items):
        self.lsritemlist.clear()
        for itty in items:
            self.lsritemlist.append([itty])

        return True

    def set_ip(self, ip):
        self.etyip.set_text(ip)

    def set_mac(self, mac):
        self.etymac.set_text(mac)

    def get_tty(self):
        combo = self.cmbbcomport
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            return model[tree_iter][0]

    def appendlog(self, text):
        self.txblog.insert(self.txilog, text)

    def panelstartconf(self, user_data):
        # print("Joe: in panelstartconf "+str(self.id))
        if (self.x is True):
            lblresultcolorfont = '<span background="darkgrey" foreground="yellow" size="xx-large"><b>Working....</b></span>'
            self.lblresult.set_markup(lblresultcolorfont)
            self.hboxpgrs.set_name("pgrs_yellow")
            self.pgrbprogress.set_text("Starting...")
            self.appendlog("\n--------[STARTED: ]\n")
            self.etyip.set_sensitive(False)
            self.etymac.set_sensitive(False)
            # self.btnstart.set_sensitive(False)
            self.x = False

        return True

    def panelstepconf(self, user_data):
        # print("Joe: in panelstepconf "+str(self.id))
        if (self.z is True):
            self.pgrbprogress.set_fraction(self.progressvalue/100)
            self.pgrbprogress.set_text(str(self.progressvalue)+" %")
            self.z = False

        return True

    def panelendconf(self, user_data):
        # print("Joe: in panelendconf "+str(self.id))
        if (self.y is True):
            if (self.w == "good"):
                self.endtime = time.time()
                timeelapsed = self.endtime - self.starttime
                elapsemin = int(timeelapsed/60)
                elapsesec = int(timeelapsed) % 60
                pgtxt = "Completed, elapsed time: "+str(elapsemin)+":"+str(elapsesec)
                self.pgrbprogress.set_text(pgtxt)
                lblresultcolorfont = '<span background="darkgrey" foreground="green" size="xx-large"><b>PASS</b></span>'
                self.lblresult.set_markup(lblresultcolorfont)
                self.hboxpgrs.set_name("pgrs_green")
            else:
                print("Joe: in selfz true panelendconf "+str(self.id))
                self.pgrbprogress.set_text("Failed")
                lblresultcolorfont = '<span background="darkgrey" foreground="red" size="xx-large"><b>FAILED</b></span>'
                self.lblresult.set_markup(lblresultcolorfont)
                self.hboxpgrs.set_name("pgrs_red")

            self.etyip.set_sensitive(True)
            self.etymac.set_sensitive(True)
            # self.btnstart.set_sensitive(True)
            self.pgrbprogress.set_fraction(0)
            self.y = False

        return True

    def setdirfl(self):

        # Set time
        """
            Time format:
            Weekday Day Month Year Hour:Minute:Second
        """
        nowtime = time.strftime("%a,%d,%m,%Y,%H:%M:%S", time.gmtime())
        print("Joe: nowtime: ", nowtime)
        t1 = nowtime.split(",")
        t1date = t1[3]+"-"+t1[2]+"-"+t1[1]
        [hour, min, sec] = t1[4].split(":")
        print("Joe: hour: %s, min: %s, sec: %s" % (hour, min, sec))
        print("Joe: date: %s" % (t1date))

        # Create the report directory
        reportdir = GPath.logdir+"/"+GCommon.active_product+"-FWLDR"+"/rev"+GCommon.active_bomrev+"/"+t1date
        print("Joe: report dir: "+reportdir)
        GPath.reportdir = reportdir

        if not (os.path.isdir(GPath.reportdir)):
            result = self.xcmd("mkdir -p " + GPath.reportdir, rtmsg=False)
            if (result is False):
                msgerrror(self, "Can't create a log directory in the USB disk")

        # Create the temporary report file
        self.templogfile = open(GPath.reportdir+"/"+GCommon.macaddr+".log", "a")
        print("Joe: templogfile: "+self.templogfile.name)

    def on_start_button_click(self, button):
        # self.starttime = time.time()
        self.x = True
        # self.dhcpsrv  = DHCPServer()
        # self.dhcpsrv.run_in_thread()
        # self.dhcpsrv.monitor_in_thread(int(dlgUserInput.deviceamount), self.fwloader_start)

    def fwloader_start(self, host):
        print("Connecting to device => mac={} ip={}".format(host.mac, host.ip))

        GCommon.macaddr = ''.join(host.mac.split(':'))
        self.fwload_cnt += 1
        if(self.fwload_cnt == 1):
            self.starttime = time.time()
            self.x = True
            self.setdirfl()

        cmd = ["sudo python3 /usr/local/sbin/fwloader.py",
               GCommon.active_product_obj['BOARDID'],
               host.mac,
               host.ip,
               str(self.fwload_cnt)]
        cmd = ' '.join(cmd)
        print(cmd)
        self.proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        GObject.io_add_watch(self.proc.stdout, GLib.IO_IN | GLib.IO_HUP, self.inspection_test, self.proc)

    def savelog(self, result):
        tmplog = self.templogfile.name
        self.templogfile.close()

        rtdir = GPath.reportdir+"/" + result
        if not os.path.isdir(rtdir):
            os.makedirs(rtdir)

        tfile = rtdir+"/"+os.path.basename(self.templogfile.name)
        print("Joe: result file: "+tfile)
        if not os.path.exists(tfile):
            shutil.move(tmplog, rtdir)
        else:
            cmd = "cat "+tmplog+" >> "+tfile
            [sto, rtc] = self.xcmd(cmd)
            if (int(rtc) > 0):
                print("Appending log failed!!")
            else:
                print("Appending log successfully")

        if os.path.exists(tmplog):
            cmd = "rm " + tmplog
            [sto, rtc] = self.xcmd(cmd)
            if (int(rtc) > 0):
                print("Deleting temp log failed!!")
            else:
                print("Deleting temp log successfully")

    def inspection_test(self, fd, cond, proc):
        if (cond == GLib.IO_HUP):
            proc.poll()
            print("pid = {}, rt = {}".format(proc.pid, proc.returncode))
            if (proc.returncode == 0):
                self.w = "good"
                self.y = True
                self.savelog("Pass")

            elif (proc.returncode == 3):
                window.dhcpsrv.monitor_in_thread(len(window.mac_list), window.dhcp_done)

            else:
                print("removing mac = {}".format(self.dev_mac))
                window.mac_list.remove(self.dev_mac)
                window.dhcpsrv.mac_filter_set(window.mac_list)
                print("now mac list = {}, len={}".format(window.mac_list, len(window.mac_list)))

                self.w = "bad"
                self.y = True
                self.savelog("Fail")

            return False

        else:
            x = fd.readline()
            raw2str = x.decode()
            self.appendlog(str(raw2str))
            self.templogfile.write(raw2str)

            pattern = re.compile("^=== (\d+) .*$")
            pgvalue = pattern.match(raw2str)
            if (pgvalue is not None):
                self.z = True
                self.progressvalue = int(pgvalue.group(1))

            return True


class dlgUserInput(Gtk.Dialog):
    deviceamount = 0
    dev_macs = ["", "", "", ""]

    def __init__(self, parent):
        Gtk.Dialog.__init__(self,
                            "User Input Dialog",
                            parent,
                            0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)
        self.vboxuserauth = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # Load products info json file
        f = open('/usr/local/sbin/'+'Products-info.json')
        self.prods = json.load(f)
        f.close()

        # Product Series combo box
        self.lblpds = Gtk.Label("Select a product series:")
        self.lsrpdslist = Gtk.ListStore(str)
        for item in sorted(self.prods.keys()):
            self.lsrpdslist.append([item])

        self.crtrpdslist = Gtk.CellRendererText()
        self.cmbbpds = Gtk.ComboBox.new_with_model(self.lsrpdslist)
        self.cmbbpds.pack_start(self.crtrpdslist, True)
        self.cmbbpds.add_attribute(self.crtrpdslist, "text", 0)
        self.cmbbpds.connect("changed", self.on_pds_combo_changed)

        # Product combo box
        self.lblallpd = Gtk.Label("Select a product:")
        self.lsrallpdlist = Gtk.ListStore(int, str)

        self.crtrallpdlist = Gtk.CellRendererText()
        self.cmbballpd = Gtk.ComboBox.new_with_model(self.lsrallpdlist)
        self.cmbballpd.pack_start(self.crtrallpdlist, True)
        self.cmbballpd.add_attribute(self.crtrallpdlist, "text", 1)
        self.cmbballpd.connect("changed", self.on_allpd_combo_changed)

        # BOM revision
        self.lblbomrev = Gtk.Label("BOM revision(xxx-xxxxx-xx):")
        self.etybomrev = Gtk.Entry()
        self.etybomrev.connect("changed", self.on_bomrev_changed)

        # amount of devices
        # self.lblamount = Gtk.Label("Enter amount of devices (max=4)")
        # self.etyamount = Gtk.Entry()
        # self.etyamount.connect("changed", self.on_amount_changed)

        self.lblbarcde = Gtk.Label("Enter Bar-code of devices (max=4)")
        self.etybarcde1 = Gtk.Entry()
        self.etybarcde2 = Gtk.Entry()
        self.etybarcde3 = Gtk.Entry()
        self.etybarcde4 = Gtk.Entry()
        self.etybarcde1.connect("changed", self.on_barcde1_changed)
        self.etybarcde2.connect("changed", self.on_barcde2_changed)
        self.etybarcde3.connect("changed", self.on_barcde3_changed)
        self.etybarcde4.connect("changed", self.on_barcde4_changed)

        self.vboxuserauth.pack_start(self.lblpds, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbbpds, False, False, 0)
        self.vboxuserauth.pack_start(self.lblallpd, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbballpd, False, False, 0)
        self.vboxuserauth.pack_start(self.lblbomrev, False, False, 0)
        self.vboxuserauth.pack_start(self.etybomrev, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbballpd, False, False, 0)
        # self.vboxuserauth.pack_start(self.lblamount, False, False, 0)
        # self.vboxuserauth.pack_start(self.etyamount, False, False, 0)
        self.vboxuserauth.pack_start(self.lblbarcde, False, False, 0)
        self.vboxuserauth.pack_start(self.etybarcde1, False, False, 0)
        self.vboxuserauth.pack_start(self.etybarcde2, False, False, 0)
        self.vboxuserauth.pack_start(self.etybarcde3, False, False, 0)
        self.vboxuserauth.pack_start(self.etybarcde4, False, False, 0)

        self.area = self.get_content_area()
        self.area.add(self.vboxuserauth)
        self.show_all()

    def on_amount_changed(self, entry):
        maxamount = 4
        dlgUserInput.deviceamount = int(self.etyamount.get_text())
        if dlgUserInput.deviceamount:
            if dlgUserInput.deviceamount > maxamount:
                dlgUserInput.deviceamount = maxamount

        print("The amount of devices: " + str(dlgUserInput.deviceamount))

    def on_barcde1_changed(self, entry):
        barcode = self.etybarcde1.get_text()
        barcode = barcode.strip()
        mac = barcode.split("-")[0]
        dlgUserInput.dev_macs[0] = mac.upper()

    def on_barcde2_changed(self, entry):
        barcode = self.etybarcde2.get_text()
        barcode = barcode.strip()
        mac = barcode.split("-")[0]
        dlgUserInput.dev_macs[1] = mac.upper()

    def on_barcde3_changed(self, entry):
        barcode = self.etybarcde3.get_text()
        barcode = barcode.strip()
        mac = barcode.split("-")[0]
        dlgUserInput.dev_macs[2] = mac.upper()

    def on_barcde4_changed(self, entry):
        barcode = self.etybarcde4.get_text()
        barcode = barcode.strip()
        mac = barcode.split("-")[0]
        dlgUserInput.dev_macs[3] = mac.upper()

    def on_pds_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            GCommon.active_product_series = model[tree_iter][0]
            print("The Product Series: "+GCommon.active_product_series)

        self.lsrallpdlist.clear()
        [GCommon.active_productidx, GCommon.active_product] = ["", ""]
        for key, val in sorted(self.prods[GCommon.active_product_series].items()):
            self.lsrallpdlist.append([val['INDEX'], key])

    def on_allpd_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            [GCommon.active_productidx, GCommon.active_product] = model[tree_iter][:2]
            GCommon.active_product_obj = self.prods[GCommon.active_product_series][GCommon.active_product]
            print("The product index: "+str(GCommon.active_productidx))
            print("The product: "+GCommon.active_product)

    def on_bomrev_changed(self, entry):
        GCommon.active_bomrev = self.etybomrev.get_text()
        print("The BOM revision: "+GCommon.active_bomrev)

    def on_region_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            GCommon.active_region = model[tree_iter][0]

        print("The region: "+GCommon.active_region)

    def check_inputs(self):
        idx = GCommon.active_productidx
        if (GCommon.active_productidx == "" or
           GCommon.active_product == ""):
            return False

        ubomrev = GCommon.active_bomrev.split("-")
        print("Joe: 1st ubomrev: "+str(ubomrev))
        if (len(ubomrev) < 2):
            print("BOM revision format incorrect")
            return False
        else:
            ubomrev = ubomrev[0]+"-"+ubomrev[1]
            print("Joe: 2nd ubomrev: "+str(ubomrev))

        if (ubomrev != GCommon.active_product_obj['BOMREV']):
            print("Joe: input BOM revision is not match to product")
            return False


class dlgBarcodeinput(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self,
                            "Waiting for barcode",
                            parent,
                            0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.vboxbarcode = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        # self.set_default_response("ok")

        self.lbltitle = Gtk.Label("Waiting for barcode")
        self.lblmac = Gtk.Label("------------")
        self.etymacedit = Gtk.Entry()
        self.etymacedit.set_visibility(True)
        self.etymacedit.set_activates_default(True)
        self.etymacedit.connect("changed", self.on_etymacedit_changed)

        self.vboxbarcode.pack_start(self.lbltitle, False, False, 0)
        self.vboxbarcode.pack_start(self.lblmac, False, False, 0)
        self.vboxbarcode.pack_start(self.etymacedit, False, False, 0)

        self.area = self.get_content_area()
        self.area.add(self.vboxbarcode)
        self.show_all()

    def on_etymacedit_changed(self, entry):
        barcode = self.etymacedit.get_text()
        barcode = barcode.strip()
        GCommon.barcode = barcode
        GCommon.barcodelen = len(barcode)
        print("The barcode: %s" % GCommon.barcode)
        print("The barcode: %d" % GCommon.barcodelen)


class winFcdFactory(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        # vboxdashboard used to show each DUT information
        self.vboxdashboard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.lblprod = Gtk.Label('')
        # self.lblprod.set_text(prodlist[0][4])

        self.frame1 = fraMonitorPanel("0", "Slot 1")
        self.frame2 = fraMonitorPanel("1", "Slot 2")
        self.frame3 = fraMonitorPanel("2", "Slot 3")
        self.frame4 = fraMonitorPanel("3", "Slot 4")

        self.vboxdashboard.pack_start(self.lblprod, False, False, 0)
        self.vboxdashboard.pack_start(self.frame1, False, False, 0)
        self.vboxdashboard.pack_start(self.frame2, False, False, 0)
        self.vboxdashboard.pack_start(self.frame3, False, False, 0)
        self.vboxdashboard.pack_start(self.frame4, False, False, 0)

        self.ntbmsg = Gtk.Notebook()
        self.ntbmsg.append_page(self.frame1.scllog, Gtk.Label("Slot 1"))
        self.ntbmsg.append_page(self.frame2.scllog, Gtk.Label("Slot 2"))
        self.ntbmsg.append_page(self.frame3.scllog, Gtk.Label("Slot 3"))
        self.ntbmsg.append_page(self.frame4.scllog, Gtk.Label("Slot 4"))

        # operation log
        self.epdoplog = Gtk.Expander()
        self.epdoplog.set_label('Output of production scripts')
        self.epdoplog.set_expanded(False)
        self.epdoplog.add(self.ntbmsg)

        # Main window
        self.vboxMainWindow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.vboxMainWindow.pack_start(self.vboxdashboard, False, False, 0)
        self.vboxMainWindow.pack_start(self.epdoplog, True, True, 0)
        self.set_title("UBNT FW LOADER PROGRAM")
        self.set_border_width(2)
        self.set_default_size(640, 480)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.add(self.vboxMainWindow)

        self.connect("destroy", self.on_destroy)

    def on_destroy(self, widget):
        Gtk.main_quit()

    def envinitial(self):
        if (self.network_status_set() is False):
            msgerrror(self, "Network configure faile. Exiting...")
            return False

        if (self.find_usb_storage() is False):
            msgerrror(self, "No USB storage found. Exiting...")
            return False

        if (self.check_key_files() is False):
            msgerrror(self, "Security key files missing. Exiting...")
            return False

        if (self.call_input_dlg() is False):
            msgerrror(self, "Inputs information incorrect. Exiting...")
            return False

        return True

    def net_setting_inspect(self, fd, cond, proc):
        if (cond == GLib.IO_HUP):
            proc.poll()
            if (proc.returncode != 0):
                self.log.info("In network_status_set(), returncode: " + str(proc.returncode))
                self.dialog.response(Gtk.ResponseType.NO)
                return False

            self.dialog.response(Gtk.ResponseType.YES)

            return False

    def network_status_set(self):
        self.dialog = Gtk.MessageDialog(self, 0,
                                        Gtk.MessageType.INFO,
                                        Gtk.ButtonsType.CANCEL,
                                        "Initializing environment, please wait.")
        self.dialog.format_secondary_text("Press cancel button to stop setting and close program")
        cmd = "sudo sh /usr/local/sbin/prod-network.sh"
        output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        GObject.io_add_watch(output.stdout,
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
        cmd = "ls -ls /dev/disk/by-id | grep usb-"
        output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output.wait()
        [stdout, stderr] = output.communicate()
        """
        Linux shell script return code:
            pass: 0
            failed: 1
        """
        if (output.returncode == 1):
            print("returncode: " + str(output.returncode))
            return False

        stdoutarray = stdout.decode().splitlines()
        for row in stdoutarray:
            device = row.split("/")[-1]
            print(device)
            file = open("/proc/mounts", "r")
            line = file.readline()
            while line:
                print(line)
                if re.search(device, line):
                    tmp = line.split(" ")
                    if (tmp[1] and tmp[1] != "/cdrom"):
                        GPath.logdir = tmp[1]
                        print("Found storage at " + GPath.logdir + "\n")
                        file.close()
                        return True

                line = file.readline()

            file.close()

        print("No USB storage found")
        return False

    def check_key_files(self):
        GPath.keydir = GPath.logdir + "/keys/"
        print(GPath.keydir)
        for name in GCommon.keyfilenames:
            print("check keyfile: "+name)
            if not (os.path.isfile(GPath.keydir+name)):
                print("name doesn't exist!!\n")
                return False

        return True

    def check_comport(self):
        cmd = "ls /dev | grep ttyUSB"
        output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output.wait()
        [stdout, stderr] = output.communicate()
        """
        Linux shell script return code:
            pass: 0
            failed: 1
        """
        if (output.returncode == 1):
            print("returncode: " + str(output.returncode))
            return False

        exist_tty = stdout.decode().splitlines()
        for itty in exist_tty:
            cmd = "stty -F /dev/"+itty+" speed 115200 > /dev/null 2>/dev/null"
            output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            output.wait()
            [stdout, stderr] = output.communicate()
            if (output.returncode == 1):
                print("returncode: " + str(output.returncode))
                return False

            GCommon.active_tty.append(itty)

        num = len(GCommon.active_tty)
        self.frame1.apply_comport_item(GCommon.active_tty)
        self.frame2.apply_comport_item(GCommon.active_tty)
        self.frame3.apply_comport_item(GCommon.active_tty)
        self.frame4.apply_comport_item(GCommon.active_tty)
        id = 0
        if id < num:
            self.frame1.cmbbcomport.set_active(id)
            id += +1
        if id < num:
            self.frame2.cmbbcomport.set_active(id)
            id += +1

        if id < num:
            self.frame3.cmbbcomport.set_active(id)
            id += +1

        if id < num:
            self.frame4.cmbbcomport.set_active(id)
            id += +1
        return True

    def dhcp_done(self, current_hosts):
        for idx, host in enumerate(current_hosts):
            if host.mac == self.frame1.dev_mac and self.frame1.w != "bad":
                self.frame1.set_mac(host.mac)
                self.frame1.set_ip(host.ip)
                self.frame1.fwloader_start(host)
            elif host.mac == self.frame2.dev_mac and self.frame2.w != "bad":
                self.frame2.set_mac(host.mac)
                self.frame2.set_ip(host.ip)
                self.frame2.fwloader_start(host)
            elif host.mac == self.frame3.dev_mac and self.frame3.w != "bad":
                self.frame3.set_mac(host.mac)
                self.frame3.set_ip(host.ip)
                self.frame3.fwloader_start(host)
            elif host.mac == self.frame4.dev_mac and self.frame4.w != "bad":
                self.frame4.set_mac(host.mac)
                self.frame4.set_ip(host.ip)
                self.frame4.fwloader_start(host)
            else:
                msgerrror(self, "Too much devices")
            time.sleep(2)

    def set_mac_string(self, mac):
        return ':'.join([mac[i:i+2] for i in range(0, 12, 2)])

    def get_mac_list(self, mac_list):

        rt = True
        m1 = dlgUserInput.dev_macs[0]
        m2 = dlgUserInput.dev_macs[1]
        m3 = dlgUserInput.dev_macs[2]
        m4 = dlgUserInput.dev_macs[3]

        mac_seen = set()
        if m1 != "" and (m1 not in mac_seen):
            if len(m1) == 12:
                mac_seen.add(m1)
                self.frame1.dev_mac = self.set_mac_string(m1)
                mac_list.append(self.frame1.dev_mac)
                self.frame1.x = True
            else:
                msgerrror(self, "Invalid mac of device 1")
                rt = False

        if m2 != "" and (m2 not in mac_seen):
            if len(m2) == 12:
                mac_seen.add(m2)
                self.frame2.dev_mac = self.set_mac_string(m2)
                mac_list.append(self.frame2.dev_mac)
                self.frame2.x = True
            else:
                msgerrror(self, "Invalid mac of device 2")
                rt = False

        if m3 != "" and (m3 not in mac_seen):
            if len(m3) == 12:
                mac_seen.add(m3)
                self.frame3.dev_mac = self.set_mac_string(m3)
                mac_list.append(self.frame3.dev_mac)
                self.frame3.x = True
            else:
                msgerrror(self, "Invalid mac of device 3")
                rt = False

        if m4 != "" and (m4 not in mac_seen):
            if len(m4) == 12:
                mac_seen.add(m4)
                self.frame4.dev_mac = self.set_mac_string(m4)
                mac_list.append(self.frame4.dev_mac)
                self.frame4.x = True
            else:
                msgerrror(self, "Invalid mac of device 4")
                rt = False

        return rt

    def call_input_dlg(self):
        dialog = dlgUserInput(self)

        rt = False
        while (rt is False):
            response = dialog.run()
            if (response == Gtk.ResponseType.OK):
                print("The OK button was clicked")
                result = dialog.check_inputs()
                if (result is False):
                    msgerrror(self, "Any one of inputs is not correct")
                    response = ""
                    rt = False
                else:
                    idx = GCommon.active_productidx
                    title = "%s, %s" % (GCommon.active_product_obj['DESC'], GCommon.active_product_obj['BOMREV'])
                    self.lblprod.set_text(title)
                    self.mac_list = []
                    if self.get_mac_list(self.mac_list) is True:
                        self.dhcpsrv = dhcp.DHCPServer(mac_filter_list=self.mac_list)
                        self.dhcpsrv.run_in_thread()
                        self.dhcpsrv.monitor_in_thread(len(self.mac_list), self.dhcp_done)
                        rt = True
                    else:
                        rt = False
            else:
                print("The Cancel button was clicked")
                rt = True

        dialog.destroy()

        return True


def main():
    window = winFcdFactory()
    window.show_all()
    window.envinitial()
    # window.connect("destroy", Gtk.main_quit)
    Gtk.main()


def debugdlgUserInput():
    dialog = dlgUserInput()
    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        print("The OK button was clicked")
    elif response == Gtk.ResponseType.CANCEL:
        print("The Cancel button was clicked")

    dialog.destroy()
    return True

# main()

window = winFcdFactory()
window.show_all()
window.envinitial()
Gtk.main()

# if __name__ == "__main__":
#     main()
#     #debugdlgUserInput()
