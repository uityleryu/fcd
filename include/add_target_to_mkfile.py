import os
import re
import sys
import locale
import json
import time
import subprocess
import glob


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


curdir = os.getcwd()
cn = UIpopen()
product_dir = os.path.join(curdir, "../config/includes.chroot/usr/local/sbin/prod_json")
libarary_dir = "/home/vjc/malon/library/fcd-image/images"


def main():
    tsx = os.path.join(product_dir, "*/*")
    products = glob.glob(tsx)
    for sp in products:
        find_not_link = False
        if ".json" in sp:
            # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_00526_e7e7.json
            fh = open(sp)
            pjson = json.load(fh)
            fh.close()

            for ss in pjson.keys():
                pdl = ss
                print("Product line: " + pdl)

            for ss in pjson[pdl].keys():
                model = ss

            mk_filename = "{}.mk".format(pdl)
            cmd = "cat {}".format(mk_filename)
            [stdo, rtc] = cn.xcmd(cmd)
            m_file = re.findall(r"pd_(.*).json", sp)
            if m_file:
                xfs = m_file[0].replace("_", "-")
                if xfs not in stdo:
                    fh = open(mk_filename, "a")
                    linetext = "$(eval $(call ProductCompress2,{0}))\n".format(xfs)
                    print("Line Text: " + linetext)
                    fh.write(linetext)
                    fh.close()


if __name__ == "__main__":
    main()
