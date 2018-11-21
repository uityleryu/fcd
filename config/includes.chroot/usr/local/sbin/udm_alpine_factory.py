#!/usr/bin/python3

from ubntlib.gui.gui_variable import GPath, GCommon
from ubntlib.Commonlib import *
from ubntlib.fcd.helper import FCDHelper

import sys
import time
import os
import stat
import filecmp

"""
    command parameter description for security registration
    command: python3
    pyfile:  script
    para0:   slot ID
    para1:   UART device number
    para2:   FCD host IP
    para3:   system ID (board ID)
    para4:   MAC address
    para5:   passphrase
    para6:   key directory
    para7:   BOM revision
    para8:   QR code
    para9:   Region Code
"""
idx = sys.argv[0]
tty = "/dev/" + sys.argv[1]
svip = sys.argv[2]
boardid = sys.argv[3]
macaddr = sys.argv[4]
pshr = sys.argv[5]
keydir = sys.argv[6]
bomrev = sys.argv[7]
qrcode = sys.argv[8]
region = sys.argv[9]

prod_ip_base = 31
prod_pfx_len = 34
prod_dev_ip_base = prod_ip_base + int(idx)
prod_dev_ip = "192.168.1." + str(prod_dev_ip_base)

prod_dev_tmp_mac = "00:15:6d:00:00:0"+idx

tmpdir = "/tmp/"
tftpdir = "/tftpboot/"
proddir = tftpdir + boardid + "/"
toolsdir = "tools/"

# U-boot prompt
ubpmt = "UBNT_UDM"

# linux console prompt
lnxpmt = "#"

# switch chip
swchip = {
    'ea11': "qca8k",
    'ea13': "rtl83xx",
    'ea15': "rtl83xx"
}

wsysid = {
    'ea11': "770711ea",
    'ea13': "770713ea",
    'ea15': "770715ea"
}

# switch initalialized message
swmsg = {
    'ea11': "al_eth1: QCA8K_ID_QCA8337 0x13",
    'ea13': "rtk_switch_probe: CHIP_RTL8370B",
    'ea15': "rtk_switch_probe: CHIP_RTL8370B"
}

# number of Ethernet
ethnum = {
    'ea11': "5",
    'ea13': "7",
    'ea15': "9"
}

# number of WiFi
wifinum = {
    'ea11': "2",
    'ea13': "2",
    'ea15': "0"
}

# number of Bluetooth
btnum = {
    'ea11': "1",
    'ea13': "1",
    'ea15': "1"
}

eepmexe = "al324-ee"
eeprom_bin = "e.b." + idx
eeprom_txt = "e.t." + idx
eeprom_tgz = "e." + idx + ".tgz"
eeprom_signed = "e.s." + idx
eeprom_check = "e.c." + idx
helperexe = "helper_AL324_release"
dropbearexe = "dropbear_arm64"
dropbearkeyexe = "dropbearkey_arm64"
mtdpart = "/dev/mtdblock4"

bootimg = tftpdir + "boot.img"
uimage = tftpdir + "uImage"
dtimg = tftpdir + "dt.img"

# write system ID to the EEPROM partition
write_sysid_cmd = "mw.l 0x08000000 "+wsysid[boardid]
fcd = FCDHelper()


def IOconfig():
    cmd = "xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'"
    [sto, rtc] = fcd.common.xcmd(cmd)
    if int(sto.decode()) > 0:
        error_critical("Caps Lock is on")
    else:
        log_debug("Caps Lock is off")

    cmd = "sudo chmod 777 " + tty
    [sto, rtc] = fcd.common.xcmd(cmd)
    if int(rtc) > 0:
        error_critical("Can't set " + tty + " to 777 failed!!")
    else:
        log_debug("Configure " + tty + " to 777 successfully")

    time.sleep(0.5)

    cmd = "stty -F " + tty + " sane 115200 raw -parenb -cstopb cs8 -echo onlcr"
    [sto, rtc] = fcd.common.xcmd(cmd)
    if int(rtc) > 0:
        error_critical("stty configuration failed!!")
    else:
        log_debug("Configure stty successfully")

    time.sleep(0.5)

    msg(5, "Starting: key parameters")
    print("prod_dev_tmp_mac: " + prod_dev_tmp_mac)
    print("prod_dev_ip: " + prod_dev_ip)
    print("idx: " + str(idx))
    print("tty: " + str(tty))
    print("passphrase: " + str(pshr))
    print("macaddr: " + str(macaddr))
    print("boardid: " + str(boardid))
    print("keydir: " + str(keydir))
    print("svip: " + str(svip))
    print("bomrev: " + str(bomrev))
    print("qrcode: " + str(qrcode))
    print("region: " + str(region))


