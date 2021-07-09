import os
import re
import sys
import locale
import json
import time
import subprocess
import glob

from uiopen import UIpopen

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
