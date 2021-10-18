#!/usr/bin/python3
from soc_lib.ipq5018 import IPQ5018BSPFactory

class AFIPQ5018BspFactory(IPQ5018BSPFactory):
    def __init__(self):
        super(AFIPQ5018BspFactory, self).__init__()
        self.init_vars()

def main():
    afipq5018_bspfactory = AFIPQ5018BspFactory()
    afipq5018_bspfactory.run()

if __name__ == "__main__":
    main()
