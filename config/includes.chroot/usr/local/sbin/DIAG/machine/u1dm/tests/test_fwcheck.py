'''
Created on Sep 5, 2018
Rev 01 on Sep 5, 2018 by JosephChou

@author: joseph.chou

Test firmware check
'''
import logging
import time
import sys

from tests import test_def
from machine.u1dm.cmd_diag import conn

global conn
log = logging.getLogger('Diag')

FWVER = "0.9.0.417"

def _pre_action():
    return test_def.TEST_OK

def _post_action():
    return test_def.TEST_OK

def _test():
    log.info("In firmware check")
    rt_buf = []
    conn.expect2act(5, '#', "cat /etc/os-release", rt_buf)
    words = rt_buf[0].split("\r")
    '''
    example:

      0: cat /etc/os-release
      1: NAME=UbiOS
      2: VERSION=0.9.0.417-gf934c2d
      3: ID=ubios
      4: VERSION_ID=0.9.0.417
      5: PRETTY_NAME="UbiOS 0.9.0.417"
    '''

    if (words[4].endswith(FWVER)):
        log.info(words[4])
        return test_def.TEST_OK
    else:
        return test_def.TEST_FAIL

