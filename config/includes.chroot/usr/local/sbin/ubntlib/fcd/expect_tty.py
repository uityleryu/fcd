#!/usr/bin/python3
import time
import sys
import pexpect
import logging
from io import StringIO

class ExpttyProcess():

    TIMEOUT = -1
    EOF = -2

    def __init__(self, id, cmd, newline, logger_name=None):
        self.id = id
        self.proc = pexpect.spawn(cmd, encoding='utf-8', codec_errors='replace', timeout=2000)
        self.proc.logfile_read = sys.stdout
        self.newline = newline
        # Using default logger shows message to stdout
        if(logger_name == None):
            self.log = logging.getLogger()
            self.log.setLevel(logging.DEBUG)
            log_stream = logging.StreamHandler(sys.stdout)
            log_stream.setLevel(logging.DEBUG)
            self.log.addHandler(log_stream)
        # Using customized logger shows message
        else:
            self.log = logging.getLogger(logger_name)

    def expect_only(self, timeout, exptxt):
        """Simply expect.
            Will exit if expect timeout or EOF.
        """
        return self.__expect_base(timeout=timeout, exptxt=exptxt)

    def expect_action(self, timeout, exptxt, action):
        """Expect and send action cmd.
            Will exit if expect timeout or EOF.
        """
        return self.__expect_base(timeout=timeout, exptxt=exptxt, action=action)

    def expect_get_index(self, timeout, exptxt):
        """Expect and get index which expect found.
        Returns:
            [int] -- index if found, -1 if timeout
        """
        return self.__expect_base(timeout=timeout, exptxt=exptxt, end_if_timeout=False, get_result_index=True)

    def expect_get_output(self, action, prompt, timeout=3):
        """Expect and only get output which expect found.
        Returns:
            [string] -- all output after this function been called in the timeout perioud
        """
        return self.__expect_base(timeout=timeout, exptxt="dump_string_for_output_purpose_only",  action=action,
                                  end_if_timeout=False, get_output=True, prompt=prompt)

    def __expect_base(self, timeout, exptxt, action=None, end_if_timeout=True, get_result_index=False,
                      prompt=None, get_output=False):
        """
        Args:
            timeout {int}:
            exptxt {string or list}:
            action {string}: the action command
            end_if_timeout {bool}: if timeout, exit or return -1
            get_result_index {bool}: if true, return index which expect found
        Returns:
            return 0 means success
            return index if get_result_index is True
        """
        ex = []
        if isinstance(exptxt, list):
            for e in exptxt:
                ex.append(e)
        else:
            ex.append(exptxt)
        ex.append(pexpect.EOF)
        ex.append(pexpect.TIMEOUT)

        if (action is not None) and (get_output is True):
            self.proc.expect([prompt, pexpect.EOF, pexpect.TIMEOUT], timeout)  # for clearing previous stdout
            self.proc.send(action + self.newline)

        index = self.proc.expect(ex, timeout)
        if(index == (len(ex) - 2 )):
            print("[ERROR:EOF]: Expect \"" + str(exptxt) + "\"")
            exit(1)
        if(index == (len(ex) - 1)):
            if not get_output:
                print("[ERROR:Timeout]: Expect \"" + str(exptxt) + "\" more than " + str(timeout) + " seconds")
            else:
                output = str(self.proc.buffer)
                self.proc.expect([prompt, pexpect.EOF, pexpect.TIMEOUT], timeout)
                self.proc.send(self.newline)  # for getting prompt
                return output
            if end_if_timeout is True:
                exit(1)
            else:
                return self.TIMEOUT

        if (action is not None) and (index >= 0):
            self.proc.send(action + self.newline)

        if get_result_index is True:
            return index
        else:
            return 0

    def expect2act(self, timeout, exptxt, action, rt_buf=None):
        sys.stdout = mystdout = StringIO()
        self.proc.logfile_read = sys.stdout

        # expect last time command buffer
        index = self.proc.expect([exptxt, pexpect.EOF, pexpect.TIMEOUT], timeout)
        if(index == 1):
            self.log.error("[ERROR:EOF]: Expect \"" + exptxt + "\"")
            return -1
        if(index == 2):
            self.log.error("[ERROR:Timeout]: Expect \"" + exptxt + "\" more than " + str(timeout) + " seconds")
            return -1

        sys.stdout = sys.__stdout__
        self.log.debug(mystdout.getvalue())

        # send action
        self.proc.send(action + self.newline)

        # re-init
        sys.stdout = mystdout = StringIO()
        self.proc.logfile_read = sys.stdout

        # capture action output message, if you pass not None rt_buf
        if(rt_buf != None):
            # read action output
            index = self.proc.expect([exptxt, pexpect.EOF, pexpect.TIMEOUT], timeout)
            if(index == 1):
                self.log.error("[ERROR:EOF]: Expect \"" + exptxt + "\"")
                return -1
            if(index == 2):
                self.log.error("[ERROR:Timeout]: Expect \"" + exptxt + "\" more than " + str(timeout) + " seconds")
                return -1

            sys.stdout = sys.__stdout__
            rt_buf.insert(0, mystdout.getvalue())
            self.log.debug(rt_buf[0])

            # only senf newline for getting hint
            self.proc.send(self.newline)

        sys.stdout = sys.__stdout__
        return 0
