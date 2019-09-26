#!/usr/bin/python3

import tkinter as tk
import tkinter.scrolledtext
import os
import json
import logging
import data.constant as Constant

from tkinter import ttk, filedialog
from gui_funs.logsyncfunc import LogsyncFunc

"""
    tk componet
    Prefix expression
        fra    : Frame
        lbf    : LableFrame
        ety    : Entry
        cmbb   : ComboBox
        lbl    : Lable
        btn    : Button
        cbtn   : CheckButton
        txv    : TextView
        scl    : Scrolledtext
        epd    : Expander
        mgdi   : MessageDialog
        lsr    : ListStore
        crt    : CellRendererText
        dlg    : Dialog
        ntb    : Notebook
        txb    : TextBuffer
        txi    : TextIter
        strv   : StringVar
"""


class LogSyncUI(tk.Tk):
    def __init__(self, args):
        super().__init__()
        self.prodir =  "/usr/local/sbin"
        ver_file = os.path.join(self.prodir, "data", "version.txt")
        fver = open(ver_file, "r")
        self.title("Log Sync Utility Version " + fver.read().strip())
        # self.geometry("500x250")
        self.geometry("450x250")
        self.funs = LogsyncFunc(self)
        self.create_ui_outline()
        self.log = logging.getLogger('upload')
        '''
            Default sync period: every 60 seconds
        '''
        Constant.SYNC_PERIOD = 60

    def create_ui_outline(self):
        self.menubar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Open file", command=self._open_file)

        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.config(menu=self.menubar)

        self.notebook = ttk.Notebook(self)
        self.fra_panel = tk.Frame(self.notebook)
        self.fra_log = tk.Frame(self.notebook)


        rowidx = 0
        '''
            File server IP address
        '''
        self.lbl_srvip = ttk.Label(self.fra_panel, text="File Server IP:", font=8)
        self.lbl_srvip.grid(row=rowidx, column=0, sticky=tk.W, padx=10)
        self.strv_srvip = tk.StringVar()
        self.ety_srvip = ttk.Entry(self.fra_panel, textvariable=self.strv_srvip)
        self.ety_srvip.grid(row=rowidx, column=1, padx=10, pady=5)
        self.ety_srvip.focus_set()

        '''
            File server port
        '''
        rowidx += 1
        self.lbl_srvport = ttk.Label(self.fra_panel, text="File Server port:", font=8)
        self.lbl_srvport.grid(row=rowidx, column=0, sticky=tk.W, padx=10)
        self.strv_srvport = tk.StringVar()
        self.ety_srvport = ttk.Entry(self.fra_panel, textvariable=self.strv_srvport)
        self.ety_srvport.grid(row=rowidx, column=1, padx=10, pady=5)
        self.ety_srvport.focus_set()

        '''
            File server Share Folder
        '''
        rowidx += 1
        self.lbl_sharedoc = ttk.Label(self.fra_panel, text="Share Folder:", font=8)
        self.lbl_sharedoc.grid(row=rowidx, column=0, sticky=tk.W, padx=10)
        self.strv_sharedoc = tk.StringVar()
        self.ety_sharedoc = ttk.Entry(self.fra_panel, textvariable=self.strv_sharedoc)
        self.ety_sharedoc.grid(row=rowidx, column=1, padx=10, pady=5)
        self.ety_sharedoc.focus_set()

        '''
            File server allowed user name
        '''
        rowidx += 1
        self.lbl_user = ttk.Label(self.fra_panel, text="Server username:", font=8)
        self.lbl_user.grid(row=rowidx, column=0, sticky=tk.W, padx=10)
        self.strv_user = tk.StringVar()
        self.ety_user = ttk.Entry(self.fra_panel, textvariable=self.strv_user)
        self.ety_user.grid(row=rowidx, column=1, padx=10, pady=5)
        self.ety_user.focus_set()

        '''
            File server allowed user password
        '''
        rowidx += 1
        self.lbl_pwd = ttk.Label(self.fra_panel, text="Server password:", font=8)
        self.lbl_pwd.grid(row=rowidx, column=0, sticky=tk.W, padx=10)
        self.strv_pwd = tk.StringVar()
        self.ety_pwd = ttk.Entry(self.fra_panel, textvariable=self.strv_pwd)
        self.ety_pwd.grid(row=rowidx, column=1, padx=10, pady=5)
        self.ety_pwd.focus_set()

        '''
            time peroid of syncing logs (in second format)
        '''
        rowidx += 1
        self.lbl_tperiod = ttk.Label(self.fra_panel, text="Time period:", font=8)
        self.lbl_tperiod.grid(row=rowidx, column=0, sticky=tk.W, padx=10)
        self.strv_tperiod = tk.StringVar()
        self.ety_tperiod = ttk.Entry(self.fra_panel, textvariable=self.strv_tperiod)
        self.ety_tperiod.grid(row=rowidx, column=1, padx=10, pady=5)
        self.ety_tperiod.focus_set()

        '''
            Connection and sync
        '''
        rowidx += 1
        btn_color = 'peach puff'
        self.btn_connect = tk.Button(self.fra_panel, text="Connect/Sync", background='white', command=self.funs.connect_srv)
        self.btn_connect.grid(row=rowidx, column=0, pady=5)
        self.btn_connect.config(background=btn_color)

        '''
            Load configuration file
        '''
        self.btn_loadconfig = tk.Button(self.fra_panel, text="Load config", background='white', command=self.funs.load_config)
        self.btn_loadconfig.grid(row=rowidx, column=1, pady=5)
        self.btn_loadconfig.config(background=btn_color)

        '''
            Stop syncing
        '''
        # self.btn_stop = tk.Button(self.fra_panel, text="Stop Sync", background='white', command=self.funs.stop_sync)
        # self.btn_stop.grid(row=rowidx, column=2, pady=5)
        # self.btn_stop.config(background=btn_color)

        self.lbf_log = ttk.LabelFrame(self.fra_log, text="Output", relief=tk.RIDGE)
        self.lbf_log.pack(fill=tk.BOTH, expand=True)

        self.scl_log = tk.scrolledtext.ScrolledText(self.lbf_log)
        self.scl_log.pack(fill=tk.BOTH, expand=True)
        self.scl_log.configure(state='normal')

        self.notebook.add(self.fra_panel, text="Panel")
        self.notebook.add(self.fra_log, text="Log")
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def _open_file(self):
        """use by menu button [Open file]"""
        FILE_PATH = filedialog.askopenfilename(initialdir=self.prodir, title="Select file",
                                                        filetypes=(("config files", "*.ini"), ("all files", "*.*")))
        self.log.info("Current file :" + FILE_PATH)
        return FILE_PATH
