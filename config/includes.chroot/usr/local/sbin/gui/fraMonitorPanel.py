#!/usr/bin/python3

import sys
import time
import subprocess
import os
import re
import logging
import shutil
import data.constant as CONST
import gi
import json
import datetime
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GLib, GObject
from ubntlib.fcd.common import Common
from gui.dlgBarcodeinput import dlgBarcodeinput
from threading import Thread
import datetime,tarfile

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


class fraMonitorPanel(Gtk.Frame):
    def __init__(self, slotid, frametitle):
        self.slotid = slotid
        Gtk.Frame.__init__(self, label=frametitle)

        self.frawin = Gtk.Window()

        self.xcmd = Common().xcmd
        self.pcmd = Common().pcmd

        self.starttime = 0
        self.endtime = 0

        self.proc = ""
        self.reg_process_stop = False

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(CONST.css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.hbox.set_border_width(5)
        self.add(self.hbox)

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
        for item in CONST.dftty:
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

        if CONST.feature == "register":
            self.hbox.pack_start(self.etyproductname, False, False, 0)
            self.hbox.pack_start(self.etybomrev, False, False, 0)
            self.hbox.pack_start(self.etyregion, False, False, 0)
            self.hbox.pack_start(self.cmbbcomport, False, False, 0)
            self.hbox.pack_start(self.lblmacqr, False, False, 0)
            self.hbox.pack_start(self.hboxpgrs, True, True, 0)
            self.hbox.pack_end(self.btnstart, False, False, 0)
            self.hbox.pack_end(self.lblresult, False, False, 0)
        else:
            # Erase WiFi calibratio checkbutton
            self.cbtnerasecal = Gtk.CheckButton("Erase-caldata")
            if CONST.erasewifidata[int(self.slotid)] is True:
                self.cbtnerasecal.set_active(True)
            else:
                self.cbtnerasecal.set_active(False)
            self.cbtnerasecal.connect("toggled", self.on_cbtnerasecal_toggled)

            # Erase devreg-data checkbutton
            self.cbtnerase_devreg = Gtk.CheckButton("Erase-devreg")
            if CONST.erasewifidata[int(self.slotid)] is True:
                self.cbtnerase_devreg.set_active(True)
            else:
                self.cbtnerase_devreg.set_active(False)
            self.cbtnerase_devreg.connect("toggled", self.on_cbtnerase_devreg_toggled)

            self.hbox.pack_start(self.etyproductname, False, False, 0)
            self.hbox.pack_start(self.cmbbcomport, False, False, 0)
            self.hbox.pack_start(self.cbtnerasecal, False, False, 0)
            self.hbox.pack_start(self.cbtnerase_devreg, False, False, 0)
            self.hbox.pack_start(self.lblmacqr, False, False, 0)
            self.hbox.pack_start(self.hboxpgrs, True, True, 0)
            self.hbox.pack_end(self.btnstart, False, False, 0)
            self.hbox.pack_end(self.lblresult, False, False, 0)

    def autoscroll(self, iter, text, length, user_param1):
        self.txvlog.scroll_to_mark(self.endmark, 0.0, False, 1.0, 1.0)

    def on_cmbbcomport_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            CONST.finaltty[int(self.slotid)] = model[tree_iter][0]

    def on_start_button_click(self, button):
        __FUNC = sys._getframe().f_code.co_name
        rt = False
        rt = self._check_product_info()

        if rt is True:
            rt = self._open_barcode_diaglog()
        else:
            rtmsg = "{0}: check product info failed".format(__FUNC)
            log.info(rtmsg)

        if rt is True:
            self._set_macqr()
            self._create_report_dir()
            GObject.idle_add(self._lock_slot_gui_setting)
            self._run_regcmd()
        else:
            rtmsg = "{0}: barcdoe check failed".format(__FUNC)
            log.info(rtmsg)

        return rt

    def on_cbtnerasecal_toggled(self, button):
        CONST.erasewifidata[int(self.slotid)] = not CONST.erasewifidata[int(self.slotid)]

    def on_cbtnerase_devreg_toggled(self, button):
        CONST.erase_devreg_data[int(self.slotid)] = not CONST.erase_devreg_data[int(self.slotid)]

    '''
        Check if produc, BOM revision and region are empty
    '''
    def _check_product_info(self):
        tty = self.get_tty()
        product = self.etyproductname.get_text()

        if CONST.feature == "register":
            region = self.etyregion.get_text()
            tmp = self.etybomrev.get_text().split("-")
            bomrev = tmp[1] + "-"

            if (tty == "" or product == "" or bomrev == "" or region == ""):
                msgerrror(self, "Information is not adequate. Exiting...")
                return False
        else:
            if (tty == "" or product == ""):
                msgerrror(self, "Information is not adequate. Exiting...")
                return False

        return True

    def _open_barcode_diaglog(self):
        __FUNC = sys._getframe().f_code.co_name

        dialog = dlgBarcodeinput(self.frawin)
        response = dialog.run()
        if (response == Gtk.ResponseType.OK):
            rtmsg = "{0}: this is barcode response ok".format(__FUNC)
            log.info(rtmsg)

            stm = [0]
            rt = dialog.check_barcode(stm)
            self.starttime = stm[0]
        else:
            rtmsg = "{0}, this is barcode response cancel".format(__FUNC)
            log.info(rtmsg)
            rt = False

        if self.is_capslock_off() is False:
            msgerror(self.frawin, "Caps Lock key is on, please disable it")

        dialog.destroy()
        self.frawin.destroy()

        return rt

    def is_capslock_off(self):
        output, ret = self.xcmd("xset -q | grep \"Caps Lock\"")
        match = re.search(r"Caps Lock: *off", output)
        if match:
            return True
        else:
            log.info("Caps Lock key is on")
            return False

    def _set_macqr(self):
        __FUNC = sys._getframe().f_code.co_name
        """
            MAC address + QR code format:
            XX:XX:XX:XX:XX:XX-XXXXXX
        """
        g = CONST.macaddr.upper()
        imacqr = "{0}:{1}:{2}:{3}:{4}:{5}-{6}".format(g[0:2], g[2:4], g[4:6], g[6:8], g[8:10], g[10:12], CONST.qrcode)
        self.lblmacqr.set_label(imacqr)
        rtmsg = "{0}: mac-qr: {1}".format(__FUNC, imacqr)
        log.info(rtmsg)

    def _create_report_dir(self):
        __FUNC = sys._getframe().f_code.co_name
        '''
            Create the report directory
            EX: /media/usbdisk/reg_logs/USW-LEAF/rev-113-02997-23/World/2019-12-03
        '''
        t = time.time()
        date = time.strftime("%Y-%m-%d", time.localtime(t))

        if CONST.feature == "register":
            CONST.reportdir = "{0}/{1}/rev-{2}/{3}/{4}".format(CONST.logdir, CONST.active_product, CONST.active_bomrev, CONST.active_region, date)
        else:
            CONST.reportdir = "{0}/{1}/backart/{2}".format(CONST.logdir, CONST.active_product, date)

        rtmsg = "{0}: report dir: {1}".format(__FUNC, CONST.reportdir)
        log.info(rtmsg)

        if not (os.path.isdir(CONST.reportdir)):
            cmd = "mkdir -p {0}".format(CONST.reportdir)
            result = self.pcmd(cmd)
            if result is False:
                msgerrror(self,frawin, "Can't create a log directory in the USB disk")
        else:
            rtmsg = "{0}: {1} is existed".format(__FUNC, CONST.reportdir)
            log.info(rtmsg)

        '''
            Create the temporary report file
            EX: 112233445566_2019-11-17-1415.log
        '''
        t = time.time()
        nowtime = time.strftime("%Y-%m-%d-%H%M%S", time.localtime(t))
        CONST.templogfile[int(self.slotid)] = "{0}_{1}.log".format(CONST.macaddr.upper(), nowtime)
        rtmsg = "{0}: templogfile: {1}".format(__FUNC, CONST.templogfile[int(self.slotid)])
        log.info(rtmsg)

    '''
        This API is used for locking all components in order to prevent from chaning the
        information after pressing start button
    '''
    def _lock_slot_gui_setting(self):
        lblresultcolorfont = '<span background="darkgrey" foreground="yellow" size="xx-large"><b>Working....</b></span>'
        self.lblresult.set_markup(lblresultcolorfont)
        self.hboxpgrs.set_name("pgrs_yellow")
        self.pgrbprogress.set_text("Starting...")
        self._appendlog("\n--------[STARTED: ]\n")

        self.etyproductname.set_sensitive(False)
        self.cmbbcomport.set_sensitive(False)
        self.btnstart.set_sensitive(False)

        if CONST.feature == "register":
            self.etybomrev.set_sensitive(False)
            self.etyregion.set_sensitive(False)

    def _default_slot_gui_setting(self):
        self.etyproductname.set_sensitive(True)
        self.cmbbcomport.set_sensitive(True)
        self.btnstart.set_sensitive(True)
        self.pgrbprogress.set_fraction(0)

        if CONST.feature == "register":
            self.etybomrev.set_sensitive(False)
            self.etyregion.set_sensitive(False)

    def _slot_gui_result_setting(self, result):
        __FUNC = sys._getframe().f_code.co_name
        rtmsg = "{0}: start time: {1}".format(__FUNC, self.starttime)
        log.info(rtmsg)
        self.endtime = time.time()
        rtmsg = "{0}: end time: {1}".format(__FUNC, self.endtime)
        log.info(rtmsg)
        timeelapsed = self.endtime - self.starttime
        elapsemin = int(timeelapsed / 60)
        elapsesec = int(timeelapsed) % 60

        if result == "pass":
            pgtxt = "Completed, elapsed time: {0}:{1}".format(str(elapsemin), str(elapsesec))
            self.pgrbprogress.set_text(pgtxt)
            lblresultcolorfont = '<span background="darkgrey" foreground="green" size="xx-large"><b>PASS</b></span>'
            self.lblresult.set_markup(lblresultcolorfont)
            self.hboxpgrs.set_name("pgrs_green")
        else:
            pgtxt = "Failed, elapsed time: {0}:{1}".format(str(elapsemin), str(elapsesec))
            self.pgrbprogress.set_text(pgtxt)
            lblresultcolorfont = '<span background="darkgrey" foreground="red" size="xx-large"><b>FAILED</b></span>'
            self.lblresult.set_markup(lblresultcolorfont)
            self.hboxpgrs.set_name("pgrs_red")

    def _run_regcmd(self):
        __FUNC = sys._getframe().f_code.co_name

        if CONST.feature == "register":
            cmd = self._call_register_script()
        else:
            cmd = self._call_backtot1_script()

        rtmsg = "{0}: cmd: {1}".format(__FUNC, cmd)
        log.info(rtmsg)

        self.proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        GObject.io_add_watch(
            self.proc.stdout,
            GLib.IO_HUP,
            self._inspection, self.proc)

        self.reg_process_stop = False
        progress_thrd = Thread(target=self._update_progress)
        progress_thrd.setDaemon(True)
        progress_thrd.start()

    def _call_register_script(self):
        for idx in range(5):
            if (CONST.active_region == CONST.region_names[idx]):
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
            "/usr/local/sbin/" + CONST.active_product_obj['FILE'],
            "-pline=" + CONST.active_product_series,
            "-pname=" + CONST.active_product,
            "-s=" + self.slotid,
            "-d=" + CONST.finaltty[int(self.slotid)],
            "-ts=" + CONST.fcdhostip,
            "-b=" + CONST.active_product_obj['BOARDID'],
            "-m=" + CONST.macaddr,
            "-p='" + CONST.active_passphrase + "'",
            "-k=" + CONST.keydir,
            "-bom=" + CONST.active_bomrev[4:],
            "-q=" + CONST.qrcode,
            "-r=" + CONST.region_codes[regcidx]
        ]
        cmd = " ".join(cmd)
        return cmd

    def _call_backtot1_script(self):
        """
            command parameter description for BackToT1
            command: python3
            para0:   script
            para1:   slot ID
            para2:   UART device number
            para3:   FCD host IP
            para4:   system ID
            para5:   Erase calibration data selection
        """
        cmd = [
            "sudo /usr/bin/python3",
            "/usr/local/sbin/" + CONST.active_product_obj['T1FILE'],
            "-s=" + self.slotid,
            "-d=" + CONST.finaltty[int(self.slotid)],
            "-ts=" + CONST.fcdhostip,
            "-b=" + CONST.active_product_obj['BOARDID'],
            "-e=" + str(CONST.erasewifidata[int(self.slotid)]),
            "-ed=" + str(CONST.erase_devreg_data[int(self.slotid)]),
            "-m=" + CONST.macaddr
        ]
        cmd = " ".join(cmd)
        return cmd

    def _inspection(self, fd, cond, proc):
        __FUNC = sys._getframe().f_code.co_name
        proc.poll()
        time.sleep(1)
        self.reg_process_stop = True
        testresult =''
        if (proc.returncode == 0):
            GObject.idle_add(self._slot_gui_result_setting, "pass")
            # EX: /media/usbdisk/reg_logs/USW-LEAF/rev-113-02997-23/World/2019-12-03/Pass
            tempdir = os.path.join(CONST.reportdir, "Pass")
            testresult = "Pass"
        else:
            GObject.idle_add(self._slot_gui_result_setting, "fail")
            # EX: /media/usbdisk/reg_logs/USW-LEAF/rev-113-02997-23/World/2019-12-03/Fail
            tempdir = os.path.join(CONST.reportdir, "Fail")
            testresult = "Fail"

        GObject.idle_add(self._default_slot_gui_setting)

        if not os.path.isdir(tempdir):
            os.makedirs(tempdir)

        tfile = os.path.join(tempdir, CONST.templogfile[int(self.slotid)])
        sfile = "/tftpboot/log_slot{0}.log".format(self.slotid)

        rtmsg = "{0}: target file: {1}".format(__FUNC, tfile)
        log.info(rtmsg)
        rtmsg = "{0}: source file: {1}".format(__FUNC, sfile)
        log.info(rtmsg)

        if os.path.isfile(sfile):
            shutil.copy2(sfile, tfile)
            time.sleep(1)
        else:
            rtmsg = "{0}: can't find the source file".format(__FUNC)
            log.info(rtmsg)

        self.upload_prepare(self.starttime, self.slotid, CONST.macaddr, CONST.active_bomrev, testresult)

        return False


    def upload_prepare(self, ori_starttime, slotid, mac, bom, finalresult):

        tpe_tz = datetime.timezone(datetime.timedelta(hours=8))
        start_time = datetime.datetime.fromtimestamp( ori_starttime, tpe_tz)
        end_time = datetime.datetime.now(tpe_tz)
        timestamp = start_time.strftime('%Y-%m-%d_%H_%M_%S_%f')

        upload_root_folder = "/media/usbdisk/upload"
        upload_dut_folder = os.path.join(upload_root_folder, timestamp + '_' + mac)
        upload_dut_filename = '_'.join([timestamp,mac,finalresult])
        upload_dut_logpath = os.path.join(upload_dut_folder, upload_dut_filename + ".log")
        upload_dut_jsonpath = os.path.join(upload_dut_folder, upload_dut_filename + ".json")

        sfile = "/tftpboot/log_slot{0}.log".format(slotid)
        jfile = "/tftpboot/log_slot{0}.json".format(slotid)

        if not os.path.isdir(upload_dut_folder):
            os.makedirs(upload_dut_folder)

        with open(jfile, 'r') as jsonfile:
            json_decode = json.load(jsonfile)
            json_decode['test_result'] = finalresult
            json_decode['test_starttime'] = start_time.strftime('%Y-%m-%d_%H:%M:%S')
            json_decode['test_endtime']   = end_time.strftime('%Y-%m-%d_%H:%M:%S')
            json_decode['test_duration'] =  (end_time-start_time).seconds

        with open(jfile, 'w') as jsonfile:
            json.dump(json_decode, jsonfile, sort_keys=True, indent=4)

        upload_file_dict = {
            sfile : upload_dut_logpath ,
            jfile : upload_dut_jsonpath
        }

        for ori_file,copy_file in upload_file_dict.items():
            if os.path.isfile(ori_file):
                shutil.copy2(ori_file, copy_file)
                log.info("\n[Collect UploadLog]\n From {}\n copy to {}\n".format(ori_file, copy_file))
                time.sleep(1)

        self.uploadlog(uploadfolder=upload_dut_folder, mac=mac, bom=bom)
        self.uploadlog_to_mike(uploadfolder=upload_dut_folder, mac=mac, bom=bom , upload_dut_logpath=upload_dut_logpath)

    def uploadlog(self,uploadfolder,mac,bom):
        """
            command parameter description for trigger /api/v1/uploadlog WebAPI in Cloud
            command: python3
            --path:   uploadfolder or uploadpath
            --mac:   mac address with lowercase
            --bom:   BOM Rev version
            --stage:   FCD or FTU
        """
        cmd = [
            "sudo", "/usr/bin/python3",
            "/usr/local/sbin/logupload_client.py",
            '--path', uploadfolder,
            '--mac', mac,
            '--bom', bom,
            '--stage', 'FCD'
        ]
        execcmd = ' '.join(cmd)
        log.info(execcmd)

        try :
            uploadproc = subprocess.check_output(execcmd, shell=True)
            self._appendlog('\n[Uploadlog Success-logupload_client]\n')

        except subprocess.CalledProcessError as e:
            self._appendlog('\n{}\n{}\n[Uploadlog Fail-logupload_client]\n'.format(e.output.decode('utf-8') , e.returncode) )

    def uploadlog_to_mike(self,uploadfolder,mac,bom,upload_dut_logpath):
        """
            Mike Taylor's uploadlog client. If any error , give up uploading
        """
        try:
            stage = 'FCD'
            timestampstr = '%Y-%m-%d_%H_%M_%S_%f'
            tpe_tz = datetime.timezone(datetime.timedelta(hours=8))
            start_time = datetime.datetime.now(tpe_tz)
            start_timestr = start_time.strftime(timestampstr)
            uploadpath = os.path.join(uploadfolder, '{}_{}{}'.format(start_timestr, mac, ".tar.gz"))
            with tarfile.open(uploadpath, mode="w:gz") as tf:
                if os.path.isdir(upload_dut_logpath):
                    tar_dir = os.path.join(stage, bom, start_timestr + '_' + mac)
                    tf.add(upload_dut_logpath, tar_dir)
                elif os.path.isfile(upload_dut_logpath):
                    tar_dir = os.path.join(stage, bom, start_timestr + '_' + mac, os.path.basename(upload_dut_logpath))
                    tf.add(upload_dut_logpath, tar_dir)

            clientbin = "/usr/local/sbin/upload_x86_release"
            regparam = [
                "-h stage.udrs.io",
                "--input field=name,format=binary,value={}".format(os.path.basename(uploadpath)),
                "--input field=content,format=binary,pathname={}".format(uploadpath),
                "--input field=type_id,format=hex,value=00000001",
                "--output field=result",
                "--output field=upload_id",
                "--output field=registration_status_id",
                "--output field=registration_status_msg",
                "--output field=error_message",
                "-k " + CONST.active_passphrase,
                "-x " + os.path.join(CONST.keydir, "ca.pem"),
                "-y " + os.path.join(CONST.keydir, "key.pem"),
                "-z " + os.path.join(CONST.keydir, "crt.pem")
            ]
            regparam = ' '.join(regparam)
            execcmd = "sudo {0} {1}".format(clientbin, regparam)
            log.info(execcmd)
            self._appendlog('\n[Start upload_x86_client Command]\n{}\n'.format(execcmd))

            uploadproc = subprocess.check_output(execcmd, shell=True)
            self._appendlog('\n{}\n[Uploadlog Success-upload_x86_release]'.format(uploadproc.decode('utf-8')))

        except subprocess.CalledProcessError as e:
            self._appendlog('\n{}\n{}\n[Uploadlog Fail-upload_x86_release]'.format(e.output.decode('utf-8') , e.returncode) )

        except Exception as e:
            self._appendlog('\n{}\n{}\n[Uploadlog Fail-upload_x86_release]'.format(e.output.decode('utf-8') , e.returncode) )


    def _update_progress(self):
        while self.reg_process_stop is False:
            x = self.proc.stdout.readline()
            raw2str = x.decode()
            GObject.idle_add(self._appendlog, str(raw2str))
            pattern = re.compile(r"^=== (\d+) .*$")
            pgvalue = pattern.match(raw2str)
            if pgvalue is not None:
                GObject.idle_add(self._progstep, pgvalue.group(1))

    '''
        This API is used for appending message to the Gtk.TextView
    '''
    def _appendlog(self, text):
        self.txblog.insert(self.txilog, text)

    '''
        This API is used for controlling the percentage of the progressing bar dynamically
    '''
    def _progstep(self, value):
        self.pgrbprogress.set_fraction(int(value) / 100)
        self.pgrbprogress.set_text(str(value) + " %")

    def apply_comport_item(self, items):
        self.lsritemlist.clear()
        for itty in items:
            self.lsritemlist.append([itty])

    def set_bomrev(self, rev):
        self.etybomrev.set_text(rev)

    def set_region(self, country):
        self.etyregion.set_text(country)

    def set_product(self, pd):
        self.etyproductname.set_text(pd)

    def get_tty(self):
        tree_iter = self.cmbbcomport.get_active_iter()
        if tree_iter is not None:
            model = self.cmbbcomport.get_model()
            return model[tree_iter][0]
