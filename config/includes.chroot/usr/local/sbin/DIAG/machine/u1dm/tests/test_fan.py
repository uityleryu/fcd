'''
Created on May 24, 2018
Rev 01 on July 17, 2018 by MasanXu

@author: ivan.liao

Test Fan operation
'''
import logging
import time
import sys

from tests import test_def
from machine.u1dm.cmd_diag import conn

global conn
log = logging.getLogger('Diag')

interval = 200
rmptarget25p = 1900
rmptarget50p = 3200
rmptarget75p = 4600
rmptarget100p = 6300

def _pre_action():
    # Switching on the pwm1_enable so that we can configure the pwm1
    conn.expect2act(5, '#', "echo 1 > /sys/class/hwmon/hwmon0/pwm1_enable")
    return test_def.TEST_OK

def _post_action():
    # Switching off the pwm1_enable so that we can configure the pwm1
    conn.expect2act(5, '#', "echo 2 > /sys/class/hwmon/hwmon0/pwm1_enable")
    return test_def.TEST_OK

def _test():
    log.debug("In Fan test")
    conn.expect2act(5, '#', "echo 110 > /sys/class/hwmon/hwmon0/pwm1")
    time.sleep(5)
    rt_buf = []
    conn.expect2act(10, '#', "cat /sys/class/hwmon/hwmon0/fan1_input", rt_buf)

    words = rt_buf[0].split("\n")
    log.info("25% RPM: "+words[1])
    if (int(words[1]) > rmptarget25p-interval) and (int(words[1]) < rmptarget25p+interval):
        log.info("Test 25% PWM is good")
    else:
        log.info("Test 25% PWM is bad")
        return test_def.TEST_FAIL

    conn.expect2act(5, '#', "echo 140 > /sys/class/hwmon/hwmon0/pwm1")
    time.sleep(5)
    rt_buf = []
    conn.expect2act(10, '#', "cat /sys/class/hwmon/hwmon0/fan1_input", rt_buf)

    words = rt_buf[0].split("\n")
    log.info("50% RPM: "+words[1])
    if (int(words[1]) > rmptarget50p-interval) and (int(words[1]) < rmptarget50p+interval):
        log.info("Test 50% PWM is good")
    else:
        log.info("Test 50% PWM is bad")
        return test_def.TEST_FAIL

    conn.expect2act(5, '#', "echo 200 > /sys/class/hwmon/hwmon0/pwm1")
    time.sleep(5)
    rt_buf = []
    conn.expect2act(10, '#', "cat /sys/class/hwmon/hwmon0/fan1_input", rt_buf)

    words = rt_buf[0].split("\n")
    log.info("75% RPM: "+words[1])
    if (int(words[1]) > rmptarget75p-interval) and (int(words[1]) < rmptarget75p+interval):
        log.info("Test 75% PWM is good")
    else:
        log.info("Test 75% PWM is bad")
        return test_def.TEST_FAIL

    conn.expect2act(5, '#', "echo 255 > /sys/class/hwmon/hwmon0/pwm1")
    time.sleep(5)
    rt_buf = []
    conn.expect2act(10, '#', "cat /sys/class/hwmon/hwmon0/fan1_input", rt_buf)

    words = rt_buf[0].split("\n")
    log.info("100% RPM: "+words[1])
    if (int(words[1]) > rmptarget100p-interval) and (int(words[1]) < rmptarget100p+interval):
        log.info("Test 100% PWM is good")
    else:
        log.info("Test 100% PWM is bad")
        return test_def.TEST_FAIL

    log.info("Fan test is good")
    return test_def.TEST_OK
