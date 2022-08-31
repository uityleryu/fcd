#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical
from PAlib.Framework.fcd.ssh_client import SSHClient

class UNIFIBMCFactory(ScriptBase):
    def __init__(self):
        super(UNIFIBMCFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # common variable
        self.ver_extract()
        self.dut_ssh = None
        self.devregpart = "/dev/sda4"
        self.cpuid = "0x00050657"
        self.flash_jedecid = ""
        self.flash_uuid = ""
        self.bmcip = "192.168.1." + str((int(self.row_id) + 41))

        # number of mac
        self.macnum = {
            '0000': "1",
            'e990': "3"
        }

        # number of WiFi
        self.wifinum = {
            '0000': "0",
            'e990': "0"
        }

        # number of Bluetooth
        self.btnum = {
            '0000': "1",
            "e990": "1"
        }

        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

        self.PROVISION_EN       = True
        self.GETHWINFO_EN       = True
        self.REGISTER_EN        = True
        self.WRITE_CHECK        = True
        self.WRITE_MAC_EN       = True
        self.HALTHOST_EN        = True
        self.WRITE_MAC2_EN      = True

    def set_bmc_network(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 " + self.bmcip + " up")

        retry = 10
        for i in range(0, retry):
            time.sleep(3)
            try:
                self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, "64 bytes from")

                return
            except Exception as e:
                print("set network fail..." + str(i))
                continue
            break
        else:
            print("set network retry fail")
            raise NameError('set network retry fail')

    def set_host_network(self):

        cmd = "systemctl disable --now systemd-networkd-fallbacker@eth0.service; systemctl disable --now systemd-networkd-fallbacker@eth1.service"

        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig eth0 " + self.dutip)

        retry = 10
        for i in range(0, retry):
            time.sleep(3)
            try:
                self.pexp.expect_lnxcmd(10, self.linux_prompt, "ping -c 1 " + self.tftp_server, "64 bytes from")

                sshclient_obj = SSHClient(host=self.dutip,
                                    username="ubnt",
                                    password="ubnt",
                                    polling_connect=True,
                                    polling_mins=3)

                self.set_sshclient_helper(ssh_client=sshclient_obj)

                return

            except Exception as e:
                print("set network fail..." + str(i))
                continue
            break
        else:
            print("set network retry fail")
            raise NameError('set network retry fail')

    def set_host_fan(self):
        cmd = "systemctl stop uhwd"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        for i in ['1','2','3','6']:
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "echo {} > /sys/class/hwmon/hwmon0/pwm{} ".format(70, i))
            time.sleep(3)

    '''
        Host call to scp file from DUT to Host
    '''
    def scp_put(self, dut_user, dut_pass, dut_ip, dut_file, host_file):
        cmd = [
            'sshpass -p ' + dut_pass,
            'scp',
            '-o StrictHostKeyChecking=no',
            '-o UserKnownHostsFile=/dev/null',
            dut_user + "@" + dut_ip + ":" + dut_file,
            host_file,
        ]
        cmdj = ' '.join(cmd)
        log_debug('Exec "{}"'.format(cmdj))
        [stout, rv] = self.fcd.common.xcmd(cmdj)
        if int(rv) != 0:
            error_critical('Exec "{}" failed'.format(cmdj))
        else:
            log_debug('scp successfully')

    def data_provision_64k(self, netmeta, post_en=True):
        self.gen_rsa_key()

        post_exp = None
        if post_en is True:
            post_exp = self.linux_prompt

        otmsg = "Starting to do {0} ...".format(self.eepmexe)
        log_debug(otmsg)
        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe)
        sstr = [
            flasheditor,
            "-F",
            "-f " + self.eegenbin_path,
            "-r 113-{0}".format(self.bom_rev),
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + netmeta['ethnum'][self.board_id],
            "-w " + netmeta['wifinum'][self.board_id],
            "-b " + netmeta['btnum'][self.board_id],
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
        log_debug("flash editor cmd: " + sstr)
        [sto, rtc] = self.cnapi.xcmd(sstr)
        time.sleep(0.5)
        if int(rtc) > 0:
            otmsg = "Flash editor filling out {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Flash editor filling out {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        # Ex: dd if=/dev/mtdblock2 of=/tmp/e.org.0 bs=1k count=64
        cmd = "dd if={0} of={1}/{2} bs=1k count=64".format(self.devregpart, self.dut_tmpdir, self.eeorg)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(0.1)

        srcpath = "{0}/{1}".format(self.dut_tmpdir, self.eeorg)
        self.scp_put(dut_user="ubnt", dut_pass="ubnt", dut_ip=self.dutip, 
                     dut_file=srcpath,
                     host_file=self.eebin_path)

    def get_hardware_info(self):

        cmd= 'ipmitool raw 0x32 0x41'
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)
        self.flash_jedecid = "0x00" + "".join(out.split(" "))
        log_debug("JEDECID: " + self.flash_jedecid)

        cmd = 'ipmitool raw 0x32 0x40'
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)
        self.flash_uuid = "0x" + "".join(out.split(" "))
        log_debug("FLASUUID: " + self.flash_uuid)

        return

    def registration(self, regsubparams = None):
        log_debug("Starting to do registration ...")
        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        clientbin = "/usr/local/sbin/client_rpi4_release"
        regparam = [
            "-h prod.udrs.io",
            "-k {}".format(self.pass_phrase),
            "-i field=product_class_id,format=hex,value=0014",
            "-i field=cpu_rev_id,format=hex,value={}".format(self.cpuid),
            "-i field=flash_jedec_id,format=hex,value={}".format(self.flash_jedecid),
            "-i field=flash_uid,format=hex,value={}".format(self.flash_uuid),
            reg_qr_field,
            "-i field=flash_eeprom,format=binary,pathname={}".format(self.eegenbin_path),
            "-i field=fcd_version,format=hex,value={}".format(self.sem_ver),
            "-i field=sw_id,format=hex,value={}".format(self.sw_id),
            "-i field=sw_version,format=hex,value={}".format(self.fw_ver),
            "-o field=flash_eeprom,format=binary,pathname={}".format(self.eesign_path),
            "-o field=registration_id",
            "-o field=result",
            "-o field=device_id",
            "-o field=registration_status_id",
            "-o field=registration_status_msg",
            "-o field=error_message",
            "-x {}ca.pem".format(self.key_dir),
            "-y {}key.pem".format(self.key_dir),
            "-z {}crt.pem".format(self.key_dir)
        ]

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)
        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Security Service Device Registration Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        self.pass_devreg_client = True

        log_debug("Excuting client registration successfully")
        if self.FCD_TLV_data is True:
            self.add_FCD_TLV_info()

    def write_signed_check(self):
        
        eewrite = self.eesigndate
        eewrite_dut_path = os.path.join(self.dut_tmpdir, eewrite)
        eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)

        # Copy signed file to DUT
        self.scp_get("ubnt", "ubnt", self.dutip, self.eesigndate_path, eewrite_dut_path)

        cmd = "dd if={0} of={1} bs=1k count=64".format(eewrite_dut_path, self.devregpart)
        out = self.session.execmd_getmsg(cmd)

        cmd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
        out = self.session.execmd_getmsg(cmd)

        # Copy chk file from DUT to host
        self.scp_put(dut_user="ubnt", dut_pass="ubnt", dut_ip=self.dutip, dut_file=eechk_dut_path,
                     host_file=self.eechk_path)

        otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, eewrite)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.eechk_path, self.eesigndate_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")

    def update_mac_addr(self):
        mac1tool = "eeupdate64e"

        mac1tool_path = os.path.join(self.tftpdir, self.tools, "uck", mac1tool)
        self.scp_get("ubnt", "ubnt", self.dutip, mac1tool_path, "/tmp/"+mac1tool)

        cmd = "/tmp/" + mac1tool + " /nic=1 /mac=" + self.mac
        out = self.session.execmd_getmsg(cmd)

        mac_2  = self.mac[0:6]+str(hex(int(self.mac[6:12], 16)+1))[2:8].upper()
        mac2 = mac_2[0:2]+":"+mac_2[2:4]+":"+mac_2[4:6]+":"+mac_2[6:8]+":"+mac_2[8:10]+":"+mac_2[10:12]

        mac2tool = "bnxtnvm"
        mac2tool_path = os.path.join(self.tftpdir, self.tools, "uck", mac2tool)
        self.scp_get("ubnt", "ubnt", self.dutip, mac2tool_path, "/tmp/"+mac2tool)

        cmd = "/tmp/"+ mac2tool + " -dev=eth1 setoption=mac_address:0#" + mac2
        out = self.session.execmd_getmsg(cmd)

    def halt_host(self):
        out = self.session.execmd("sync;sync;sync;poweroff", get_exit_val=False, e_except=False)
        self.session.close()

    def write_bmc_mac(self):

        sshclient_obj = SSHClient(host=self.bmcip,
                    username="root",
                    password="0penBmc",
                    polling_connect=True,
                    polling_mins=3)

        self.set_sshclient_helper(ssh_client=sshclient_obj)

        cmd = "ifconfig; killall -9 obmc-console-client"
        out = self.session.execmd_getmsg(cmd)
        self.session.close()

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig")

        mac_3  = self.mac[0:6]+str(hex(int(self.mac[6:12], 16)+2))[2:8].upper()

        cmd = "write_eeprom_mac.sh " + mac_3
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ifconfig")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg")

        return

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        time.sleep(30)

        self.login(timeout=300, username="root", password="0penBmc")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n1", self.linux_prompt)
        msg(10, "OpenBMC login success")

        time.sleep(30)
        self.set_bmc_network()

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "obmc-console-client -i host" )

        self.login(timeout=300, username="ubnt", password="ubnt")

        self.pexp.expect_lnxcmd(10, self.linux_prompt, "dmesg -n1" )
        msg(20, "Host login success")

        self.set_host_fan()

        self.set_host_network()
        msg(30, "Host network config success")

        if self.PROVISION_EN is True:
            self.erase_eefiles()
            
            self.data_provision_64k(self.devnetmeta)
            msg(40, "Generate new EEPROM complete")

        if self.GETHWINFO_EN is True:
            self.get_hardware_info()
            msg(50, "Get Hardware information success")

        if self.REGISTER_EN is True:
            self.registration()
            msg(60, "Registration success")
            
        if self.WRITE_CHECK is True:
            self.write_signed_check()
            msg(70, "Write EEPROM and Check success")

        if self.WRITE_MAC_EN is True:
            self.update_mac_addr()
            msg(80, "Write Host NIC MAC success")

        if self.HALTHOST_EN is True:
            self.halt_host()
            msg(90, "Halt Host success")

        if self.WRITE_MAC2_EN is True:
            self.write_bmc_mac()
            msg(95, "Write BMC MAC success")

        msg(100, "Complete FCD process ...")
        self.close_fcd()

def main():
    factory = UNIFIBMCFactory()
    factory.run()

if __name__ == "__main__":
    main()
