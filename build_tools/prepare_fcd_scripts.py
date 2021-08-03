
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
    "blacklist"
]

# Ex: this is common tools for every project
common_tools = [
    "common",
    "common/sshd_config",
    "common/tmux.conf",
    "common/x86-64k-ee",
    "common/aarch64-rpi4-64k-ee"
]

pjson = ""
fcdname = ""
series_type = False
'''
   Main Function
'''
curdir = os.getcwd()
ostrich_bs_dir = os.path.join(curdir, "output/ostrich")
reg_bs_dir = os.path.join(curdir, "config/includes.chroot/usr/local/sbin")
prod_json_dir = os.path.join(reg_bs_dir, "prod_json")
ftp_server_url = "http://10.2.0.33:8088"
devreg_server_url = "https://10.2.2.174:20000/api/v1/product_mapping"

print("Current DIR: " + curdir)
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
else:
    nickname_en = False


def download_images():
    # Ex: /home/vjc/malon/uifcd1/output/ostrich/tftp
    ostrich_tftp_dir = os.path.join(ostrich_bs_dir, "tftp")
    if os.path.isdir(ostrich_tftp_dir) is False:
        os.makedirs(ostrich_tftp_dir)

    download_wget_list = []
    for im in pjson[pl].keys():
        rmsg = "**** WGET FTP files for Model: {} ****".format(im)
        print(rmsg)

        if "DOWNLOAD_FILE" in pjson[pl][im].keys():
            download_list = pjson[pl][im]["DOWNLOAD_FILE"]
            for item in download_list:
                # Ex: http://10.2.0.33:8088/images/fcd-image/am-fw
                url_dir = os.path.join(ftp_server_url, item["SRC_PATH"])
                # Ex: /home/vjc/malon/uifcd1/output/ostrich/tftp/am-fw
                local_dir = os.path.join(ostrich_tftp_dir, item["DST_PATH"])
                if os.path.isdir(local_dir) is False:
                    os.makedirs(local_dir)

                if len(item["FILES"]) > 0:
                    for i in item["FILES"]:
                        # Ex: http://10.2.0.33:8088/images/fcd-image/am-fw/u-boot-art-qca955x.bin
                        src_file_path = os.path.join(url_dir, i)
                        src_file_path = src_file_path.replace("\\", "/")
                        cmd = "wget -P {} {}".format(local_dir, src_file_path)
                        if cmd not in download_wget_list:
                            download_wget_list.append(cmd)
                else:
                    # Ex: url_dir: http://10.2.0.33:8088/images/fcd-image/am-fw
                    # Ex: local_dir: /home/vjc/malon/uifcd1/output/ostrich/tftp/am-fw
                    '''
                        wget -P /home/vjc/malon/uifcd1/output/ostrich/tftp/am-fw -r -np -nd http://10.2.0.33:8088/images/fcd-image/am-fw/
                        It must need a "/" after the url http://10.2.0.33:8088/images/fcd-image/am-fw, then wget could download all files
                        under the folder "am-fw", or it will copy all files under "fcd-image"
                    '''
                    url_dir = url_dir.replace("\\", "/")
                    src_pattern = r"images/fcd-image[/]$|images/tools[/]$"
                    match_url = re.findall(src_pattern, url_dir)
                    if match_url:
                        print("!!!!!!!!! Fatal Error, you are going to copy all images from the FTP server !!!!!!!!!!!!")
                        print("You attempt to copy http://10.2.0.33:8088/images/fcd-image/ or http://10.2.0.33:8088/images/tools/")
                        exit(1)

                    cmd = "wget -P {} -r -np -nd {}".format(local_dir, url_dir)
                    print("copy whole folder: " + cmd)
                    if cmd not in download_wget_list:
                        download_wget_list.append(cmd)
        else:
            print("Can't find the DOWNLOAD_FILE the projects")

    print(download_wget_list)
    for wgetcmd in download_wget_list:
        print("WGET: " + wgetcmd)
        rtc = os.system(wgetcmd)
        if rtc != 0:
            print("WGET failed filename: " + wgetcmd)
            exit(1)

    ostrich_tools_dir = os.path.join(ostrich_bs_dir, "tftp", "tools")
    cmd = "chmod -R 777 {}".format(ostrich_tools_dir)
    cn.xcmd(cmd)

    for im in pjson[pl].keys():
        if "CREATE_LINK" in pjson[pl][im].keys():
            symoblic_list = pjson[pl][im]["CREATE_LINK"]
            for item in symoblic_list:
                # Ex: ../am-fw/u-boot-art-qca955x.bin
                src_path = item[1]
                # Ex: /home/vjc/malon/uifcd1/output/ostrich/tftp/images/e7e7-art-uboot.bin
                dst_path = os.path.join(ostrich_bs_dir, item[0])
                dst_dir = os.path.dirname(dst_path)
                if os.path.isdir(dst_dir) is False:
                    os.makedirs(dst_dir)

                if os.path.islink(dst_path) is False:
                    cmd = "ln -s {} {}".format(src_path, dst_path)
                    cn.xcmd(cmd)

    tools_dir = os.path.join(ostrich_tftp_dir, "tools")
    tools_all = []
    for dh in glob.glob(tools_dir + "/*"):
        tools_all.append(os.path.basename(dh))

    tg = " ".join(tools_all)
    cmd = "cd {}; tar -cvzf tools.tar {}; chmod 777 tools.tar".format(tools_dir, tg)
    print("TAR cmd: " + cmd)
    cn.xcmd(cmd)
    for i in tools_all:
        i_path = os.path.join(tools_dir, i)
        if os.path.isdir(i_path) is True:
            shutil.rmtree(i_path)


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
            print("Can't find the product series in product_series_glossory.json")
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
                for iz in pjson[pl].keys():
                    thk[pl][iz] = pjson[pl][iz]
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
    # Ex: /home/vjc/malon/uifcd1/output/ostrich/version.txt
    dst_verfile = os.path.join(ostrich_bs_dir, "version.txt")
    shutil.copyfile(verfile, dst_verfile)


