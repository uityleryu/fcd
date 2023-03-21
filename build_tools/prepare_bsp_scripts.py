
import os
import re
import sys
import locale
import argparse
import shutil
import json
import time
import subprocess
import glob

from uiopen import UIpopen

'''
    Registration scripts and libraries
'''
register_libs = [
    "data",
    "soc_lib",
    "script_base.py",
    "Products-info.json",
    "rpi-config.py",
    "blacklist",
    "prepare_bsp_img.py",
    "prod_json/bsp/pd_bsp_img_info.json",
    "back2art"
]

pjson = ""
fcdname = ""
series_type = False
'''
   Main Function
'''
curdir = os.getcwd()
tmp_wget_dir = os.path.join(curdir, "output", "tmp_wget")
reg_bs_dir = os.path.join(curdir, "config", "includes.chroot", "usr", "local", "sbin")
prod_json_dir = os.path.join(reg_bs_dir, "prod_json")
ftp_server_url = "http://10.2.0.33:8088"
devreg_server_url = "https://ec2-18-166-47-160.ap-east-1.compute.amazonaws.com:20000/api/v1/product_mapping"

print("Current DIR: " + curdir)
print("Temp wget DIR: " + tmp_wget_dir)
print("register base DIR: " + reg_bs_dir)
print("prod json DIR: " + prod_json_dir)

cn = UIpopen()
parse = argparse.ArgumentParser(description="Generating product json file")
parse.add_argument('--prodline', '-pl', dest='prodline', help='Product Line', default=None)
parse.add_argument('--prodname', '-pn', dest='prodname', help='Product Name', default=None)
parse.add_argument('--fcdver', '-v', dest='fcdver', help='FCD version', default=None)
parse.add_argument('--fwver', '-j', dest='fwver', help='FW version', default=None)
parse.add_argument('--type', '-tp', dest='type', help='Build Type', default=None)
parse.add_argument('--nicken', '-nc', dest='nickname_en', help='Nickname enabled', default=None)
parse.add_argument('--ostype', '-os', dest='ostype', help='OS type', default=None)
args, _ = parse.parse_known_args()

if args.prodline is None:
    print("Please give a product line")
    exit(1)
else:
    pl = args.prodline
    print("Product Line: " + pl)

if args.prodname is None:
    print("Please provide a product name")
    exit(1)
else:
    pn = args.prodname
    print("Product Name: " + pn)

if args.nickname_en == "y":
    nickname_en = True
    print("Nick enable: true")
else:
    nickname_en = False
    print("Nick enable: false")

if args.ostype == "ISO":
    ostype_dir = os.path.join(curdir, "output", "stage", "NewSquashfs")
    dst_verfile = os.path.join(ostype_dir, "etc", "skel", "Desktop", "version.txt")
    ostype_sbin_dir = os.path.join(ostype_dir, "usr", "local", "sbin")
    ostype_tftp_dir = os.path.join(ostype_dir, "srv", "tftp")
    ostype_softlink_dir = os.path.join(ostype_dir, "srv")
elif args.ostype == "RPI":
    ostype_dir = os.path.join(curdir, "output", "ostrich")
    dst_verfile = os.path.join(ostype_dir, "version.txt")
    ostype_sbin_dir = os.path.join(ostype_dir, "sbin")
    ostype_tftp_dir = os.path.join(ostype_dir, "tftp")
    ostype_softlink_dir = ostype_dir
else:
    ostype_dir = os.path.join(curdir, "output", "ostrich")
    dst_verfile = os.path.join(ostype_dir, "version.txt")
    ostype_sbin_dir = os.path.join(ostype_dir, "sbin")
    ostype_tftp_dir = os.path.join(ostype_dir, "tftp")
    ostype_softlink_dir = ostype_dir

print("Build the FCD to run in {}".format(args.ostype))




