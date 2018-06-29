#!/usr/bin/python3

import gi
import re
import os
import subprocess
import time
import random
import threading
import shutil
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GObject
from ubntlib.Product import prodlist
from ubntlib.Variables import GPath, GCommon
from time import sleep
from ubntlib.Commonlib import msgerrror, msginfo, pcmd, xcmd

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

        self.devregready = False
        self.progressvalue = 0
        self.starttime = ""
        self.endtime = ""
        self.rtdevreg = 0
        self.x = False
        self.y = False
        self.z = False
        self.w = "na"
        self.proc = ""

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.hbox.set_border_width(5)
        self.add(self.hbox)

        self.win = Gtk.Window()

        # Product
        self.etyproductname = Gtk.Entry()
        self.etyproductname.set_editable(False)
        self.etyproductname.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))

        # BOM revision
        self.etybomrev = Gtk.Entry()
        self.etybomrev.set_editable(False)
        self.etyproductname.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))

        # Region - country
        self.etyregion = Gtk.Entry()
        self.etyregion.set_editable(False)
        self.etyregion.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))

        # Serail COM port
        self.lsritemlist = Gtk.ListStore(str)
        for item in GCommon.dftty:
            self.lsritemlist.append([item])

        self.crtcmblist = Gtk.CellRendererText()
        self.cmbbcomport = Gtk.ComboBox.new_with_model(self.lsritemlist)
        self.cmbbcomport.pack_start(self.crtcmblist, True)
        self.cmbbcomport.add_attribute(self.crtcmblist, "text", 0)
        self.cmbbcomport.connect("changed", self.on_cmbbcomport_combo_changed)
        self.cmbbcomport.set_active(0)

        # MAC address + QR code
        self.lblmacqr = Gtk.Label('xx:xx:xx:xx:xx:xx-xxxxxx')

        # Progressing bar
        self.hboxpgrs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pgrbprogress = Gtk.ProgressBar()
        self.pgrbprogress.set_text("None")
        self.pgrbprogress.set_show_text(True)
        self.pgrbprogress.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))
        self.hboxpgrs.pack_start(self.pgrbprogress, True, True, 0)

        # start button
        self.btnstart = Gtk.Button()
        self.btnstart.set_label(" Start ")
        self.btnstart.set_focus_on_click(False)
        self.btnstart.connect("clicked", self.on_start_button_click)

        # Text view for showing log
        self.txvlog = Gtk.TextView()
        self.txvlog.set_editable(False)
        self.scllog = Gtk.ScrolledWindow()
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
        #self.lblresult.set_alignment(0.0, 0.0)
        self.lblresult.set_halign(Gtk.Align.CENTER)
        self.lblresult.set_valign(Gtk.Align.CENTER)
        lblresultcolorfont = '<span foreground="black" size="xx-large"><b>Idle....</b></span>'
        self.lblresult.set_markup(lblresultcolorfont)

        self.hbox.pack_start(self.etyproductname, False, False, 0)
        self.hbox.pack_start(self.etybomrev, False, False, 0)
        self.hbox.pack_start(self.etyregion, False, False, 0)
        self.hbox.pack_start(self.cmbbcomport, False, False, 0)
        self.hbox.pack_start(self.lblmacqr, False, False, 0)
        self.hbox.pack_start(self.hboxpgrs, True, True, 0)
        self.hbox.pack_end(self.btnstart, False, False, 0)
        self.hbox.pack_end(self.lblresult, False, False, 0)

        GObject.timeout_add(700, self.panelstartconf, None)
        GObject.timeout_add(300, self.panelstepconf, None)
        GObject.timeout_add(700, self.panelendconf, None)

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

    def set_bomrev(self, rev):
        self.etybomrev.set_text(rev)

    def set_region(self, country):
        self.etyregion.set_text(country)

    def set_product(self, pd):
        self.etyproductname.set_text(pd)

    def get_bomrev(self):
        return self.etybomrev.get_text()

    def get_region(self):
        return self.etyregion.get_text()

    def get_product(self):
        return self.etyproductname.get_text()

    def get_tty(self):
        combo = self.cmbbcomport
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            return model[tree_iter][0]

    def appendlog(self, text):
        self.txblog.insert(self.txilog, text)

    def panelstartconf(self, user_data):
#         print("Joe: in panelstartconf "+str(self.id))
        if (self.x == True):
            lblresultcolorfont = '<span background="darkgrey" foreground="yellow" size="xx-large"><b>Working....</b></span>'
            self.lblresult.set_markup(lblresultcolorfont)
            self.hboxpgrs.set_name("pgrs_yellow")
            self.pgrbprogress.set_text("Starting...")
            self.appendlog("\n--------[STARTED: ]\n")
            self.etybomrev.set_sensitive(False)
            self.etyproductname.set_sensitive(False)
            self.etyregion.set_sensitive(False)
            self.cmbbcomport.set_sensitive(False)
            self.btnstart.set_sensitive(False)
            self.x = False

        return True

    def panelstepconf(self, user_data):