def fcd_name_check():
        '''
            Good example:
            FCD_e7f9_1.77.15_8.7.4
        '''
        print("FCD filename: " + fcdname)

        naming_rule_re = re.compile(
            r'^FCD_(?P<systemid>[a-f0-9]{4}|.*\_.*\-.*)\_'
            r'(?P<FCD_major>0|[1-9]\d*)\.(?P<FCD_minor>0|[1-9]\d*)\.(?P<FCD_patch>0|[1-9]\d*)(?:-'
            r'(?P<FCD_prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+'
            r'(?P<FCD_buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\_'
            r'(?P<FW_major>0|[1-9]\d*)\.(?P<FW_minor>0|[1-9]\d*)\.(?P<FW_patch>0|[1-9]\d*)(?:-'
            r'(?P<FW_prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+'
            r'(?P<FW_buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?'
        )

        result = naming_rule_re.findall(fcdname)

        if len(result) < 1 or len(result[0]) < 11:
            print("======================================")
            print("  Version format is invalid !!! ")
            print("======================================")
            exit(1)

        print("======================================")
        print("  Product System ID: {}".format(result[0][0]))

        if result[0][4] == '':
            fcdmsg = "  FCD version: {}.{}.{}".format(result[0][1], result[0][2], result[0][3])
        else:
            fcdmsg = "  FCD version: {}.{}.{}-{}".format(result[0][1], result[0][2], result[0][3], result[0][4])

        print(fcdmsg)

        if result[0][9] == '':
            fwmsg = "  FW version: {}.{}.{}".format(result[0][6], result[0][7], result[0][8])
        else:
            fwmsg = "  FW version: {}.{}.{}-{}".format(result[0][6], result[0][7], result[0][8], result[0][9])

        print(fwmsg)
        print("======================================")


def copy_required_files():
    sclient_f = ""
    for im in pjson[pl].keys():
        rmsg = "**** Model: {} ****".format(im)
        print(rmsg)
        if "CLIENT_FILE" not in pjson[pl][im].keys():
            sclient_f = "client_rpi4_release"
        else:
            sclient_f = pjson[pl][im]['CLIENT_FILE']

        print("Will use {}".format(sclient_f))
        if sclient_f not in register_libs:
            register_libs.append(sclient_f)

        if "FILE" in pjson[pl][im].keys():
            poq = pjson[pl][im]['FILE']
            if poq not in register_libs:
                register_libs.append(poq)

        if "T1FILE" in pjson[pl][im].keys():
            poq = pjson[pl][im]['T1FILE']
            if poq not in register_libs:
                register_libs.append(poq)

    # Ex: /home/vjc/malon/uifcd1/output/ostrich/bin
    ostrich_bin_dir = os.path.join(ostrich_bs_dir, "sbin")
    if os.path.isdir(ostrich_bin_dir) is False:
        os.makedirs(ostrich_bin_dir)

    for ct in register_libs:
        if ct == "":
            continue

        src = os.path.join(reg_bs_dir, ct)
        cmd = "cp -rfL {} {}".format(src, ostrich_bin_dir)
        print("cmd: " + cmd)
        cn.xcmd(cmd)

    cmd = "cd {}; ln -s {} client_rpi4".format(ostrich_bin_dir, sclient_f)
    print("cmd: " + cmd)
    cn.xcmd(cmd)


def create_fcd_tgz():
    output_dir = os.path.join(curdir, "output")
    cmd = "cd {}; tar -cvzf {}.tgz ostrich".format(output_dir, fcdname)
    print("cmd: " + cmd)
    cn.xcmd(cmd)


def main():
    gen_prod_json()
    fcd_name_check()
    download_images()
    copy_required_files()
    create_fcd_tgz()


if __name__ == "__main__":
    main()
