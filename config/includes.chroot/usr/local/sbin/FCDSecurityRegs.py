#!/usr/bin/python3

from gi.repository import Gtk, Gdk, GLib, GObject
from ubntlib.gui.gui_variable import GPath, GCommon
from time import sleep
from ubntlib.gui.msgdialog import msgerrror, msginfo
from ubntlib.fcd.common import Common

import gi
import re
import os
import sys
import subprocess
import time
import random
import threading
import shutil
import json
import logging
gi.require_version('Gtk', '3.0')


"""
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
    def __init__(self, id, frametitle, log):
        self.id = id
        Gtk.Frame.__init__(self, label=frametitle)
        self.log = log
        self.xcmd = Common().xcmd
        self.pcmd = Common().pcmd
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

        self.log.info("The finaltty[%s]: %s " % (self.id, str(GCommon.finaltty[int(self.id)])))

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
        if self.x is True:
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
        if self.z is True:
            self.pgrbprogress.set_fraction(self.progressvalue / 100)
            self.pgrbprogress.set_text(str(self.progressvalue) + " %")
            self.z = False

        return True

    def panelendconf(self, user_data):
        if self.y is True:
            if self.w is "good":
                self.endtime = time.time()
                timeelapsed = self.endtime - self.starttime
                elapsemin = int(timeelapsed / 60)
                elapsesec = int(timeelapsed) % 60
                pgtxt = "Completed, elapsed time: " + str(elapsemin) + ":" + str(elapsesec)
                self.pgrbprogress.set_text(pgtxt)
                lblresultcolorfont = '<span background="darkgrey" foreground="green" size="xx-large"><b>PASS</b></span>'
                self.lblresult.set_markup(lblresultcolorfont)
                self.hboxpgrs.set_name("pgrs_green")
            else:
                self.log.info("In panelendconf(), self.w is not good " + str(self.id))
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
        bomrev = tmp[1] + "-"

        if (tty == "" or \
            product == "" or \
            bomrev == "" or \
            region == ""):
            msgerrror(self, "Information is not adequate. Exiting...")
            return False

        # win = Gtk.Window()
        dialog = dlgBarcodeinput(self.win, self.log)
        response = dialog.run()
        if (response == Gtk.ResponseType.OK):
            self.log.info("In aquirebarcode(), this is barcode response ok")
            barcode = GCommon.barcode
            barcodelen = GCommon.barcodelen
            macaddrlen = GCommon.macaddrlen
            qrcodelen = GCommon.qrcodelen
            self.log.info("In aquirebarcode(), the length of the macaddr+qrcode: %d" % (macaddrlen + qrcodelen))
            qrcheck = GCommon.active_product_obj['QRCHECK']
            if qrcheck == "True":
                if (barcodelen == (macaddrlen + qrcodelen + 1)):
                    btmp = barcode.split("-")
                    if ((len(btmp[0]) != macaddrlen) or \
                        (len(btmp[1]) != qrcodelen)):
                        msgerrror(self.win, "Barcode invalid. Exiting...")
                        rt = False
                    else:
                        pattern = re.compile(r'[^0-9a-fA-F]')
                        pres = pattern.match(btmp[0])
                        if pres is not None:
                            self.log.info("In aquirebarcode(), the macaddr format is incorrect")
                            msgerrror(self.win, "MAC adress invalid. Exiting...")
                            rt = False
                        else:
                            self.log.info("In aquirebarcode(), the barcode is valid")
                            GCommon.macaddr = btmp[0]
                            GCommon.qrcode = btmp[1]
                            self.starttime = time.time()
                            self.log.info("In aquirebarcode(), start time: " + str(self.starttime))
                            rt = True
                else:
                    msgerrror(self.win, "Barcode invalid. Exiting...")
                    rt = False
            else:
                if (barcodelen == (macaddrlen)):
                    pattern = re.compile(r'[^0-9a-fA-F]')
                    pres = pattern.match(barcode)
                    if pres is not None:
                        self.log.info("In aquirebarcode(), the macaddr format is incorrect")
                        msgerrror(self.win, "MAC adress invalid. Exiting...")
                        rt = False
                    else:
                        self.log.info("In aquirebarcode(), the barcode is valid")
                        GCommon.macaddr = barcode
                        self.starttime = time.time()
                        self.log.info("In aquirebarcode(), start time: " + str(self.starttime))
                        rt = True
                else:
                    msgerrror(self.win, "Barcode invalid. Exiting...")
                    rt = False
        else:
            self.log.info("In aquirebarcode(), this is barcode response cancel")
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
        info = g[0:2] + ":" + g[2:4] + ":" + g[4:6] + ":" + g[6:8] + ":" + g[8:10] + ":" + g[10:12] + "-" + GCommon.qrcode
        self.log.info("In setdirfl(), mac+qr: " + info)
        self.lblmacqr.set_label(info)

        # Set time
        """
            Time format:
        """
        date = time.strftime("%Y-%m-%d", time.gmtime())

        # Create the report directory
        reportdir = GPath.logdir + "/" + GCommon.active_product + "/rev" + GCommon.active_bomrev + "/" + GCommon.active_region + "/" + date
        self.log.info("In setdirfl(), report dir: " + reportdir)
        GPath.reportdir = reportdir

        if not (os.path.isdir(GPath.reportdir)):
            result = self.pcmd("mkdir -p " + GPath.reportdir)
            if result is False:
                msgerrror(self, "Can't create a log directory in the USB disk")

        # Create the temporary report file
        nowtime = time.strftime("%Y-%m-%d-%H%M", time.gmtime())
        GPath.templogfile[int(self.id)] = GCommon.macaddr + "_" + nowtime + ".log"
        self.log.info("In setdirfl(), templogfile: " + GPath.templogfile[int(self.id)])

    def on_start_button_click(self, button):
        rt = self.aquirebarcode()

        if rt is True:
            self.setdirfl()
            self.x = True
            self.run_streamcmd()

        return rt

    def run_streamcmd(self):
        for idx in range(5):
            if (GCommon.active_region == GCommon.region_names[idx]):
                regcidx = idx
                break
            else:
                regcidx = 0

        """
            command parameter description for security registration
            command: python3
            para0:   script
            para1:   slot ID
            para2:   UART device number
            para3:   FCD host IP
            para4:   system ID (board ID)
            para5:   MAC address
            para6:   passphrase
            para7:   key directory
            para8:   BOM revision
            para9:   QR code
            para10:  Region Code
        """
        cmd = [
            "sudo /usr/bin/python3",
            "/usr/local/sbin/" + GCommon.active_product_obj['FILE'],
            "-s=" + self.id,
            "-d=" + GCommon.finaltty[int(self.id)],
            "-ts=" + GCommon.fcdhostip,
            "-b=" + GCommon.active_product_obj['BOARDID'],
            "-m=" + GCommon.macaddr,
            "-p=" + GCommon.active_passphrase,
            "-k=" + GPath.keydir,
            "-bom=" + GCommon.active_bomrev[4:],
            "-q=" + GCommon.qrcode,
            "-r=" + GCommon.region_codes[regcidx]
        ]
        str1 = " ".join(str(x) for x in cmd)
        self.log.info("In run_streamcmd(), cmd: " + str1)
        self.proc = subprocess.Popen(str1, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        GObject.io_add_watch(
            self.proc.stdout,
            GLib.IO_IN | GLib.IO_HUP,
            self.inspection, self.proc)

    def inspection(self, fd, cond, proc):
        if (cond == GLib.IO_HUP):
            proc.poll()
            self.y = True
            if (proc.returncode == 0):
                self.w = "good"
                passdir = GPath.reportdir + "/Pass"
                if not os.path.isdir(passdir):
                    os.makedirs(passdir)

                tfile = passdir + "/" + GPath.templogfile[int(self.id)]
            else:
                self.w = "bad"
                faildir = GPath.reportdir + "/Fail"
                if not os.path.isdir(faildir):
                    os.makedirs(faildir)

                tfile = faildir + "/" + GPath.templogfile[int(self.id)]

            self.log.info("In inspection(), target file: " + tfile)
            sfile = os.path.join(
                "/tftpboot/",
                "log_slot" + self.id + ".log")
            self.log.info("In inspection(), source file: " + sfile)

            if os.path.isfile(sfile):
                shutil.copy2(sfile, tfile)
            else:
                self.log.info("In inspection(), can't find the source file")

            return False
        else:
            x = fd.readline()
            raw2str = x.decode()
            self.appendlog(str(raw2str))
            pattern = re.compile(r"^=== (\d+) .*$")
            pgvalue = pattern.match(raw2str)
            if pgvalue is not None:
                self.z = True
                self.progressvalue = int(pgvalue.group(1))

            return True


class dlgUserInput(Gtk.Dialog):
    def __init__(self, parent, log):
        Gtk.Dialog.__init__(
            self, "User Input Dialog", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.log = log
        self.set_default_size(150, 100)
        self.vboxuserauth = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # Pass phrase
        self.lblpassphrase = Gtk.Label("Please enter pass-phrase:")
        self.etypassphrase = Gtk.Entry()
        self.etypassphrase.set_visibility(False)
        self.etypassphrase.set_activates_default(True)
        self.etypassphrase.connect("changed", self.on_phassphrase_changed)

        # Load test items
        f = open('/usr/local/sbin/' + 'Products-info.json')
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

        # Region combo box
        self.lblregion = Gtk.Label("Region:")
        self.lsrregionlist = Gtk.ListStore(str)
        for item in GCommon.region_names:
            self.lsrregionlist.append([item])

        self.crtregionlist = Gtk.CellRendererText()
        self.cmbbregion = Gtk.ComboBox.new_with_model(self.lsrregionlist)
        self.cmbbregion.pack_start(self.crtregionlist, True)
        self.cmbbregion.add_attribute(self.crtregionlist, "text", 0)
        # self.cmbbregion.set_active(0)
        self.cmbbregion.connect("changed", self.on_region_combo_changed)

        self.vboxuserauth.pack_start(self.lblpassphrase, False, False, 0)
        self.vboxuserauth.pack_start(self.etypassphrase, False, False, 0)
        self.vboxuserauth.pack_start(self.lblpds, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbbpds, False, False, 0)
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
        passphrase = self.etypassphrase.get_text()
        GCommon.active_passphrase = passphrase.strip()
        self.log.info("In on_phassphrase_changed(), the passphrse: " + GCommon.active_passphrase)

    def on_pds_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            GCommon.active_product_series = model[tree_iter][0]
            self.log.info("In on_pds_combo_changed(), the Product Series: " + GCommon.active_product_series)

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
            self.log.info("In on_allpd_combo_changed(), the product index: " + str(GCommon.active_productidx))
            self.log.info("In on_allpd_combo_changed(), the product: " + GCommon.active_product)

    def on_bomrev_changed(self, entry):
        bomrev = self.etybomrev.get_text()
        GCommon.active_bomrev = bomrev.strip()
        self.log.info("In on_bomrev_changed(), the BOM revision: " + GCommon.active_bomrev)

    def on_region_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            GCommon.active_region = model[tree_iter][0]

        self.log.info("In on_region_combo_changed(), the region: " + GCommon.active_region)

    def check_inputs(self):
        idx = GCommon.active_productidx
        if (GCommon.active_passphrase == "" or \
           GCommon.active_productidx == "" or \
           GCommon.active_product == "" or \
           GCommon.active_bomrev == "" or \
           GCommon.active_region == ""):
            return False

        ubomrev = GCommon.active_bomrev.split("-")
        self.log.info("In check_inputs(), 1st ubomrev: " + str(ubomrev))
        if (len(ubomrev) < 2):
            self.log.info("In check_inputs(), BOM revision format incorrect")
            return False
        else:
            ubomrev = ubomrev[0] + "-" + ubomrev[1]
            self.log.info("In check_inputs(), 2nd ubomrev: " + str(ubomrev))

        if (ubomrev != GCommon.active_product_obj['BOMREV']):
            self.log.info("In check_inputs(), input BOM revision is not match to product")
            return False


class dlgBarcodeinput(Gtk.Dialog):
    def __init__(self, parent, log):
        Gtk.Dialog.__init__(
            self, "Waiting for barcode", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.log = log
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
        self.log.info("In on_etymacedit_changed(), the barcode: %s" % GCommon.barcode)
        self.log.info("In on_etymacedit_changed(), the barcode length: %d" % GCommon.barcodelen)


class winFcdFactory(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        self.init_logs()
        # vboxdashboard used to show each DUT information
        self.vboxdashboard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.hboxdashboard = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.lblflavor = Gtk.Label("Flavor: ")
        self.lblprod = Gtk.Label('')

        # set the FCD host IP
        self.lblhostip = Gtk.Label("FCD host IP:")
        self.etyhostip = Gtk.Entry()
        self.etyhostip.set_text(GCommon.fcdhostip)
        self.etyhostip.connect("changed", self.on_etyhostip_changed)

        # Enable to set the FCD host IP
        self.cbtnsethostip = Gtk.CheckButton("Enable-set-host-IP")
        if GCommon.hostipsetenable is True:
            self.log.info("GCommon.hostipsetenable: %s" % (GCommon.hostipsetenable))
            self.etyhostip.set_editable(True)
            self.etyhostip.set_sensitive(True)
            self.cbtnsethostip.set_active(True)
        else:
            self.log.info("GCommon.hostipsetenable: %s" % (GCommon.hostipsetenable))
            self.etyhostip.set_editable(False)
            self.etyhostip.set_sensitive(False)
            self.cbtnsethostip.set_active(False)

        self.cbtnsethostip.connect("toggled", self.on_cbtnsethostip_toggled)

        self.hboxdashboard.pack_start(self.lblhostip, False, False, 0)
        self.hboxdashboard.pack_start(self.etyhostip, False, False, 0)
        self.hboxdashboard.pack_start(self.cbtnsethostip, False, False, 0)

        self.frame1 = fraMonitorPanel("0", "Slot 1", self.log)
        self.frame2 = fraMonitorPanel("1", "Slot 2", self.log)
        self.frame3 = fraMonitorPanel("2", "Slot 3", self.log)
        self.frame4 = fraMonitorPanel("3", "Slot 4", self.log)

        self.vboxdashboard.pack_start(self.lblflavor, False, False, 0)
        self.vboxdashboard.pack_start(self.lblprod, False, False, 0)
        self.vboxdashboard.pack_start(self.hboxdashboard, False, False, 0)
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
        self.set_title("UBNT FCD factory program")
        self.set_border_width(2)
        self.set_default_size(640, 480)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.add(self.vboxMainWindow)

    def on_etyhostip_changed(self, entry):
        fcdhostip = self.etyhostip.get_text()
        GCommon.fcdhostip = fcdhostip.strip()
        self.log.info("In on_etyhostip_changed(), the FCD host IP: " + GCommon.fcdhostip)

    def on_cbtnsethostip_toggled(self, button):
        GCommon.hostipsetenable = not GCommon.hostipsetenable
        if GCommon.hostipsetenable is True:
            self.log.info("GCommon.hostipsetenable: %s" % (GCommon.hostipsetenable))
            self.etyhostip.set_editable(True)
            self.etyhostip.set_sensitive(True)
        else:
            self.log.info("GCommon.hostipsetenable: %s" % (GCommon.hostipsetenable))
            self.etyhostip.set_editable(False)
            self.etyhostip.set_sensitive(False)

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
            self.log.info("In find_usb_storage(), returncode: " + str(output.returncode))
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
                        self.log.info("In find_usb_storage(), found storage at " + GPath.logdir + "\n")
                        file.close()
                        return True

                line = file.readline()

            file.close()

        self.log.info("In find_usb_storage(), No USB storage found")
        return False

    def check_key_files(self):
        GPath.keydir = GPath.logdir + "/keys/"
        print(GPath.keydir)
        for name in GCommon.keyfilenames:
            self.log.info("In check_key_files(), check keyfile: " + name)
            if not (os.path.isfile(GPath.keydir + name)):
                self.log.info("In check_key_files(), name doesn't exist!!\n")
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
            self.log.info("In check_comport(), returncode: " + str(output.returncode))
            return False

        exist_tty = stdout.decode().splitlines()
        for itty in exist_tty:
            cmd = "stty -F /dev/" + itty + " speed 115200 > /dev/null 2>/dev/null"
            output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            output.wait()
            [stdout, stderr] = output.communicate()
            if (output.returncode == 1):
                self.log.info("In check_comport(), returncode: " + str(output.returncode))
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
        dialog = dlgUserInput(self, self.log)

        rt = False
        while rt is False:
            response = dialog.run()
            if (response == Gtk.ResponseType.OK):
                self.log.info("In call_input_dlg(), the OK button was clicked")
                result = dialog.check_inputs()
                if result is False:
                    msgerrror(self, "Any one of inputs is not correct")
                    response = ""
                    rt = False
                else:
                    idx = GCommon.active_productidx
                    title = "%s, %s" % (GCommon.active_product_obj['DESC'], GCommon.active_product_obj['BOMREV'])
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
                self.log.info("In call_input_dlg(), the Cancel button was clicked")
                rt = True

        dialog.destroy()

        return True

    def init_logs(self, usb_dir=None):
        if usb_dir is None:
            usb_dir = "/media/usbdisk/logs"
            timestamp = time.strftime('%Y-%m-%d-%H')
            log_file_name = usb_dir + '/' + 'FCDSecurityRegGUI_' + timestamp + '.log'

        self.log = logging.getLogger('FCDSecurityRegGUI_')
        self.log.setLevel(logging.INFO)

        # console log handler
        log_stream = logging.StreamHandler(sys.stdout)
        log_stream.setLevel(logging.DEBUG)

        # file log handler
        if not os.path.exists(usb_dir):
            os.makedirs(usb_dir)

        log_file = logging.FileHandler(log_file_name)
        log_file.setFormatter(logging.Formatter('[%(asctime)s - %(filename)s:%(lineno)d] %(message)s', '%Y-%m-%d %H:%M:%S'))
        log_file.setLevel(logging.DEBUG)

        self.log.addHandler(log_stream)
        self.log.addHandler(log_file)


def main():
    window = winFcdFactory()
    window.show_all()
    window.envinitial()
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()

main()

# if __name__ == "__main__":
#     main()
#     #debugdlgUserInput()
