#!/usr/bin/python3
from soc_lib.ipq5018 import IPQ5018BSPFactory

class AMIPQ5018BspFactory(IPQ5018BSPFactory):
    def __init__(self):
        super(AMIPQ5018BspFactory, self).__init__()
        self.init_vars()

def main():
    amipq5018_bspfactory = AMIPQ5018BspFactory()
    amipq5018_bspfactory.run()

if __name__ == "__main__":
    main()
