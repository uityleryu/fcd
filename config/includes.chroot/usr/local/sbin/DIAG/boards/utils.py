'''
Created on May 24, 2018

@author: ivan.liao
'''
import subprocess
import logging

log = logging.getLogger('Diag')

def sys_set_cmd(command, params=None):
    log.debug("[UTILS] sys_set_cmd command=%s, params=%s" % (command, params))
    if params is not None:
        cmdline = [command] + params
    try:
        subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        log.error("[UTILS] sys_set_cmd command = %s failed." % command)

def sys_get_cmd(command, params=None):
    log.debug("[UTILS] sys_get_cmd command=%s, params=%s" % (command, params))
    if params is not None:
        cmdline = [command] + params
    try:
        result = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        log.error("[UTILS] sys_get_cmd command = %s failed." % command)
        return ''
    log.debug("[UTILS] sys_get_cmd result = %s" % result)
    return result

if __name__ == '__main__':
    # shell_cmd('ps', ['-a','-x'])
    # sys_set_cmd('tools/intelgpio', '17 1 0')
    print sys_get_cmd('tools/ipmitool', ['sensor', 'reading', 'CPU Temp'])