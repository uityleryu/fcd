#!/usr/bin/python3

from soc_lib.ls104x_lib import LS104XFactory

class AFLS104XFactory(LS104XFactory):
    def __init__(self):
        super(AFLS104XFactory, self).__init__()

    def run(self):
        self.airos_run()

def main():
    af_ls104x_factory = AFLS104XFactory()
    af_ls104x_factory.run()

if __name__ == "__main__":
    main()
