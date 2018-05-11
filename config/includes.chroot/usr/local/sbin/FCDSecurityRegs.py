#!/usr/bin/python3.6

import gi
import re
import os
import subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from ubntlib.Product import prodlist
from ubntlib.Variables import GPath, GCommon

# Prefix expression
#     fra    : Gtk.Frame
#     ety    : Gtk.Entry
#     cmbb   : Gtk.ComboBox
#     lbl    : Gtk.Lable
#     btn    : Gtk.Button
#     txv    : Gtk.TextView
#     scl    : Gtk.ScrolledWindow
#     epd    : Gtk.Expander
#     mgdi   : Gtk.MessageDialog
#     lsr    : Gtk.ListStore
#     crt    : Gtk.CellRendererText
#     dlg    : Gtk.Dialog

css = b"""
#myGrid {
    background-color: cyan;
    border-style: solid;
    border-color: black;
    border-width: 1px;
}

#myChildTop {
    background-color: white;
}

#myButton_red{
    background-color: red;
    color: white;
    font-family: DejaVu Sans;
    font-style: normal;
    font-weight: bold;
    font-size: 20px;
    border-radius: 15px;
}

#myButton_yellow{
    background-color: #131313;
    color: red;
    font-family: DejaVu Sans;
    font-style: normal;
    font-weight: bold;
    font-size: 20px;
    border-radius: 15px;
}

#myButton_green{
    background-color: green;
    color: white;
    font-family: DejaVu Sans;
    font-style: normal;
    font-weight: bold;
    font-size: 20px;
    border-radius: 15px;
}

#myButton_blue{
    background-color: white;
    color: blue;
    font-family: DejaVu Sans;
    font-style: normal;
    font-weight: bold;
    font-size: 20px;
    border-radius: 15px;
}
"""

class fraMonitorPanel(Gtk.Frame):
    def __init__(self, id, frametitle):
        self.id = id
        Gtk.Frame.__init__(self, label=frametitle)

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.hbox.set_border_width(5)
        self.add(self.hbox)

        self.etyproductname = Gtk.Entry()
        self.etyproductname.set_editable(False)
        #self.etyproductname.set_name("myButton_blue")

        # BOM revision
        self.etybomrev = Gtk.Entry()
        self.etybomrev.set_editable(False)
        #self.etybomrev.set_name("myButton_blue")

        # Region - country
        self.etyregion = Gtk.Entry()
        self.etyregion.set_editable(False)
        #self.etyregion.set_name("myButton_blue")

        # Serail COM port
        self.lsritemlist = Gtk.ListStore(str)
        for item in GCommon.dftty:
            self.lsritemlist.append([item])

        self.crtcmblist = Gtk.CellRendererText()
        self.cmbbcomport = Gtk.ComboBox.new_with_model(self.lsritemlist)
        self.cmbbcomport.pack_start(self.crtcmblist, True)
        self.cmbbcomport.add_attribute(self.crtcmblist, "text", 0)
        self.cmbbcomport.set_active(0)

        # MAC address + QR code
        self.lblmacqr = Gtk.Label('xx:xx:xx:xx:xx:xx-xxxxxx')

        # Progressing bar
        self.pgrbprogress = Gtk.ProgressBar()

        # start button
        self.btnstart = Gtk.Button()
        self.btnstart.set_label(" Start ")
        self.btnstart.set_focus_on_click(False)
        self.btnstart.connect("clicked", self.startreg)
        #btnstart.set_name("myButton_yellow")

        lblresult = Gtk.Label('')

        self.hbox.pack_start(self.etyproductname, False, False, 0)
        self.hbox.pack_start(self.etybomrev, False, False, 0)
        self.hbox.pack_start(self.etyregion, False, False, 0)
        self.hbox.pack_start(self.cmbbcomport, False, False, 0)
        self.hbox.pack_start(self.lblmacqr, False, False, 0)
        self.hbox.pack_start(self.pgrbprogress, False, False, 0)
        self.hbox.pack_end(self.btnstart, False, False, 0)
        self.hbox.pack_end(lblresult, False, False, 0)

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

    def startreg(self, button):
        tty = self.get_tty()
        product = self.get_product()
        bomrev = self.get_bomrev()
        region = self.get_region()
        id = self.id
        manufid = "fcd"
        print("Joe: in startreg, "+str(tty))
        print("Joe: in startreg, "+str(product))
        print("Joe: in startreg, "+str(bomrev))
        print("Joe: in startreg, "+str(id))
        tmp = bomrev.split("-")
        bomrev = tmp[1]+"-"

        if (tty == "" or \
            product == "" or \
            bomrev == "" or \
            region == ""):
            msgerrror(self, "Information is not adequate. Exiting...")
            return False

        win = Gtk.Window()
        dialog = dlgBarcodeinput(win)
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
                    msgerrror(win, "Barcode invalid. Exiting...")
                else:
                    print("Joe: the barcode is valid")
                    GCommon.macaddr = btmp[0]
                    GCommon.qrcode = btmp[1]
            else:
                msgerrror(win, "Barcode invalid. Exiting...")
        else:
            print("Joe: this is barcode response cancel")

        dialog.destroy()
        win.destroy()

class ntbMessage(Gtk.Notebook):
    def __init__(self):
        Gtk.Notebook.__init__(self)
        txvlog1 = Gtk.TextView()
        txvlog2 = Gtk.TextView()
        txvlog3 = Gtk.TextView()
        txvlog4 = Gtk.TextView()
        scllog1 = Gtk.ScrolledWindow()
        scllog2 = Gtk.ScrolledWindow()
        scllog3 = Gtk.ScrolledWindow()
        scllog4 = Gtk.ScrolledWindow()
        scllog1.add(txvlog1)
        scllog2.add(txvlog2)
        scllog3.add(txvlog3)
        scllog4.add(txvlog4)
        self.append_page(scllog1, Gtk.Label("Slot 1"))
        self.append_page(scllog2, Gtk.Label("Slot 2"))
        self.append_page(scllog3, Gtk.Label("Slot 3"))
        self.append_page(scllog4, Gtk.Label("Slot 4"))


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

    def on_etymacedit_changed(self):
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

        self.msg = ntbMessage()

        # operation log
        self.epdoplog = Gtk.Expander()
        self.epdoplog.set_label('Output of production scripts')
        self.epdoplog.set_expanded(False)
        self.epdoplog.add(self.msg)

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
        self.connect("destroy", Gtk.main_quit)

    def envinitial(self):
#         if (self.network_status_set() == False):
#             msgerrror("Network configure faile. Exiting...")
#             return False
#
        if (self.find_usb_storage() == False):
            msgerrror(self, "No USB storage found. Exiting...")
            return False

        if (self.check_key_files() == False):
            msgerrror(self, "Security key files missing. Exiting...")
            return False

        if (self.check_comport() == False):
            msgerrror(self, "Check host ttys failed. Exiting...")
            return False

        self.call_input_dlg()
        return True

    def network_status_set(self):
#         cmd = "sudo sh prod-network.sh"
#         output = subprocess.Popen([t], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
#         output.wait()
#         [stdout, stderr] = output.communicate()
#         if (output.returncode == 0):
#             print("returncode: " + str(output.returncode))
#             return False
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
            if not os.path.isfile(GPath.keydir+name):
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
                    msgerrror("Any one of inputs is not correct")
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

def main():
    window = winFcdFactory()
    window.show_all()
    window.envinitial()
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

if __name__ == "__main__":
    main()
    #debugdlgUserInput()
