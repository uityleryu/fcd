import glob
import importlib
import os
import sys

result = {}

if __name__ != "__main__":
    exit()

print("================================\nFind Python Scripts")
modules = glob.glob('*_*_*.py')
modules.sort()

shutup = open(os.devnull, 'w')

print("================================\nParsing Python Scripts")

for mod_f in modules:
    print("Got module file " + mod_f)

    if mod_f in sys.argv[0]:
        continue
    
    try:
        mod = importlib.import_module(mod_f[:-3])
    except Exception as err:
        print(type(err))
        print(err.args)
        print(err)

    for item in dir(mod):
        if "Fact" in item or "MFG" in item:
            print(" Found class " + item)

            test_class = getattr(mod, item)
            
            result.update({item: 'PASS'})

            try:
                sys.stdout = shutup
                test_instance = test_class()
                sys.stdout = sys.__stdout__
            except Exception as err:
                sys.stdout = sys.__stdout__
                print("  " + str(type(err)) )
                print(err.args)
                #print(err.args)
                #print(err)
                result.update({item: 'ERROR'})

        test_instance = None

#local_obj = locals()

#print("\n local_obj\n\n" + str(local_obj))

print("================================\nFinal Result")

for item in result:
    print(str(item)+ " " + result[item])


