'''
Created on Dec 13, 2017

@author: ivan.liao
'''
import cmd
import logging
import sys

from dcmds.cmd_default import DefaultCmd

log = logging.getLogger('Diag')

DEBUG_ARGS = [ 'on', 'off' ]
SHOW_ARGS = ['devs', 'platform']
TEST_ARGS = [ 'list', 'on', 'off' , 'all', 'summary', 'clear', 'set' ]
TEST_LIST = ['default', 'all']
TEST_ON_OFF = ['on', 'off']

class DefaultDiagCmd(DefaultCmd):
    def __init__(self, board):
        DefaultCmd.__init__(self)
        self.board = board
        self.prompt = "DIAG-" + board.machine + "# "

    def do_debug(self, args):
        """Usage:
        debug on  - Print all debugging messages
        debug off - Disable debugging messages
        """
        if args == 'on':
            #log = logging.getLogger('Diag')
            log.setLevel(logging.DEBUG)
            log.info('Set debug level to \"DEBUG\"')
        if args == 'off':
            #log = logging.getLogger('Diag')
            log.setLevel(logging.INFO)
            log.info('Set debug level to \"INFO\"')

    def complete_debug(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in DEBUG_ARGS if s.startswith(mline)]

    def do_test(self, line):
        """Usage:
        test list - list all test items
        test summary - show all test items summary
        test on <ID> - enable test items
        test off <ID> - disable test items
        test clear - clear all test counters
        test set {default|all|burn-in} - set to a specific test list
        test {all|burn-in} [debug] [<loop>] - test enabled items
        test <ID> [debug] [<loop>] - test selected item
        """
        tests = self.board.diag_tests
        args = line.split(' ')
        argc = len(args)

        if args[0] == 'list':
            tests.show_all_test_items()
        elif args[0] == 'summary':
            tests.show_summary()
        elif args[0] == 'on':
            tests.switch_test_items(1, line)
        elif args[0] == 'off':
            tests.switch_test_items(0, line)
        elif args[0] == 'clear':
            tests.clear_test_counter()
        elif args[0] == 'set' and argc > 1:
            if args[1] == 'all':
                if args[2] == 'on':
                    tests.set_test_items(tests.item_list)
                if args[2] == 'off':
                    tests.set_test_items(None)
#            elif args[1] == 'burn-in':
#                tests.set_test_items(None)
            elif args[1] == 'default':
                tests.set_test_items(tests.default_tid_list)
        elif args[0] == 'all' or args[0] == 'burn-in' or args[0].isdigit():
            test_id = args.pop(0)
            # check debug flag
            test_debug = 0
            if len(args) > 0 and args[0] == 'debug':
                test_debug = 1
                args.pop(0)
            # check loop count
            loop_count = 1
            if len(args) > 0 and args[0].isdigit():
                loop_count = int(args.pop(0), 10)
            # do test
            if test_id == 'all':
                tests.run_all_test_items(loop=loop_count, debug=test_debug)
            elif test_id == 'burn-in':
                # tests.set_test_items(self.tests.burnin_tid_list)
                # tests.run_all_test_items(loop=loop_count, debug=test_debug)
                pass
            else:
                tests.run_test_item(int(test_id, 10), loop=loop_count, debug=test_debug)

    def complete_test(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        # test sub-command
        sline = mline.partition(' ')[0]
        if sline != text:  # check for completion
            if sline == 'set':
                if not text:
                    return TEST_LIST
                else:
                    return [f for f in TEST_LIST if f.startswith(text)]
        offs = len(mline) - len(text)
        return [s[offs:] for s in TEST_ARGS if s.startswith(mline)]

#    def do_show(self, line):
#        """Usage:
#        show devs - List all devs
#        """
#        if line == 'devs':
#            for k, dev in self.board.plat_devs.items():
#                print('%s: %s' % (dev.__class__.__name__, dev.name))
#        elif line == 'platform':
#            print('Platform: %s' %self.board.name)
#        pass
#
#    def complete_show(self, text, line, begidx, endidx):
#        mline = line.partition(' ')[2]
#        offs = len(mline) - len(text)
#        return [s[offs:] for s in SHOW_ARGS if s.startswith(mline)]
#
#
#    def do_uled(self, line):
#        """Usage:
#        uled <color> (on|off) - Turn on/off ULogo LED
#        uled <color> brightness <0-100> - Set brightness of ULogo LED
#        """
#        cmd_uled.do_uled(self, line)
#
#    def complete_uled(self, text, line, begidx, endidx):
#        return cmd_uled.complete_uled(self, text, line, begidx, endidx)
#
#
#    def do_i2c(self, line):
#        """Usage:
#        i2c readb <bus> <addr> <offset>
#        i2c writeb <bus> <addr> <offset> <data>
#        i2c readw <bus> <addr> <offset>
#        i2c writew <bus> <addr> <offset> <data>
#        i2c list
#        """
#       cmd_i2c.do_i2c(self, line)
#
#    def complete_i2c(self, text, line, begidx, endidx):
#        return cmd_i2c.complete_i2c(self, text, line, begidx, endidx)
#
#    def do_gpio(self, line):
#        """Usage:
#        gpio dump <dev> - List all pins and state
#        gpio set <dev> <pin> {0|1} - Set pin as 0 or 1
#        """
#        cmd_gpio.do_gpio(self, line)
#
#    def complete_gpio(self, text, line, begidx, endidx):
#        return cmd_gpio.complete_gpio(self, text, line, begidx, endidx)
#
#    def do_fan(self, line):
#        '''Usage:
#        fan show {<name>|all}   - Show fan speed
#        fan pwm <name> <0-100>  - Set duty cycle of fans
#        '''
#        cmd_fan.do_fan(self, line)
#
#    def complete_fan(self, text, line, begidx, endidx):
#        return cmd_fan.complete_fan(self, text, line, begidx, endidx)
#
#    def do_temp(self, line):
#        '''Usage:
#        temp show <name>         - Show temperature
#        '''
#        cmd_temp.do_temp(self, line)
#
#    def complete_temp(self, text, line, begidx, endidx):
#        return cmd_temp.complete_temp(self, text, line, begidx, endidx)
