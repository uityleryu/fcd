#!/usr/bin/python3

from soc_lib.ipq80xx import IPQ80XXMFG

class AFIPQ80XXMFG(IPQ80XXMFG):
    def __init__(self):
        super(AFIPQ80XXMFG, self).__init__()

def main():
    af_ipq80xx_mfg = AFIPQ80XXMFG()
    af_ipq80xx_mfg.run()

if __name__ == "__main__":
    main()
