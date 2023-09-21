#!/usr/bin/python3


SRV_IP = ""
SRV_PORT = ""
SRV_SHAREDOC = ""
SRV_USER = ""
SRV_PWD = ""
SYNC_PERIOD = ""

css = b"""
#pgrs_yellow {
    background-color: yellow;
}

#pgrs_green {
    background-color: #00FF00;
}

#pgrs_red {
    background-color: #FF0000;
}

#lbl_black {
    background-color: #D3D3D3;
    color: black;
    font-size: 15px;
}

#lbl_red {
    background-color: #D3D3D3;
    color: red;
    font-size: 15px;
}

#lbl_yellow {
    background-color: #D3D3D3;
    color: yellow;
    font-size: 15px;
}

#lbl_green {
    background-color: #D3D3D3;
    color: green;
    font-size: 15px;
}
"""

feature = ""
usbrootdir = ""
logdir = ""
keydir = ""
reportdir = ""
app_dir = "/usr/local/sbin/"

# Temporary log file
templogfile = [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]

keyfilenames = (
    "ca.pem",
    "crt.pem",
    "key.pem"
)

dftty = (
    "ttyUSB0",
    "ttyUSB1",
    "ttyUSB2",
    "ttyUSB3",
    "ttyUSB4",
    "ttyUSB5",
    "ttyUSB6",
    "ttyUSB7",
    "ttyACM0"
)

active_tty = []

finaltty = [
    "na",
    "na",
    "na",
    "na",
    "na",
    "na",
    "na",
    "na"
]

region_names = (
    "World",
    "USA/Canada (UI)",
    "Indonesia",
    "Israsel",
    "Japan",
    "Thailand",
    "Australia",
    "United Kingdom",
    "Canada"
)

# UI-defined region code
# 0x8100 + country code (HEX, ISO-3166)
# https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
region_codes = (
    '0000',    # World
    '002a',    # USA/Canada/FCC
    '8168',    # Indonesia
    '8178',    # Israsel
    '8188',    # Japan
    '82fc',    # Thailand
    '8124',    # Australia
    '843a',    # United kingdom
    '817c'     # Canada
)

country_codes = (
    '0',      # World
    '840',    # USA/Canada
    '360',    # Indonesia (HEX: 0x168)
    '376',    # Israsel  (HEX: 0x178)
    '392',    # Japan  (HEX: 0x188)
    '764',    # Thailand  (HEX: 0x2FC)
    '36',     # Australia  (HEX: 0x24)
    '826',    # United Kingdom  (HEX: 0x33A)
    '124'     # Canada (HEX: 0x7C)
)

unifi_region_codes = (
    '0000ffffffffffffffffffffffffffff',    # World
    '002affffffffffffffffffffffffffff',    # USA/Canada
    '8168ffffffffffffffffffffffffffff',    # Indonesia (HEX: 0x168)
    '8178ffffffffffffffffffffffffffff',    # Israsel  (HEX: 0x178)
    '8188ffffffffffffffffffffffffffff',    # Japan  (HEX: 0x188)
    '82fcffffffffffffffffffffffffffff',    # Thailand  (HEX: 0x2FC)
    '8124ffffffffffffffffffffffffffff',    # Australia  (HEX: 0x24)
    '843affffffffffffffffffffffffffff',    # United kingdom  (HEX: 0x33A)
    '817cffffffffffffffffffffffffffff'     # Canada  (HEX: 0x7C)
)

erasewifidata = [
    True,
    True,
    True,
    True,
    True,
    True,
    True,
    True
]

erase_devreg_data = [
    True,
    True,
    True,
    True,
    True,
    True,
    True,
    True
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
active_product_series = ""
