'''
Created on May 24, 2018
Rev 01 on July 17, 2018 by MasanXu

@author: ivan.liao

Test Factory reset button
'''
import logging
import time
import sys

from tests import test_def
from machine.u1dm.cmd_diag import conn

global conn
log = logging.getLogger('Diag')

def _pre_action():
    return test_def.TEST_OK

def _post_action():
    return test_def.TEST_OK

def _test():
    log.debug("In factory test")
    sstr = ["tftp",
            "-g",
            "-r tools/evtest",
            "-l /tmp/evtest",
            "192.168.1.19"]
    sstrj = ' '.join(sstr)
    conn.expect2act(5, '#', sstrj)
    conn.expect2act(5, '#', "chmod 777 /tmp/evtest")
    conn.expect2act(5, '#', "cd /tmp; ./evtest")
    conn.expect2act(5, 'Select the device event number', "0")

    log.info("Pressing the reset within 10 seconds")
    rt = conn.expect2act(10, 'value 1', "")
    if (rt < 0):
        conn.expect2act(5, '', "\003\003")
        conn.expect2act(5, '', "")
        return test_def.TEST_FAIL

    rt = conn.expect2act(5, 'value 0', "")
    if (rt < 0):
        conn.expect2act(5, '', "\003\003")
        conn.expect2act(5, '', "")
        return test_def.TEST_FAIL

    time.sleep(1)
    conn.expect2act(5, '', "\003\003")
    conn.expect2act(5, '', "")

    return test_def.TEST_OK
