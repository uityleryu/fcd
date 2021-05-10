
import logging
import re
import time
import sys
import data.constant as CONST
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from PAlib.FrameWork.gui.msgdialog import msgerrror

log = logging.getLogger('uigui')


class dlgBarcodeinput(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(
            self, "Waiting for barcode", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.vboxbarcode = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        # self.set_default_response("ok")

        self.dlgwin = parent
        self.lbltitle = Gtk.Label("Waiting for barcode")
        self.lblmac = Gtk.Label("------------")
        self.etymacedit = Gtk.Entry()
        self.etymacedit.set_visibility(True)
        self.etymacedit.set_activates_default(True)
        self.etymacedit.connect("changed", self.on_etymacedit_changed)
        self.etymacedit.set_activates_default(True)
        okButton = self.get_widget_for_response(response_id=Gtk.ResponseType.OK)
        okButton.set_can_default(True)
        okButton.grab_default()

        self.vboxbarcode.pack_start(self.lbltitle, False, False, 0)
        self.vboxbarcode.pack_start(self.lblmac, False, False, 0)
        self.vboxbarcode.pack_start(self.etymacedit, False, False, 0)

        self.area = self.get_content_area()
        self.area.add(self.vboxbarcode)
        self.show_all()

    def on_etymacedit_changed(self, entry):
        __FUNC = "on_etymacedit_changed()"
        CONST.barcode = self.etymacedit.get_text().strip()
        CONST.barcodelen = len(CONST.barcode)
        lmsg = "{0}: barcode: {1}, length: {2}".format(__FUNC, CONST.barcode, CONST.barcodelen)
        log.info(lmsg)

    '''
        This function is used for checking the format of the barcode
        and extracting the MAC and QR code.
    '''
    def check_barcode(self, stm):
        __FUNC = sys._getframe().f_code.co_name

        barcode = CONST.barcode
        barcodelen = CONST.barcodelen
        macaddrlen = CONST.macaddrlen
        qrcodelen = CONST.qrcodelen

        qrcheck = CONST.active_product_obj['QRCHECK']
        if qrcheck == "True":
            if (barcodelen == (macaddrlen + qrcodelen + 1)):
                btmp = barcode.split("-")
                if ((len(btmp[0]) != macaddrlen) or \
                    (len(btmp[1]) != qrcodelen)):
                    msgerrror(self.dlgwin, "Barcode invalid. Exiting...")
                    rt = False
                else:
                    mac_speci_char = re.search(r'[^0-9a-fA-F]', btmp[0])
                    qr_speci_char = re.search(r'[^0-9a-zA-Z]', btmp[1])
                    if mac_speci_char is not None:
                        rtmsg = "{}: the macaddr format is incorrect".format(__FUNC)
                        log.info(rtmsg)
                        msgerrror(self.dlgwin, "MAC address invalid. Exiting...")
                        rt = False
                    elif qr_speci_char is not None:
                        rtmsg = "{}: the QR code format is incorrect".format(__FUNC)
                        log.info(rtmsg)
                        msgerrror(self.dlgwin, "QR code invalid. Exiting...")
                        rt = False
                    else:
                        rtmsg = "{}: the barcode is valid".format(__FUNC)
                        log.info(rtmsg)
                        CONST.macaddr = btmp[0]
                        CONST.qrcode = btmp[1]
                        stm[0] = time.time()
                        rtmsg = "{0}: start time: {1}".format(__FUNC, stm[0])
                        log.info(rtmsg)
                        rt = True
            else:
                msgerrror(self.dlgwin, "Barcode invalid. Exiting...")
                rt = False
        else:
            if (barcodelen == (macaddrlen)):
                mac_speci_char = re.search(r'[^0-9a-fA-F]', barcode)
                if mac_speci_char is not None:
                    rtmsg = "{} the macaddr format is incorrect".format(__FUNC)
                    log.info(rtmsg)
                    msgerrror(self.dlgwin, "MAC address invalid. Exiting...")
                    rt = False
                else:
                    rtmsg = "{}: the barcode is valid".format(__FUNC)
                    log.info(rtmsg)
                    CONST.macaddr = barcode
                    stm[0] = time.time()
                    rtmsg = "{0}: start time: {1}".format(__FUNC, stm[0])
                    log.info(rtmsg)
                    rt = True
            else:
                msgerrror(self.dlgwin, "Barcode invalid. Exiting...")
                rt = False

        return rt
