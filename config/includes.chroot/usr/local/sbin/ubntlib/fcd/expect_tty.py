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
        if(logger_name is None):
            self.log = logging.getLogger()
            self.log.setLevel(logging.DEBUG)
            log_stream = logging.StreamHandler(sys.stdout)
            log_stream.setLevel(logging.DEBUG)
            self.log.addHandler(log_stream)
        # Using customized logger shows message
        else:
            self.log = logging.getLogger(logger_name)

    def expect_only(self, timeout, exptxt, err_msg=None):
        """Simply expect.
            Will raise ExceptionPexpect if expect timeout
            exit if expect come accross EOF
        """
        return self.__expect_base(timeout=timeout, exptxt=exptxt, err_msg=err_msg)

    def expect_action(self, timeout, exptxt, action, err_msg=None):
        """Expect and send action cmd.
            Will raise ExceptionPexpect if expect timeout
            exit if expect come accross EOF
        """
        return self.__expect_base(timeout=timeout, exptxt=exptxt, action=action, err_msg=err_msg)

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

    def __expect_base(self, timeout, exptxt, action=None, err_msg=None, end_if_timeout=True, get_result_index=False,
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
            return output if get_output is True
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
        detail = str(err_msg) if err_msg is not None else ""
        if(index == (len(ex) - 2)):
            print("[ERROR:EOF]: Expect \"" + str(exptxt) + "\"")
            raise pexpect.ExceptionPexpect(detail)
        if(index == (len(ex) - 1)):
            if get_output is True:
                output = str(self.proc.buffer)
                self.proc.expect([prompt, pexpect.EOF, pexpect.TIMEOUT], timeout)
                self.proc.send(self.newline)  # for getting prompt
                return output  # return all output including sended command
            if end_if_timeout is True:
                print("[ERROR:Timeout]: Expect \"" + str(exptxt) + "\" more than " + str(timeout) + " seconds. " + detail)
                raise pexpect.ExceptionPexpect(detail)
            else:
                return self.TIMEOUT

        if (action is not None) and (index >= 0):
            self.proc.send(action + self.newline)

        if get_result_index is True:
            return index
        else:
            return 0
