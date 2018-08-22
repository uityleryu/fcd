#!/usr/bin/env python

import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--mac', nargs='+', help='mac address', required=True)
parser.add_argument('--boardid', nargs='+', help='board id', required=True)
parser.add_argument('--bomid', nargs='+', help='bom id', required=True)
parser.add_argument('--bomrev', nargs='+', help='bom rev', required=True)
parser.add_argument('--region', nargs='+', help='world/fcc', required=True)

eeprom = bytearray()

for i in range(0, 64*1024):
    eeprom.append(0xFF)

args = parser.parse_args()

# set MAC addresses
mac = args.mac[0].decode('hex')
for i in range(0, 6):
    eeprom[i] = mac[i]
    eeprom[i+6] = mac[i]

if eeprom[11] + 1 <= 0xFF:
    eeprom[11] = eeprom[11] + 1
else:
    eeprom[11] = 0
    if eeprom[10] + 1 <= 0xFF:
        eeprom[10] = eeprom[10] + 1
    else:
        eeprom[10] = 0
        eeprom[9] = eeprom[9] + 1

# set board ID
boardid = args.boardid[0].decode('hex')
for i in range(0, 2):
    eeprom[i+12] = boardid[i]

# set vendor ID
eeprom[i+13] = '\x07'
eeprom[i+14] = '\x77'

# set bom ID
bomid = int(args.bomid[0])
eeprom[i+15] = (bomid>>16)&0xFF
eeprom[i+16] = (bomid>>8)&0xFF
eeprom[i+17] = (bomid>>0)&0xFF

# set bom revision
bomrev = int(args.bomrev[0])
eeprom[i+18] = bomrev&0xFF

# set region
region=1
if args.region[0] == "fcc":
    region=2
eeprom[0x1000] = region

sys.stdout.write(eeprom)
sys.stdout.flush()
