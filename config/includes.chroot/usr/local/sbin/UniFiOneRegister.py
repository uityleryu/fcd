#!/usr/bin/python3

import re
import sys
import time
import os, stat

from ubntlib.Product import prodlist
from ubntlib.Variables import GPath, GCommon
from ubntlib.Commonlib import *


boardid = sys.argv[1]
macaddr = sys.argv[2]
pshr = sys.argv[3]
keydir = sys.argv[4]
tty = "/dev/"+sys.argv[5]
idx = sys.argv[6]
bomrev = sys.argv[7]
qrcode = sys.argv[8]
svip = "192.168.1.222"

prod_ip_base = 31
prod_pfx_len = 34
prod_dev_ip_base = prod_ip_base + int(idx)
prod_dev_ip = "192.168.1." + str(prod_dev_ip_base)

prod_dev_tmp_mac = "00:15:6d:00:00:0"+idx

modelname = {'ed01': 'UniFi USC-8!',
             'ed02': 'UniFi USC-8P-60!',
             'ed03': 'UniFi USC-8P-150!'}

ubpmt = "ALPINE_UBNT_PLUS>"
lnxpmt = "#"

prod_dir = "usc8"
fullbomrev = "113-$bomrev"
do_devreg = "1"
tmpdir = "/tmp/"
tftpdir = "/tftpboot/"
eepmexe = "al324-ee"
eeprom_bin = "e.b."+idx
eeprom_txt = "e.t."+idx
eeprom_tgz = "e."+idx+".tgz"
eeprom_signed = "e.s."+idx
eeprom_check = "e.c."+idx
e_s_gz = eeprom_signed+".gz"
e_c_gz = "$eeprom_check.gz"
helperexe = "helper_AL324_release"

def IOconfig():
    cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
    [sto, rtc] = xcmd(cmd)
    if (int(sto.decode()) > 0):
        error_critical("Caps Lock is on")

    cmd = "sudo chmod 777 /dev/ttyUSB0"
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("Can't set tty to 777 failed!!")
    else:
        log_debug("Configure tty to 777 successfully")
 
    time.sleep(0.5)

    cmd = "stty -F /dev/ttyUSB0 sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("stty configuration failed!!")
    else:
        log_debug("Configure stty successfully")

    time.sleep(0.5)



