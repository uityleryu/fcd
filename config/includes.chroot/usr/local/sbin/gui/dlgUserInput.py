
import logging
import json
import os
import sys
import data.constant as CONST
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
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


class dlgUserInput(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(
            self, "User Input Dialog", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)
        self.vboxuserauth = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # Pass phrase
        self.lblpassphrase = Gtk.Label("Please enter pass-phrase:")
        self.etypassphrase = Gtk.Entry()
        self.etypassphrase.set_visibility(False)
        self.etypassphrase.set_activates_default(True)
        self.etypassphrase.connect("changed", self.on_phassphrase_changed)

        # Load test items
        # Product info file: /usr/local/sbin/Products-info.json
        fpath = os.path.join(CONST.app_dir, "Products-info.json")
        fh = open(fpath)
        self.prods = json.load(fh)
        fh.close()

        if CONST.active_product_series == "":
            log.info("The Product Series is empty ")
            exit(1)
        else:
            log.info("The Product Series: " + CONST.active_product_series)

        # Product combo box
        self.lblallpd = Gtk.Label("Select a product:")
        self.lsrallpdlist = Gtk.ListStore(int, str)

        self.lsrallpdlist.clear()
        [CONST.active_productidx, CONST.active_product] = ["", ""]

        for key, val in sorted(self.prods[CONST.active_product_series].items()):
            if val['FILE'] != "":
                self.lsrallpdlist.append([val['INDEX'], key])

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
        for item in CONST.region_names:
            self.lsrregionlist.append([item])

        self.crtregionlist = Gtk.CellRendererText()
        self.cmbbregion = Gtk.ComboBox.new_with_model(self.lsrregionlist)
        self.cmbbregion.pack_start(self.crtregionlist, True)
        self.cmbbregion.add_attribute(self.crtregionlist, "text", 0)
        # self.cmbbregion.set_active(0)
        self.cmbbregion.connect("changed", self.on_region_combo_changed)

        if CONST.feature == "register":
            self.vboxuserauth.pack_start(self.lblpassphrase, False, False, 0)
            self.vboxuserauth.pack_start(self.etypassphrase, False, False, 0)
            self.vboxuserauth.pack_start(self.lblallpd, False, False, 0)
            self.vboxuserauth.pack_start(self.cmbballpd, False, False, 0)
            self.vboxuserauth.pack_start(self.lblbomrev, False, False, 0)
            self.vboxuserauth.pack_start(self.etybomrev, False, False, 0)
            self.vboxuserauth.pack_start(self.lblregion, False, False, 0)
            self.vboxuserauth.pack_start(self.cmbbregion, False, False, 0)
        else:
            self.vboxuserauth.pack_start(self.lblallpd, False, False, 0)
            self.vboxuserauth.pack_start(self.cmbballpd, False, False, 0)

        self.area = self.get_content_area()
        self.area.add(self.vboxuserauth)
        self.show_all()

    def on_phassphrase_changed(self, entry):
        passphrase = self.etypassphrase.get_text()
        CONST.active_passphrase = passphrase.strip()

    def on_allpd_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            [CONST.active_productidx, CONST.active_product] = model[tree_iter][:2]
            CONST.active_product_obj = self.prods[CONST.active_product_series][CONST.active_product]

    def on_bomrev_changed(self, entry):
        bomrev = self.etybomrev.get_text()
        CONST.active_bomrev = bomrev.strip()

    def on_region_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            CONST.active_region = model[tree_iter][0]

    '''
        This is for registration
    '''
    def check_inputs_reg(self):
        __FUNC = sys._getframe().f_code.co_name
        idx = CONST.active_productidx
        if (CONST.active_passphrase == "" or \
           CONST.active_productidx == "" or \
           CONST.active_product == "" or \
           CONST.active_bomrev == "" or \
           CONST.active_region == ""):
            return False

        ubomrev = CONST.active_bomrev.split("-")
        rtmsg = "{0}: 1st ubomrev: {1}".format(__FUNC, ubomrev)
        log.info(rtmsg)
        if (len(ubomrev) < 2):
            rtmsg = "{0}: BOM revision format incorrect".format(__FUNC)
            log.info(rtmsg)
            return False
        else:
            ubomrev = ubomrev[0] + "-" + ubomrev[1]
            rtmsg = "{0}: 2nd ubomrev: {1}".format(__FUNC, ubomrev)
            log.info(rtmsg)

        if (ubomrev != CONST.active_product_obj['BOMREV']):
            rtmsg = "{0}: input BOM revision is not match to product".format(__FUNC)
            log.info(rtmsg)

            return False

        return True

    '''
        This is for back to ART
    '''
    def check_inputs_bta(self):
        __FUNC = sys._getframe().f_code.co_name
        idx = CONST.active_productidx
        if (CONST.active_productidx == "" or \
           CONST.active_product == ""):
            return False

        return True

