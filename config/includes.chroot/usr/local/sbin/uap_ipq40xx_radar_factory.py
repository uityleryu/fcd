#!/usr/bin/python3

from ipq40xx_radar import IPQ40XXFactory

class UAPIPQ40XXFactory(IPQ40XXFactory):
    def __init__(self):
        super(UAPIPQ40XXFactory, self).__init__()

    def run(self):
        self.airos_run()

def main():
    uap_ipq840xx_factory = UAPIPQ40XXFactory()
    uap_ipq840xx_factory.run()

if __name__ == "__main__":
    main()