def gen_prod_json():
    global pn
    global fcdname
    global pjson

    m_type = re.findall(r'[0-9]{5}_[0-9a-f]{4}', pn)
    if m_type:
        build_type = "single"
    else:
        build_type = "series"

    thk = {}
    thk[pl] = {}
    kidx = 0
    if build_type == "series":
        fh = open("build_tools/product_series_category.json")
        pjson = json.load(fh)
        fh.close()

        if pn not in pjson.keys():
            print("Can't find the product series in product_series_category.json")
            exit(1)

        if pjson[pn][0] == "all":
            # Ex: /home/vjc/malon/uifcd5/config/includes.chroot/usr/local/sbin/prod_json/airMAX
            pattern = "{}/{}/*".format(prod_json_dir, pl)
            tg_list = glob.glob(pattern)
        else:
            tg_list = []
            for ix in pjson[pn]:
                # Ex: /home/vjc/malon/uifcd5/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_00552_e7fa.json
                tg_list.append("{}/{}/pd_{}.json".format(prod_json_dir, pl, ix))

        for iy in tg_list:
            print(iy)
            if os.path.isfile(iy):
                fh = open(iy)
                pjson = json.load(fh)
                fh.close()
                for tmp_pl in pjson.keys():
                    print(tmp_pl)
                    for iz in pjson[tmp_pl].keys():
                        thk[pl][iz] = pjson[tmp_pl][iz]
                        thk[pl][iz]['INDEX'] = kidx
                        kidx += 1


        output = json.dumps(thk, indent=2)

        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_AC-SERIES.json
        a_series_name = "pd_{}.json".format(pn)
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

        # Ex: FCD_AIRMAX_AC-SERIES_1.77.15_8.7.4
        fcdname = "FCD_{}_{}_{}".format(pn, args.fcdver, args.fwver)
    elif build_type == "single":
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_00526_e7e7.json
        src = "{}/{}/pd_{}.json".format(prod_json_dir, pl, pn)
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

            for i in pjson[pl].keys():
                if pjson[pl][i]['BOARDID'] == pn.split("_")[1]:
                    product_name = pjson[pl][i]['NAME']
                    break
            else:
                print("Can't find the model in Products-info.json")
                exit(1)

            if nickname_en is True:
                '''
                    This WebAPI is from Mike's security server
                '''
                cmd = "curl -s -k -H \"x-api-key: eiWee8ep9due4deeshoa8Peichai8Eih\" -X GET {}/0777{}".format(devreg_server_url, pn.split("_")[1])
                print("cmd: " + cmd)
                [devreg_pd, rtc] = cn.xcmd(cmd)

                # Ex: FCD_e7f9_1.77.15_8.7.4_LBE-5AC-Gen2
                fcdname = "FCD_{}_{}_{}_{}".format(pn.split("_")[1], args.fcdver, args.fwver, devreg_pd.replace("\"", ""))
            else:
                # Ex: FCD_e7f9_1.77.15_8.7.4
                fcdname = "FCD_{}_{}_{}".format(pn.split("_")[1], args.fcdver, args.fwver)
        else:
            rmsg = "Can't find model: {}".format(pn)
            print(rmsg)
            exit(1)

    '''
        Create version.txt as the FCD version name
    '''
    print(fcdname)
    # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/version.txt
    verfile = os.path.join(prod_json_dir, "version.txt")
    fh = open(verfile, 'w')
    fh.write(fcdname)
    fh.close()

    '''
        Copy version.txt to target folder
    '''
    # Ex: case1: /home/vjc/malon/uifcd1/output/ostrich/version.txt
    # Ex: case2: /home/vjc/malon/uifcd1/output/stage/NewSquashfs/version.txt
    print("verfile: " + verfile)
    print("dst_verfile: " + dst_verfile)
    shutil.copyfile(verfile, dst_verfile)



def copy_required_files():
    sclient_f = ""
    for im in pjson[pl].keys():
        rmsg = "**** Model: {} ****".format(im)
        print(rmsg)
        if "CLIENT_FILE" not in pjson[pl][im].keys():
            '''
                The default client binary to RPi4 or FCD ISO
            '''
            if args.ostype == "ISO":
                sclient_f = "client_x86_release"
            else:
                sclient_f = "client_rpi4_release"
        else:
            sclient_f = pjson[pl][im]['CLIENT_FILE']

        print("Will use {}".format(sclient_f))
        if sclient_f not in register_libs:
            register_libs.append(sclient_f)

        # if "FILE" in pjson[pl][im].keys():
        #     poq = pjson[pl][im]['FILE']
        #     if poq not in register_libs:
        #         register_libs.append(poq)

        if "T1FILE" in pjson[pl][im].keys():
            poq = pjson[pl][im]['T1FILE']
            if poq not in register_libs:
                register_libs.append(poq)

    # Ex: case1: /home/vjc/malon/uifcd1/output/ostrich/sbin
    # Ex: case2: /home/vjc/malon/uifcd1/output/stage/NewSquashfs/usr/local/sbin
    if os.path.isdir(ostype_sbin_dir) is False:
        os.makedirs(ostype_sbin_dir)

    for ct in register_libs:
        if ct == "":
            continue

        src = os.path.join(reg_bs_dir, ct)
        cmd = "cp -rfL {} {}".format(src, ostype_sbin_dir)
        print("cmd: " + cmd)
        cn.xcmd(cmd)

    if sclient_f != "client_x86_release" or sclient_f != "client_rpi4_release":
        if args.ostype == "ISO":
            cmd = "cd {}; ln -s {} client_x86_release".format(ostype_sbin_dir, sclient_f)
        else:
            cmd = "cd {}; ln -s {} client_rpi4_release".format(ostype_sbin_dir, sclient_f)

        print("cmd: " + cmd)
        cn.xcmd(cmd)


def create_fcd_tgz():
    output_dir = os.path.join(curdir, "output")
    cmd = "cd {}; tar -cvzf {}.tgz ostrich".format(output_dir, fcdname)
    print("cmd: " + cmd)
    cn.xcmd(cmd)


def main():
    gen_prod_json()
    copy_required_files()

    if args.ostype == "RPI":
        create_fcd_tgz()


if __name__ == "__main__":
    main()
