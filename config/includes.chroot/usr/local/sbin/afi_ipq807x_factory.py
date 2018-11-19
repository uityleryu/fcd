#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil

from ubntlib.Product import prodlist
from ubntlib.Commonlib import *

boardid = sys.argv[1]
macaddr = sys.argv[2]
pshr = sys.argv[3]
keydir = sys.argv[4]
tty = "/dev/"+sys.argv[5]
idx = sys.argv[6]
bomrev = sys.argv[7]
qrcode = sys.argv[8]
region = sys.argv[9]
svip = "192.168.1.19"

prod_ip_base = 31
prod_pfx_len = 34
prod_dev_ip_base = prod_ip_base + int(idx)
prod_dev_ip = "192.168.1." + str(prod_dev_ip_base)

prod_dev_tmp_mac = "00:15:6d:00:00:0"+idx

# Common folder
tmpdir = "/tmp/"
tftpdir = "/tftpboot/"
wifi_cal_data_dir = os.path.join(tmpdir, "IPQ8074")

# For tftpboot use
proddir = "images/"+boardid+"/"

# Absolute path for SCP
imgdir = tftpdir+"images/"
toolsdir = tftpdir+"tools/"

eepmexe = "ipq807x-aarch64-ee"
eeprom_bin = "e.b."+idx
eeprom_txt = "e.t."+idx
eeprom_tgz = "e."+idx+".tgz"
eeprom_signed = "e.s."+idx
eeprom_check = "e.c."+idx
helperexe = "helper_IPQ807x_release"
fcdssh = "user@"+svip+":"
mtdpart = "/dev/mtdblock18"

# U-boot prompt
ubpmt = {'da11': "IPQ807x",
         'da12': "IPQ807x"}

# linux console prompt
lnxpmt = {'da11': "ubnt@",
          'da12': "ubnt@"}

# number of Ethernet
ethnum = {'da11': "5",
          'da12': "7"}

# number of WiFi
wifinum = {'da11': "2",
           'da12': "2"}

# number of Bluetooth
btnum = {'da11': "1",
         'da12': "1"}

# communicating Ethernet interface
comuteth = {'da11': "br-lan",
            'da12': "br-lan"}

# temporary eeprom binary file
tempeeprom = {'da11': boardid + "/fcd_eeprom_AX.bin",
              'da12': boardid + "/AFi-AX-P_eeprom_sample.bin"}

# booting up the last message
bootmsg = {'da11': "(eth4: link becomes ready)|(eth3: PHY Link up speed)",
           'da12': "eth3: PHY Link up speed"}


def IOconfig():
    cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
    [sto, rtc] = xcmd(cmd)
    if (int(sto.decode()) > 0):
        error_critical("Caps Lock is on")
    else:
        log_debug("Caps Lock is off")

    cmd = "sudo chmod 777 "+tty
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("Can't set "+tty+" to 777 failed!!")
    else:
        log_debug("Configure "+tty+" to 777 successfully")

    time.sleep(0.5)

    cmd = "stty -F "+tty+" sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("stty configuration failed!!")
    else:
        log_debug("Configure stty successfully")

    time.sleep(0.5)

    msg(5, "Starting: key parameters")
    print("prod_dev_tmp_mac: "+prod_dev_tmp_mac)
    print("prod_dev_ip: "+prod_dev_ip)
    print("idx: "+str(idx))
    print("tty: "+str(tty))
    print("passphrase: "+str(pshr))
    print("macaddr: "+str(macaddr))
    print("boardid: "+str(boardid))
    print("keydir: "+str(keydir))
    print("svip: "+str(svip))
    print("bomrev: "+str(bomrev))
    print("qrcode: "+str(qrcode))
    print("region: "+str(region))


