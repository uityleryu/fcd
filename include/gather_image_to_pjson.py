
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

            for ss in pjson[pdl].keys():
                model = ss

            sysid = pjson[pdl][model]["BOARDID"]
            lscmd = "ls -la {}/{}*".format(libarary_dir, sysid)
            # lscmd = "ls -la {}/ee74*".format(libarary_dir)
            cmd = lscmd + " | awk '{print $9\" \"$11}'"
            [stdo, rtc] = cn.xcmd(cmd)
            match = re.findall("cannot access", stdo)
            if match:
                print("can't find the system ID: {}".format(sysid))
                continue
            else:
                miy = stdo.split("\n")
                for i in miy:
                    if os.path.islink(i.split(" ")[0]) is False:
                        find_not_link = True
                        break

                if find_not_link is True:
                    continue

                symoblic_dir = "tftp/images"
                xdir = os.path.dirname(miy[0].split(" ")[1][3:])
                afd = {}
                src_xdi = os.path.join("images", "fcd-image", xdir)
                afd["SRC_PATH"] = src_xdi
                afd["DST_PATH"] = xdir
                afd["FILES"] = []
                pou = {
                    "SRC_PATH": "images/tools/common",
                    "DST_PATH": "tools/common",
                    "FILES": [
                        "sshd_config",
                        "tmux.conf",
                        "x86-64k-ee",
                        "aarch64-rpi4-64k-ee"
                    ]
                }
                uty = {
                    "SRC_PATH": "images/tools/",
                    "DST_PATH": "tools/",
                    "FILES": []
                }
                pjson[pdl][model]["CREATE_LINK"] = []
                for i in miy:
                    yikn = []
                    fw_image = os.path.basename(i.split(" ")[1])
                    afd["FILES"].append(fw_image)
                    symoblic_path = os.path.join(symoblic_dir, os.path.basename(i.split(" ")[0]))
                    yikn.append(symoblic_path)
                    yikn.append(i.split(" ")[1])
                    if "CREATE_LINK" in pjson[pdl][model].keys():
                        pjson[pdl][model]["CREATE_LINK"].append(yikn)

                if "DOWNLOAD_FILE" in pjson[pdl][model].keys():
                    pjson[pdl][model]["DOWNLOAD_FILE"] = []
                    pjson[pdl][model]["DOWNLOAD_FILE"].append(afd)
                    pjson[pdl][model]["DOWNLOAD_FILE"].append(uty)
                    pjson[pdl][model]["DOWNLOAD_FILE"].append(pou)

                output = json.dumps(pjson, indent=2)
                ft = open(sp, 'w')
                ft.write(output)
                ft.close()

        # exit(1)


if __name__ == "__main__":
    main()
