
import os
import argparse
import shutil
import json
import subprocess

from uiopen import UIpopen


'''
   Main Function
'''
curdir = os.getcwd()
reg_bs_dir = os.path.join(curdir, "config/includes.chroot/usr/local/sbin")
prod_json_dir = os.path.join(reg_bs_dir, "prod_json")

cn = UIpopen()
parse = argparse.ArgumentParser(description="Generating product json file")
parse.add_argument('--prodline', '-pl', dest='prodline', help='Product Line', default=None)
parse.add_argument('--series', '-sr', dest='series', help='Series', default=None)
parse.add_argument('--pdseries', '-psr', dest='pdseries', help='Product Series', default=None)
args, _ = parse.parse_known_args()

if args.prodline is None:
    print("Please give a product line")
    exit(1)
else:
    pl = args.prodline
    print("Product line: " + pl)

if args.series is None:
    print("Please provide the models")
    exit(1)
else:
    print("Product series: " + args.series)
    product_series = args.series.split(" ")

a_series = args.pdseries


def main():
    print("Target dir: " + prod_json_dir)

    thk = {}
    thk[pl] = {}
    kidx = 0
    for pn in product_series:
        print(pn)
        # xpd = "pd_{}_{}.json".format(pn.split("-")[0], pn.split("-")[1].lower())
        xpd = "pd_{}.json".format(pn)
        target = os.path.join(prod_json_dir, pl, xpd)
        if os.path.isfile(target):
            fh = open(target)
            pjson = json.load(fh)
            fh.close()
            for pn in pjson[pl].keys():
                thk[pl][pn] = pjson[pl][pn]
                thk[pl][pn]['INDEX'] = kidx

        kidx += 1

    output = json.dumps(thk, indent=2)

    # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_AC-SERIES.json
    a_series_name = "pd_{}.json".format(a_series)
    src = os.path.join(prod_json_dir, pl, a_series_name)
    ft = open(src, 'w')
    ft.write(output)
    ft.close()
    print(output)


if __name__ == "__main__":
    main()
