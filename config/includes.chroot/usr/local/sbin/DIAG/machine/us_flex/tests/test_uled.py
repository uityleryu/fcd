'''
Created on May 24, 2018
Rev 01 on July 17, 2018 by MasanXu

@author: ivan.liao

Test U-Logo LED
'''
import logging
import time
import sys

from tests import test_def
from machine.us_flex.cmd_diag import conn

global conn
log = logging.getLogger('Diag')

def _pre_action():
    conn.expect2act(5, 'BZ', "echo 0 > /sys/class/leds/ubnt\:blue\:personality/brightness")
    conn.expect2act(5, 'BZ.v3.9.23#', "echo 0 > /sys/class/leds/ubnt\:white\:personality/brightness")
    return test_def.TEST_OK

def _post_action():
    conn.expect2act(5, 'BZ.v3.9.23#', "echo 1 > /sys/class/leds/ubnt\:white\:personality/brightness")
    conn.expect2act(5, 'BZ.v3.9.23#', "")
    return test_def.TEST_OK

def _test():
    conn.expect2act(5, 'BZ.v3.9.23#', "echo 1 > /sys/class/leds/ubnt\:blue\:personality/brightness")
    action = input("\nDoes LED light blue?[y/n]\n")
    if(action.lower() != 'y'):
        log.debug("LED lights blue fail")
        return test_def.TEST_FAIL

    conn.expect2act(5, 'BZ.v3.9.23#', "echo 0 > /sys/class/leds/ubnt\:blue\:personality/brightness")
    conn.expect2act(5, 'BZ.v3.9.23#', "echo 1 > /sys/class/leds/ubnt\:white\:personality/brightness")

    action = input("\nDoes LED light white?[y/n]\n")
    if(action.lower() != 'y'):
        log.debug("LED lights white fail")
        return test_def.TEST_FAIL
    conn.expect2act(5, 'BZ.v3.9.23#', "echo 0 > /sys/class/leds/ubnt\:white\:personality/brightness")
    return test_def.TEST_OK