def main():
    IOconfig()
    expcmd = "sudo picocom "+tty+" -b 115200"
    p = ExpttyProcess(idx, expcmd, "\n")

    msg(10, "Update the U-boot")
    p.expect2actu1(30, "Hit any key to stop autoboot", "\n\n")
    p.expect2actu1(30, ubpmt[boardid], "\n")
    time.sleep(3)
    p.expect2actu1(30, ubpmt[boardid], "setenv ipaddr "+prod_dev_ip)
    p.expect2actu1(30, ubpmt[boardid], "setenv serverip "+svip)
    p.expect2actu1(30, ubpmt[boardid], "ping "+svip)
    p.expect2actu1(30, "host "+svip+" is alive", "")
    sstr = ["tftpboot",
            "0x44000000",
            "images/da11_bootloader.bin"]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, ubpmt[boardid], sstrj)
    time.sleep(3)

    p.expect2actu1(30, "Bytes transferred", "sf probe")
    p.expect2actu1(30, ubpmt[boardid], "sf erase 0x490000 0xa0000")
    time.sleep(3)
    p.expect2actu1(30, "Erased: OK", "sf write 0x44000000 0x490000 0xa0000")
    time.sleep(3)
    p.expect2actu1(30, "Written: OK", "sf erase 0x480000 0x10000")
    time.sleep(3)
    p.expect2actu1(30, "Erased: OK", "")
    sstr = ["tftpboot",
            "0x44000000",
            "images/"+tempeeprom[boardid]]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, ubpmt[boardid], sstrj)
    time.sleep(3)

    p.expect2actu1(30, "Bytes transferred", "sf erase 0x610000 0x10000")
    time.sleep(3)
    p.expect2actu1(30, "Erased: OK", "sf write 0x44000000 0x610000 0x10000")
    time.sleep(3)
    p.expect2actu1(30, "Written: OK", "")
    sstr = ["tftpboot",
            "0x44000000",
            "images/da11_fw.img"]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, ubpmt[boardid], sstrj)
    time.sleep(4)

    p.expect2actu1(120, "Bytes transferred", "nand erase 0 0x10000000")
    time.sleep(8)
    p.expect2actu1(30, "Erasing at 0xffe0000", "nand write 0x44000000 0 $filesize")
    time.sleep(8)

    p.expect2actu1(30, "written: OK", "reset")
    p.expect2actu1(120, bootmsg[boardid], "\n")
    sstr = ["ifconfig",
            comuteth[boardid],
            prod_dev_ip]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, lnxpmt[boardid], "\n")

    p.expect2actu1(30, lnxpmt[boardid], "ping "+svip)
    p.expect2actu1(30, "64 bytes from", '\003')

    p.expect2actu1(30, "", "\n")
    p.expect2actu1(30, lnxpmt[boardid], "[ ! -f ~/.ssh/known_hosts ] || rm ~/.ssh/known_hosts")

    msg(20, "Send EEPROM command and set info to EEPROM ...")
    log_debug("Send "+eepmexe+"command from host to DUT ...")
    sstr = ["scp",
            fcdssh+toolsdir+eepmexe,
            "/tmp/"]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, "Do you want to continue connecting?", "y")
    p.expect2actu1(30, "password:", "live")
    time.sleep(2)

    log_debug("Send " + helperexe + "command from host to DUT ...")
    sstr = ["scp",
            fcdssh+toolsdir + helperexe,
            "/tmp/"]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, "password:", "live")
    time.sleep(2)

    log_debug("Change file permission - " + helperexe + " ...")
    sstr = ["chmod 777", tmpdir + helperexe]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, lnxpmt[boardid], "\n")

    log_debug("Change file permission - " + eepmexe + " ...")
    sstr = ["chmod 777", tmpdir + eepmexe]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, lnxpmt[boardid], "\n")

    log_debug("Starting to do "+eepmexe+"...")
    sstr = ["cd /tmp; ./" + eepmexe,
            "-F",
            "-r " + bomrev,
            "-s 0x" + boardid,
            "-m " + macaddr,
            "-c 0x" + region,
            "-e " + ethnum[boardid],
            "-w " + wifinum[boardid],
            "-b " + btnum[boardid]]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, lnxpmt[boardid], "")
    time.sleep(3)

    msg(30, "Do helper to get the output file to devreg server ...")
    log_debug("Erase existed eeprom information files ...")
    rtf = os.path.isfile(tftpdir+eeprom_bin)
    if (rtf is True):
        log_debug("Erasing File - "+eeprom_bin+" ...")
        os.chmod(tftpdir+eeprom_bin, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir+eeprom_bin)
    else:
        log_debug("File - "+eeprom_bin+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_txt)
    if (rtf is True):
        log_debug("Erasing File - "+eeprom_txt+" ...")
        os.chmod(tftpdir+eeprom_txt, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir+eeprom_txt)
    else:
        log_debug("File - "+eeprom_txt+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_signed)
    if (rtf is True):
        log_debug("Erasing File - "+eeprom_signed+" ...")
        os.chmod(tftpdir+eeprom_signed, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir+eeprom_signed)
    else:
        log_debug("File - "+eeprom_signed+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_check)
    if (rtf is True):
        log_debug("Erasing File - "+eeprom_check+" ...")
        os.chmod(tftpdir+eeprom_check, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir+eeprom_check)
    else:
        log_debug("File - "+eeprom_check+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_tgz)
    if (rtf is True):
        log_debug("Erasing File - "+eeprom_tgz+" ...")
        os.chmod(tftpdir+eeprom_tgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir+eeprom_tgz)
    else:
        log_debug("File - "+eeprom_tgz+" doesn't exist ...")

    log_debug("Starting to do "+helperexe+"...")
    sstr = ["cd /tmp; ./"+helperexe,
            "-q",
            "-c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname="+eeprom_bin,
            ">",
            eeprom_txt]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    time.sleep(2)

    sstr = ["tar",
            "cf",
            eeprom_tgz,
            eeprom_bin,
            eeprom_txt]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)

    os.mknod(tftpdir+eeprom_tgz)
    os.chmod(tftpdir+eeprom_tgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    log_debug("Send helper output tgz file from DUT to host ...")
    sstr = ["scp",
            tmpdir+eeprom_tgz,
            fcdssh+tftpdir]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, "password:", "live")
    time.sleep(2)

    cmd = "tar xvf "+tftpdir+eeprom_tgz+" -C "+tftpdir
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("Decompressing "+eeprom_tgz+" file failed!!")
    else:
        log_debug("Decompressing "+eeprom_tgz+" files successfully")

    log_debug("Starting to do registration ...")
    cmd = ["cat "+tftpdir+eeprom_txt,
           "|",
           'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
           "|",
           'grep -v \"eeprom\"',
           "|",
           "tr '\\n' ' '"]
    cmdj = ' '.join(cmd)
    [sto, rtc] = xcmd(cmdj)
    regsubparams = sto.decode('UTF-8')
    if (int(rtc) > 0):
        error_critical("Extract parameters failed!!")
    else:
        log_debug("Extract parameters successfully")

    qrhex = qrcode.encode('utf-8').hex()

    regparam = ["-h devreg-prod.ubnt.com",
                "-k "+pshr,
                regsubparams,
                "-i field=qr_code,format=hex,value="+qrhex,
                "-i field=flash_eeprom,format=binary,pathname="+tftpdir+eeprom_bin,
                "-o field=flash_eeprom,format=binary,pathname="+tftpdir+eeprom_signed,
                "-o field=registration_id",
                "-o field=result",
                "-o field=device_id",
                "-o field=registration_status_id",
                "-o field=registration_status_msg",
                "-o field=error_message",
                "-x "+keydir+"ca.pem",
                "-y "+keydir+"key.pem",
                "-z "+keydir+"crt.pem"]

    regparamj = ' '.join(regparam)

    cmd = "sudo /usr/local/sbin/client_x86_release " + regparamj
    print("cmd: "+cmd)
    [sto, rtc] = xcmd(cmd)
    time.sleep(6)
    if (int(rtc) > 0):
        error_critical("client_x86 registration failed!!")
    else:
        log_debug("Excuting client_x86 registration successfully")

    rtf = os.path.isfile(tftpdir+eeprom_signed)
    if (rtf is not True):
        error_critical("Can't find "+eeprom_signed)

    msg(40, "Finish doing registration ...")
    log_debug("Send signed eeprom file from host to DUT ...")
    sstr = ["scp",
            fcdssh+tftpdir+eeprom_signed,
            "/tmp/"]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, "password:", "live")
    time.sleep(2)

    log_debug("Change file permission - "+eeprom_signed+" ...")
    sstr = ["chmod 777", tmpdir+eeprom_signed]
    sstrj = ' '.join(sstr)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, lnxpmt[boardid], "\n")

    log_debug("Starting to write signed info to SPI flash ...")
    sstr = [
            "cd /tmp; ./"+helperexe,
            "-q",
            "-i field=flash_eeprom,format=binary,pathname="+tmpdir+eeprom_signed]
    sstrj = ' '.join(sstr)
    print("cmd: "+sstrj)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    time.sleep(2)

    log_debug("Starting to extract the EEPROM content from SPI flash ...")
    sstr = [
            "dd",
            "if="+mtdpart,
            "of="+tmpdir+eeprom_check]
    sstrj = ' '.join(sstr)
    print("cmd: "+sstrj)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    time.sleep(2)

    os.mknod(tftpdir+eeprom_check)
    os.chmod(tftpdir+eeprom_check, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    log_debug("Send "+eeprom_check+" from DUT to host ...")
    sstr = ["scp",
            tmpdir+eeprom_check,
            fcdssh+tftpdir]
    sstrj = ' '.join(sstr)
    print("cmd: "+sstrj)
    p.expect2actu1(30, lnxpmt[boardid], sstrj)
    p.expect2actu1(30, "password:", "live")
    time.sleep(2)

    if os.path.isfile(tftpdir+eeprom_check):
        log_debug("Starting to compare the"+eeprom_check+" and "+eeprom_signed+" files ...")
        cmd = ["/usr/bin/cmp",
               tftpdir+eeprom_check,
               tftpdir+eeprom_signed]
        cmdj = ' '.join(cmd)
        [sto, rtc] = xcmd(cmdj)
        if (int(rtc) > 0):
            error_critical("Comparing files failed!!")
        else:
            log_debug("Comparing files successfully")
    else:
        log_debug("Can't find the "+eeprom_check+" and "+eeprom_signed+" files ...")

    msg(50, "Finish doing signed file and EEPROM checking ...")

    log_debug("Booting up to linux console ...")
    p.expect2actu1(30, "", "\n")
    p.expect2actu1(30, lnxpmt[boardid], "reboot")
    p.expect2actu1(60, bootmsg[boardid], "\n")
    msg(70, "Firmware booting up successfully ...")
    p.expect2actu1(60, lnxpmt[boardid], "grep qrid /proc/ubnthal/system.info")
    p.expect2actu1(60, qrcode, "")
    p.expect2actu1(60, lnxpmt[boardid], "grep -c flashSize /proc/ubnthal/system.info")
    p.expect2actu1(60, lnxpmt[boardid], "")
    match = re.search(r'(\d+)', p.proc.before)
    if match:
        if int(match.group(1)) is not 1:
            error_critical(msg="Device Registration check failed!")
    else:
        error_critical(msg="Unable to get flashSize!, please checkout output by grep")
    msg(80, "Checking there's wifi calibration data exist.")
    md5sum_no_wifi_cal = "41d2e2c0c0edfccf76fa1c3e38bc1cf2"
    cal_file = os.path.join(wifi_cal_data_dir, "caldata.bin")
    p.expect2actu1(10, "", "md5sum " + cal_file)
    p.expect2actu1(10, lnxpmt[boardid], "")
    md5sum_from_dut = ""
    match = re.search(r'([a-f0-9]{32})', p.proc.before)
    if match:
        md5sum_from_dut = match.group(1)
        log_debug(msg="MD5 :" + md5sum_from_dut)
    else:
        error_critical(msg="Unable to get md5 sum, please checkout output by md5sum command")
    if md5sum_from_dut == md5sum_no_wifi_cal:
        error_critical(msg="Wifi calibration data empty!")
    time.sleep(2)
    p.expect2actu1(30, "", "ubus call firmware info")
    p.expect2act(30, "version", "")
    msg(100, "Formal firmware completed...")

if __name__ == "__main__":
    main()
