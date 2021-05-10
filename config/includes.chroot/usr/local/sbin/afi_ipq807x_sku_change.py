
#!/usr/bin/python3

import re
import sys
import time
import os
import stat
import shutil
import socket

from script_base import ScriptBase
from binascii import unhexlify
from PAlib.FrameWork.fcd.ssh_client import SSHClient
from PAlib.FrameWork.fcd.expect_tty import ExpttyProcess
from PAlib.FrameWork.fcd.logger import log_debug, log_error, msg, error_critical


class AFIIPQ807XSKUCHANGE(ScriptBase):
    def __init__(self):
        super(AFIIPQ807XSKUCHANGE, self).__init__()
        # In DUT: /tmp/afi_aln
        self.dut_afi_dir = os.path.join(self.dut_tmpdir, "afi_aln")
        # In FCD host: /tftpboot/tools/afi_aln
        self.afi_dir = os.path.join(self.fcd_toolsdir, "afi_aln")

        self.helperexe = "helper_IPQ807x_release"
        self.devregpart = "/dev/mtdblock18"
        self.dutzeroip = self.get_zeroconfig_ip(self.mac)
        self.dut_helper_path = os.path.join(self.dut_afi_dir, self.helperexe)

    def unlockssh(self):
        recoveryipaddr = "192.168.1.20"

        # Create a UDP socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_address = (recoveryipaddr, 69)
            log_debug("connect to {}".format(server_address))
            sock.connect(server_address)
            sock.settimeout(10.0)
        except socket.Timeouterror:
            log_debug("Timeout")

        request = bytearray()
        # First two bytes opcode - for read request
        request.append(0)
        request.append(2)
        # append the filename you are interested in
        filename = bytearray("as.txt".encode('utf-8'))
        request += filename

        # append the null terminator
        request.append(0)
        # append the mode of transfer
        form = bytearray(bytes("octet", 'utf-8'))
        request += form
        # append the last byte
        request.append(0)

        log_debug("Socket send write request")
        print("Request: ")
        print(request)
        sent = sock.sendto(request, server_address)

        recv = bytearray(1024)
        recv = sock.recv(1024)
        print("Receive after request: ")
        print(recv)

        log_debug("Socket send secret binary to unlock SSH")
        cmd = bytearray()
        cmd.append(0)
        cmd.append(3)
        cmd.append(0)
        cmd.append(1)
        # append the secret binary to unlock the SSH
        secretcode = 'FNApGtbLdbhoE/VPFw0M28vOMtxxa/kvBn2I8KCEVKae51Qn4k7sToXhJlvF35PB9/cpmJDvwLxVn44k7Q4DdoH0lBQ' \
                     'YNFAif9tsCrlm/yEEWPYkbz4RH6m96azgZ9+f1IjwCzmIrEbBh14pCGHHW8p+czTyp4yaKmKXgd8qtVDPfZFMh/rmus' \
                     'yuXnkFJQplvQLaDyVORFN6NvUAt0AMU2Z4lO6VtDdq/z7VYCoO6jKhmvekb6yiJRc/LcCpFj4SUkVC+K3LAr/ldpgb5' \
                     'xJ1UbM8d6GJDVHBIEDBvp4KwaR4xOLC0EVmbb9R/K9YtkTkuJUSyvlyUmcreBmsPguzs2VjaG8gc3NoIHwgcHJzdF90' \
                     'b29sIC13IG1pc2MgJiYgcHJzdF90b29sIC1lIHBhaXJpbmcgJiYgY2ZnLnNoIGVyYXNlICYmIGVjaG8gY2ZnX2RvbmU' \
                     'gPiAvcHJvYy9hZmlfbGVkcy9tb2RlICYmIHJlYm9vdCAtZmQx'

        secretcode = bytearray(secretcode.encode('utf-8'))
        cmd += secretcode
        sent = sock.sendto(cmd, server_address)
        recv = sock.recv(1024)
        print("Receive after command: ")
        print(recv)

    def get_zeroconfig_ip(self, mac):
        mac.replace(":", "")
        zeroip = "169.254."
        b1 = str(int(mac[8:10], 16))
        b2 = str(int(mac[10:12], 16))
        # ubnt specific translation
        if b2 == "0":
            b2 = "128"
        elif b2 == "255":
            b2 = "127"
        elif b2 == "19":
            b2 = "18"
        zeroip = zeroip + b1 + "." + b2
        print("zeroip:" + zeroip)

        return zeroip

    def run(self):
        msg(5, "Is going to unlock the SSH ...")
        self.unlockssh()
        time.sleep(10)

        msg(10, "Wait for DUT finish rebooting and ping sucessfully ...")
        retry = 0
        while retry < 130:
            cmd = "ping -c 3 {}".format(self.dutzeroip)
            time.sleep(1)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            print("rtc: " + str(rtc))
            if (int(rtc) == 0):
                match = re.findall("64 bytes", sto, re.S)
                if match:
                    break
                else:
                    retry += 1
            else:
                retry += 1
        else:
            log_debug("Can't PING DUT")
            exit(1)

        ssh_DUT = SSHClient(host=self.dutzeroip, username="ubnt", password="ubnt")

        log_debug("Send tools.tar from host to DUT ...")
        # In FCD host: /tftpboot/tools/afi_aln/tools.tar
        tools_tar = os.path.join(self.fcd_toolsdir, "tools.tar")
        # In DUT: /tmp/tools.tar
        dut_tar = os.path.join(self.dut_tmpdir, "tools.tar")

        '''
            To view from FCD host
            so, put file from FCD host to DUT
        '''
        ssh_DUT.put_file(tools_tar, dut_tar)

        msg(15, "Wait for DUT finish rebooting and ping sucessfully ...")
        log_debug("Unzipping the tools.tar in the DUT ...")
        cmd = "tar -xvzf {0} -C {1}".format(dut_tar, self.dut_tmpdir)
        ssh_DUT.execmd(cmd=cmd, timeout=30)

        log_debug("Change file permission to all /tmp/afi_aln ...")
        cmd = "cd {0}; chmod 777 *".format(self.dut_afi_dir)
        ssh_DUT.execmd(cmd=cmd, timeout=30)

        msg(20, "Starting to do " + self.helperexe + "...")
        cmd = [
            "cd {0}; ./{1} -q -c product_class=basic".format(self.dut_afi_dir, self.helperexe),
            "-o field=flash_eeprom,format=binary,pathname={0} > {1}".format(self.eebin, self.eetxt)
        ]
        cmd = ' '.join(cmd)
        log_debug("cmd: " + cmd)
        ssh_DUT.execmd(cmd=cmd, timeout=30)
        time.sleep(2)

        remotefile = os.path.join(self.dut_afi_dir, self.eetxt)
        ssh_DUT.get_file(remotefile, self.eetxt_path)
        remotefile = os.path.join(self.dut_afi_dir, self.eebin)
        ssh_DUT.get_file(remotefile, self.eebin_path)

        msg(25, "Starting to modify the original binary file with new SKU ...")
        mregion = unhexlify(self.region)
        print("mregion: ")
        print(mregion)
        # In DUT: /tmp/afi_aln/AFi-USA-Canada-SKU.bin
        dutskumod = os.path.join(self.afi_dir, "AFi-USA-Canada-SKU.bin")
        # offset 0x8020 = offset 32800
        cmd = "dd if={0} of={1} bs=1 seek=32800 count=2 conv=notrunc".format(dutskumod, self.eebin_path)
        log_debug("cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            error_critical("Modify the new SKU failed!!")
        else:
            log_debug("Modify the new SKU successfully")

        msg(30, "Wait for DUT finish rebooting and ping sucessfully ...")
        log_debug("Starting to do registration ...")
        cmd = [
            "cat {}".format(self.eetxt_path),
            "|",
            'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
            "|",
            'grep -v \"eeprom\"',
            "|",
            "tr '\\n' ' '"
        ]
        cmdj = ' '.join(cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmdj)
        regsubparams = sto
        if (int(rtc) > 0):
            error_critical("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")

        regparam = [
            "-h devreg-prod.ubnt.com",
            "-k {}".format(self.pass_phrase),
            regsubparams,
            "-i field=flash_eeprom,format=binary,pathname={}".format(self.eebin_path),
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
        regparamj = ' '.join(regparam)
        cmd = "sudo /usr/local/sbin/client_x86_release " + regparamj
        print("cmd: " + cmd)
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(6)
        if (int(rtc) > 0):
            error_critical("client_x86 registration failed!!")
        else:
            log_debug("Excuting client_x86 registration successfully")

        msg(40, "Wait for DUT finish rebooting and ping sucessfully ...")
        log_debug("Wait for DUT finish rebooting and ping sucessfully ...")
        remotefile = os.path.join(self.dut_afi_dir, self.eesign)
        ssh_DUT.put_file(self.eesign_path, remotefile)
        cmd = "mtd write {} eeprom".format(remotefile)
        ssh_DUT.execmd(cmd=cmd, timeout=30)
        ssh_DUT.execmd(cmd="reboot", timeout=30)
        rtc = ssh_DUT.polling_connect()
        if rtc is True:
            rmsg = ssh_DUT.execmd_getmsg(cmd="cat /proc/ubnthal/system.info | grep region")
            log_debug("Get the region: " + rmsg)

        match = re.findall("usa/canada", rmsg, re.S)
        if match:
            log_debug("The region is correct")
        else:
            error_critical("The region is not correct")

        msg(100, "Complete ...")
        self.close_fcd()


def main():
    general = AFIIPQ807XSKUCHANGE()
    general.run()

if __name__ == "__main__":
    main()
