#!/usr/bin/python3

from soc_lib.ls104x_lib import LS104XMFG

class UAPLS104XMFG(LS104XMFG):
    def __init__(self):
        super(UAPLS104XMFG, self).__init__()

def main():
    uap_ls104x_mfg = UAPLS104XMFG()
    uap_ls104x_mfg.run()

if __name__ == "__main__":
    main()
