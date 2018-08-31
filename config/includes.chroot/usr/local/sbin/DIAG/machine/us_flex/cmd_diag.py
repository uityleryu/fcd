'''
Created on 2018/07/23

@author: Masan.Xu
'''
import cmd
import logging
import Commonlib

from dcmds.cmd_default_diag import DefaultDiagCmd

'''console interface'''
conn = Commonlib.ExpttyProcess(0, "picocom /dev/ttyUSB0 -b 115200", "\n")
conn.expect2act(5, 'Terminal', "")
conn.expect2act(5, 'UBNT login:', "ubnt")
conn.expect2act(5, 'Password', "ubnt")
conn.expect2act(5, '#', "")

class DiagCmd(DefaultDiagCmd):
    def __init__(self, board):
        DefaultDiagCmd.__init__(self, board)
#        self.onecmd('test all')

    def do_exit(self, s):
        conn.expect2act(5, '#', "exit")
        conn.expect2act(5, 'Please press Enter to activate this console.', "")
        conn.expect2act(5, '', "")
        exit(0)

