#!/usr/bin/python3
try:
    from soc_lib.ipq40xx import IPQ40XXFactory
except Exception as err:
    print(type(err))
    print(err.args)
    print(err)  

class UAPIPQ40XXFactory(IPQ40XXFactory):
    def __init__(self):
        super(UAPIPQ40XXFactory, self).__init__()

    def run(self):
        self.airos_run()

def main():
    uap_ipq840xx_factory = UAPIPQ40XXFactory()

if __name__ == "__main__":

    try:
        main()
    except Exception as err:
        print(type(err))
        print(err.args)
        print(err)
        exit(-1)

    local_obj = locals()

    print("\n local_obj\n\n" + str(local_obj))

    print("\n dir UAPIPQ40XXFactory\n\n" + str(dir(local_obj['UAPIPQ40XXFactory'])))

    print("\n vars UAPIPQ40XXFactory\n\n" + str(vars(local_obj['UAPIPQ40XXFactory'])))

    print("\n keys UAPIPQ40XXFactory\n\n" + str(local_obj['UAPIPQ40XXFactory'].__dict__))

    
    print("\n dir IPQ40XXFactory\n\n" + str(dir(local_obj['IPQ40XXFactory'])))

    print("\n vars IPQ40XXFactory\n\n" + str(vars(local_obj['IPQ40XXFactory'])))

    print("\n keys IPQ40XXFactory\n\n" + str(local_obj['IPQ40XXFactory'].__dict__))

