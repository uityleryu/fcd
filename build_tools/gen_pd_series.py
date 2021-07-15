
import os
import argparse
import shutil
import json
import subprocess

from uiopen import UIpopen


'''
   Main Function
'''
# Ex: /home/vjc/malon/uifcd5/build_tools
curdir = os.getcwd()

# Ex: /home/vjc/malon/uifcd5/build_tools/../config/includes.chroot/usr/local/sbin
reg_bs_dir = os.path.join(curdir, "../config/includes.chroot/usr/local/sbin")

# Ex: /home/vjc/malon/uifcd5/build_tools/../config/includes.chroot/usr/local/sbin/prod_json
prod_json_dir = os.path.join(reg_bs_dir, "prod_json")

cn = UIpopen()
'''
    Usage:
        under ~/uifcd4/build_tools
        python3 gen_pd_series.py -pl=airMAX -bt=series -psr=AIRMAX-AC-SERIES
'''
parse = argparse.ArgumentParser(description="Generating product json file")
parse.add_argument('--prodline', '-pl', dest='prodline', help='Product Line', default=None)
parse.add_argument('--buildtype', '-bt', dest='build_type', help='Build type', default=None)
parse.add_argument('--pdseries', '-psr', dest='pdseries', help='Product Series', default=None)
args, _ = parse.parse_known_args()

if args.prodline is None:
    print("Please give a product line")
    exit(1)
else:
    pl = args.prodline
    print("Product line: " + pl)

if args.build_type is None:
    print("Please provide the build type")
    exit(1)
else:
    print("Build type: " + args.build_type)
    build_type = args.build_type

if args.pdseries is None:
    print("Please provide the product name or product series")
    exit(1)
else:
    print("Product name/series: " + args.pdseries)
    pdseries = args.pdseries


def main():
    global pdseries

    print("Target dir: " + prod_json_dir)

    thk = {}
    thk[pl] = {}
    kidx = 0
    if build_type == "series":
        fh = open("product_series_category.json")
        pjson = json.load(fh)
        fh.close()

        if pdseries not in pjson.keys():
            print("Can't find the product series in product_series_glossory.json")
            exit(1)

        if pjson[pdseries][0] == "all":
            # Ex: /home/vjc/malon/uifcd5/config/includes.chroot/usr/local/sbin/prod_json/airMAX
            pattern = "{}/{}/*".format(prod_json_dir, pl)
            tg_list = glob.glob(pattern)
        else:
            tg_list = []
            for ix in pjson[pdseries]:
                # Ex: /home/vjc/malon/uifcd5/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_00552_e7fa.json
                tg_list.append("{}/{}/pd_{}.json".format(prod_json_dir, pl, ix))

        for iy in tg_list:
            print(iy)
            if os.path.isfile(iy):
                fh = open(iy)
                pjson = json.load(fh)
                fh.close()
                for iz in pjson[pl].keys():
                    thk[pl][iz] = pjson[pl][iz]
                    thk[pl][iz]['INDEX'] = kidx

            kidx += 1

        output = json.dumps(thk, indent=2)

        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_AIRMAX-AC-SERIES.json
        a_series_name = "pd_{}.json".format(pdseries)
        src = os.path.join(prod_json_dir, pl, a_series_name)
        ft = open(src, 'w')
        ft.write(output)
        ft.close()
        print(output)

        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/Products-info.json
        dst = os.path.join(reg_bs_dir, "Products-info.json")
        if os.path.isfile(src):
            print("src: " + src)
            print("dst: " + dst)
            shutil.copyfile(src, dst)

            # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/Products-info.json
            tgfile = os.path.join(reg_bs_dir, "Products-info.json")
            fh = open(tgfile)
            pjson = json.load(fh)
            fh.close()
    elif build_type == "single":
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_00526_e7e7.json
        src = "{}/{}/pd_{}.json".format(prod_json_dir, pl, pdseries)
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/Products-info.json
        dst = os.path.join(reg_bs_dir, "Products-info.json")
        if os.path.isfile(src):
            print("src: " + src)
            print("dst: " + dst)
            shutil.copyfile(src, dst)


if __name__ == "__main__":
    main()
