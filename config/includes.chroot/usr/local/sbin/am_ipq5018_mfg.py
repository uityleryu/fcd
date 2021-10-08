#!/usr/bin/python3
from soc_lib.ipq5018 import IPQ5018MFGGeneral

class AMIPQ5018MFGGeneral(IPQ5018MFGGeneral):
    def __init__(self):
        super(AMIPQ5018MFGGeneral, self).__init__()

def main():
    am_ipq5018_mfg_general = AMIPQ5018MFGGeneral()
    am_ipq5018_mfg_general.run()

if __name__ == "__main__":
    main()
