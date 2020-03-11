#!/usr/bin/python3

from soc_lib.ipq40xx import IPQ40XXFactory

class AMIPQ40XXFactory(IPQ40XXFactory):
    def __init__(self):
        super(AMIPQ40XXFactory, self).__init__()

    def run(self):
        self.airos_run()

def main():
    am_ipq840xx_factory = AMIPQ40XXFactory()
    am_ipq840xx_factory.run()

if __name__ == "__main__":
    main()
