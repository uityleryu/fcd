#!/usr/bin/python3

from soc_lib.ipq80xx import IPQ80XXFactory

class AFIPQ80XXFactory(IPQ80XXFactory):
    def __init__(self):
        super(AFIPQ80XXFactory, self).__init__()

    def run(self):
        self.airos_run()

def main():
    af_ipq80xx_factory = AFIPQ80XXFactory()
    af_ipq80xx_factory.run()

if __name__ == "__main__":
    main()
