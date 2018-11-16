#!/usr/bin/python3


from gi.repository import Gtk, Gdk, GLib, GObject
from ubntlib.gui.gui_variable import GPath, GCommon
from time import sleep
from ubntlib.gui.msgdialog import msgerrror, msginfo
from ubntlib.fcd.common import Common
from ubntlib.fcd.logger import gui_log_info

import gi
import re
import os
import subprocess
import time
import random
import threading
import shutil
import json
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

        # Product
        self.etyproductname = Gtk.Entry()
        self.etyproductname.set_editable(False)
        self.etyproductname.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("black"))

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
        self.hbox.pack_start(self.cmbbcomport, False, False, 0)
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

        gui_log_info("The finaltty[%s]: %s " % (self.id, str(GCommon.finaltty[int(self.id)])))

    def autoscroll(self, iter, text, length, user_param1):
        self.txvlog.scroll_to_mark(self.endmark, 0.0, False, 1.0, 1.0)

    def apply_comport_item(self, items):
        self.lsritemlist.clear()
        for itty in items:
            self.lsritemlist.append([itty])

        return True

    def set_product(self, pd):
        self.etyproductname.set_text(pd)

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
            self.etyproductname.set_sensitive(False)
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
                gui_log_info("in selfz true panelendconf " + str(self.id))
                self.pgrbprogress.set_text("Failed")
                lblresultcolorfont = '<span background="darkgrey" foreground="red" size="xx-large"><b>FAILED</b></span>'
                self.lblresult.set_markup(lblresultcolorfont)
                self.hboxpgrs.set_name("pgrs_red")

            self.etyproductname.set_sensitive(True)
            self.cmbbcomport.set_sensitive(True)
            self.btnstart.set_sensitive(True)
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
        t1 = nowtime.split(",")
        t1date = t1[3] + "-" + t1[2] + "-" + t1[1]
        [hour, min, sec] = t1[4].split(":")
        gui_log_info("hour: %s, min: %s, sec: %s" % (hour, min, sec))
        gui_log_info("date: %s" % (t1date))

        # Create the report directory
        reportdir = GPath.logdir + "/" + GCommon.active_product + "/rev" + GCommon.active_bomrev + "/" + GCommon.active_region + "/" + t1date
        gui_log_info("report dir: " + reportdir)
        GPath.reportdir = reportdir

        if not (os.path.isdir(GPath.reportdir)):
            result = self.pcmd("mkdir -p " + GPath.reportdir)
            if result is False:
                msgerrror(self, "Can't create a log directory in the USB disk")

        # Create the temporary report file
        # randnum = random.randint(1, 2000)
        # GPath.templogfile[int(self.id)] = GPath.reportdir+"/"+sec+min+hour+str(randnum)+".log"
        GPath.templogfile[int(self.id)] = GPath.reportdir + "/" + GCommon.macaddr + ".log"
        gui_log_info("templogfile: " + GPath.templogfile[int(self.id)])

    def on_start_button_click(self, button):
        self.setdirfl()
        self.x = True
        self.run_streamcmd()

        return True

    def run_streamcmd(self):
        for idx in range(5):
            if GCommon.active_region == GCommon.region_names[idx]:
                regcidx = idx
                break
            else:
                regcidx = 0

        cmd = [
            "sudo /usr/bin/python3",
            "/usr/local/sbin/" + GCommon.active_product_obj['FILE'],
            GCommon.active_product_obj['BOARDID'],
            GCommon.finaltty[int(self.id)],
            self.id
        ]
        str1 = " ".join(str(x) for x in cmd)
        gui_log_info("cmd: " + str1)
        self.proc = subprocess.Popen(str1, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        GObject.io_add_watch(
            self.proc.stdout,
            GLib.IO_IN | GLib.IO_HUP,
            self.inspection, self.proc)

    def inspection(self, fd, cond, proc):
        if (cond == GLib.IO_HUP):
            proc.poll()
            self.y = True
            if proc.returncode == 0:
                self.w = "good"
                passdir = GPath.reportdir + "/Pass"
                if not os.path.isdir(passdir):
                    os.makedirs(passdir)

                tfile = passdir + "/" + GCommon.macaddr + ".log"
                gui_log_info("target file: " + tfile)
                if not os.path.isfile(tfile):
                    shutil.move(GPath.templogfile[int(self.id)], passdir)
                else:
                    cmd = "cat " + GPath.templogfile[int(self.id)] + " >> " + tfile
                    [sto, rtc] = self.xcmd(cmd)
                    if (int(rtc) > 0):
                        gui_log_info("Appending log failed!!")
                    else:
                        gui_log_info("Appending log successfully")
            else:
                self.w = "bad"
                faildir = GPath.reportdir + "/Fail"
                if not os.path.isdir(faildir):
                    os.makedirs(faildir)

                tfile = faildir + "/" + GCommon.macaddr + ".log"
                if not os.path.isfile(tfile):
                    shutil.move(GPath.templogfile[int(self.id)], faildir)
                else:
                    cmd = "cat " + GPath.templogfile[int(self.id)] + " >> " + tfile
                    [sto, rtc] = self.xcmd(cmd)
                    if int(rtc) > 0:
                        gui_log_info("Appending log failed!!")
                    else:
                        gui_log_info("Appending log successfully")

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
            if pgvalue is not None:
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

        # Load test items
        f = open('/usr/local/sbin/ubntlib/' + 'Products-info.json')
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
        # for item in prodlist:
            # self.lsrallpdlist.append([item[0], item[1]])

        self.crtrallpdlist = Gtk.CellRendererText()
        self.cmbballpd = Gtk.ComboBox.new_with_model(self.lsrallpdlist)
        self.cmbballpd.pack_start(self.crtrallpdlist, True)
        self.cmbballpd.add_attribute(self.crtrallpdlist, "text", 1)
        self.cmbballpd.connect("changed", self.on_allpd_combo_changed)

        self.vboxuserauth.pack_start(self.lblpds, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbbpds, False, False, 0)
        self.vboxuserauth.pack_start(self.lblallpd, False, False, 0)
        self.vboxuserauth.pack_start(self.cmbballpd, False, False, 0)

        self.area = self.get_content_area()
        self.area.add(self.vboxuserauth)
        self.show_all()

    def on_pds_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            GCommon.active_product_series = model[tree_iter][0]
            gui_log_info("The Product Series: " + GCommon.active_product_series)

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
            print("The product index: " + str(GCommon.active_productidx))
            print("The product: " + GCommon.active_product)

    def check_inputs(self):
        idx = GCommon.active_productidx
        if (GCommon.active_productidx == "" or
           GCommon.active_product == ""):
            return False


class winFcdFactory(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        # vboxdashboard used to show each DUT information
        self.vboxdashboard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.lblflavor = Gtk.Label("Flavor: ")
        self.lblprod = Gtk.Label('')
        # self.lblprod.set_text(prodlist[0][4])

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

    def envinitial(self):
        if self.network_status_set() is False:
            msgerrror(self, "Network configure faile. Exiting...")
            return False

        if self.find_usb_storage() is False:
            msgerrror(self, "No USB storage found. Exiting...")
            return False

        if self.check_comport() is False:
            msgerrror(self, "Check host ttys failed. Exiting...")
            return False

        if self.call_input_dlg() is False:
            msgerrror(self, "Inputs information incorrect. Exiting...")
            return False

        return True

    def network_status_set(self):
        cmd = "sudo sh /usr/local/sbin/prod-network.sh"
        output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output.wait()
        output.communicate()
        if (output.returncode == 1):
            gui_log_info("returncode: " + str(output.returncode))
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
            gui_log_info("returncode: " + str(output.returncode))
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
            gui_log_info("returncode: " + str(output.returncode))
            return False

        exist_tty = stdout.decode().splitlines()
        for itty in exist_tty:
            cmd = "stty -F /dev/" + itty + " speed 115200 > /dev/null 2>/dev/null"
            output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            output.wait()
            [stdout, stderr] = output.communicate()
            if (output.returncode == 1):
                gui_log_info("returncode: " + str(output.returncode))
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
        while rt is False:
            response = dialog.run()
            if (response == Gtk.ResponseType.OK):
                gui_log_info("The OK button was clicked")
                result = dialog.check_inputs()
                if result is False:
                    msgerrror(self, "Any one of inputs is not correct")
                    response = ""
                    rt = False
                else:
                    title = "%s, %s" % (GCommon.active_product_obj['DESC'], GCommon.active_product_obj['BOMREV'])
                    self.lblprod.set_text(title)
                    self.frame1.set_product(GCommon.active_product)
                    self.frame2.set_product(GCommon.active_product)
                    self.frame3.set_product(GCommon.active_product)
                    self.frame4.set_product(GCommon.active_product)
                    rt = True
            else:
                gui_log_info("The Cancel button was clicked")
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
        gui_log_info("The OK button was clicked")
    elif response == Gtk.ResponseType.CANCEL:
        gui_log_info("The Cancel button was clicked")

    dialog.destroy()
    return True


main()
# if __name__ == "__main__":
#     main()
#     #debugdlgUserInput()
