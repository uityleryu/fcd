
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
d_list = []
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

def findfile(name, path):
    for dirPath, dirName, fileName in os.walk(path):
        print(dirPath)
        if name in fileName:
            print(dirPath + name)
            return os.path.join(dirPath, name)
    return False

def download_images():
    # Ex: case1: /home/vjc/malon/uifcd1/output/ostrich/tftp
    # Ex: case2: /home/vjc/malon/uifcd1/output/stage/NewSquashfs/srv/tftp
    if os.path.isdir(ostype_tftp_dir) is False:
        os.makedirs(ostype_tftp_dir)

    fh = open("/usr/local/sbin/Products-info.json")
    pjson = json.load(fh)
    fh.close()

    download_wget_list = []
    for im in pjson[pl].keys():
        rmsg = "**** WGET FTP files for Model: {} ****".format(im)
        print(rmsg)

        # print("board id: " + args.boardid + "pjson[pl][im][BOARDID]: " + pjson[pl][im]["BOARDID"])
        if args.boardid != pjson[pl][im]["BOARDID"] and args.boardid != "ALL":
            continue

        if "DOWNLOAD_FILE" in pjson[pl][im].keys():
            download_list = pjson[pl][im]["DOWNLOAD_FILE"]
            for item in download_list:
                if len(item["FILES"]) > 0:
                    # Ex: http://10.2.0.33:8088/images/fcd-image/am-fw
                    url_dir = os.path.join(ftp_server_url, item["SRC_PATH"])
                    # Ex: /home/vjc/malon/uifcd1/output/ostrich/tftp/am-fw
                    local_dir = os.path.join(ostype_tftp_dir, item["DST_PATH"])
                    if os.path.isdir(local_dir) is False:
                        os.makedirs(local_dir)

                    for i in item["FILES"]:
                        dst_file_path = os.path.join(local_dir,i)
                        if os.path.isfile(dst_file_path) is False:
                            # Ex: http://10.2.0.33:8088/images/fcd-image/am-fw/u-boot-art-qca955x.bin
                            src_file_path = os.path.join(url_dir, i)
                            src_file_path = src_file_path.replace("\\", "/")
                            cmd = "wget -P {} {}".format(local_dir, src_file_path)
                            if cmd not in download_wget_list:
                                download_wget_list.append(cmd)
                                print("WGET: " + cmd)
                                rtc = os.system(cmd)
                                if rtc != 0:
                                    print("WGET failed: " + cmd)
                                    exit(1)
                else:
                    # Ex: http://10.2.0.33:8088/images/fcd-image/am-fw
                    url_dir = os.path.join(ftp_server_url, item["SRC_PATH"])
                    '''
                        wget -r -np -nH -R "index.html*" http://10.2.0.33:8088/images/fcd-image/am-fw/
                        It must need a "/" after the url http://10.2.0.33:8088/images/fcd-image/am-fw, then wget could download all files
                        under the folder "am-fw", or it will copy all files under "fcd-image"
                    '''
                    # Ex: url_dir: http://10.2.0.33:8088/images/fcd-image/am-fw
                    # Ex: local_dir: /home/vjc/malon/uifcd1/output/ostrich/tftp/am-fw
                    url_dir = url_dir.replace("\\", "/")
                    src_pattern = r"images/fcd-image[/]$|images/tools[/]$"
                    match_url = re.findall(src_pattern, url_dir)
                    if match_url:
                        print("!!!!!!!!! Fatal Error, you are going to copy all images from the FTP server !!!!!!!!!!!!")
                        print("You attempt to copy http://10.2.0.33:8088/images/fcd-image/ or http://10.2.0.33:8088/images/tools/")
                        exit(1)

                    cmd = "wget -r -np -nH -R \"index.html*\" {}".format(url_dir)
                    print("copy whole folder: " + cmd)
                    if cmd not in download_wget_list:
                        download_wget_list.append(cmd)
                        print("WGET: " + cmd)
                        os.chdir(tmp_wget_dir)
                        rtc = os.system(cmd)
                        if rtc != 0:
                            print("WGET failed: " + cmd)
                            exit(1)

                        os.chdir(curdir)

                        src_path = os.path.join(tmp_wget_dir, item["SRC_PATH"])
                        dst_path = os.path.join(ostype_tftp_dir, item["DST_PATH"])
                        shutil.copytree(src_path, dst_path)
        else:
            print("Can't find the DOWNLOAD_FILE the projects")

    print(download_wget_list)

    # Ex: case1: /home/vjc/malon/uifcd1/output/ostrich/tftp/tools
    # Ex: case2: /home/vjc/malon/uifcd1/output/stage/NewSquashfs/tftp/tools
    ostype_tools_dir = os.path.join(ostype_tftp_dir, "tools")
    cmd = "chmod -R 777 {}".format(ostype_tools_dir)
    rtc = os.system(cmd)

    for im in pjson[pl].keys():
        rmsg = "**** LINK files for Model: {} {} ****".format(im,pjson[pl][im]["BOARDID"])
        print(rmsg)

        # print("board id: " + args.boardid + "pjson[pl][im][BOARDID]: " + pjson[pl][im]["BOARDID"])
        if args.boardid != pjson[pl][im]["BOARDID"] and args.boardid != "ALL":
            continue

        if "CREATE_LINK" in pjson[pl][im].keys():
            symoblic_list = pjson[pl][im]["CREATE_LINK"]
            for item in symoblic_list:
                # Ex: ../am-fw/u-boot-art-qca955x.bin
                src_path = item[1]
                # Ex: case1: /home/vjc/malon/uifcd1/output/ostrich/tftp/images/e7e7-art-uboot.bin
                # Ex: case2: /home/vjc/malon/uifcd1/output/stage/NewSquashfs/tftp/images/e7e7-art-uboot.bin
                dst_path = os.path.join(ostype_softlink_dir, item[0])
                dst_path = dst_path.replace("tftp","tftpboot")
                dst_dir = os.path.dirname(dst_path)
                if os.path.isdir(dst_dir) is False:
                    os.makedirs(dst_dir)

                if os.path.islink(dst_path) is False:
                    cmd = "ln -s {} {}".format(src_path, dst_path)
                    rtc = os.system(cmd)

    tools_all = []
    for dh in glob.glob(ostype_tools_dir + "/*"):
        tools_all.append(os.path.basename(dh))

    tg = " ".join(tools_all)
    cmd = "cd {}; tar -cvzf tools.tar {}; chmod 777 tools.tar".format(ostype_tools_dir, tg)
    print("TAR cmd: " + cmd)
    rtc = os.system(cmd)
    for i in tools_all:
        i_path = os.path.join(ostype_tools_dir, i)
        if os.path.isdir(i_path) is True:
            shutil.rmtree(i_path)

