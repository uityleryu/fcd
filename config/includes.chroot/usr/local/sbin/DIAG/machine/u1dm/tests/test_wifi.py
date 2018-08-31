'''
Created on May 24, 2018
Rev 01 on July 17, 2018 by MasanXu

@author: ivan.liao

Test Wifi
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
    log.debug("In Wifi test")
    return test_def.TEST_OK
