#!/usr/bin/python3

from soc_lib.ipq40xx import IPQ40XXMFG

class AMIPQ40XXMFG(IPQ40XXMFG):
    def __init__(self):
        super(AMIPQ40XXMFG, self).__init__()

def main():
    am_ipq840xx_mfg = AMIPQ40XXMFG()
    am_ipq840xx_mfg.run()

if __name__ == "__main__":
    main()
