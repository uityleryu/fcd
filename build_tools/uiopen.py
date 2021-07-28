
import subprocess
import locale
import time
import sys


class UIpopen(object):
    def __init__(self):
        pass

    """
        If timeout is None, the process will non-stop when the command keeps running.
        So, give a default 10 seconds to timeout
    """
    def xcmd(self, cmd, timeout=None, rtmsg=True, retry=3):
        for i in range(0, retry+1):
            try:
                if sys.platform.startswith('win32'):
                    proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                else:
                    proc = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

                """
                    Python offical website statements:
                    deadlock when using stdout=PIPE and/or stderr=PIPE and the child process generates enough output to
                    a pipe such that it blocks waiting for the OS pipe buffer to accept more data.
                    Use communicate() to avoid that.
                """
                locd = locale.getdefaultlocale()

                if timeout is not None:
                    buf = proc.communicate(timeout=timeout)[0].decode(locd[1]).strip()
                else:
                    buf = proc.communicate()[0].decode(locd[1]).strip()

                print("coding format: " + locd[1])
                print(buf)
            except Exception as e:
                if i < retry:
                    print("xcmd Retry {}".format(i+1))
                    time.sleep(0.2)
                    continue
                else:
                    print("Exceeded maximum retry times {}".format(i))
                    raise e
            else:
                break

        if rtmsg is True:
            return [buf, proc.returncode]
        else:
            if proc.returncode != 0:
                return False
            else:
                return True
