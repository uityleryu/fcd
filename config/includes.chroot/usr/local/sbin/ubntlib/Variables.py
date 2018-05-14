#!/usr/bin/python3.6

class GPath:
    logdir = ""
    keydir = ""
    reportdir = ""
    templogfile = ""

class GCommon:
    keyfilenames = ["ca.pem", "crt.pem", "key.pem"]
    dftty = ["ttyUSB0", "ttyUSB1", "ttyUSB2", "ttyUSB3"]
    active_tty = []
    region_names = ["World", "USA/Canada", "Thailand", "Israsel"]
    active_bomrev = ""
    active_region = ""
    active_passphrase = ""
    active_product = ""
    active_productidx = ""
    barcode = ""
    barcodelen = 0
    macaddr = ""
    macaddrlen = 12
    qrcode = ""
    qrcodelen = 6
    devregready = False


def main():
    print("Joe: report dir: "+GPath.reportdir)

if __name__ == "__main__":
    main()