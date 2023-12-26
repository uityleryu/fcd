#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

import sys
import time
import os
import re
import stat
import filecmp

CHANGE_MFG_EN = True
PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
UPDATEIMG_EN = True

'''
    e960: UCKG2
    e961: UDC-CONSOLE
    e970: UCKP
'''


class UCKAPQ8053FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UCKAPQ8053FactoryGeneral, self).__init__()
        self.ver_extract()
        self.devregpart = "/dev/mtdblock0"
        self.helper_path = "uck"
        self.helperexe = "DRA_ed0eb1b5_helper_APQ8053_release.strip"

        # number of Ethernet
        ethnum = {
            'e960': "1",
            'e961': "1",
            'e970': "1",
            'e992': "1"
        }

        # number of WiFi
        wifinum = {
            'e960': "0",
            'e961': "0",
            'e970': "0",
            'e992': "0"
        }

        # number of Bluetooth
        btnum = {
            'e960': "1",
            'e961': "1",
            'e970': "1",
            'e992': "1"
        }

        flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
            'flashed_dir'     : flashed_dir
        }

        self.netif = {
            'e960': "ifconfig eth0 ",
            'e961': "ifconfig eth0 ",
            'e970': "ifconfig eth0 ",
            'e992': "ifconfig eth0 "
        }

    def login_kernel(self):
        '''
            For the postexp sets, they are for the case of that
                "Firmware version", "Launching interactive shell", "Welcome to CloudKey FCD"
                  - preload image is a certain version of the formal images before 0.8.12.
                  - when FCD is failed after uploading the MFG image. Then, the initial image will be
                  MFG image when redoing the FCD script.
        '''
        postexp = [
            "Firmware version:",
            "Launching interactive shell",
            "Welcome to CloudKey FCD"
        ]
        index = self.pexp.expect_get_index(200, postexp)
        if index == 0 or index == 1 or index == 2:
            log_debug("kernel is MFG or preload image")
            self.pexp.expect_action(10, "", "\n")
            self.pexp.expect_only(10, self.linux_prompt)
        else:
            error_critical(msg="Can't get expected string to login kernel")

        self.set_lnx_net("eth0")
        self.is_network_alive_in_linux()

    def prepare_server_need_files(self):
        rmsg = "Starting to do {} ...".format(self.helperexe) 
        log_debug(rmsg)
        srcp = os.path.join(self.tools, self.helper_path, self.helperexe)
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)
        self.tftp_get(remote=srcp, local=helperexe_path, timeout=30)

        cmd = "chmod 777 {0}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class={}".format(self.product_class),
            "-o field=flash_eeprom,format=binary,pathname={}".format(eebin_dut_path),
            "> {}".format(eetxt_dut_path)
        ]
        sstr = ' '.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt, valid_chk=True)
        cmd = "sync"
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt, valid_chk=True)
        time.sleep(1)

        files = [self.eetxt, self.eebin]
        for fh in files:
            srcp = os.path.join(self.tftpdir, fh)
            dstp = "/tmp/{0}".format(fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)

        log_debug("Send helper output files from DUT to host ...")

    def mac_colon_format(self, mac):
        mcf = [
            self.mac[0:2],
            self.mac[2:4],
            self.mac[4:6],
            self.mac[6:8],
            self.mac[8:10],
            self.mac[10:12]
        ]
        mcf = ':'.join(mcf)
        return mcf

    def run(self):
        """
        Main procedure of factory
        """

        if self.ps_state is True:
            self.set_ps_port_relay_off("eb36")
        else:
            log_debug("No need power supply control")

        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{} -b 115200".format(self.dev)
        log_debug(pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)

        if self.ps_state is True:
            self.set_ps_port_relay_on("eb36")
        else:
            log_debug("No need power supply control")

        msg(5, "Boot to linux console ...")
        if self.board_id == "e992":
            self.login(username="ui", password="ui", timeout=40)
            self.set_lnx_net("eth0")
            self.is_network_alive_in_linux()
        else:
            self.login_kernel()

        colon_mac = self.mac_colon_format(self.mac)
        msg(10, "Boot up to linux console and network is good ...")

        if CHANGE_MFG_EN is True:
            '''
               It can not use this self.tftp_get() at here.
               Because it needs to add a "busybox" at the begining of the command
            '''
            cmd = "busybox tftp -b 4096 -g -r images/{0}-mfg.bin -l /tmp/{0}-mfg.bin {1}".format(self.board_id, self.tftp_server)
            self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)

            cmd = "dd if=/tmp/{}-mfg.bin of=/dev/disk/by-partlabel/boot bs=1M".format(self.board_id)
            self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)
            time.sleep(5)
            msg(15, "Upgrade to the MFG image successfully")

        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            self.pexp.expect_lnxcmd(20, self.linux_prompt, "reboot -f")
            self.login_kernel()

            cmd = "ck-ee -F -r 113-{} -s 0x{} -m {} 2>/dev/null".format(self.bom_rev, self.board_id, self.mac)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

            cmd = "ck-ee -I 2>&1"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
            self.pexp.expect_only(5, "EEPROM is valid")
            self.pexp.expect_only(5, "MAGIC: 55424e54")
            self.pexp.expect_only(5, "eth0 hwaddr: {}".format(colon_mac.upper()))
            self.pexp.expect_only(5, "system ID: 0777:{}".format(self.board_id))
            self.pexp.expect_only(5, "BOM: 113-{}".format(self.bom_rev))

            cmd = "ax88179-ee weeprom 0 /firmware/ax88179/std-eeprom.bin 512"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, "Write completely")

            cmd = "ax88179-ee chgmac 0 {} 128".format(colon_mac.upper())
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, "Chgmac completely")

            cmd = "echo USBETH=$(lsusb | grep -c 0b95:1790 2>/dev/null)"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, "USBETH=1")

            cmd = "echo USBSATA=$(lsusb | grep -c '174c:1153\|174c:55aa' 2>/dev/null)"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, "USBSATA=1")
            msg(15, "Check the provisioning data successfully")

            src = os.path.join(self.tools, self.helper_path, "check-part.txt")
            dst = os.path.join(self.dut_tmpdir, "check-part.txt")
            self.tftp_get(src, dst)

            src = os.path.join(self.tools, self.helper_path, "check-part.sh")
            dst = os.path.join(self.dut_tmpdir, "check-part.sh")
            self.tftp_get(src, dst)

            cmd = "chmod +x {}/check-part.sh".format(self.dut_tmpdir)
            self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)

            cmd = "cd /tmp; ./check-part.sh"
            self.pexp.expect_lnxcmd(600, self.linux_prompt, cmd, self.linux_prompt)
            msg(20, "Send tools to DUT and data provision ...")

        if DOHELPER_EN is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files()

        if REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
            ============ Registration End ============
        '''

        if UPDATEIMG_EN is True:
            cmd = "dd if=/dev/zero of=/dev/disk/by-partlabel/overlay bs=32M >/dev/null 2>/dev/null"
            self.pexp.expect_lnxcmd(240, self.linux_prompt, cmd, self.linux_prompt)

            cmd = "dd if=/dev/zero of=/dev/disk/by-partlabel/persist bs=32M >/dev/null 2>/dev/null"
            self.pexp.expect_lnxcmd(120, self.linux_prompt, cmd, self.linux_prompt)

            cmd = "dd if=/dev/zero of=/dev/disk/by-partlabel/appdata bs=32M >/dev/null 2>/dev/null"
            self.pexp.expect_lnxcmd(1200, self.linux_prompt, cmd, self.linux_prompt)

            cmd = "dd if=/dev/zero of=/dev/sda bs=32M count=1"
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt)

            cmd = "tftp -b 4096 -g -r {0}/{1}-recovery.bin -l /tmp/{1}-recovery.bin {2}".format(self.image, self.board_id, self.tftp_server)
            self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)

            cmd = "tftp -b 4096 -g -r {0}/{1}-kernel.bin -l /tmp/{1}-kernel.bin {2}".format(self.image, self.board_id, self.tftp_server)
            self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)

            cmd = "tftp -b 16384 -g -r {0}/{1}-rootfs.bin -l /tmp/{1}-rootfs.bin {2}".format(self.image, self.board_id, self.tftp_server)
            self.pexp.expect_lnxcmd(120, self.linux_prompt, cmd, self.linux_prompt, valid_chk=True)

            src = "{}/{}/mmc-prep.sh".format(self.tools, self.helper_path)
            dst = "/tmp/mmc-prep.sh"
            self.tftp_get(src, dst)

            cmd = "chmod +x /tmp/mmc-prep.sh"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, self.linux_prompt)

            cmd = "cd /tmp; ./mmc-prep.sh {} 32M".format(self.board_id)
            self.pexp.expect_lnxcmd(300, self.linux_prompt, cmd, "DONE")

            cmd = "reboot -f"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

            log_debug("kerenl is normal FW")
            self.login(username="ui", password="ui", retry=12)
            self.set_lnx_net("eth0")
            self.is_network_alive_in_linux()
            msg(70, "Completing the image update")

        if self.board_id == "e970":
            cmd = "grep -q 'App Startup Complete.' /srv/unifi-protect/logs/app.log"
            self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)

        cmd = "grep -q 'WebRTC library version' /usr/lib/unifi/logs/server.log"
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd, self.linux_prompt)
        msg(80, "Completing the initialization of UniFi")

        cmd = "ubnt-tools id"
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd)
        self.pexp.expect_only(5, "board.sysid=0x".format(self.board_id))
        self.pexp.expect_only(5, "board.cpu.id=410fd034-00000000")
        self.pexp.expect_only(5, "board.uuid=........-....-5...-....-............")
        self.pexp.expect_only(5, "board.bom=".format(self.bom_rev))

        cmd = "touch /boot/reset2defaults; sync; sync"
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd)

        cmd = "ubnt-tools qrid"
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, "{}".format(self.qrcode))

        cmd = "busybox tftp -b 4096 -g -r {}/{}/ck-ee -l /tmp/ck-ee {}".format(self.tools, self.helper_path, self.tftp_server)
        self.pexp.expect_lnxcmd(60, self.linux_prompt, cmd, self.linux_prompt)

        cmd = "cd /tmp; chmod +x ck-ee; ./ck-ee -I 2>&1"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.pexp.expect_only(5, "EEPROM is valid")
        self.pexp.expect_only(5, "MAGIC: 55424e54")
        self.pexp.expect_only(5, "eth0 hwaddr: {}".format(colon_mac.upper()))
        self.pexp.expect_only(5, "system ID: 0777:{}".format(self.board_id))
        self.pexp.expect_only(5, "BOM: 113-{}".format(self.bom_rev))

        cmd = "cat /usr/lib/version"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        if self.board_id == ["e970", "e992"]:
            cmd = "poweroff"
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
            time.sleep(50)

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        factory = UCKAPQ8053FactoryGeneral()
        factory.run()

if __name__ == "__main__":
    main()
