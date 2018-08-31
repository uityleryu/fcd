'''
Created on 2018/07/23

@author: Masan.Xu
'''
import cmd
import logging
import Commonlib

from dcmds.cmd_default_diag import DefaultDiagCmd

dutip = "192.168.1.1"
dutssh = "root@"+dutip

'''console interface'''
conn = Commonlib.ExpttyProcess(0, "ssh -o \"StrictHostKeyChecking=no\" "+dutssh, "\n", 'Diag')
conn.expect2act(5, dutssh+'\'s password:', "ubnt")
conn.expect2act(5, '#', "")

class DiagCmd(DefaultDiagCmd):
    def __init__(self, board):
        DefaultDiagCmd.__init__(self, board)

    def do_exit(self, s):
        conn.expect2act(5, '#', "exit")
        conn.expect2act(5, 'Connection to '+dutip+' closed.', "")
        conn.expect2act(5, '', "")
        exit(0)
