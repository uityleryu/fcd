#!/usr/bin/python3
import argparse
import sys
import time
import os
import tkinter as tk

append_dir = os.path.dirname(os.getcwd())
sys.path.append(append_dir)

from gui.ui_logsync import LogSyncUI
from gui_funs.logsyncfunc import LogsyncFunc
# from PAlib.FrameWork.fcd.common import Common
# from threading import Thread


# def set_window_size(win, width, height):
#     # calculate x and y coordinates for the Tk root window
#     shift_w = (win.winfo_screenwidth()/2) - (width/2)
#     shift_h = (win.winfo_screenheight()/2) - (height/2)

#     # fix position to center of window
#     win.geometry('%dx%d+%d+%d' % (width, height, shift_w, shift_h))


# class MessageDialog(object):
#     def __init__(self, msg, title="Message"):
#         self.msg_dialog = tk.Tk()
#         self.msg_dialog.title(title)
#         set_window_size(self.msg_dialog, width=800, height=40)
#         self.msg = msg
#         self.label = None
#         self._create_ui()

#     def _create_ui(self):
#         self.label = tk.Label(self.msg_dialog, text=self.msg, font=(25))
#         self.label.pack()

#     def show(self, msg=""):
#         if msg:
#             self.msg = msg
#             self.label['text'] = self.msg
#         self.msg_dialog.update()

#     def close(self):
#         self.msg_dialog.destroy()


parse = argparse.ArgumentParser(description="log sync args Parser")
args, _ = parse.parse_known_args()

# comm = Common()
# cmd = "/usr/local/sbin/prod-network.sh"
# thrd = Thread(target=comm.xcmd, args=(cmd, ))
# thrd.start()
# dialog = MessageDialog("Please wait until networking configuration ready")
# dialog.show()
# time.sleep(2)
# dialog.close()


if __name__ == '__main__':
    app = LogSyncUI(args)
    app.mainloop()
