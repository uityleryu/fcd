#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil

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
svip = "192.168.1.19"
 
prod_ip_base = 31
prod_pfx_len = 34
prod_dev_ip_base = prod_ip_base + int(idx)
prod_dev_ip = "192.168.1." + str(prod_dev_ip_base)
 
prod_dev_tmp_mac = "00:15:6d:00:00:0"+idx
 
ubpmt = "ALPINE_UBNT>"
lnxpmt = "#"

fullbomrev = "113-$bomrev"
tmpdir = "/tmp/"
tftpdir = "/tftpboot/"
proddir = tftpdir+boardid+"/"
eepmexe = "al324-ee"
eeprom_bin = "e.b."+idx
eeprom_txt = "e.t."+idx
eeprom_tgz = "e."+idx+".tgz"
eeprom_signed = "e.s."+idx
eeprom_check = "e.c."+idx
helperexe = "helper_AL324_release"
mtdpart = "/dev/mtdblock4"

bootimg = tftpdir+"boot.img"
uimage = tftpdir+"uImage"
dtimg = tftpdir+"dt.img"
upgradetar = tftpdir+"upgrade.tar"
fcddtimg = proddir+"fcd/fcd-dt.img"
fcduimage = proddir+"fcd/fcd-uImage"
fcdpreload = proddir+"fcd/preload.img"
fwbootimg = proddir+"fw/ubnt_one_rev4_boot.img"
fwuimage = proddir+"fw/fw-uImage"
fwupgradetar = proddir+"fw/upgrade.tar"

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
    p = ExpttyProcess(idx, tty)

    msg(10, "Boot from tftp ...")
    p.expect2act(30, "Hit any key to stop autoboot", "\n\n")
    p.expect2act(30, ubpmt, "\n")

    rtf = os.path.isfile(bootimg)
    if (rtf == True):
        log_debug("Erasing File - "+bootimg+" ...")
        os.chmod(bootimg, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(bootimg)
    else:
        log_debug("File - "+bootimg+" doesn't exist ...")

    rtf = os.path.isfile(uimage)
    if (rtf == True):
        log_debug("Erasing File - "+uimage+" ...")
        os.chmod(uimage, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(uimage)
    else:
        log_debug("File - "+uimage+" doesn't exist ...")

    rtf = os.path.isfile(dtimg)
    if (rtf == True):
        log_debug("Erasing File - "+dtimg+" ...")
        os.chmod(dtimg, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(dtimg)
    else:
        log_debug("File - "+dtimg+" doesn't exist ...")

    rtf = os.path.isfile(fcddtimg)
    if (rtf == True):
        log_debug("Copy File - "+fcddtimg+" to "+dtimg)
        shutil.copyfile(fcddtimg, dtimg)
    else:
        log_debug("File - "+fcddtimg+" doesn't exist ...")

    rtf = os.path.isfile(fcduimage)
    if (rtf == True):
        log_debug("Copy File - "+fcduimage+" to "+uimage)
        shutil.copyfile(fcduimage, uimage)
    else:
        log_debug("File - "+fcduimage+" doesn't exist ...")

    rtf = os.path.isfile(fcdpreload)
    if (rtf == True):
        log_debug("Copy File - "+fcdpreload+" to "+bootimg)
        shutil.copyfile(fcdpreload, bootimg)
    else:
        log_debug("File - "+fcdpreload+" doesn't exist ...")

    p.expect2act(30, ubpmt, "qca8k")
    p.expect2act(30, "al_eth1: QCA8K_ID_QCA8337 0x13", "\n")
    p.expect2act(30, ubpmt, "setenv ipaddr "+prod_dev_ip)
    p.expect2act(30, ubpmt, "setenv serverip "+svip)
    p.expect2act(30, ubpmt, "run bootupd")
    p.expect2act(60, "bootupd done", "")
    p.expect2act(60, ubpmt, "reset")
    p.expect2act(30, "Hit any key to stop autoboot", "\n")
    p.expect2act(30, ubpmt, "\n")

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
    sstr = ["tftp",
            "-g",
            "-r "+eepmexe,
            "-l "+tmpdir+eepmexe,
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    log_debug("Send "+helperexe+"command from host to DUT ...")
    sstr = ["tftp",
            "-g",
            "-r "+helperexe,
            "-l "+tmpdir+helperexe,
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    log_debug("Change file permission - "+helperexe+" ...")
    sstr = ["chmod 777", tmpdir+helperexe]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    log_debug("Change file permission - "+eepmexe+" ...")
    sstr = ["chmod 777", tmpdir+eepmexe]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    log_debug("Starting to do "+eepmexe+"...")
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

    log_debug("Starting to do "+helperexe+"...")
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
            "-r "+eeprom_tgz,
            "-l "+eeprom_tgz,
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
    cmd = "sudo /usr/local/sbin/client_x86_release "+regparamj
    print("cmd: "+cmd)
    [sto, rtc] = xcmd(cmd)
    time.sleep(5)
    if (int(rtc) > 0):
        error_critical("client_x86 registration failed!!")
    else:
        log_debug("Excuting client_x86 registration successfully")

    rtf = os.path.isfile(tftpdir+eeprom_signed)
    if (rtf != True):
        error_critical("Can't find "+eeprom_signed)

    msg(40, "Finish doing registration ...")
    log_debug("Send signed eeprom file from host to DUT ...")
    sstr = ["tftp",
            "-g",
            "-r "+eeprom_signed,
            "-l "+tmpdir+eeprom_signed,
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    log_debug("Change file permission - "+eeprom_signed+" ...")
    sstr = ["chmod 777", tmpdir+eeprom_signed]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)
    p.expect2act(30, lnxpmt, "\n")

    log_debug("Starting to write signed info to SPI flash ...")
    sstr = ["."+tmpdir+helperexe,
           "-q",
           "-i field=flash_eeprom,format=binary,pathname="+tmpdir+eeprom_signed]
    sstrj = ' '.join(sstr)
    print("cmd: "+sstrj)
    p.expect2act(30, lnxpmt, sstrj)

    log_debug("Starting to extract the EEPROM content from SPI flash ...")
    sstr = ["dd",
           "if="+mtdpart,
           "of="+tmpdir+eeprom_check]
    sstrj = ' '.join(sstr)
    print("cmd: "+sstrj)
    p.expect2act(30, lnxpmt, sstrj)
    time.sleep(2)

    os.mknod(tftpdir+eeprom_check)
    os.chmod(tftpdir+eeprom_check, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)

    log_debug("Send "+eeprom_check+" from DUT to host ...")
    sstr = ["tftp",
            "-p",
            "-r "+eeprom_check,
            "-l "+tmpdir+eeprom_check,
            svip]
    sstrj = ' '.join(sstr)
    print("cmd: "+sstrj)
    p.expect2act(30, lnxpmt, sstrj)

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

    log_debug("Change to use FW uImage and upgrade tar file ...")
    rtf = os.path.isfile(bootimg)
    if (rtf == True):
        log_debug("Erasing File - "+bootimg+" ...")
        os.chmod(bootimg, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(bootimg)
    else:
        log_debug("File - "+bootimg+" doesn't exist ...")

    rtf = os.path.isfile(uimage)
    if (rtf == True):
        log_debug("Erasing File - "+uimage+" ...")
        os.chmod(uimage, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(uimage)
    else:
        log_debug("File - "+uimage+" doesn't exist ...")

    rtf = os.path.isfile(dtimg)
    if (rtf == True):
        log_debug("Erasing File - "+dtimg+" ...")
        os.chmod(dtimg, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        os.remove(dtimg)
    else:
        log_debug("File - "+dtimg+" doesn't exist ...")

    rtf = os.path.isfile(fwbootimg)
    if (rtf == True):
        log_debug("Copy File - "+fwbootimg+" to "+bootimg)
        shutil.copyfile(fwbootimg, bootimg)
    else:
        log_debug("File - "+fwbootimg+" doesn't exist ...")

    rtf = os.path.isfile(fwuimage)
    if (rtf == True):
        log_debug("Copy File - "+fwuimage+" to "+uimage)
        shutil.copyfile(fwuimage, uimage)
    else:
        log_debug("File - "+fwuimage+" doesn't exist ...")

    rtf = os.path.isfile(fwupgradetar)
    if (rtf == True):
        log_debug("Copy File - "+fwupgradetar+" to "+upgradetar)
        shutil.copyfile(fwupgradetar, upgradetar)
    else:
        log_debug("File - "+fwupgradetar+" doesn't exist ...")

    log_debug("Change to product U-boot ...")
    p.expect2act(30, "", "\n")
    p.expect2act(30, lnxpmt, "reboot")
    p.expect2act(30, 'Hit any key to stop autoboot', "\n")
    p.expect2act(30, ubpmt, "\n")

    p.expect2act(30, ubpmt, "qca8k")
    p.expect2act(30, "al_eth1: QCA8K_ID_QCA8337 0x13", "\n")
    p.expect2act(30, ubpmt, "setenv ipaddr "+prod_dev_ip)
    p.expect2act(30, ubpmt, "setenv serverip "+svip)
    p.expect2act(30, ubpmt, "run bootupd")
    p.expect2act(60, "bootupd done", "\n")
    p.expect2act(30, ubpmt, "reset")
    p.expect2act(30, 'Hit any key to stop autoboot', "\n")
    p.expect2act(30, ubpmt, "\n")
    p.expect2act(30, ubpmt, "run delenv")
    msg(60, "Finish changing to product U-boot ...")

    log_debug("Starting to run the product kernel ...")
    p.expect2act(30, ubpmt, "qca8k")
    p.expect2act(30, "al_eth1: QCA8K_ID_QCA8337 0x13", "\n")
    p.expect2act(30, ubpmt, "setenv ipaddr "+prod_dev_ip)
    p.expect2act(30, ubpmt, "setenv serverip "+svip)
    p.expect2act(30, ubpmt, "setenv bootargs pci=pcie_bus_perf console=ttyS0,115200")
    p.expect2act(30, ubpmt, "cp.b $fdtaddr $loadaddr_dt 7ffc")
    p.expect2act(30, ubpmt, "fdt addr $loadaddr_dt")
    p.expect2act(30, ubpmt, "tftpboot $loadaddr uImage")
    p.expect2act(30, "Bytes transferred", "")
    p.expect2act(30, ubpmt, "bootm $loadaddr - $fdtaddr")
    p.expect2act(60, "login:", "root")
    p.expect2act(30, "Password:", "ubnt\n")
    msg(70, "Succeeding in booting to product firmware upgraded linux console ...")

    p.expect2act(30, "", "\n")
    p.expect2act(30, lnxpmt, "dmesg -n 1")

    sstr = ["ifconfig",
            "eth0",
            prod_dev_ip,
            "up"]
    sstrj = ' '.join(sstr)
    p.expect2act(30, lnxpmt, sstrj)

    p.expect2act(30, lnxpmt, "ping "+svip)
    p.expect2act(30, "64 bytes from", '\003')

    p.expect2act(30, "", "\n")
    p.expect2act(30, lnxpmt, "echo \"\" > /tmp/upgrade.tar")
    p.expect2act(30, lnxpmt, "ls -la /tmp")

    sstr = ["tftp",
            "-g",
            "-r upgrade.tar",
            "-l "+tmpdir+"upgrade.tar",
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(120, lnxpmt, sstrj)
    p.expect2act(30, "", "\n")
    time.sleep(120)
    p.expect2act(30, "", "\n")

    sstr = ["tftp",
            "-g",
            "-r upgrade.tar",
            "-l "+tmpdir+"upgrade.tar",
            svip]
    sstrj = ' '.join(sstr)
    p.expect2act(120, lnxpmt, sstrj)
    p.expect2act(30, "", "\n")
    time.sleep(120)
    p.expect2act(30, "", "\n")
    msg(80, "Succeeding in downloading the upgrade tarf file ...")
 
    p.expect2act(30, lnxpmt, "sh /sbin/flash-factory.sh")
    p.expect2act(30, "uImage: OK", "")
    p.expect2act(30, "rootfs.squashfs: OK", "")
    p.expect2act(120, "Writing superblocks and filesystem accounting information", "")
  
    p.expect2act(60, "login:", "root")
    p.expect2act(30, "Password:", "ubnt")
    p.expect2act(30, "", "\n")
    p.expect2act(30, lnxpmt, "")
    msg(100, "Completing firmware upgrading ...")
    time.sleep(2)
    exit(0)


if __name__ == "__main__":
    main()


