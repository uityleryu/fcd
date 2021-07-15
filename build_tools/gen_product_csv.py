

import json
import csv
import glob
import os
import time

curdir = os.getcwd()
product_dir = os.path.join(curdir, "../config/includes.chroot/usr/local/sbin/prod_json")


def main():
    header_created = False
    t = time.time()
    time_mon_day = time.strftime("%Y-%m-%d", time.localtime(t))
    filename = "product_info_{}.csv".format(time_mon_day)
    csv_file = open(filename, 'w')
    csv_writer = csv.writer(csv_file)
    epm = {}
    pjson = {}
    tsx = os.path.join(product_dir, "*/*")
    products = glob.glob(tsx)
    for sp in products:
        if ".json" in sp:
            # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_00526_e7e7.json
            fh = open(sp)
            pjson = json.load(fh)
            fh.close()

            for ss in pjson.keys():
                pdl = ss

            for ss in pjson[pdl].keys():
                model = ss

            epm["PRODUCT_LINE"] = pdl
            for itm in pjson[pdl][model].keys():
                if itm == "DOWNLOAD_FILE":
                    continue

                if itm == "CREATE_LINK":
                    continue

                epm[itm] = pjson[pdl][model][itm]

            if header_created is False:
                header_created = True
                header = epm.keys()
                csv_writer.writerow(header)

            csv_writer.writerow(epm.values())

        epm = {}
        pjson = {}

    csv_file.close()


if __name__ == "__main__":
   main()
