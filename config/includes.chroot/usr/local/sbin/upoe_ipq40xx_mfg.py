#!/usr/bin/python3
from soc_lib.ipq40xxbsp import IPQ40XXMFGGeneral

class UPOEIPQ40XXMFGGeneral(IPQ40XXMFGGeneral):
    def __init__(self):
        super(UPOEIPQ40XXMFGGeneral, self).__init__()

def main():
    upoe_ipq40xx_mfg_general = UPOEIPQ40XXMFGGeneral()
    upoe_ipq40xx_mfg_general.run()

if __name__ == "__main__":
    main()
