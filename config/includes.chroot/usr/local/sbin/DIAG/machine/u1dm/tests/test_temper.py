'''
Created on May 24, 2018
Rev 01 on July 17, 2018 by MasanXu

@author: ivan.liao

Test temperature sensor
'''
import logging
import time
import sys

from tests import test_def
from machine.u1dm.cmd_diag import conn

global conn
log = logging.getLogger('Diag')

interval = 15
localavg = 50
remoteavg = 55

def _pre_action():
    return test_def.TEST_OK

def _post_action():
    return test_def.TEST_OK

def _test():
    log.info("In temper test")
    rt_buf = []
    conn.expect2act(5, '#', "cat /sys/class/hwmon/hwmon0/temp1_input", rt_buf)
    words = rt_buf[0].split("\n")
    mes = int(words[1])/1000

    log.info("lm63 temperature: "+str(mes))
    if (mes > localavg-interval) and (mes < localavg+interval):
        log.info("Local temperature is good")
    else:
        log.info("Local temperature is bad")
        return test_def.TEST_FAIL

    rt_buf = []
    conn.expect2act(5, '#', "cat /sys/class/hwmon/hwmon0/temp2_input", rt_buf)
    words = rt_buf[0].split("\n")
    mes = int(words[1])/1000

    log.info("Remote temperature: "+str(mes))
    if (mes > remoteavg-interval) and (mes < remoteavg+interval):
        log.info("Remote temperature is good")
    else:
        log.info("Remote temperature is bad")
        return test_def.TEST_FAIL

    log.info("Temperature test is good")
    return test_def.TEST_OK
