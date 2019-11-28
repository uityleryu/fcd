#!/usr/bin/python3

import argparse
import sys
import time
import os

append_dir = os.path.dirname(os.getcwd())
sys.path.append(append_dir)
sys.path.append("/usr/local/sbin")

import logging
import data.constant as CONST
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gui.winFcdFactory import winFcdFactory


# EX: /media/usbdisk/gui_logs
guilogdir = "/media/usbdisk/gui_logs"
timestamp = time.strftime('%Y-%m-%d-%H')
log_file_name = "{0}/uigui_{1}.log".format(guilogdir, timestamp)

if not os.path.exists(guilogdir):
    os.makedirs(guilogdir)

log = logging.getLogger('uigui')
log.setLevel(logging.INFO)

# console log handler
log_stream = logging.StreamHandler(sys.stdout)
log_stream.setLevel(logging.DEBUG)

# file log handler
log_file = logging.FileHandler(log_file_name)
log_file.setFormatter(logging.Formatter('[%(asctime)s - %(filename)s:%(lineno)d] %(message)s', '%Y-%m-%d %H:%M:%S'))
log_file.setLevel(logging.DEBUG)

log.addHandler(log_stream)
log.addHandler(log_file)

parse = argparse.ArgumentParser(description="log sync args Parser")
parse.add_argument('--product', '-p', dest='prodline', help='The product line', default=None)
parse.add_argument('--feature', '-ft', dest='feature', help='Feature', default=None)
args, _ = parse.parse_known_args()

if args.prodline is None:
    log.info("Warning: please add product line parameter")
    exit(1)
else:
    CONST.active_product_series = args.prodline

if args.feature is None:
    log.info("Warning: please add feature parameter")
    exit(1)
else:
    CONST.feature = args.feature

if __name__ == '__main__':
    window = winFcdFactory()
    window.show_all()
    window.envinitial()
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()
