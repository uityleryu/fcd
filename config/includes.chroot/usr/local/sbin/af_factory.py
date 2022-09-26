#!/usr/bin/python

import re
import sys
import time
import os
import stat
import shutil
import datetime

from pexpect import *
from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.common import Common
from PAlib.Framework.fcd.pyssh import pyssh
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical


class AFAMEFactroy(ScriptBase):
    def __init__(self):
        super(AFAMEFactroy, self).__init__()
        self.target_ip = '192.168.1.20'
        soctype = {
            'ae06': 'AME',
            'ae08': 'AME',
            'ae0b': 'AME',
            'ae10': 'AME',
            'ae11': 'AME',
            'ae0f': 'AME',
            'ae13': 'AME'
        }

        self.product = soctype[self.board_id]
        self.client_utility = "/usr/local/sbin/client_rpi4_release"
        self.tooldir = "/tftpboot/tools"

    def run(self):
        for _ in range (1, 10):
            cmd = "ping {} -c 3 -q".format(self.target_ip)
            '''
                The following run command is from pexpect package
            '''
            (output, status) = run(cmd, withexitstatus=1)

            if os.path.isdir(self.fcd_toolsdir) is False:
                error_critical("Can't find {}".format(self.fcd_toolsdir))

            if os.path.isdir("/home/ubnt/usbdisk/keys") is False:
                error_critical("Can't find keys")

            if status:
                log_debug("Wait Device network up")
                time.sleep(5)
                if _ == 10:
                    error_critical("Cannot ping to Device")
            else:
                log_debug("DUT is up")
                time.sleep(5)
                break

        log_debug("Signing Radio ip=%s, username=%s, password=%s, product=%s" 
            %( self.target_ip, self.user, self.password, self.product ))

        ssh = pyssh(self.target_ip, self.user, self.password)
        scp = pyssh(self.target_ip, self.user, self.password)
        (status, stdout) = ssh.login(verbose=True)

        if status == False:
            error_critical("Device not found or Login fail: %s" % stdout)

        if self.product == 'AF':
            helper = os.path.join(self.fcd_toolsdir, "helper_AM18xx")
            mtd = "/dev/mtdblock7"
            dump_cmd = "dd if={} of=/var/tmp/EEPROM".format(mtd)
        elif self.product == 'AME':
            helper = os.path.join(self.fcd_toolsdir, "af_ltu5", "helper_UBNTAME")
            mtd = "/dev/mtdblock4"
            dump_cmd = "/var/tmp/helper -q -o field=flash_eeprom,format=binary,pathname=/var/tmp/EEPROM"

        msg(5, "Download Helper File")
        ssh.scp(helper, ':/var/tmp/helper')
        ssh.write_wait('ls -l /var/tmp/helper; chmod 555 /var/tmp/helper')
        
        msg(10, "Run Helper File")
        ssh.write_wait("/var/tmp/helper -c product_class=airfiber,format=hex >/var/tmp/helperfile")

        msg(15, 'Copy helper output file to host')
        scp.scp(":/var/tmp/helperfile", "/tmp/helperfile")
        
        msg(20,'Reading image from flash')
        ssh.write_wait(dump_cmd, timeout=5)

        msg(25, 'Copying image to computer')
        scp.scp(':/var/tmp/EEPROM', '/tmp/EEPROM')

        msg(50, 'Signing image')
        with open("/tmp/helperfile", 'r') as content_file:
            content = content_file.read()

        content = content.splitlines()
        log_debug( content[9] + "\n" + content[11] + "\n" + content[12] + "\n" + content[13])
        if self.product == 'AF':
            regparam = [
                "-i field=flash_eeprom,format=binary,pathname=/tmp/EEPROM",
                "-o field=flash_eeprom,format=binary,pathname=/tmp/EEPROM_SIGNED",
                "-k {}".format(self.pass_phrase),
                "-i {}".format(content[9]),
                "-i {}".format(content[10]),
                "-i {}".format(content[11]),
                "-i {}".format(content[7]),
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
        elif self.product == 'AME':
            regparam = [
                "-i field=flash_eeprom,format=binary,pathname=/tmp/EEPROM",
                "-o field=flash_eeprom,format=binary,pathname=/tmp/EEPROM_SIGNED",
                "-k {}".format(self.pass_phrase),
                "-i {}".format(content[9]),
                "-i {}".format(content[11]),
                "-i {}".format(content[12]),
                "-i {}".format(content[13]),
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
        cmd = "sudo {0} {1}".format(self.client_utility, regparam)
        log_debug(cmd)
        '''
            The following run command is from pexpect package
        '''
        (output, status ) = run(cmd, withexitstatus=1)
        log_debug(output.decode("utf-8"))

        if status:
            if int(status) == 231:
                print("Wrong key used? key=%s" % self.key)

            print("Device Not Signed")
            ssh.logout()
            error_critical("Signature Failed Error: %d" % status)

        msg(60, 'Copying signed image to unit')
        scp.scp('/tmp/EEPROM_SIGNED', ':/var/tmp/EEPROM_SIGNED')

        msg(70, "Writing image to flash")
        if self.product == 'AF':
            ssh.write_wait("dd of=" + mtd + " if=/var/tmp/EEPROM_SIGNED", timeout=20)
        elif self.product == 'AME':
            ssh.write_wait("/var/tmp/helper -q -i field=flash_eeprom,format=binary,pathname=/var/tmp/EEPROM_SIGNED", timeout=20)

        ssh.write_wait("hexdump -C -s 0x0 -n 1000 " + mtd)
        ssh.write_wait('hexdump -C -s 0x0 -n 1000 /tmp/EEPROM_SIGNED')
        ssh.write_wait("hexdump -C -s 0xa000 -n 200 " + mtd)
        ssh.write_wait('hexdump -C -s 0xa000 -n 200 /tmp/EEPROM_SIGNED')

        ssh.write_wait("dd if=" + mtd + " of=/tmp/mtdblock4 bs=65536 count=1")

        sum1 = ssh.write_wait("md5sum /tmp/EEPROM_SIGNED | cut -f 1 -d ' '").decode("utf-8")
        sum1 = sum1.splitlines()
        sum2 = ssh.write_wait("md5sum /tmp/mtdblock4 | cut -f 1 -d ' '").decode("utf-8")
        sum2 = sum2.splitlines()
        log_debug(sum1[-1] + " " + sum2[-1])
        if sum1[-1] == sum2[-1]:
            msg(90, "Device Signed!")
        else:
            error_critical("Check EEPROM data error")

        ssh.write_wait("reboot")
        sys.stdout.flush()
        time.sleep(10)
        msg(100, "Process Completed")
        try:
            if self.upload:
                # Compute test_time/duration
                self.test_endtime_datetime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
                self.test_duration = (self.test_endtime_datetime - self.test_starttime_datetime).seconds
                self.test_starttime = self.test_starttime_datetime.strftime('%Y-%m-%d_%H:%M:%S')
                self.test_endtime = self.test_endtime_datetime.strftime('%Y-%m-%d_%H:%M:%S')

                # Dump all var
                self._dumpJSON()

                self._upload_prepare()
        except AttributeError:
            pass

        self.close_fcd()

#===========================================================================
#           main entry
#===========================================================================

# target_ip=$IP key=$KEY
if __name__ == '__main__':
    
    af_reg = AFAMEFactroy()
    af_reg.run()
