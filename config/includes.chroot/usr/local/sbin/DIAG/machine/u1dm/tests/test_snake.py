'''
Created on May 24, 2018
Rev 01 on July 17, 2018 by MasanXu

@author: ivan.liao

Snake test for traffic
'''
import logging
import time
import sys

from tests import test_def
from machine.u1dm.cmd_diag import conn

global conn
log = logging.getLogger('Diag')

def _pre_action():
    conn.expect2act(5, '#', "pkill -9 /sbin/udhcpc")
    conn.expect2act(5, '#', "sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    conn.expect2act(5, '#', "sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    return test_def.TEST_OK

def _post_action():
    conn.expect2act(5, '#', "swconfig dev switch0 port 2 set enable_vlan 0")
    conn.expect2act(5, '#', "swconfig dev switch0 port 3 set enable_vlan 0")
    conn.expect2act(5, '#', "swconfig dev switch0 port 4 set enable_vlan 0")
    conn.expect2act(5, '#', "swconfig dev switch0 port 5 set enable_vlan 0")
    conn.expect2act(5, '#', "")
    return test_def.TEST_OK

def _test():
    rt_buf = []
    log.info("Start snake test vlan settings")
    conn.expect2act(5, '#', "swconfig dev switch0 port 2 set enable_vlan 1")
    conn.expect2act(5, '#', "swconfig dev switch0 port 3 set enable_vlan 1")
    conn.expect2act(5, '#', "swconfig dev switch0 port 4 set enable_vlan 1")
    conn.expect2act(5, '#', "swconfig dev switch0 port 5 set enable_vlan 1")
    conn.expect2act(5, '#', "swconfig dev switch0 vlan 0 set ports \'0 1\'")
    conn.expect2act(5, '#', "swconfig dev switch0 vlan 10 set ports \'2 3\'")
    conn.expect2act(5, '#', "swconfig dev switch0 vlan 11 set ports \'4 5\'")
    conn.expect2act(5, '#', "swconfig dev switch0 set apply")
    conn.expect2act(5, '#', "swconfig dev switch0 show", rt_buf)
    conn.expect2act(5, '#', "ifconfig", rt_buf)
    conn.expect2act(5, '#', "")
    log.info("")
    log.info("Snake test vlan settings is done")
    log.info("Please connect port2&5 to packet generator individually and connect port 3&4 with cable")
    log.info("Please send traffic and check trffic status with packet generator")

    action = input("Does traffic status is true?[y/n]")
    if(action.lower() != 'y'):
        log.info("snake test FAIL!!")
        return test_def.TEST_FAIL

    return test_def.TEST_OK
