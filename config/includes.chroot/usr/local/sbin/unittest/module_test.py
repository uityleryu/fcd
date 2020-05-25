import glob
import importlib
import os
import sys
from nose import with_setup 

class TestFCDObjects:

    def __init__(self):
        print("TestFCDObjects:__init__()")

    @classmethod
    def setup_class(cls):
        print("TestFCDObjects:setup_class()")
        cls.files = glob.glob('*_*_*.py')
        cls.files.sort()
        #cls.shutup = open(os.devnull, 'w')
        cls.modules = []

        fake_input = "-pline=UniFiAP -pname=UAP-Building-Bridge -s=0 -d=ttyUSB0 -ts=192.168.1.19 -b=0000 -m=FCECDA77AEC3 -p='4w3IYmVMHKzj' -k=/media/usbdisk/keys/ -bom=00694-07 -q=yu5Fsu -r=0000 -ed=False -e=False"
        inputs = fake_input.split(' ')
        for item in inputs:
            sys.argv.append(item)

    @classmethod
    def teardown_class(cls):
        print ("TestFCDObjects:teardown_class()")

    def test_ImportFiles(cls):

        for script_file in cls.files:
            #print("Got module file " + mod_f)

            if script_file in sys.argv[0]:
                continue
    
            yield cls.check_file, script_file

    def check_file(cls, script_file):

        mod = importlib.import_module(script_file[:-3])
        
        cls.modules.append(mod)

    def test_Modules(cls):

        for mod in cls.modules:
            for item in dir(mod):
                if "Fact" in item or "MFG" in item:
                    print(" Found class " + item)

                    test_class = getattr(mod, item)

                    yield cls.check_class, test_class

    def check_class(cls, test_class):

        test_instance = test_class()
        
        test_instance = None
