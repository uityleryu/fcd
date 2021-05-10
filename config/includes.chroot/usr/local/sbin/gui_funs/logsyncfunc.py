
import re
import os
import data.constant as Constant
import time
import stat
import configparser
import tkinter as tk

from PAlib.FrameWork.fcd.common import Common
from threading import Thread


class LogsyncFunc(object):
    def __init__(self, root):
        self.root = root
        self.common = Common()
        self.thrd_sync = ""
        self.thrd_indicator = ""
        self.tftpdir = "/srv/tftp"
        self.srvdoc = os.path.join(self.tftpdir, "srvdoc")
        self.prodir = "/usr/local/sbin"
        self.usbpath = "/media/usbdisk"

        '''
            This file will be created by the /usr/local/sbin/prod-network.sh
        '''
        self.filedev = "devnet.txt"

        self.hostmac = self._host_mac()
        self.srvmacdir = os.path.join(self.srvdoc, self.hostmac)

    def connect_srv(self):
        if self.thrd_sync != "":
            print("sync thread is still alive")
            return False

        if self.thrd_indicator != "":
            print("flashing thread is still alive")
            return False

        if self.root.ety_srvip.get() == "":
            return False

        if self.root.ety_srvport.get() == "":
            return False

        if self.root.ety_sharedoc.get() == "":
            return False

        if self.root.ety_user.get() == "":
            return False

        if self.root.ety_pwd.get() == "":
            return False

        if self.root.ety_tperiod.get() == "":
            return False

        print("SRV_IP:" + Constant.SRV_IP)
        print("SRV_PORT:" + Constant.SRV_PORT)
        print("SRV_SHAREDOC:" + Constant.SRV_SHAREDOC)
        print("SRV_USER:" + Constant.SRV_USER)
        print("SRV_PWD:" + Constant.SRV_PWD)
        print("SYNC_PERIOD:" + Constant.SYNC_PERIOD)

        #cmd = "ping -c 1 {0}".format(Constant.SRV_IP)
        #[rtmsg, rtc] = self.common.xcmd(cmd)
        #if rtc == 0:
        #    match = re.findall("64 bytes from", rtmsg)
        #    if match:
        #        print("Find the server")
        #    else:
        #        print("Can't ping the server")
        #        exit(1)
        #else:
        #    print("Command executed failed")
        #    exit(1)

        if os.path.isdir(self.srvdoc) is True:
            print(self.srvdoc + " is existed")
        else:
            print(self.srvdoc + " is not existed")
            os.mkdir(self.srvdoc)
            os.chmod(self.srvdoc, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        cmd = "mount -v | grep {0}".format(self.srvdoc)
        [rtmsg, rtc] = self.common.xcmd(cmd)
        '''
            If the grep command parse desired patter, it will return 0
            otherwise, will return > 0
        '''
        if rtc > 0:
            print("Network disk hasn't been mounted, starting mounting ...")
            cmdlist = []
            cmd = "mount -t cifs //{0}/{1} {2} -o username={3},password={4},vers=3.0".format(
                Constant.SRV_IP, Constant.SRV_SHAREDOC, self.srvdoc, Constant.SRV_USER, Constant.SRV_PWD)
            cmdlist.append(cmd)
            if Constant.SRV_PORT != "":
                option = ",port={}".format(Constant.SRV_PORT)
                cmdlist.append(option)

            cmd = ''.join(cmdlist)
            print("CMD: " + cmd)
            [rtmsg, rtc] = self.common.xcmd(cmd)
        else:
            print("Network disk has been mounted")

        self.thrd_sync = Thread(target=self._sync)
        self.thrd_sync.setDaemon(True)
        self.thrd_sync.start()

        time.sleep(1)
        self.thrd_indicator = Thread(target=self._link_flashing)
        self.thrd_indicator.setDaemon(True)
        self.thrd_indicator.start()

    def load_config(self):
        filepath = self.root._open_file()
        if os.path.isfile(filepath) is True:
            print(filepath + " is existed")
            self.config = configparser.ConfigParser()
            self.config.read(filepath)
            self.root.strv_srvip.set(self.config['SERVER']['SRVIP'])
            self.root.strv_srvport.set(self.config['SERVER']['SRVPORT'])
            self.root.strv_sharedoc.set(self.config['SERVER']['SRVDOC'])
            self.root.strv_user.set(self.config['SERVER']['SRVUSER'])
            self.root.strv_pwd.set(self.config['SERVER']['SRVPWD'])
            self.root.strv_tperiod.set(self.config['SERVER']['TPERIOD'])

            Constant.SRV_IP = self.root.ety_srvip.get()
            Constant.SRV_PORT = self.root.ety_srvport.get()
            Constant.SRV_SHAREDOC = self.root.ety_sharedoc.get()
            Constant.SRV_USER = self.root.ety_user.get()
            Constant.SRV_PWD = self.root.ety_pwd.get()
            Constant.SYNC_PERIOD = self.root.ety_tperiod.get()
        else:
            print(filepath + " is not existed")

    def _host_mac(self):
        hostmac = ""
        fpath = os.path.join(self.prodir, self.filedev)
        f = open(fpath, 'r')
        for idx in range(2):
            line = f.readline()
            match = re.findall("external", line)
            if match:
                f.close()
                break

        temp = line.split(" ")
        devnet = temp[1].strip()
        cmd = "ifconfig | grep -A 3 {0} | grep ether".format(devnet)
        print("cmd: " + cmd)
        [rtmsg, rtc] = self.common.xcmd(cmd)
        '''
            If the grep command parse desired patter, it will return 0
            otherwise, will return > 0
        '''
        if rtc > 0:
            print("Can't find the FCD host MAC address")
            exit(1)
        else:
            temp = rtmsg.split()
            hostmac = temp[1].replace(":", "-")
            print("Host MAC: " + hostmac)

        return hostmac

    def stop_sync(self):
        # self.root.btn_stop.configure(state=tk.DISABLED)
        self.root.scl_log.insert(tk.END, " It may take a few seconds, please wait until stop ready ... ")
        filepath = os.path.join(self.tftpdir, "stopsync.txt")
        print("filepath: " + filepath)
        f = open(filepath, 'w')
        f.write("stop")
        f.close()
        os.chmod(filepath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def _sync(self):
        self.root.btn_connect.configure(state=tk.DISABLED)
        filepath = os.path.join(self.tftpdir, "stopsync.txt")
        if os.path.isfile(filepath):
            os.remove(filepath)

        cmd = "ls -la {0} | grep {1}".format(self.srvdoc, self.hostmac)
        [rtmsg, rtc] = self.common.xcmd(cmd)
        '''
            If the grep command parse desired patter, it will return 0
            otherwise, will return > 0
        '''
        if rtc > 0:
            print(self.srvmacdir + " is not existed")
            os.mkdir(self.srvmacdir)
            os.chmod(self.srvmacdir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        else:
            print(self.srvmacdir + " is existed")

        reglogpath = os.path.join(self.usbpath, "reg_logs")
        if os.path.isdir(reglogpath) is False:
            print(reglogpath + " is not existed")
            exit(1)
        else:
            print(reglogpath + " is existed")

        self.root.scl_log.delete(1.0, tk.END)

        while True:
            self.root.scl_log.insert(tk.END, " === Sync starting === ")
            cmd = "rsync -av --ignore-existing {0} {1}".format(reglogpath, self.srvmacdir)
            [rtmsg, rtc] = self.common.xcmd(cmd)
            if rtc == 0:
                self.root.scl_log.insert(tk.END, rtmsg)
                self.root.scl_log.insert(tk.END, "\n\n")
            else:
                print("Command executed failed, do next time ... ")

            time.sleep(int(Constant.SYNC_PERIOD))
            if os.path.isfile("/tftpboot/stopsync.txt") is True:
                self.root.scl_log.insert(tk.END, " === Stop ===")
                # self.root.btn_stop.configure(state=tk.NORMAL)
                self.root.btn_connect.configure(state=tk.NORMAL)
                break

        self.thrd_sync = ""

    def _link_flashing(self):
        while True:
            self.root.btn_connect.config(background='lawn green')
            time.sleep(2)
            self.root.btn_connect.config(background='snow')
            time.sleep(2)

            if self.thrd_sync.isAlive() is False:
                break

            if os.path.isfile("/tftpboot/stopsync.txt") is True:
                self.root.btn_connect.config(background='peach puff')
                break

        self.thrd_indicator = ""