#         print("Joe: in panelstepconf "+str(self.id))
        if (self.z == True):
            self.pgrbprogress.set_fraction(self.progressvalue/100)
            self.pgrbprogress.set_text(str(self.progressvalue)+" %")
            self.z = False

        return True

    def panelendconf(self, user_data):
#         print("Joe: in panelendconf "+str(self.id))
        if (self.y == True):
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

            self.etybomrev.set_sensitive(True)
            self.etyproductname.set_sensitive(True)
            self.etyregion.set_sensitive(True)
            self.cmbbcomport.set_sensitive(True)
            self.btnstart.set_sensitive(True)
            self.pgrbprogress.set_fraction(0)
            self.y = False

        return True

    def aquirebarcode(self):
        rt = False
        tty = self.get_tty()
        product = self.get_product()
        bomrev = self.get_bomrev()
        region = self.get_region()
        id = int(self.id)
        manufid = "fcd"
        tmp = bomrev.split("-")
        bomrev = tmp[1]+"-"

        if (tty == "" or \
            product == "" or \
            bomrev == "" or \
            region == ""):
            msgerrror(self, "Information is not adequate. Exiting...")
            return False

        #win = Gtk.Window()
        dialog = dlgBarcodeinput(self.win)
        response = dialog.run()
        if (response == Gtk.ResponseType.OK):
            print("Joe: this is barcode response ok")
            barcode = GCommon.barcode
            barcodelen = GCommon.barcodelen
            macaddrlen = GCommon.macaddrlen
            qrcodelen = GCommon.qrcodelen
            print("Joe: the macaddr+qrcode: %d" % (macaddrlen+qrcodelen))
            if (barcodelen == (macaddrlen+qrcodelen+1)):
                btmp = barcode.split("-")
                if ((len(btmp[0]) != macaddrlen) or \
                    (len(btmp[1]) != qrcodelen)):
                    msgerrror(self.win, "Barcode invalid. Exiting...")
                    rt = False
                else:
                    pattern = re.compile(r'[^0-9a-fA-F]')
                    pres = pattern.match(btmp[0])
                    if (pres != None):
                        print("Joe: the macaddr format is incorrect")
                        msgerrror(self.win, "MAC adress invalid. Exiting...")
                        rt = False
                    else:
                        print("Joe: the barcode is valid")
                        GCommon.macaddr = btmp[0]
                        GCommon.qrcode = btmp[1]
                        self.starttime = time.time()
                        print("Joe: start time: "+str(self.starttime))
                        rt = True
            else:
                msgerrror(self.win, "Barcode invalid. Exiting...")
                rt = False
        else:
            print("Joe: this is barcode response cancel")
            rt = False

        dialog.destroy()
        self.win.destroy()
        return rt

    def setdirfl(self):
        # Set the correct MAC-QR to control panel
        g = GCommon.macaddr

        """
            MAC address + QR code format:
            XX:XX:XX:XX:XX:XX-XXXXXX
        """
        info = g[0:2]+":"+g[2:4]+":"+g[4:6]+":"+g[6:8]+":"+g[8:10]+":"+g[10:12]+"-"+GCommon.qrcode
        print("Joe: mac+qr: "+info)
        self.lblmacqr.set_label(info)

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
        reportdir = GPath.logdir+"/"+GCommon.active_product+"/rev"+GCommon.active_bomrev+"/"+GCommon.active_region+"/"+t1date
        print("Joe: report dir: "+reportdir)
        GPath.reportdir = reportdir

        if not (os.path.isdir(GPath.reportdir)):
            result = pcmd("mkdir -p "+GPath.reportdir)
            if (result == False):
                msgerrror(self, "Can't create a log directory in the USB disk")

        # Create the temporary report file
        randnum = random.randint(1, 2000)
        #GPath.templogfile[int(self.id)] = GPath.reportdir+"/"+sec+min+hour+str(randnum)+".log"
        GPath.templogfile[int(self.id)] = GPath.reportdir+"/"+GCommon.macaddr+".log"
        print("Joe: templogfile: "+GPath.templogfile[int(self.id)])

    def on_start_button_click(self, button):
        rt = self.aquirebarcode()

        if (rt == True):
            self.setdirfl()
            self.x = True
            self.run_streamcmd()

        return rt

    def run_streamcmd(self):
        for idx in range(4):
            if (GCommon.active_region == GCommon.region_names[idx]):
                regcidx = idx
            else:
                regcidx = 0

        cmd = ["sudo /usr/bin/python3",
               "/usr/local/sbin/u1-base-ea11.py",
               prodlist[GCommon.active_productidx][2],
               GCommon.macaddr,
               GCommon.active_passphrase,
               GPath.keydir,
               GCommon.finaltty[int(self.id)],
               self.id,
               GCommon.active_bomrev,
               GCommon.qrcode,
               GCommon.region_codes[regcidx]]
        str1 = " ".join(str(x) for x in cmd)
        print("Joe: cmd: "+str1)
        self.proc = subprocess.Popen(str1, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        GObject.io_add_watch(self.proc.stdout,
                          GLib.IO_IN|GLib.IO_HUP,
                          self.inspection, self.proc)

    def inspection(self, fd, cond, proc):
        if (cond == GLib.IO_HUP):
            proc.poll()
            self.y = True
            if (proc.returncode == 0):
                self.w = "good"
                passdir = GPath.reportdir+"/Pass"
                if not os.path.isdir(passdir):
                    os.makedirs(passdir)

                tfile = passdir+"/"+GCommon.macaddr+".log"
                print("Joe: target file: "+tfile)
                if not os.path.isfile(tfile):
                    shutil.move(GPath.templogfile[int(self.id)], passdir)
                else:
                    cmd = "cat "+GPath.templogfile[int(self.id)]+" >> "+tfile
                    [sto, rtc] = xcmd(cmd)
                    if (int(rtc) > 0):
                        print("Appending log failed!!")
                    else:
                        print("Appending log successfully")
            else:
                self.w = "bad"
                faildir = GPath.reportdir+"/Fail"
                if not os.path.isdir(faildir):
                    os.makedirs(faildir)

                tfile = faildir+"/"+GCommon.macaddr+".log"
                if not os.path.isfile(tfile):
                    shutil.move(GPath.templogfile[int(self.id)], faildir)
                else:
                    cmd = "cat "+GPath.templogfile[int(self.id)]+" >> "+tfile
                    [sto, rtc] = xcmd(cmd)
                    if (int(rtc) > 0):
                        print("Appending log failed!!")
                    else:
                        print("Appending log successfully")

            return False
        else:
            f = open(GPath.templogfile[int(self.id)], "a")
            x = fd.readline()
            raw2str = x.decode()
            self.appendlog(str(raw2str))
            f.write(raw2str)
            f.close()
            pattern = re.compile("^=== (\d+) .*$")
            pgvalue = pattern.match(raw2str)
            if (pgvalue != None):
                self.z = True
                self.progressvalue = int(pgvalue.group(1))

            return True

class dlgUserInput(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self,
                            "User Input Dialog",
                            parent,
                            0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)
        self.vboxuserauth = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # Pass phrase
        self.lblpassphrase = Gtk.Label("Please enter pass-phrase:")
        self.etypassphrase = Gtk.Entry()
        self.etypassphrase.set_visibility(False)
        self.etypassphrase.set_activates_default(True)
        self.etypassphrase.connect("changed", self.on_phassphrase_changed)

        # Product combo box
        self.lblallpd = Gtk.Label("(for all slots) Product:")
        self.lsrallpdlist = Gtk.ListStore(int, str)
        print(prodlist[0])
        for item in prodlist:
            self.lsrallpdlist.append([item[0], item[1]])

        self.crtrallpdlist = Gtk.CellRendererText()
        self.cmbballpd = Gtk.ComboBox.new_with_model(self.lsrallpdlist)
        self.cmbballpd.pack_start(self.crtrallpdlist, True)
        self.cmbballpd.add_attribute(self.crtrallpdlist, "text", 1)
        self.cmbballpd.connect("changed", self.on_allpd_combo_changed)

        # BOM revision
        self.lblbomrev = Gtk.Label("BOM revision(xxx-xxxxx-xx):")
        self.etybomrev = Gtk.Entry()
        self.etybomrev.connect("changed", self.on_bomrev_changed)

        # Region combo box
        self.lblregion = Gtk.Label("Region:")
        self.lsrregionlist = Gtk.ListStore(str)
        for item in GCommon.region_names:
            self.lsrregionlist.append([item])

        self.crtregionlist = Gtk.CellRendererText()
        self.cmbbregion = Gtk.ComboBox.new_with_model(self.lsrregionlist)
        self.cmbbregion.pack_start(self.crtregionlist, True)
        self.cmbbregion.add_attribute(self.crtregionlist, "text", 0)
        #self.cmbbregion.set_active(0)
        self.cmbbregion.connect("changed", self.on_region_combo_changed)

        self.vboxuserauth.pack_start(self.lblpassphrase, False, False, 0)
        self.vboxuserauth.pack_start(self.etypassphrase, False, False, 0)
        self.vboxuserauth.pack_start(self.lblallpd, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbballpd, False, False, 0)
        self.vboxuserauth.pack_start(self.lblbomrev, False, False, 0)
        self.vboxuserauth.pack_start(self.etybomrev, False, False, 0)
        self.vboxuserauth.pack_start(self.lblregion, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbbregion, False, False, 0)

        self.area = self.get_content_area()
        self.area.add(self.vboxuserauth)
        self.show_all()

    def on_phassphrase_changed(self, entry):
        GCommon.active_passphrase = self.etypassphrase.get_text()
        print("The passphrse: "+GCommon.active_passphrase)

    def on_allpd_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            [GCommon.active_productidx, GCommon.active_product] = model[tree_iter][:2]

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
        if (GCommon.active_passphrase == "" or \
           GCommon.active_productidx == "" or \
           GCommon.active_product == "" or \
           GCommon.active_bomrev == "" or \
           GCommon.active_region == ""):
            return False

        ubomrev = GCommon.active_bomrev.split("-")
        print("Joe: 1st ubomrev: "+str(ubomrev))
        if (len(ubomrev) < 2):
            print("BOM revision format incorrect")
            return False
        else:
            ubomrev = ubomrev[0]+"-"+ubomrev[1]
            print("Joe: 2nd ubomrev: "+str(ubomrev))

        if (ubomrev != prodlist[idx][3]):
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
        #self.set_default_response("ok")

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

        self.lblflavor = Gtk.Label("Flavor: ")
        self.lblprod = Gtk.Label('')
        self.lblprod.set_text(prodlist[0][4])

        self.frame1 = fraMonitorPanel("0", "Slot 1")
        self.frame2 = fraMonitorPanel("1", "Slot 2")
        self.frame3 = fraMonitorPanel("2", "Slot 3")
        self.frame4 = fraMonitorPanel("3", "Slot 4")

        self.vboxdashboard.pack_start(self.lblflavor, False, False, 0)
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
        self.epdoplog.set_expanded(True)
        self.epdoplog.add(self.ntbmsg)

        # Main window
        self.vboxMainWindow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.vboxMainWindow.pack_start(self.vboxdashboard, False, False, 0)
        self.vboxMainWindow.pack_start(self.epdoplog, True, True, 0)
        self.set_title("UBNT FCD factory program")
        self.set_border_width(2)
        self.set_default_size(640, 480)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.add(self.vboxMainWindow)

    def envinitial(self):
        if (self.network_status_set() == False):
            msgerrror(self, "Network configure faile. Exiting...")
            return False

        if (self.find_usb_storage() == False):
            msgerrror(self, "No USB storage found. Exiting...")
            return False

        if (self.check_key_files() == False):
            msgerrror(self, "Security key files missing. Exiting...")
            return False

        if (self.check_comport() == False):
            msgerrror(self, "Check host ttys failed. Exiting...")
            return False

        if (self.call_input_dlg() == False):
            msgerrror(self, "Inputs information incorrect. Exiting...")
            return False

        return True

    def network_status_set(self):
        cmd = "sudo sh /usr/local/sbin/prod-network.sh"
        output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output.wait()
        [stdout, stderr] = output.communicate()
        if (output.returncode == 1):
            print("returncode: " + str(output.returncode))
            return False

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

    def call_input_dlg(self):
        dialog = dlgUserInput(self)

        rt = False
        while (rt == False):
            response = dialog.run()
            if (response == Gtk.ResponseType.OK):
                print("The OK button was clicked")
                result = dialog.check_inputs()
                if (result == False):
                    msgerrror(self, "Any one of inputs is not correct")
                    response = ""
                    rt = False
                else:
                    idx = GCommon.active_productidx
                    title = "%s, %s" % (prodlist[idx][4], prodlist[idx][3])
                    self.lblprod.set_text(title)
                    self.frame1.set_bomrev(GCommon.active_bomrev)
                    self.frame1.set_region(GCommon.active_region)
                    self.frame1.set_product(GCommon.active_product)
                    self.frame2.set_bomrev(GCommon.active_bomrev)
                    self.frame2.set_region(GCommon.active_region)
                    self.frame2.set_product(GCommon.active_product)
                    self.frame3.set_bomrev(GCommon.active_bomrev)
                    self.frame3.set_region(GCommon.active_region)
                    self.frame3.set_product(GCommon.active_product)
                    self.frame4.set_bomrev(GCommon.active_bomrev)
                    self.frame4.set_region(GCommon.active_region)
                    self.frame4.set_product(GCommon.active_product)
                    rt = True
            else:
                print("The Cancel button was clicked")
                rt = True

        dialog.destroy()

        return True

def main():
    window = winFcdFactory()
    window.show_all()
    window.envinitial()
    window.connect("destroy", Gtk.main_quit)
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

main()
# if __name__ == "__main__":
#     main()
#     #debugdlgUserInput()
