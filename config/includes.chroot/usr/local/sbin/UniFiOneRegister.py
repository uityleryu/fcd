#!/usr/bin/python3.6

import re
import sys
import time

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
svip = "192.168.1.19"

prod_ip_base = 31
prod_pfx_len = 34
prod_dev_ip_base = prod_ip_base + int(idx)
prod_dev_ip = "192.168.1." + str(prod_dev_ip_base)

prod_dev_tmp_mac = "00:15:6d:00:00:0"+idx

modelname = {'ed01': 'UniFi USC-8!',
             'ed02': 'UniFi USC-8P-60!',
             'ed03': 'UniFi USC-8P-150!'}

timeout = ""
ret = ""
prod_dir = "usc8"
fullbomrev = "113-$bomrev"
do_devreg = "1"
tftpdir = "/tftpboot"
devregcmd = "vsc7514-ee"
cpuname = "VSC7514"
eeprom_bin = "e.b.$idx"
eeprom_txt = "e.t.$idx"
eeprom_tgz = "e.$idx.tgz"
eeprom_signed = "e.s.$idx"
eeprom_check = "e.c.$idx"
e_s_gz = "$eeprom_signed.gz"
e_c_gz = "$eeprom_check.gz"
helper = "helper_VSC7514"
helpercmd = "/tmp/$helper -q -c product_class=basic -o field=flash_eeprom,format=binary,pathname=$eeprom_bin > $eeprom_txt";

def IOconfig():
    cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
    [sto, rtc] = xcmd(cmd)
    if (int(sto.decode()) > 0):
        error_critical("Caps Lock is on")

    cmd = "stty -F /dev/ttyUSB0 sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
    [sto, rtc] = xcmd(cmd)
    if (int(sto.decode()) > 0):
        error_critical("stty configuration failed!!")

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
    p.expect2act(30, 'Hit any key to stop autoboot:', '\n')
    p.expect2act(30, 'uboot>', "setenv ipaddr 192.168.1.31")
    p.expect2act(30, 'uboot>', "setenv serverip 192.168.1.11")
    p.expect2act(30, 'uboot>', "ping 192.168.1.11")
    p.expect2act(30, 'host 192.168.1.11 is alive', "")
    p.expect2act(30, 'uboot>', "printenv")
    p.expect2act(30, 'uboot>', "reset")
    p.expect2act(60, 'Please press Enter to activate', "\n")
    p.expect2act(30, 'UBNT login:', "ubnt")
    p.expect2act(30, 'Password:', "ubnt")
    p.expect2act(30, 'US.pcb-mscc', "\n")
    p.expect2act(30, 'US.pcb-mscc', "cat /proc/ubnthal/system.info")
    p.expect2act(30, 'US.pcb-mscc', "")
    time.sleep(5)
    p.close()
    #exit(1)
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






