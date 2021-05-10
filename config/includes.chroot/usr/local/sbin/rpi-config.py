#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import argparse

from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.common import Common
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical


class FCDhostConfig():
    def __init__(self):
        super(FCDhostConfig, self).__init__()
        # self.input_args = self._init_parse_inputs()
        self.DHCPOUT = "/tmp/dhcp_out.txt"
        self.WGETOUT = "/tmp/wget_out.txt"
        self.test_url = "http://www.baidu.com/"
        self.host_ip = "192.168.1.19"
        self.cur_intf = []
        self.comn = Common()

    def init(self):
        self.untar_tools()
        if os.path.isfile("/tmp/prod-setup.done") is True:
            log_debug("Nothing to do - everything is already done.")
            exit(0)

        self.kill_dhclient_proc()
        rt = self.net_interface_check()
        if rt is True:
            self.dhclient_reg_net(dhtime=60, wgettime=15, iface="eth1")

        self.set_product_net("eth0")
        self.activate_server()

    def untar_tools(self):
        if os.path.isfile("/tftpboot/tools/tools.tar") is True:
            log_debug("Unzipping the tools.tar to /tftpboot/tools")
            cmd = "cd /tftpboot/tools; tar -xvzf /tftpboot/tools/tools.tar"
            [sto, rtc] = self.comn.xcmd(cmd)
            if rtc < 0:
                error_critical("decompress tools.tar failed !!!")
        else:
            error_critical("Can't find tools.tar !!!")

    def kill_dhclient_proc(self):
        cmd = "sudo killall -9 dhclient >/dev/null 2>&1"
        [sto, rtc] = self.comn.xcmd(cmd)
        if rtc < 0:
            error_critical("Kill dhclient failed !!!")

    def net_interface_check(self):
        cmd = "ifconfig"
        rmsg = "Current active networking interface\nand current IP address before dhclient"
        log_debug(rmsg)
        [sto, rtc] = self.comn.xcmd(cmd)
        if "wlan0" in sto:
            cmd = "ifconfig wlan0 down"
            [sto, rtc] = self.comn.xcmd(cmd)
            if rtc < 0:
                error_critical("Stop wlan0 failed !!!")

        log_debug("Current existed networking interface")
        cmd = "grep \":\" /proc/net/dev | awk -F: '{print $1}' | grep -v lo | grep -v wlan0"
        [sto, rtc] = self.comn.xcmd(cmd)
        if rtc < 0:
            error_critical("Can't check the networking interface !!!")
        else:
            sto = sto.strip()
            sto = sto.split("\n")
            log_debug("Current number of existed intf: " + str(len(sto)))
            if len(sto) < 2:
                error_critical("Should be at least two networking interface")
            else:
                self.cur_intf = ''.join(sto)
                log_debug("Current targeted intf: " + self.cur_intf)
                return True

    def dhclient_reg_net(self, dhtime, wgettime, iface):
        cmd = "ip addr flush dev {0}".format(iface)
        [sto, rtc] = self.comn.xcmd(cmd)

        cmd = "sudo timeout {0} dhclient {1} >/dev/null 2>{2}".format(dhtime, iface, self.DHCPOUT)
        [sto, dhclient_rtc] = self.comn.xcmd(cmd)
        if dhclient_rtc == 0:
            cmd = "timeout {0} wget -q -O {1} {2} >/dev/null 2>&1".format(wgettime, self.WGETOUT, self.test_url)
            [sto, wget_rtc] = self.comn.xcmd(cmd)
            if wget_rtc == 0:
                cmd = "ifconfig"
                [sto, rtc] = self.comn.xcmd(cmd)
                match = re.findall("192.168.1.", sto, re.S)
                if match:
                    error_critical("The external IP adrees is incorrect")
                else:
                    log_debug("External IP address: " + sto)
            else:
                rmsg = "Fail to wget over {0}".format(wgettime)
                error_critical(rmsg)
        else:
            rmsg = "Failed to dhclient for {0} over {1}".format(iface, dhtime)
            error_critical(rmsg)

    def set_product_net(self, iface):
        cmd = "ip addr flush dev {0}".format(iface)
        [sto, rtc] = self.comn.xcmd(cmd)
        cmd = "ip addr add {0}/24 dev {1}".format(self.host_ip, iface)
        [sto, rtc] = self.comn.xcmd(cmd)
        cmd = "ifconfig {0} up".format(iface)
        [sto, rtc] = self.comn.xcmd(cmd)
        cmd = "ifconfig {0}:0 169.254.1.19/16".format(iface)
        [sto, rtc] = self.comn.xcmd(cmd)
        cmd = "ifconfig"
        [sto, rtc] = self.comn.xcmd(cmd)

    def activate_server(self):
        cmd = "/etc/init.d/atftpd restart"
        [sto, rtc] = self.comn.xcmd(cmd)
        if rtc < 0:
            rmsg = "Failed to start TFTP server"
            error_critical(rmsg)

    def usage(self):
        print("Usage of this command:")

    # def _init_parse_inputs(self):
    #     parse = argparse.ArgumentParser(description="FCD configuration args Parser")
    #     parse.add_argument('--initcfg', '-ic', dest='initconfig', help='configuring FCD host', default=None)

    #     args, _ = parse.parse_known_args()
    #     self.init_config = args.initconfig

    #     return args

    # def run(self):
    #     pass


def main():
    config = FCDhostConfig()
    # config.run()
    if sys.argv[1] == "init":
        config.init()
    elif sys.argv[1] == "checknet":
        config.net_interface_check()
    elif sys.argv[1] == "setprodnet":
        config.set_product_net("eth0")
    elif sys.argv[1] == "dhregnet":
        config.dhclient_reg_net("eth1")
    elif sys.argv[1] == "":
        config.usgae()
    else:
        print("Not support !!!")


if __name__ == "__main__":
    main()
