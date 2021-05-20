
import json
import csv
import glob
import os

curdir = os.getcwd()
product_dir = os.path.join(curdir, "../config/includes.chroot/usr/local/sbin/prod_json")


def main():
    defined_key_order = [
        "INDEX",
        "NAME",
        "BOARDID",
        "BOMREV",
        "DESC",
        "FILE",
        "T1FILE",
        "QRCHECK",
        "SW_ID",
        "DOWNLOAD_FILE",
        "CREATE_LINK"
    ]
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
                epm[pdl] = {}

            for ss in pjson[pdl].keys():
                model = ss
                epm[pdl][model] = {}

            for itm in defined_key_order:
                print("itm 1: " + itm)
                if itm in pjson[pdl][model].keys():
                    epm[pdl][model][itm] = pjson[pdl][model][itm]
                else:
                    if itm == "INDEX":
                        epm[pdl][model][itm] = "0"
                    elif itm == "DOWNLOAD_FILE" or itm == "CREATE_LINK":
                        epm[pdl][model][itm] = []
                    else:
                        epm[pdl][model][itm] = {}

            output = json.dumps(epm, indent=2)
            ft = open(sp, 'w')
            ft.write(output)
            ft.close()
            # print(output)

            epm = {}
            pjson = {}


if __name__ == "__main__":
   main()
