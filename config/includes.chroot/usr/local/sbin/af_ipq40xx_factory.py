#!/usr/bin/python3

from soc_lib.ipq40xx import IPQ40XXFactory

class AFIPQ40XXFactory(IPQ40XXFactory):
    def __init__(self):
        super(AFIPQ40XXFactory, self).__init__()

    def run(self):
        self.airos_run()

def main():
    af_ipq840xx_factory = AFIPQ40XXFactory()
    af_ipq840xx_factory.run()

if __name__ == "__main__":
    main()