def main():
    IOconfig()
    expcmd = "sudo picocom " + tty + " -b 115200"
    p = ExpttyProcess(idx, expcmd, "\n")

    msg(10, "Boot from tftp with installer ...")
    p.expect2actu1(15, "to stop", "\033\033")

    # Set the system ID to the DUT
    p.expect2actu1(10, ubpmt, write_sysid_cmd)
    p.expect2actu1(10, ubpmt, "sf probe")
    p.expect2actu1(10, ubpmt, "sf erase 0x1f0000 0x1000")
    p.expect2actu1(30, "Erased: OK", "")
    p.expect2actu1(10, ubpmt, "sf write 0x8000000 0x1f000c 0x4")
    p.expect2actu1(30, "Written: OK", "")
    p.expect2actu1(10, ubpmt, "reset")
    p.expect2actu1(10, "to stop", "\033\033")

    p.expect2actu1(10, ubpmt, swchip[boardid])
    p.expect2actu1(10, ubpmt, "setenv ipaddr " + prod_dev_ip)
    p.expect2actu1(10, ubpmt, "setenv serverip " + svip)
    p.expect2actu1(10, ubpmt, "setenv tftpdir images/" + boardid + "_signed_")
    time.sleep(2)
    p.expect2actu1(10, ubpmt, "ping " + svip)
    p.expect2actu1(10, "host " + svip + " is alive", "")
    p.expect2actu1(10, ubpmt, "run bootupd")
    p.expect2actu1(30, "Written: OK", "")
    p.expect2actu1(10, "bootupd done", "")
    p.expect2actu1(10, ubpmt, "reset")
    p.expect2actu1(10, "to stop", "\033\033")

    # Set the Ethernet IP
    p.expect2actu1(10, ubpmt, swchip[boardid])
    p.expect2actu1(10, ubpmt, "setenv ipaddr " + prod_dev_ip)
    p.expect2actu1(10, ubpmt, "setenv serverip " + svip)
    time.sleep(2)
    p.expect2actu1(10, ubpmt, "ping " + svip)
    p.expect2actu1(10, "host " + svip + " is alive", "")
    p.expect2actu1(10, ubpmt, "setenv bootargs ubnt-flash-factory pci=pcie_bus_perf console=ttyS0,115200")
    p.expect2actu1(10, ubpmt, "cp.b $fdtaddr $loadaddr_dt 7ffc")
    p.expect2actu1(10, ubpmt, "fdt addr $loadaddr_dt")
    p.expect2actu1(10, ubpmt, "tftpboot $loadaddr images/" + boardid + "-recovery")
    p.expect2actu1(10, "Bytes transferred", "")
    p.expect2actu1(10, ubpmt, "bootm $loadaddr - $fdtaddr")
    p.expect2actu1(60, "login:", "root")
    p.expect2actu1(10, "Password:", "ubnt")

    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, "dmesg -n 1")

    p.expect2actu1(10, lnxpmt, "ifconfig eth0 " + prod_dev_ip)
    time.sleep(2)
    p.expect2actu1(10, lnxpmt, "ping " + svip)
    p.expect2actu1(10, "64 bytes from", '\003')

    msg(20, "Send EEPROM command and set info to EEPROM ...")

    log_debug("Send " + eepmexe + " command from host to DUT ...")
    sstr = [
        "tftp",
        "-g",
        "-r " + toolsdir + eepmexe,
        "-l " + tmpdir + eepmexe,
        svip
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    log_debug("Send " + helperexe + " command from host to DUT ...")
    sstr = [
        "tftp",
        "-g",
        "-r " + toolsdir + helperexe,
        "-l " + tmpdir + helperexe,
        svip
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    log_debug("Change file permission - " + helperexe + " ...")
    sstr = [
        "chmod 777",
        tmpdir + helperexe
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    log_debug("Change file permission - " + eepmexe + " ...")
    sstr = [
        "chmod 777",
        tmpdir + eepmexe
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    log_debug("Starting to initialize the dropbear")
    sstr = [
        "mkdir",
        "-p",
        "/var/run/dropbear; ",
        "dropbear -R"
        ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)
    time.sleep(1)

    log_debug("Starting to do " + eepmexe + "...")
    sstr = [
        tmpdir + eepmexe,
        "-F",
        "-r " + bomrev,
        "-s 0x" + boardid,
        "-m " + macaddr,
        "-c 0x" + region,
        "-e " + ethnum[boardid],
        "-w " + wifinum[boardid],
        "-b " + btnum[boardid],
        "-k",
        "-p Factory"
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)
    p.expect2actu1(10, "ssh-dss", "")
    p.expect2actu1(10, "ssh-rsa", "")

    msg(30, "Do helper to get the output file to devreg server ...")
    log_debug("Erase existed eeprom information files ...")
    rtf = os.path.isfile(tftpdir + eeprom_bin)
    if rtf is True:
        log_debug("Erasing File - " + eeprom_bin + " ...")
        os.chmod(tftpdir + eeprom_bin, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir + eeprom_bin)
    else:
        log_debug("File - " + eeprom_bin + " doesn't exist ...")

    rtf = os.path.isfile(tftpdir + eeprom_txt)
    if rtf is True:
        log_debug("Erasing File - " + eeprom_txt + " ...")
        os.chmod(tftpdir + eeprom_txt, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir + eeprom_txt)
    else:
        log_debug("File - " + eeprom_txt + " doesn't exist ...")

    rtf = os.path.isfile(tftpdir + eeprom_signed)
    if rtf is True:
        log_debug("Erasing File - " + eeprom_signed + " ...")
        os.chmod(tftpdir + eeprom_signed, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir + eeprom_signed)
    else:
        log_debug("File - " + eeprom_signed + " doesn't exist ...")

    rtf = os.path.isfile(tftpdir + eeprom_check)
    if rtf is True:
        log_debug("Erasing File - " + eeprom_check + " ...")
        os.chmod(tftpdir + eeprom_check, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir + eeprom_check)
    else:
        log_debug("File - " + eeprom_check + " doesn't exist ...")

    rtf = os.path.isfile(tftpdir + eeprom_tgz)
    if rtf is True:
        log_debug("Erasing File - " + eeprom_tgz + " ...")
        os.chmod(tftpdir + eeprom_tgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.remove(tftpdir + eeprom_tgz)
    else:
        log_debug("File - " + eeprom_tgz + " doesn't exist ...")

    log_debug("Starting to do " + helperexe + "...")
    sstr = [
        tmpdir + helperexe,
        "-q",
        "-c product_class=basic",
        "-o field=flash_eeprom,format=binary,pathname=" + eeprom_bin,
        ">",
        eeprom_txt
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    sstr = [
        "tar",
        "cf",
        eeprom_tgz,
        eeprom_bin,
        eeprom_txt
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    os.mknod(tftpdir + eeprom_tgz)
    os.chmod(tftpdir + eeprom_tgz, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    log_debug("Send helper output tgz file from DUT to host ...")
    sstr = [
        "tftp",
        "-p",
        "-r " + eeprom_tgz,
        "-l " + eeprom_tgz,
        svip
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)
    time.sleep(2)

    cmd = "tar xvf " + tftpdir + eeprom_tgz + " -C " + tftpdir
    [sto, rtc] = fcd.common.xcmd(cmd)
    time.sleep(1)
    if int(rtc) > 0:
        error_critical("Decompressing " + eeprom_tgz + " file failed!!")
    else:
        log_debug("Decompressing " + eeprom_tgz + " files successfully")

    log_debug("Starting to do registration ...")
    cmd = [
        "cat " + tftpdir + eeprom_txt,
        "|",
        'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
        "|",
        'grep -v \"eeprom\"',
        "|",
        "tr '\\n' ' '"
    ]
    cmdj = ' '.join(cmd)
    [sto, rtc] = fcd.common.xcmd(cmdj)
    regsubparams = sto.decode('UTF-8')
    if int(rtc) > 0:
        error_critical("Extract parameters failed!!")
    else:
        log_debug("Extract parameters successfully")

    qrhex = qrcode.encode('utf-8').hex()

    regparam = [
        "-h devreg-prod.ubnt.com",
        "-k " + pshr,
        regsubparams,
        "-i field=qr_code,format=hex,value=" + qrhex,
        "-i field=flash_eeprom,format=binary,pathname=" + tftpdir + eeprom_bin,
        "-o field=flash_eeprom,format=binary,pathname=" + tftpdir + eeprom_signed,
        "-o field=registration_id",
        "-o field=result",
        "-o field=device_id",
        "-o field=registration_status_id",
        "-o field=registration_status_msg",
        "-o field=error_message",
        "-x " + keydir + "ca.pem",
        "-y " + keydir + "key.pem",
        "-z " + keydir + "crt.pem"
        ]

    regparamj = ' '.join(regparam)

    cmd = "sudo /usr/local/sbin/client_x86_release " + regparamj
    print("cmd: " + cmd)
    [sto, rtc] = fcd.common.xcmd(cmd)
    time.sleep(6)
    if int(rtc) > 0:
        error_critical("client_x86 registration failed!!")
    else:
        log_debug("Excuting client_x86 registration successfully")

    rtf = os.path.isfile(tftpdir + eeprom_signed)
    if rtf is not True:
        error_critical("Can't find " + eeprom_signed)

    msg(40, "Finish doing registration ...")
    log_debug("Send signed eeprom file from host to DUT ...")
    sstr = [
        "tftp",
        "-g",
        "-r " + eeprom_signed,
        "-l " + tmpdir + eeprom_signed,
        svip
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)
    time.sleep(2)

    log_debug("Change file permission - " + eeprom_signed + " ...")
    sstr = [
        "chmod 777",
        tmpdir + eeprom_signed
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    log_debug("Starting to write signed info to SPI flash ...")
    sstr = [
        tmpdir + helperexe,
        "-q",
        "-i field=flash_eeprom,format=binary,pathname=" + tmpdir + eeprom_signed
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)

    log_debug("Starting to extract the EEPROM content from SPI flash ...")
    sstr = [
        "dd",
        "if=" + mtdpart,
        "of=" + tmpdir + eeprom_check
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)
    time.sleep(1)

    os.mknod(tftpdir + eeprom_check)
    os.chmod(tftpdir + eeprom_check, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    log_debug("Send " + eeprom_check + " from DUT to host ...")
    sstr = [
        "tftp",
        "-p",
        "-r " + eeprom_check,
        "-l " + tmpdir + eeprom_check,
        svip
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)
    time.sleep(2)

    if os.path.isfile(tftpdir + eeprom_check):
        log_debug("Starting to compare the " + eeprom_check + " and " + eeprom_signed + " files ...")
        rtc = filecmp.cmp(tftpdir + eeprom_check, tftpdir + eeprom_signed)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")
    else:
        log_debug("Can't find the " + eeprom_check + " and " + eeprom_signed + " files ...")

    msg(50, "Finish doing signed file and EEPROM checking ...")

    sstr = [
        "tftp",
        "-g",
        "-r images/" + boardid + "-diag.bin",
        "-l " + tmpdir + "upgrade.bin",
        svip
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(120, lnxpmt, sstrj)
    p.expect2actu1(10, "", "")
    time.sleep(120)
    p.expect2actu1(10, "", "")

    sstr = [
        "tftp",
        "-g",
        "-r images/" + boardid + "-recovery",
        "-l " + tmpdir + "uImage.r",
        svip
    ]
    sstrj = ' '.join(sstr)
    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, sstrj)
    p.expect2actu1(10, "", "")
    time.sleep(60)
    p.expect2actu1(10, "", "")

    msg(80, "Succeeding in downloading the upgrade tarf file ...")
    p.expect2actu1(10, lnxpmt, "sh /usr/bin/ubnt-upgrade -d /tmp/upgrade.bin")
    p.expect2actu1(30, "Firmware version", "")
    p.expect2actu1(30, "Writing recovery", "")

    p.expect2actu1(100, "Calling CRDA to update world regulatory domain", "")
    p.expect2actu1(80, "login:", "root")
    p.expect2actu1(30, "Password:", "ubnt")

    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, "dmesg -n 1")
    p.expect2actu1(10, lnxpmt, "ifconfig eth0 "+prod_dev_ip)
    time.sleep(2)
    p.expect2actu1(10, lnxpmt, "ping "+svip)
    p.expect2actu1(10, "64 bytes from", '\003')

    p.expect2actu1(10, lnxpmt, "info")
    p.expect2actu1(10, "Version:", "")

    p.expect2actu1(10, "", "")
    p.expect2actu1(10, lnxpmt, "cat /proc/ubnthal/system.info")
    p.expect2actu1(10, "systemid="+boardid, "")

    if boardid == "na":
        p.expect2actu1(10, "", "")
        p.expect2actu1(10, lnxpmt, "modprobe rlt_wifi")
        p.expect2actu1(10, lnxpmt, "modprobe mt_wifi")
        p.expect2actu1(10, lnxpmt, "lsmod")
        p.expect2actu1(10, "mt_wifi", "")
        p.expect2actu1(10, "rlt_wifi", "")
        p.expect2actu1(10, lnxpmt, "ifconfig rai0 up")
        p.expect2actu1(10, lnxpmt, "ifconfig")
        p.expect2actu1(10, "rai0", "")

        p.expect2actu1(10, lnxpmt, "flash_erase /dev/mtd3 0x0 0x0")
        p.expect2actu1(10, "100 % complete", "")

        p.expect2actu1(10, lnxpmt, "hexdump /dev/mtd3 | head")
        p.expect2actu1(10, "0000000 ffff ffff ffff ffff ffff ffff ffff ffff", "")
        p.expect2actu1(10, "\*", "")
        p.expect2actu1(10, "0010000", "")

        p.expect2actu1(10, lnxpmt, "iwpriv rai0 set bufferLoadFromEfuse=1")
        time.sleep(0.5)
        p.expect2actu1(10, lnxpmt, "hexdump /dev/mtd3 | head")
        p.expect2actu1(10, "0000000 ffff ffff ffff ffff ffff ffff ffff ffff", "")
        p.expect2actu1(10, "\*", "")
        p.expect2actu1(10, "0010000", "")

        p.expect2actu1(10, lnxpmt, "iwpriv rai0 set ATE=ATESTART")
        time.sleep(0.5)
        p.expect2actu1(10, lnxpmt, "hexdump /dev/mtd3 | head")
        p.expect2actu1(10, "0000000 ffff ffff ffff ffff ffff ffff ffff ffff", "")
        p.expect2actu1(10, "\*", "")
        p.expect2actu1(10, "0010000", "")

        p.expect2actu1(10, lnxpmt, "iwpriv rai0 set ATE=RXFRAME")
        time.sleep(0.5)
        p.expect2actu1(10, lnxpmt, "hexdump /dev/mtd3 | head")
        p.expect2actu1(10, "0000000 ffff ffff ffff ffff ffff ffff ffff ffff", "")
        p.expect2actu1(10, "\*", "")
        p.expect2actu1(10, "0010000", "")

        p.expect2actu1(10, lnxpmt, "iwpriv rai0 set ATE=RXSELFTEST")
        time.sleep(2)
        p.expect2actu1(10, lnxpmt, "hexdump /dev/mtd3 | head")
        p.expect2actu1(10, "0000000 ffff ffff ffff ffff ffff ffff ffff ffff", "")
        p.expect2actu1(10, "\*", "")
        p.expect2actu1(10, "0008000 7615", "")

    msg(100, "Completing firmware upgrading ...")
    time.sleep(2)
    exit(0)


if __name__ == "__main__":
    main()


