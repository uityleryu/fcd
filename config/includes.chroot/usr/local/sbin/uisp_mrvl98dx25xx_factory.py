from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import os
import time

class UispMrvl98Dx25xx(ScriptBase):
    def __init__(self):
        super(UispMrvl98Dx25xx, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ver_extract()
        self.devregpart = "/dev/mtdblock3"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "Marvell>>"
        self.fwimg = self.board_id + "-fw.bin"
        self.imageName = 'uisp-s-plus_256.ubi'
        self.devregDebug = 'devreg_MRVL_ACT5_debug'

        # number of Ethernet
        self.macnum = {
            'ee7c': "10"
        }

        # number of WiFi
        self.wifinum = {
            'ee7c': "0"
        }

        # number of Bluetooth
        self.btnum = {
            'ee7c': "1"
        }

        self.netif = {
            'ee7c': "ifconfig eth1 "
        }

        devregpart = {
            'ee7c': "/dev/mtdblock3"
        }

        helper_path = {
            'ee7c': "uisp_s_plus",

        }

        helperexe = {
            'ee7c': "helper_MRVL_ACT5_release",
        }

        self.devregpart = devregpart[self.board_id]
        self.helper_path = helper_path[self.board_id]
        self.helperexe = helperexe[self.board_id]
        self.netif = self.netif[self.board_id]

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

    def stop_uboot(self, uappinit_en=False):
        log_debug("Stopping U-boot")
        self.pexp.expect_action(90, "Hit any key to stop autoboot", "\x1b")

    def is_network_alive_in_linux(self, ipaddr=None, retry=5):
        if ipaddr is None:
            ipaddr = self.tftp_server

        cmd = "ifconfig; ping -c 3 {0}".format(ipaddr)
        exp = r"64 bytes from {0}".format(ipaddr)
        ping_retry_cnt = 0
        
        while ping_retry_cnt < 2:
            try:
                self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=exp, retry=retry)
                log_debug('ping is successful, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -n')
                break
            except:
                log_error('ping is failed, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -n')
                ping_retry_cnt += 1
        else:
            error_critical('ping is failed in linux kernel, after {} retries.'.format(retry * (ping_retry_cnt)))

    def setEnv(self):
        cmd = [
            'set bootdelay 3',
            'set ethaddr; set ipaddr {} && set serverip {}'.format(self.dutip, self.tftp_server),
            'set mtdids nand0=nand0 && set mtdparts mtdparts=nand0:255M@0x0(ubi0)',
            'set kernel_addr_r 0x209000000; set image_name {}'.format(self.imageName),
            "set KERNEL_UPDATE_N 'usb start && tftpboot $kernel_addr_r $image_name && nand erase.chip && nand erase 0x0 0x3c00000 && nand write $kernel_addr_r 0x0 $filesize'",
            "set get_images_nand 'ubi part ubi0 && ubi read $kernel_addr_r kernel'",
            "set console 'console=ttyS0,115200 earlycon=uart8250,mmio32,0x7f012000'",
            "set set_bootargs 'setenv bootargs $console $root $cpuidle'",
            "set bootcmd 'run get_images_nand && run set_bootargs && bootm $kernel_addr_r'"
        ]

        for i in cmd:
          self.pexp.expect_ubcmd(30, self.bootloader_prompt, i)

        self.pexp.expect_ubcmd(70, self.bootloader_prompt, "saveenv")

    def upgradeToDiag(self):
        self.pexp.expect_ubcmd(70, self.bootloader_prompt, "run KERNEL_UPDATE_N", post_exp='OK')
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "boot")

    def createSymLink(self):
        fwpath = '/tftpboot/{}'.format(self.imageName)
        if not self.isExist(fwpath):
          self._createSymLink(src='/tftpboot/images/{}'.format(self.fwimg), dst='/tftpboot/{}'.format(self.imageName))
        if not self.isExist(fwpath):
          error_critical('Can not get FW: "{}"'.format(self.imageName))

    def _createSymLink(self, src, dst):
        log_debug('Create softlink, src = "{}", dst = "{}"'.format(src, dst))
        os.symlink(src, dst)

    def isExist(self, path):
        if os.path.exists(path):
          log_debug('"{}" is existed.'.format(path));
          return True
        log_debug('"{}" is not existed.'.format(path));
        return False

    def configEthernet(self):
        log_debug('Config ethernet.')

        cmd = ['ifconfig tap0 down', 'ifconfig eth1 192.168.1.20 up']
        for i in cmd:
          self.pexp.expect_lnxcmd(timeout=5, pre_exp=self.linux_prompt, action=i)

        cmd = '{} {} netmask 255.255.255.0'.format(self.netif, self.dutip)
        self.pexp.expect_lnxcmd(timeout=5, pre_exp=self.linux_prompt, action=cmd)

        self.is_network_alive_in_linux(self.tftp_server)

    def inKernel(self):
        log_debug('Is in kernel ?')
        cmd = 'ifconfig'
        expected = 'Link encap:Local Loopback'
        self.pexp.expect_lnxcmd(timeout=5, pre_exp=self.linux_prompt, action=cmd,  post_exp=expected, retry=10)
    
    def devregDebugTest(self):
        cmd = '{} test'.format(self.devregDebug)
        expected = 'Signed board.  All checks passed.'
        self.pexp.expect_lnxcmd(timeout=5, pre_exp=self.linux_prompt, action=cmd,  post_exp=expected, retry=3)
        log_debug('Pass, found "{}".'.format(expected))

    def gotoLinuxShell(self):
        self.pexp.expect_lnxcmd(60, "UBNT_Diag", "sh\r", self.linux_prompt)
        log_debug('From diag shell go to linux shell')

    def setTelnet(self):
        cmd = "setenv telnet 1\r"
        self.pexp.expect_lnxcmd(30, "UBNT_Diag", cmd)

        cmd = "getenv telnet\r"
        self.pexp.expect_lnxcmd(30, "UBNT_Diag", cmd, "env = 1")

    def goToDiag(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "exit\r")
        
    def clearEnv(self):
        self.stop_uboot()

        cmds = [
            'sf probe',
            'sf erase 0x1e0000 +0x10000',
            'reset'
            ]
        for i in cmds:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, i)

    def run(self):  
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        msg(15, "Clear Env ...")
        self.clearEnv()

        msg(17, "Create softlink ...")
        self.createSymLink()

        self.stop_uboot()
        msg(20, "Set Env ...")
        self.setEnv()

        msg(25, "Upgrade to Diag FW ...")
        self.upgradeToDiag()

        msg(30, "Go to Linux shell ...")
        self.gotoLinuxShell()

        msg(35, "Config ethernet ...")
        self.configEthernet()

        msg(50, "Send tools to DUT and data provision ...")
        self.copy_and_unzipping_tools_to_dut(timeout=60)
        self.data_provision_64k(self.devnetmeta)

        msg(70, "Do helper to get the output file to devreg server ...")
        self.erase_eefiles()
        self.prepare_server_need_files()

        self.registration()
        msg(75, "Finish doing registration ...")

        self.check_devreg_data()
        msg(80, "Finish doing signed file and EEPROM checking ...")

        self.devregDebugTest()
        msg(95, "Finish doing devreg debug test ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()

def main():
    uispMrvl98dx25xx = UispMrvl98Dx25xx()
    uispMrvl98dx25xx.run()

if __name__ == "__main__":
    main()
