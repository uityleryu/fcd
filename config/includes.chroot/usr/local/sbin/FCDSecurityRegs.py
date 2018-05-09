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
        self.id=id
        Gtk.Frame.__init__(self, label=frametitle)
        
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        hbox.set_border_width(5)
        self.add(hbox)
        etyproductname = Gtk.Entry()
        etyproductname.set_editable(False)
        #etyproductname.set_name("myButton_blue")
        
        # BOM revision
        etybomrev = Gtk.Entry()
        etybomrev.set_editable(False)
        #etybomrev.set_name("myButton_blue")
        
        etyregion = Gtk.Entry()
        etyregion.set_editable(False)
        #etyregion.set_name("myButton_blue")
        
        # Serail COM port
        cmbbcomport = Gtk.ComboBox()
        
        # MAC address + QR code
        lblmacqr = Gtk.Label('xx:xx:xx:xx:xx:xx-xxxxxx')
        
        # Progressing bar
        pgrbprogress = Gtk.ProgressBar()

        # start button
        btnstart = Gtk.Button()
        btnstart.set_label(" Start ")
        #btnstart.set_name("myButton_yellow")

        lblresult = Gtk.Label('')

        hbox.pack_start(etyproductname, False, False, 0)
        hbox.pack_start(etybomrev, False, False, 0)
        hbox.pack_start(etyregion, False, False, 0)
        hbox.pack_start(cmbbcomport, False, False, 0)
        hbox.pack_start(lblmacqr, False, False, 0)
        hbox.pack_start(pgrbprogress, False, False, 0)
        hbox.pack_end(btnstart, False, False, 0)
        hbox.pack_end(lblresult, False, False, 0)


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


class winFcdFactory(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        # vboxdashboard used to show each DUT information
        vboxdashboard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        lblflavor = Gtk.Label("Flavor: ")
        lblprod = Gtk.Label('')
        lblprod.set_text(prodlist[0][4])

        frame1 = fraMonitorPanel("0", "Slot 1")
        frame2 = fraMonitorPanel("1", "Slot 2")
        frame3 = fraMonitorPanel("2", "Slot 3")
        frame4 = fraMonitorPanel("3", "Slot 4")
        
        vboxdashboard.pack_start(lblflavor, False, False, 0)
        vboxdashboard.pack_start(lblprod, False, False, 0)
        vboxdashboard.pack_start(frame1, False, False, 0)
        vboxdashboard.pack_start(frame2, False, False, 0)
        vboxdashboard.pack_start(frame3, False, False, 0)
        vboxdashboard.pack_start(frame4, False, False, 0)

        msg = ntbMessage()
        
        # operation log
        epdoplog = Gtk.Expander()
        epdoplog.set_label('Output of production scripts')
        epdoplog.set_expanded(False)
        epdoplog.add(msg)
        
        # Main window
        vboxMainWindow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vboxMainWindow.pack_start(vboxdashboard, False, False, 0)
        vboxMainWindow.pack_start(epdoplog, True, True, 0)
        self.set_title("UBNT FCD factory program")
        self.set_border_width(2)
        self.set_default_size(640, 480)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.add(vboxMainWindow)
        self.connect("destroy", Gtk.main_quit)
        
    def envinitial(self):
#         if (self.network_status_set() == False):
#             self.msgerrror("Network configure faile. Exiting...")
#             return False
#
#         if (self.find_usb_storage() == False):
#             self.msgerrror("No USB storage found. Exiting...")
#             return False
# 
#         if (self.check_key_files() == False):
#             self.msgerrror("Security key files missing. Exiting...")
#             return False
        if (self.check_comport() == False):
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
        if (output.returncode == 0):
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
        if (output.returncode == 1):
            print("returncode: " + str(output.returncode))
            return False

        exist_tty = stdout.decode().splitlines()
        print(exist_tty)
        for itty in exist_tty:
            cmd = "stty -F /dev/"+itty+" speed 115200 > /dev/null 2>/dev/null"
            output = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            output.wait()
            [stdout, stderr] = output.communicate()
            if (output.returncode == 1):
                print("returncode: " + str(output.returncode))
                return False

            GCommon.active_tty.append(itty)

        return True
         
    def msgerrror(self, msg):
        mgdimsg = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, "")
        mgdimsg.format_secondary_text(msg)
        mgdimsg.run()
        mgdimsg.destroy()
        return False
        
    def msginfo(self, msg):
        mgdimsg = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.NONE, "")
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

if __name__ == "__main__":
    main()
    
    