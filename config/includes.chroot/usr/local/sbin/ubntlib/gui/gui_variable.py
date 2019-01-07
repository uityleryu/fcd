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
        "Japan"
    ]
    region_codes = [
        '0000',
        '002a',
        '82fc',
        '8178',
        '8188'
    ]
    country_codes = [
        '0',
        '840',
        '764',
        '376',
        '392'
    ]
    unifi_region_codes = [
        '0000ffffffffffffffffffffffffffff',
        '002affffffffffffffffffffffffffff',
        '82fcffffffffffffffffffffffffffff',
        '8178ffffffffffffffffffffffffffff',
        '8188ffffffffffffffffffffffffffff'
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
