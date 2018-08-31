'''
Created on Dec 13, 2017

@author: ivan.liao
'''
#import pexpect
import cmd
import subprocess
import logging
DEBUG_ARGS = [ 'info', 'on', 'off' ]

class DefaultCmd(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "PY-SH# "

    def do_history(self, args):
        """Print a list of commands that have been entered"""
        print(self._hist)

    def do_exit(self, s):
        return True

    def do_quit(self, s):
#        if operation_confirm():
#            exit(0)
        pass

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist  = []      ## No history yet
        self._locals  = {}    ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print("Exiting...")

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop
    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    ## Customized commands ##
    def do_debug(self, args):
        """Usage:
        debug  - Print all debugging messages
        debug info - Priint some debugging messages
        debug warn - Disable debugging messages
        """
        """
        if args == 'on':
            logging.root.handlers = []
            logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
            print("Debug mode on")
        if args == 'info':
            logging.root.handlers = []
            logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
            print("Debug mode info")
        if args == 'off':
            logging.root.handlers = []
            logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.WARNING)
            print("Debug mode off")
        """
        pass

    def complete_debug(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in DEBUG_ARGS if s.startswith(mline)]

    def do_prog(self, line):
        """Enter the PROG sehll
        """
        if prog.shell != None:
            #sys.stdout.write (self.prog_shell.after)
            sys.stdout.write("Type 'Ctrl + Y' to exit .\n")
            sys.stdout.flush()

            prog.shell.interact(escape_character=chr(25))
            sys.stdout.write ('\n')
            sys.stdout.flush()
        pass

    def do_shell(self, line):
        """Enter the Linux sehll
        """
        subprocess.call(['/bin/sh'])
        pass

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception as e:
            print(e.__class__, ":", e)

def operation_confirm():
    s = input('Are you sure to do this? (y/N): ')
    if s.lower() == 'y':
        return True
    else:
        return False
