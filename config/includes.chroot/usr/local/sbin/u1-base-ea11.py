#!/usr/bin/python3.6

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
region = sys.argv[9]
svip = "192.168.1.11"
 
prod_ip_base = 31
prod_pfx_len = 34
prod_dev_ip_base = prod_ip_base + int(idx)
prod_dev_ip = "192.168.1." + str(prod_dev_ip_base)
 
prod_dev_tmp_mac = "00:15:6d:00:00:0"+idx
 
ubpmt = "ALPINE_UBNT>"
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


eeprom_bin = "e.b.0"
eeprom_txt = "e.t.0"
eeprom_tgz = "e.0.tgz"

def IOconfig():
    cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
    [sto, rtc] = xcmd(cmd)
    if (int(sto.decode()) > 0):
        error_critical("Caps Lock is on")
    else:
        log_debug("Caps Lock is off")

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

def main2():
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


def main():
    msg(5, "Starting: key parameters")
    IOconfig()
    p = ExpttyProcess(idx, tty)
    tm = 0.5
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
    msg(10, "Boot from tftp ...")

    p.expect2act(30, 'Hit any key to stop autoboot', "\n")
    p.expect2act(30, ubpmt, "qca8k")
    p.expect2act(30, "al_eth1: QCA8K_ID_QCA8337 0x13", "\n")
    p.expect2act(30, ubpmt, "setenv ipaddr "+prod_dev_ip)
    p.expect2act(30, ubpmt, "setenv serverip "+svip)
    p.expect2act(30, ubpmt, "setenv bootargs pci=pcie_bus_perf console=ttyS0,115200")
    p.expect2act(30, ubpmt, "run boottftp")

    p.expect2act(60, "Calling CRDA to update world", "\n")
    sstr = ["ifconfig", "eth1", prod_dev_ip, "up\n"]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    p.expect2act(30, lnxpmt, "ifconfig\n")

    p.expect2act(30, lnxpmt, "ping "+svip)
    p.expect2act(30, "64 bytes from", '\003')
    p.expect2act(30, lnxpmt, "")

    msg(20, "Send EEPROM command and set info to EEPROM ...")
    log_debug("Send "+eepmexe+"command from host to DUT ...")
    sstr = ["tftp -g -r", tftpdir+eepmexe, "-l", tmpdir+eepmexe, svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    log_debug("Starting to do "+eepmexe+"...")
    sstr = ["chmod 777", tmpdir+eepmexe]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    sstr = ["."+tmpdir+eepmexe,
            "-F",
            "-r "+bomrev,
            "-s 0x"+boardid,
            "-m "+macaddr,
            "-c 0x"+region,
            "-e 4",
            "-w 2",
            "-b 1",
            "-k",
            "-p Factory"]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    time.sleep(3)

    msg(30, "Do helper to get the output file to devreg server ...")
    log_debug("Erase existed eeprom information files ...")
    rtf = os.path.isfile(tftpdir+eeprom_bin)
    if (rtf == True):
        log_debug("Erasing File - "+eeprom_bin+" ...")
        os.chmod(tftpdir+eeprom_bin, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(tftpdir+eeprom_bin)
    else:
        log_debug("File - "+eeprom_bin+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_txt)
    if (rtf == True):
        log_debug("Erasing File - "+eeprom_txt+" ...")
        os.chmod(tftpdir+eeprom_txt, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(tftpdir+eeprom_txt)
    else:
        log_debug("File - "+eeprom_txt+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_signed)
    if (rtf == True):
        log_debug("Erasing File - "+eeprom_signed+" ...")
        os.chmod(tftpdir+eeprom_signed, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(tftpdir+eeprom_signed)
    else:
        log_debug("File - "+eeprom_signed+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_check)
    if (rtf == True):
        log_debug("Erasing File - "+eeprom_check+" ...")
        os.chmod(tftpdir+eeprom_check, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(tftpdir+eeprom_check)
    else:
        log_debug("File - "+eeprom_check+" doesn't exist ...")

    rtf = os.path.isfile(tftpdir+eeprom_tgz)
    if (rtf == True):
        log_debug("Erasing File - "+eeprom_tgz+" ...")
        os.chmod(tftpdir+eeprom_tgz, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(tftpdir+eeprom_tgz)
    else:
        log_debug("File - "+eeprom_tgz+" doesn't exist ...")

    log_debug("Send "+helperexe+"command from host to DUT ...")
    sstr = ["tftp",
            "-g",
            "-r "+tftpdir+helperexe,
            "-l "+tmpdir+helperexe,
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    log_debug("Starting to do "+helperexe+"...")
    sstr = ["chmod 777", tmpdir+helperexe]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    sstr = ["."+tmpdir+helperexe,
            "-q",
            "-c product_class=basic",
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
            eeprom_tgz,
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, "", "\n")
    p.expect2act(30, lnxpmt, sstrj)

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

    regparam = ["-k"+pshr,
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
    cmd = "/usr/local/sbin/client_x86 "+regparamj
    print("cmd: "+cmd)
    [sto, rtc] = xcmd(cmd)
    time.sleep(10)
    if (int(rtc) > 0):
        error_critical("client_x86 registration failed!!")
    else:
        log_debug("Excuting client_x86 registration successfully")

    rtf = os.path.isfile(tftpdir+eeprom_signed)
    if (rtf != True):
        error_critical("Can't find "+eeprom_signed)

    msg(40, "Finish doing registration ...")

#     cmd = "gzip "+tftpdir+eeprom_signed
#     [sto, rtc] = xcmd(cmd)
#     if (int(rtc) > 0):
#         error_critical("zip signed eeprom failed!!")
#     else:
#         log_debug("zip signed eeprom successfully")
# 
#     time.sleep(2)
# 
#     log_debug("Send zipped signed eeprom file from host to DUT ...")
#     sstr = ["tftp",
#             "-g",
#             "-r",
#             tftpdir+e_s_gz,
#             "-l",
#             tftpdir+e_s_gz,
#             svip]
#     sstrj = ' '.join(sstr)
#     p.expect2act(30, lnxpmt, sstrj)


    log_debug("Send signed eeprom file from host to DUT ...")
    sstr = ["tftp",
            "-g",
            "-r",
            tftpdir+eeprom_signed,
            "-l",
            eeprom_signed,
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    log_debug("Starting to write signed info to SPI flash ...")
    cmd = ["."+tmpdir+helperexe,
           "-q",
           "-i field=flash_eeprom,format=binary,pathname="+tftpdir+eeprom_signed]
    cmdj = ' '.join(cmd)
    [sto, rtc] = xcmd(cmdj)
    rt = sto.decode('UTF-8')
    if (int(rtc) > 0):
        error_critical("Writing the signed info failed!!")
    else:
        log_debug("Writing the signed info successfully")
        print(rt)

    log_debug("Starting to extract the EEPROM content from SPI flash ...")
    sstr = ["dd",
           "if=/dev/mtdblock4",
           "of="+tftpdir+eeprom_check]
    sstrj = ' '.join(cmd)
    p.expect2act(30, lnxpmt, sstrj)

    log_debug("Send e.c. from DUT to host ...")
    sstr = ["tftp",
            "-p",
            "-r",
            tftpdir+eeprom_check,
            "-l",
            eeprom_tgz,
            svip]
    sstrj = ' '.join(cmd)
    p.expect2act(30, lnxpmt, sstrj)

    log_debug("Starting to compare the e.c. and e.s. files ...")
    cmd = ["/usr/bin/cmp",
           tftpdir+eeprom_check,
           tftpdir+eeprom_signed]
    cmdj = ' '.join(cmd)
    [sto, rtc] = xcmd(cmdj)
    rt = sto.decode('UTF-8')
    if (int(rtc) > 0):
        error_critical("Comparing files failed!!")
    else:
        log_debug("Comparing files successfully")
        print(rt)
        
    msg(50, "Finish doing signed file and EEPROM checking ...")

    exit(0)


if __name__ == "__main__":
    main()






