#!/usr/bin/python3
from soc_lib.ipq5018 import IPQ5018MFGGeneral

class AFIPQ5018MFGGeneral(IPQ5018MFGGeneral):
    def __init__(self):
        super(AFIPQ5018MFGGeneral, self).__init__()

def main():
    af_ipq5018_mfg_general = AFIPQ5018MFGGeneral()
    af_ipq5018_mfg_general.run()

if __name__ == "__main__":
    main()
