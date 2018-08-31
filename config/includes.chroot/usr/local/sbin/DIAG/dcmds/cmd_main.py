'''
Created on Dec 13, 2017

@author: ivan.liao
'''
import cmd
import subprocess
import logging

from dcmds.cmd_default import DefaultCmd
import importlib

log = logging.getLogger('Diag')
class MainCmd(DefaultCmd):
    def __init__(self, board):
        DefaultCmd.__init__(self)
        self.board = board
        self.prompt = "# "
        log.info('\n=============================\nWelcome to UBNT DIAG PyShell!\n=============================\n')
        self.onecmd('diag') #Auto type-in 'diag' command

    def do_diag(self, line):
        """Enter diag sehll
        """
        module  = importlib.import_module('machine.' + self.board.machine  + '.cmd_diag')

        diag = module.DiagCmd(self.board)
        if self.board.auto_run == 1:
            diag.onecmd('test all')
        if self.board.burn_in == 1:
            pass
        diag.cmdloop()
