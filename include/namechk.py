

import sys
import re


def main():
    '''
        Good example:
        FCD_US_US-24-PRO_3.2.5_5.0.55-rc2
    '''
    fw_filename = sys.argv[1]
    print("filename: " + fw_filename)

    naming_rule_re = re.compile(
        r'^FCD_([A-Za-z0-9\-]+)\_([A-Za-z0-9\-]+)\_'
        r'(?P<FCD_major>0|[1-9]\d*)\.(?P<FCD_minor>0|[1-9]\d*)\.(?P<FCD_patch>0|[1-9]\d*)(?:-'
        r'(?P<FCD_prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+'
        r'(?P<FCD_buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\_'
        r'(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-'
        r'(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+'
        r'(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?')

    result = naming_rule_re.findall(fw_filename)

    if len(result) < 1 or len(result[0]) < 11:
        print("======================================") 
        print("  Version format is invalid !!! ")
        print("======================================") 
        exit(1)

    print("======================================")  
    print("  Product Line: {}".format(result[0][0]))
    print("  Model name: {}".format(result[0][1]))

    if result[0][5] == '':
        fcdmsg = "  FCD version: {}.{}.{}".format(result[0][2], result[0][3], result[0][4])
    else:
        fcdmsg = "  FCD version: {}.{}.{}-{}".format(result[0][2], result[0][3], result[0][4], result[0][5])

    print(fcdmsg)

    if result[0][10] == '':
        fwmsg = "  FW version: {}.{}.{}".format(result[0][7], result[0][8], result[0][9])
    else:
        fwmsg = "  FW version: {}.{}.{}-{}".format(result[0][7], result[0][8], result[0][9], result[0][10])

    print(fwmsg)
    print("======================================")
    exit(0)

if __name__ == "__main__":
    main()
