
import os
import argparse
import shutil
import json
import subprocess


class UIpopen(object):
    def __init__(self):
        pass

    """
        If timeout is None, the process will non-stop when the command keeps running.
        So, give a default 10 seconds to timeout
    """
    def xcmd(self, cmd, timeout=None, rtmsg=True, retry=3):
        for i in range(0, retry+1):
            try:
                if sys.platform.startswith('win32'):
                    proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                else:
                    proc = subprocess.Popen([cmd], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

                """
                    Python offical website statements:
                    deadlock when using stdout=PIPE and/or stderr=PIPE and the child process generates enough output to
                    a pipe such that it blocks waiting for the OS pipe buffer to accept more data.
                    Use communicate() to avoid that.
                """
                locd = locale.getdefaultlocale()

                if timeout is not None:
                    buf = proc.communicate(timeout=timeout)[0].decode(locd[1]).strip()
                else:
                    buf = proc.communicate()[0].decode(locd[1]).strip()

                print("coding format: " + locd[1])
                print(buf)
            except Exception as e:
                if i < retry:
                    print("xcmd Retry {}".format(i+1))
                    time.sleep(0.2)
                    continue
                else:
                    print("Exceeded maximum retry times {}".format(i))
                    raise e
            else:
                break

        if rtmsg is True:
            return [buf, proc.returncode]
        else:
            if proc.returncode != 0:
                return False
            else:
                return True


'''
    Product series definition
'''
airmax_ac_series = [
    "00492_e3d6", "00406_e7e5", "00513_e7e6", "00526_e7e7", "00546_e7e8", "00497_e7f9",
    "00552_e7fa", "00556_e7fc", "00569_e4f3", "00962_e7ff"
]


'''
   Main Function
'''
cwd_dir = os.getcwd()

cn = UIpopen()
parse = argparse.ArgumentParser(description="Generating product json file")
parse.add_argument('--prodline', '-p', dest='prodline', help='Product Line', default=None)
parse.add_argument('--model', '-m', dest='model', help='Model', default=None)
args, _ = parse.parse_known_args()

if args.prodline is None:
    print("Please give a product line")
    exit(1)
else:
    pl = args.prodline
    print("Product line: " + pl)

if args.model is None:
    print("Please provide the models")
    exit(1)
else:
    mdl = args.model
    print("Model: " + mdl)
    if mdl == "AC-SERIES":
        model_list = airmax_ac_series
    else:
        print("Build singel model")

def main():
    target_dir = os.path.join(cwd_dir, pl)
    print("Target dir: " + target_dir)

    thk = {}
    thk[pl] = {}
    kidx = 0
    for i in model_list:
        xpd = "pd_{}.json".format(i.lower())
        target = os.path.join(target_dir, xpd)
        if os.path.isfile(target):
            print("product: " + target)
            fh = open(target)
            pjson = json.load(fh)
            fh.close()
            for pn in pjson[pl].keys():
                thk[pl][pn] = pjson[pl][pn]
                thk[pl][pn]['INDEX'] = kidx

        kidx += 1

    output = json.dumps(thk, indent=2)

    # Ex: /home/vjc/malon/uifcd1/config/includes.chroot/usr/local/sbin/prod_json/airMAX/pd_AC-SERIES.json
    pd_series_name = "pd_{}.json".format(mdl)
    src = os.path.join(cwd_dir, pl, pd_series_name)
    ft = open(src, 'w')
    ft.write(output)
    ft.close()
    print(output)


if __name__ == "__main__":
    main()