def main():
    IOconfig()
    p = ExpttyProcess(idx, tty)
    tm = 0.5
    msg(10, "Starting: ")
    print("Joe: prod_dev_tmp_mac: "+prod_dev_tmp_mac)
    print("Joe: prod_dev_ip: "+prod_dev_ip)
    print("Joe: idx: "+str(idx))
    print("Joe: tty: "+str(tty))
    print("Joe: passphrase: "+str(pshr))
    print("Joe: macaddr: "+str(macaddr))
    print("Joe: boardid: "+str(boardid))
    print("Joe: keydir: "+str(keydir))
    print("Joe: svip: "+str(svip))
    print("Joe: bomrev: "+str(bomrev))
    print("Joe: qrcode: "+str(qrcode))
    time.sleep(tm)
    msg(20, "Starting: ")

    p.expect2act(30, 'Hit any key to stop autoboot', "\n")
    p.expect2act(30, ubpmt, "rtl83xx")
    p.expect2act(30, "rtk_switch_probe: CHIP_RTL8370B", "\n")
    p.expect2act(30, ubpmt, "setenv serverip"+svip)
    p.expect2act(30, ubpmt, "dhcp")
    p.expect2act(30, ubpmt, "run bootupd")
    p.expect2act(30, ubpmt, "run kernelupd")
    p.expect2act(30, ubpmt, "run rootfsupd")
    p.expect2act(30, ubpmt, "boot")
    p.expect2act(90, 'Starting udapi-bridge', "\n")
    p.expect2act(30, lnxpmt, "ifconfig\n")
    time.sleep(2)

    sstr = ["ifconfig", "eth1", prod_dev_ip, "\n"]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    time.sleep(1)
    p.expect2act(30, lnxpmt, "ifconfig\n")
    time.sleep(1)
    p.expect2act(30, lnxpmt, "ping "+svip)
    p.expect2act(30, "64 bytes from", '\003')
    p.expect2act(30, lnxpmt, "")

    log_debug("Send "+eepmexe+"command from host to DUT ...")
    sstr = ["tftp -g -r", tftpdir+eepmexe, "-l", tmpdir+eepmexe, svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    log_debug("Starting to do "+eepmexe+"...")
    sstr = ["chmod 777", tmpdir+eepmexe]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
#     sstr = "./{}{} -r {} -F -s {} -m {} -c 0000 -e 5 -w 2 -b 1 -k -p Factory".format(tmpdir, eepmexe, bomrev, boardid, macaddr)
    sstr = ["."+tmpdir+eepmexe,
            "-r "+bomrev,
            "-F -s "+boardid,
            "-m "+macaddr,
            "-c",
            "-e 3",
            "-k"]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")
#     p.expect2act(30, "Generating key, this may take a while...", "")
#     p.expect2act(30, "fingerprint", "\n\n")

#     log_debug("Send "+helperexe+"command from host to DUT ...")
#     sstr = ["tftp -g -r", tftpdir+helperexe, "-l", tmpdir+helperexe, svip]
#     sstrj = ' '.join(sstr)
#     p.expect2act(30, lnxpmt, sstrj)
#     p.expect2act(30, lnxpmt, "\n")

    log_debug("Erase existed eeprom information files ...")
    rtf = os.path.isfile(eeprom_bin)
    if (rtf == True):
        rtfd = os.remove(eeprom_bin)
    else:
        log_debug("File - e.b. doesn't exist ...")

    rtf = os.path.isfile(eeprom_txt)
    if (rtf == True):
        rtfd = os.remove(eeprom_txt)
    else:
        log_debug("File - e.t. doesn't exist ...")

    rtf = os.path.isfile(eeprom_tgz)
    if (rtf == True):
        rtfd = os.remove(eeprom_tgz)
    else:
        log_debug("File - e.tgz doesn't exist ...")

    log_debug("Starting to do "+helperexe+"...")
    sstr = ["chmod 777", tmpdir+helperexe]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    sstr = ["."+tmpdir+helperexe,
            "-q -c product_class=basic",
            "-o field=flash_eeprom,format=binary,pathname="+eeprom_bin,
            ">",
            eeprom_txt]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    sstr = ["tar",
            "cf",
            eeprom_tgz,
            eeprom_bin,
            eeprom_txt]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    os.mknod(tftpdir+eeprom_tgz)
    os.chmod(tftpdir+eeprom_tgz, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)

    log_debug("Send helper output tgz file from DUT to host ...")
    sstr = ["tftp",
            "-p",
            "-r",
            tftpdir+eeprom_tgz,
            "-l",
            tftpdir+eeprom_tgz,
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    cmd = "tar xvf"+tftpdir+eeprom_tgz
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("Decompressing e.x.tgz file failed!!")
    else:
        log_debug("Decompressing e.x.tgz files successfully")

    time.sleep(0.5)

    log_debug("Starting to do registration ...")
    cmd = ["cat", tftpdir+eeprom_txt, "|",
           'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"', "|",
           'grep -v \"eeprom\"', "|",
           "tr '\\n' ' '"]
    cmdj = ' '.join(cmd)
    [sto, rtc] = xcmd(cmdj)
    regsubparams = sto.decode('UTF-8')
    if (int(rtc) > 0):
        error_critical("Extract parameters failed!!")
    else:
        log_debug("Extract parameters successfully")
        print(regsubparams)

    time.sleep(0.5)

    qrhex = qrcode.encode('utf-8').hex()

    regparam = ["-k"+pshr,
                "-i field=product_class_id,value=basic",
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
                "-x"+keydir+"ca.pem",
                "-y"+keydir+"key.pem",
                "-z"+keydir+"crt.pem"]
    
    cmd = "/usr/local/sbin/client_x86"+regparam
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("client_x86 registration failed!!")
    else:
        log_debug("Excuting client_x86 registration successfully")

    time.sleep(2)

    cmd = "gzip "+tftpdir+eeprom_signed
    [sto, rtc] = xcmd(cmd)
    if (int(rtc) > 0):
        error_critical("zip signed eeprom failed!!")
    else:
        log_debug("zip signed eeprom successfully")

    time.sleep(2)

    log_debug("Send zipped signed eeprom file from host to DUT ...")
    sstr = ["tftp -g -r", tftpdir+e_s_gz, "-l", tftpdir+e_s_gz, svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    #p.close()
    exit(1)
#     msg(30, "Starting: ")
#     time.sleep(tm)
#     msg(40, "Starting: ")

#     try:
#         p = ExpttyProcess(idx, tty)
#         tm = 0.5
#         time.sleep(3)
#         msg(10, "Starting: ")
#         print("Joe: prod_dev_tmp_mac: "+prod_dev_tmp_mac)
#         print("Joe: prod_dev_ip: "+prod_dev_ip)
#         print("Joe: idx: "+str(idx))
#         print("Joe: tty: "+str(tty))
#         print("Joe: passphrase: "+str(pshr))
#         print("Joe: macaddr: "+str(macaddr))
#         print("Joe: boardid: "+str(boardid))
#         print("Joe: keydir: "+str(keydir))
#         print("Joe: svip: "+str(svip))
#         print("Joe: bomrev: "+str(bomrev))
#         print("Joe: qrcode: "+str(qrcode))
#         time.sleep(tm)
#         msg(20, "Starting: ")
#         p.expect2act(30, 'Hit any key to stop autoboot:', '\cC')
#         p.expect2act(30, 'uboot', "setenv ipaddr 192.168.1.31\n")
#         p.expect2act(30, 'uboot', "setenv serverip 192.168.1.11\n")
#         p.expect2act(30, 'uboot', "ping 192.168.1.11\n")
#         p.expect2act(30, 'host 192.168.1.11 is alive', "")
#         p.expect2act(30, 'uboot>', "printenv\n")
#         p.expect2act(30, 'uboot>', "reset\n")
#         #time.sleep(1)
#         #exit(1)
#         msg(30, "Starting: ")
#         p.expect2act(60, 'Please press Enter to activate', "\n")
#         p.expect2act(30, 'UBNT login:', "ubnt\n")
#         p.expect2act(30, 'Password:', "ubnt")
#         p.expect2act(30, 'US.pcb-mscc#:', "cat /proc/ubnthal/system.info\n")
#         p.expect2act(30, 'US.pcb-mscc#:', "")
#         time.sleep(tm)
#         msg(40, "Starting: ")
#         #exit(1)
#         time.sleep(tm)
#         msg(50, "Starting: ")
#         time.sleep(tm)
#         msg(60, "Starting: ")
#         time.sleep(tm)
#         msg(70, "Starting: ")
#         time.sleep(tm)
#         msg(80, "Starting: ")
#         time.sleep(tm)
#         msg(90, "Starting: ")
#         time.sleep(tm)
#         msg(100, "Starting: ")
#         time.sleep(tm)
#         msg(110, "Starting: ")
#     except:
#         print("Something wrong")


if __name__ == "__main__":
    main()






