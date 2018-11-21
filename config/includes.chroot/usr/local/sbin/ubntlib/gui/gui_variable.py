#!/usr/bin/python3


class GPath(object):
    logdir = ""
    keydir = ""
    reportdir = ""

    # Temporary log file
    templogfile = [
        "",
        "",
        "",
        ""
    ]


class GCommon(object):
    keyfilenames = [
        "ca.pem",
        "crt.pem",
        "key.pem"
    ]
    dftty = [
        "ttyUSB0",
        "ttyUSB1",
        "ttyUSB2",
        "ttyUSB3"
    ]
    active_tty = []
    finaltty = [
        "na",
        "na",
        "na",
        "na"
    ]
    region_names = [
        "World",
        "USA/Canada",
        "Thailand",
        "Israsel",
        "Fcc"
    ]
    region_codes = [
        '0000',
        '002a',
        '82fc',
        '8178',
        '0002'
    ]
    erasewifidata = [
        False,
        False,
        False,
        False
    ]
    fcdhostip = "192.168.1.19"
    hostipsetenable = False
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


def main():
    pass

if __name__ == "__main__":
    main()
