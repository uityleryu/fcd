#!/usr/bin/python
'''
Created on Dec 13, 2017

@author: ivan.liao
'''
import sys
import os
import time

from boards.platform import NewBoard
from dcmds.cmd_main import MainCmd
from Commonlib import pcmd

'''
import prog here
'''

def usage():
    print('Usage:\n')
    print('  upydiag.py <machine>\n')
    print('<machine>: Supported models which described by \n\
            machine/<machine>/<machine>.json\n')

if __name__ == '__main__':
    rtf = os.path.isfile("/home/user/.ssh/known_hosts")
    if (rtf == True):
        fh = os.path.getsize("/home/user/.ssh/known_hosts")
        if (fh > 0):
            rt = pcmd("ssh-keygen -f \"/home/user/.ssh/known_hosts\" -R 192.168.1.1")
            if (rt == True):
                print("The user ssh data has been deleted")
            else:
                print("The user ssh data hasn't been deleted")
        else:
            print("The user known_hosts is 0")
    else:
        print("The user known_hosts isn't existed")

    rtf = os.path.isfile("/root/.ssh/known_hosts")
    if (rtf == True):
        fh = os.path.getsize("/root/.ssh/known_hosts")
        if (fh > 0):
            rt = pcmd("ssh-keygen -f \"/root/.ssh/known_hosts\" -R 192.168.1.1")
            if (rt == True):
                print("The root ssh data has been deleted")
            else:
                print("The root ssh data hasn't been deleted")
        else:
            print("The root known_hosts is 0")
    else:
        print("The root known_hosts isn't existed")

    time.sleep(3)

    if len(sys.argv) == 1:
        usage()
        exit(1)
    else:
        machine = sys.argv[1]

    board = NewBoard(machine)
    MainCmd(board).cmdloop()

    # SSH debugging
    # import pexpect
    # cmd = "ssh -o \"StrictHostKeyChecking=no\" root@192.168.1.1"
    # proc = pexpect.spawn(cmd, encoding='utf-8', codec_errors='replace', timeout=2000)
    # proc.logfile_read = sys.stdout

    # index = proc.expect(["password:", pexpect.EOF, pexpect.TIMEOUT], 10)
    # if(index == 1):
    #     print("EOF")

    # if(index == 2):
    #     print("TIMEOUT")

    # proc.send("ubnt\n")