def download_bsp_images():
    if os.path.isdir(ostype_tftp_dir) is False:
        os.makedirs(ostype_tftp_dir)

    fh = open("/usr/local/sbin/pd_bsp_img_info.json")
    pjson = json.load(fh)
    fh.close()

    # if args.boardid is None and args.boardid != "ALL":
    #     print("Please provide a board id")
    #     exit(1)

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

                fcd_file_path=findfile(f, ostype_tftp_dir)

                if os.path.isfile(fcd_file_path) is True:
                    print("Find image in FCD dir: " + fcd_file_path)

                    link_dir = os.path.join(ostype_tftp_dir, "images")
                    link_file_path = os.path.join(link_dir,ln)
                    print("Link " + link_file_path)
                    if os.path.islink(link_file_path) is True:
                        os.remove(link_file_path)

                    if os.path.isdir(link_dir) is False:
                        os.makedirs(link_dir)

                    cmd = "ln -s {} {}".format(fcd_file_path, link_file_path)
                    print("LN: " + cmd)
                    rtc = os.system(cmd)
                    if cmd not in d_list:
                        d_list.append(cmd)

                else:
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
        print("Not support in pd_bsp_img_info.json, board id : " + args.boardid)
        exit(1)


def main():
    if args.boardid is None and args.boardid != "ALL":
        print("Please provide a board id")
        exit(1)

    download_images()
    download_bsp_images()



if __name__ == "__main__":
    main()
