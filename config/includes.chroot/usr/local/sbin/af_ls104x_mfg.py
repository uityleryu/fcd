#!/usr/bin/python3

from soc_lib.ls104x_lib import LS104XMFG

class AFLS104XMFG(LS104XMFG):
    def __init__(self):
        super(AFLS104XMFG, self).__init__()

def main():
    af_ls104x_mfg = AFLS104XMFG()
    af_ls104x_mfg.run()

if __name__ == "__main__":
    main()
