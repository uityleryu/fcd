#!/usr/bin/python3

from soc_lib.ipq40xx import IPQ40XXMFG

class AFIPQ40XXMFG(IPQ40XXMFG):
    def __init__(self):
        super(AFIPQ40XXMFG, self).__init__()

def main():
    af_ipq840xx_mfg = AFIPQ40XXMFG()
    af_ipq840xx_mfg.run()

if __name__ == "__main__":
    main()
