
import os
import re
import sys
import locale
import argparse
import shutil
import json
import time
import subprocess


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
args, _ = parse.parse_known_args()

if args.type is None:
    print("Please give a Build Type")
    exit(1)
else:
    build_type = args.type
    print("Build Type: " + build_type)

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


def gen_prod_json():
    global pjson
    global fcdname
    global series_type

    '''
        Copy specific product json file to Product-info.json
    '''
    if build_type == "buildsingle":
        tg = "pd_{}_{}.json".format(pn.split("-")[0], pn.split("-")[1])
    else:
        tg = "pd_{}.json".format(pn)

    cmd = "find -L {} -name {}".format(prod_json_dir, tg)
    print(cmd)
    [tg_path, rtc] = cn.xcmd(cmd)
    match = re.findall(tg, tg_path)
    if match:
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_00526_e7e7.json
        src = tg_path
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/Products-info.json
        dst = os.path.join(reg_bs_dir, "Products-info.json")
        print("src: " + src)
        print("dst: " + dst)
        shutil.copyfile(src, dst)
    else:
        rmsg = "Can't find model: {}".format(pn)
        print(rmsg)
        exit(1)

    if build_type == "buildsingle":
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/Products-info.json
        tgfile = os.path.join(reg_bs_dir, "Products-info.json")
        fh = open(tgfile)
        pjson = json.load(fh)
        fh.close()

        for i in pjson[pl].keys():
            if pjson[pl][i]['BOARDID'] == pn.split("-")[1]:
                product_name = pjson[pl][i]['NAME']
                break
        else:
            print("Can't find the model in Products-info.json")
            exit(1)

        '''
            Create version.txt as the FCD version name
        '''
        fcdname = "FCD_{0}_{1}_{2}_{3}".format(pl, product_name, args.fcdver, args.fwver)
        print(fcdname)
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/version.txt
        verfile = os.path.join(prod_json_dir, "version.txt")
        fh = open(verfile, 'w')
        fh.write(fcdname)
        fh.close()
    else:
        # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/Products-info.json
        tgfile = os.path.join(reg_bs_dir, "Products-info.json")
        fh = open(tgfile)
        pjson = json.load(fh)
        fh.close()

        '''
            Create version.txt as the FCD version name
        '''
        fcdname = "FCD_{0}_{1}_{2}_{3}".format(pl, pn, args.fcdver, args.fwver)
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
            FCD_US_US-24-PRO_3.2.5_5.0.55-rc2
        '''
        print("FCD filename: " + fcdname)

        naming_rule_re = re.compile(
            r'^FCD_([A-Za-z0-9\-]+)\_([A-Za-z0-9\-]+)\_'
            r'(?P<FCD_major>0|[1-9]\d*)\.(?P<FCD_minor>0|[1-9]\d*)\.(?P<FCD_patch>0|[1-9]\d*)(?:-'
            r'(?P<FCD_prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+'
            r'(?P<FCD_buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\_'
            r'(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-'
            r'(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+'
            r'(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?')

        result = naming_rule_re.findall(fcdname)

        if len(result) < 1 or len(result[0]) < 11:
            print("======================================")
            print("  Version format is invalid !!! ")
            print("======================================")
            exit(1)

        print("======================================")
        print("  Product Line: {}".format(result[0][0]))
        print("  Model name: {}".format(result[0][1]))

        if result[0][5] == '':
            fcdmsg = "  FCD version: {}.{}.{}".format(result[0][2], result[0][3], result[0][4])
        else:
            fcdmsg = "  FCD version: {}.{}.{}-{}".format(result[0][2], result[0][3], result[0][4], result[0][5])

        print(fcdmsg)

        if result[0][10] == '':
            fwmsg = "  FW version: {}.{}.{}".format(result[0][7], result[0][8], result[0][9])
        else:
            fwmsg = "  FW version: {}.{}.{}-{}".format(result[0][7], result[0][8], result[0][9], result[0][10])

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
    copy_required_files()
    create_fcd_tgz()


if __name__ == "__main__":
    main()
