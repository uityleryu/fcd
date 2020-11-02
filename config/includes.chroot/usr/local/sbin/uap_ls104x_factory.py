#!/usr/bin/python3

from soc_lib.ls104x_lib import LS104XFactory

class UAPLS104XFactory(LS104XFactory):
    def __init__(self):
        super(UAPLS104XFactory, self).__init__()

    def run(self):
        self.airos_run()

def main():
    uap_ls104x_factory = UAPLS104XFactory()
    uap_ls104x_factory.run()

if __name__ == "__main__":
    main()
