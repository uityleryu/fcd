#!/usr/bin/python3

from gi.repository import Gtk

import gi
gi.require_version('Gtk', '3.0')


def msgerrror(parent, msg):
    mgdimsg = Gtk.MessageDialog(
        parent,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.ERROR,
        Gtk.ButtonsType.CLOSE,
        "")
    mgdimsg.format_secondary_text(msg)
    mgdimsg.run()
    mgdimsg.destroy()


def msginfo(parent, msg):
    mgdimsg = Gtk.MessageDialog(
        parent,
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