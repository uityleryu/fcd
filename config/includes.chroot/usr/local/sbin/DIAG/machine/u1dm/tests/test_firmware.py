'''
Created on Sep 4, 2018
Rev 01 on Sep 4, 2018 by JosephChou

@author: Joseph Chou

Firmware loading
'''
import logging
import time
import sys

from tests import test_def
from machine.u1dm.cmd_diag import conn

global conn
log = logging.getLogger('Diag')

svip = "192.168.1.19"

def _pre_action():
    # giving an Enter
    conn.expect2act(30, "", "")
    sstr = ["tftp",
            "-g",
            "-r images/u1-fwcommon-upgrade.tar",
            "-l /tmp/upgrade.tar",
            svip]
    sstrj = ' '.join(sstr)
    log.info("Is about to download firemware from FCD host")
    conn.expect2act(30, "#", sstrj)
    conn.expect2act(120, "", "")
    time.sleep(120)
    log.info("Finish firemware downloading from FCD host")
    return test_def.TEST_OK

def _post_action():
    return test_def.TEST_OK

def _test():
    log.info("In firmware loading")
    conn.expect2act(5, "#", "flash.sh")
    time.sleep(60)
    log.info("Exit the DIAG test and reopen to check the new firmware")
    return test_def.TEST_OK
