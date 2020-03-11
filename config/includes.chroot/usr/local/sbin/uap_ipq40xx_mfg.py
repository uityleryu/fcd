#!/usr/bin/python3

from soc_lib.ipq40xx import IPQ40XXMFG

class UAPIPQ40XXMFG(IPQ40XXMFG):
    def __init__(self):
        super(UAPIPQ40XXMFG, self).__init__()

def main():
    uap_ipq840xx_mfg = UAPIPQ40XXMFG()
    uap_ipq840xx_mfg.run()

if __name__ == "__main__":
    main()
