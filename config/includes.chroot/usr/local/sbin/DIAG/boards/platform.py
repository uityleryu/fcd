#!/usr/bin/python
'''
Created on Dec 13, 2017

@author: ivan.liao

Controller of platform
'''
import logging
import time
import json
import sys
import os

from tests.test_def import DiagTests, Item_test, TestParams
import Commonlib
import importlib


DiagTestMap = {
'''Basic test  (-99)'''
  'LED Test'         : 1  ,
  'Factory Reset'    : 2  ,

'''Storage test(100-199)'''
  'Flash Test'       : 100,

'''POE test    (200-299)'''
  'POE test'         : 200,

'''Traffic test(300-399)'''
  'Snake test'       : 300,

'''Wifi test   (400-499)'''
  'Wifi XX test'     : 400,

'''Audio test  (500-599)'''
  'Audio XX test'    : 500,

'''BLE test    (600-699)'''
  'BLE XX test'      : 600,

'''Fan test    (700-799)'''
  'Fan test   '      : 700,

'''Temperature (800-899)'''
  'Temperature test' : 800
}

diagdir = "/usr/local/sbin/DIAG"
usblogdir = "/media/usbdisk/logs"

class DiagTest(object):
    def __init__(self, test_id, test_name, test_func):
        self.ID = test_id
        self.name = test_name
        self.func = test_func

    def get_ID(self):
        return self.ID

class NewBoard(object):
    '''
    Main system definition
    '''

    def __init__(self, machine):
        self.machine = machine
        self.init_log()
        self.DiagTestMap = ()
        self.auto_run = None
        self.burn_in = None

        # Load test items
        f = open(diagdir+'/machine/'+ self.machine + '/' + self.machine + '.json')
        self.machine_data = json.load(f)
        f.close()

        self.diag_tests = self.init_diag_test_items()

    def init_diag_test_items(self):
        diag_tests = DiagTests()

        for name, ID in DiagTestMap.items():
          for testitem in self.machine_data['DiagTestItems']:
            # Dynamically load test module based on machine name
            module = importlib.import_module('machine.' + self.machine + '.tests.' + testitem['File'])
            if testitem['ID'] == ID:
              diag_tests.add(Item_test(testitem['EN'], testitem['ID'], testitem['Name'], module, TestParams(self)))

        if 'auto_run' in self.machine_data:
            self.auto_run = self.machine_data['auto_run']
        if 'burn_in' in self.machine_data:
            self.burn_in = self.machine_data['burn_in']

        return diag_tests

    def init_log(self):
        log = logging.getLogger('Diag')
        log.setLevel(logging.INFO)

        # console log handler
        log_stream = logging.StreamHandler(sys.stdout)
        log_stream.setLevel(logging.DEBUG)

        # file log handler
        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
        if not os.path.exists(usblogdir):
            os.makedirs(usblogdir)

        logfilename = usblogdir + '/' + timestamp + '_test.log'
        log_file = logging.FileHandler(logfilename)
        log_file.setFormatter(logging.Formatter('[%(asctime)s - %(filename)s:%(lineno)d] %(message)s', '%Y-%m-%d %H:%M:%S'))
        log_file.setLevel(logging.DEBUG)

        log.addHandler(log_stream)
        log.addHandler(log_file)
