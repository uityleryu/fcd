
import json
import os
import glob
import sys
import shutil

# Ex: /home/vjc/malon/uifcd5/build_tools
curdir = os.getcwd()

# Ex: /home/vjc/malon/uifcd5/build_tools/../config/includes.chroot/usr/local/sbin
reg_bs_dir = os.path.join(curdir, "../config/includes.chroot/usr/local/sbin")

# Ex: /home/vjc/malon/uifcd5/build_tools/../config/includes.chroot/usr/local/sbin/prod_json
prod_json_dir = os.path.join(reg_bs_dir, "prod_json")

def main():
    filename = os.path.join(reg_bs_dir, "Products-info.json")
    fh = open(filename)
    org_prod_json = json.load(fh)
    fh.close()

    for i in org_prod_json.keys():
        pfn = os.path.join(prod_json_dir, i)
        if not os.path.isdir(pfn):
            os.mkdir(pfn)

    newpd = {}
    for pl in org_prod_json.keys():
        newpd[pl] = {}
        for pn in org_prod_json[pl].keys():
            newpd[pl][pn] = {}
            newpd[pl][pn] = org_prod_json[pl][pn]
            newpd[pl][pn]["INDEX"] = 0
            bomrev = newpd[pl][pn]["BOMREV"].split("-")[1]
            sysid = newpd[pl][pn]["BOARDID"]
            output = json.dumps(newpd, indent=2)
            n_pdname = "pd_{}_{}.json".format(bomrev, sysid)
            ft = open(n_pdname, 'w')
            ft.write(output)
            ft.close()
            src = os.path.join(curdir, n_pdname)
            dst = os.path.join(prod_json_dir, pl, n_pdname)
            shutil.move(src, dst)
            newpd[pl] = {}

        newpd = {}


if __name__ == "__main__":
    main()
