#!/usr/bin/python3
from soc_lib.ipq40xxbsp import IPQ40XXBSPFactory

class UPOEIPQ40XXFactory(IPQ40XXBSPFactory):
    def __init__(self):
        super(UPOEIPQ40XXFactory, self).__init__()
        self.init_vars()

def main():
    upoe_ipq40xx_factory = UPOEIPQ40XXFactory()
    upoe_ipq40xx_factory.run()

if __name__ == "__main__":
    main()
