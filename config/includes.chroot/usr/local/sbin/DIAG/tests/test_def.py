'''
Created on May 21, 2018

@author: ivan.liao
'''
#import pexpect
import signal
#import sys
import time
import logging
import os

log = logging.getLogger('Diag')
BREAK_LOOP = 0
SHOW_TITLE = ['EN', 'ID', 'Test Name', 'Count', 'Pass/Fail']
BOARD = None

# Return value
TEST_OK = 0
TEST_FAIL = -1
TEST_PREACT_ERR = -2
TEST_POSTACT_ERR = -3

"""
# This function is deprecated. The ctrl-c is catched by keyboardInterrupt
# exception in diag.py.

def signal_handler(signal, frame):
        global BREAK_LOOP
        BREAK_LOOP = 1
        log.info('BREAK_LOOP = %d' % BREAK_LOOP)
    #sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
"""

class Item_test(object):
    def __init__(self, en, id, description, module, param=None):
        self.en = en
        self.id = id
        self.description = description
        self._pre_action = module._pre_action
        self._test = module._test
        self._post_action = module._post_action
        self.test_param = param
        self.pass_count = 0
        self.fail_count = 0

    def show_test_item(self):
        str_en = ' '

        if self.en == 1:
            str_en = '*'

        log.info(' %s  %03s   %s' % (str_en, self.id, self.description))

    def enable_test(self):
        self.en = 1

    def disable_test(self):
        self.en = 0

class TestParams(object):
    def __init__(self, board):
        self.board = board
        self.param = None

    def set_param(self, obj):
        self.param = obj

    def set_debug(self, debug):
        self.debug = debug

class DiagTests(object):
    def __init__(self, board=None):
        self.item_list = {}
        self.default_tid_list = {}
        self.burnin_tid_list = {}
        self.env_info = None
        self.board = board

    def show_all_test_items(self):
        log.info('')
        log.info('%s  %s    %s' % (SHOW_TITLE[0], SHOW_TITLE[1],SHOW_TITLE[2]))
        log.info('===================================')
        for i in sorted(self.item_list):
            self.item_list[i].show_test_item()

    def show_summary(self):
        log.info('')
        log.info('%03s  %-20s  %s  %s' % (SHOW_TITLE[1],
                                          SHOW_TITLE[2],
                                          SHOW_TITLE[3],
                                          SHOW_TITLE[4]))

        log.info('===============================================')
        for i in sorted(self.item_list):
            log.info('%03s  %-20s    %-3d   %3d/%-3d' % (self.item_list[i].id,
                                                         self.item_list[i].description,
                                                         self.item_list[i].pass_count + self.item_list[i].fail_count,
                                                         self.item_list[i].pass_count,
                                                         self.item_list[i].fail_count))


    def switch_test_items(self, switch, args):
        args = args.split(' ')
        argc = len(args)
        log.info('%d %s' %(argc,args))

        for i in range(1,argc,1):
            try:
                test_num = int(args[i],10)

                if test_num in self.item_list:
                    self.item_list[test_num].en = switch
                else:
                    log.info('%d is not a valid test ID' % test_num)
                    return

            except Exception as e:
                log.info('Params is not a number')
                return

    def set_test_items(self, id_list):
        '''
        Select items from a specific list
        '''
        for i in self.item_list:
            try:
                test_num = i

                if test_num in id_list:
                    self.item_list[test_num].en = 1
                else:
                    self.item_list[test_num].en = 0

            except Exception as e:
                log.info('Params is not a number')
                return

    def run_test_item(self, id, loop=1, debug=0):
        global BREAK_LOOP
        BREAK_LOOP = 0

        if id in self.item_list:
            pass_count = 0
            fail_count = 0

            # loop test, otherwise You pressed Ctrl+C
            for l in range(0,loop):
                if BREAK_LOOP == 1: break # Ctrl + C
                log.info("Loop %d..." % (l+1))
                if self.item_list[id].en == 1:
                    rv = TEST_OK
                    # Pre-action for test
                    rv = self.item_list[id]._pre_action()

                    # test core
                    if(rv == TEST_OK):
                        rv |= self.item_list[id]._test()

                    # Post-action for test
                    rv |= self.item_list[id]._post_action()

                    if rv == TEST_OK :
                        pass_count += 1
                    else:
                        fail_count += 1

            log.info('')
            log.info('%s %s  %s %s' % (SHOW_TITLE[1],
                                       SHOW_TITLE[2].center(25," "),
                                       SHOW_TITLE[3],
                                       SHOW_TITLE[4]))

            log.info('===============================================')
            log.info('%s %s  %4d %4d/%d' % (self.item_list[id].id,
                                            self.item_list[id].description.center(25," "),
                                            loop,
                                            pass_count,
                                            fail_count))

            self.item_list[id].pass_count += pass_count
            self.item_list[id].fail_count += fail_count
        else:
            log.error('test item %d is invalid' % id)

    def run_all_test_items(self, loop=1, debug=0):
        global BREAK_LOOP
        BREAK_LOOP = 0

        pass_count = {}
        fail_count = {}

        # loop test, otherwise You pressed Ctrl+C
        for l in range(0,loop):
            if BREAK_LOOP == 1: break # Ctrl + C

            # print env info every loop
            if self.env_info:       self.env_info()

            log.info("Loop %d..." % (l+1))
            for id in sorted(self.item_list):
                if not id in pass_count:
                    pass_count[id] = 0
                    fail_count[id] = 0

                if BREAK_LOOP == 1: break # Ctrl + C
                if self.item_list[id].en == 1:
                    rv = TEST_OK
                    # Pre-action for test
                    rv = self.item_list[id]._pre_action()

                    # test core
                    if(rv == TEST_OK):
                        rv |= self.item_list[id]._test()

                    # Post-action for test
                    rv |= self.item_list[id]._post_action()

                    if rv == TEST_OK :
                        pass_count[id] += 1
                        self.item_list[id].pass_count += 1
                    else:
                        fail_count[id] += 1
                        self.item_list[id].fail_count += 1

        # print env info again
        if self.env_info:       self.env_info()

        log.info('')
        log.info('%03s  %-20s  %s  %s' % (SHOW_TITLE[1],
                                          SHOW_TITLE[2],
                                          SHOW_TITLE[3],
                                          SHOW_TITLE[4]))

        log.info('===============================================')
        for i in sorted(self.item_list):
            log.info('%03s  %-20s    %-3d   %3d/%-3d' % (self.item_list[i].id,
                                                         self.item_list[i].description,
                                                         pass_count[i] + fail_count[i],
                                                         pass_count[i],
                                                         fail_count[i]))

    def change_item_list(self, list):
        self.item_list = list

    def clear_test_counter(self):
        for id in self.item_list:
            #clear all test items pass & fail count
            self.item_list[id].pass_count = 0
            self.item_list[id].fail_count = 0

    def add(self, item_test):
        self.item_list[item_test.id] = item_test
