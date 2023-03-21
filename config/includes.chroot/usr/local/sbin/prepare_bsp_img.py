
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

pjson = ""
'''
   Main Function
'''
curdir = os.getcwd()
ftp_server_url = "http://10.2.0.33:8088"

print("Current DIR: " + curdir)

parse = argparse.ArgumentParser(description="Generating product json file")
parse.add_argument('--prodline', '-pl', dest='prodline', help='Product Line', default="bsp")
parse.add_argument('--boardid', '-bid', dest='boardid', help='Board ID', default=None)
args, _ = parse.parse_known_args()

pl = args.prodline
print("Product Line: " + pl)

# ostype_dir = os.path.join(curdir, "output", "ostrich")
ostype_dir = os.path.join("/")
dst_verfile = os.path.join(ostype_dir, "version.txt")
ostype_sbin_dir = os.path.join(ostype_dir, "sbin")
ostype_tftp_dir = os.path.join(ostype_dir, "tftpboot")
ostype_softlink_dir = ostype_dir



def download_images():
    if os.path.isdir(ostype_tftp_dir) is False:
        os.makedirs(ostype_tftp_dir)

    fh = open("/usr/local/sbin/pd_bsp_img_info.json")
    pjson = json.load(fh)
    fh.close()

    if args.boardid is None and args.boardid != "ALL":
        print("Please provide a board id")
        exit(1)

    d_list = []
    for im in pjson[pl].keys():
        rmsg = "**** Model: {} ****".format(im)
        print(rmsg)

        # print("board id: " + args.boardid + "pjson[pl][im][BOARDID]: " + pjson[pl][im]["BOARDID"])
        if args.boardid != pjson[pl][im]["BOARDID"] and args.boardid != "ALL":
            continue

        if "DOWNLOAD_FILE" in pjson[pl][im].keys():
            download_list = pjson[pl][im]["DOWNLOAD_FILE"]
            # Ex: http://10.2.0.33:8088/images/fcd-image/am-fw
            url_dir = os.path.join(ftp_server_url, "images/bsp_images")
            local_dir = os.path.join(ostype_tftp_dir, "bsp_img")
            if os.path.isdir(local_dir) is False:
                os.makedirs(local_dir)


            rmsg = "**** WGET FTP files for Model: {} ****".format(im)
            print(rmsg)
            # for item in download_list:
            for ln, f in download_list.items():
                print("ln:" + ln + " file:" + f + " download_list[ln]: " + download_list[ln])
                # if len(item["FILES"]) > 0:
                dst_file_path = os.path.join(local_dir,f)
                if os.path.isfile(dst_file_path) is False:
                    print("Download " + dst_file_path)
                    # Ex: http://10.2.0.33:8088/images/bsp_images/xxx.bin
                    src_file_path = os.path.join(url_dir, f)
                    print(src_file_path)
                    src_file_path = src_file_path.replace("\\", "/")
                    cmd = "wget -P {} {}".format(local_dir, src_file_path)
                    print("WGET: " + cmd)
                    rtc = os.system(cmd)
                    if rtc != 0:
                        print("WGET failed: " + cmd)
                        exit(1)


                link_dir = os.path.join(ostype_tftp_dir, "images")
                link_file_path = os.path.join(link_dir,ln)
                print("Link " + link_file_path)
                if os.path.islink(link_file_path) is True:
                    os.remove(link_file_path)

                if os.path.isdir(link_dir) is False:
                    os.makedirs(link_dir)

                cmd = "ln -s {} {}".format(dst_file_path, link_file_path)
                print("LN: " + cmd)
                rtc = os.system(cmd)
                if cmd not in d_list:
                    d_list.append(cmd)
        else:
            print("Can't find the DOWNLOAD_FILE of the projects")

    # print("len of download list: " , len(download_wget_list))
    if len(d_list) == 0:
        print("Not support the board id: " + args.boardid)
        exit(1)



def main():
    download_images()


if __name__ == "__main__":
    main()
