'''
Created on May 24, 2018
Rev 01 on July 17, 2018 by MasanXu

@author: ivan.liao

Test U-Logo LED
'''
import logging
import time

from tests import test_def

log = logging.getLogger('Diag')

def _pre_action():
    return test_def.TEST_OK

def _post_action():
    return test_def.TEST_OK

def _test():
    print("In XXX test")
    return test_def.TEST_OK

