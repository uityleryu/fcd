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
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.common import Common
from ubntlib.fcd.pyssh import pyssh
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

class AFAMEFactroy(ScriptBase):
    def __init__(self):
        self.target_ip = '192.168.1.20'
        self.username = 'ubnt'
        self.password = 'ubnt'
        self.key = 'ENGINEERING'
        self.product = 'AME'
        super(AFAMEFactroy, self).__init__()

    def run(self):
        if self.key == 'ENGINEERING':
            keypath = self.key_dir
            passphrase = self.pass_phrase
        elif self.key == 'FACTORY':
            keypath = '/media/usbdisk/PlexusKeys'
            passphrase = ''
        else:
            print("Invalid Key: %s" % self.key)
            return
        
        for _ in range (1, 10):
            cmd = 'ping ' + self.target_ip + ' -c 3 -q'
            (output, status ) = run(cmd, withexitstatus=1)
            #log_debug(output.decode("utf-8"))
            if status:
                log_debug("Wait Device network up")
                time.sleep(5)
                if _ == 10:
                    self.write_qst("FAIL")
                    error_critical("Cannot ping to Device")
            else:
                time.sleep(5)
                break

        log_debug("Signing Radio ip=%s, username=%s, password=%s, product=%s" 
            %( self.target_ip, self.username, self.password, self.product ))
        ssh = pyssh(self.target_ip, self.username, self.password)
        scp = pyssh(self.target_ip, self.username, self.password)
        (status, stdout) = ssh.login(verbose=False)

        if status == False:
            self.write_qst("FAIL")
            error_critical("Device not found or Login fail: %s" % stdout)

        if self.product == 'AF':
            helper = "/tftpboot/tools/helper_AM18xx"
            mtd = "/dev/mtdblock7"
            dump_cmd = "dd if=" + mtd + " of=/var/tmp/EEPROM"
        elif self.product == 'AME':
            helper = "/tftpboot/tools/af_ltu5/helper_UBNTAME"
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
            cmd = './client_x86_release -h devreg-prod.ubnt.com' \
                ' -i field=flash_eeprom,format=binary,pathname=/tmp/EEPROM' \
                ' -o field=flash_eeprom,format=binary,pathname=/tmp/EEPROM_SIGNED' \
                ' -k '+ passphrase + \
                ' -i '+content[9] + \
                ' -i '+content[10] + \
                ' -i '+content[11] + \
                ' -i '+content[7] + \
                '-x '+keypath+'/ca.pem ' + \
                '-y '+keypath+'/key.pem ' + \
                '-z '+keypath+'/crt.pem '
        elif self.product == 'AME':
            cmd = './client_x86_release -h devreg-prod.ubnt.com' \
                ' -i field=flash_eeprom,format=binary,pathname=/tmp/EEPROM' \
                ' -o field=flash_eeprom,format=binary,pathname=/tmp/EEPROM_SIGNED' \
                ' -o field=result' \
                ' -k '+passphrase + \
                ' -i '+content[9] + \
                ' -i '+content[11 ] + \
                ' -i '+content[12 ] + \
                ' -i '+content[13 ] + \
                ' -x '+keypath+'/ca.pem' + \
                ' -y '+keypath+'/key.pem' + \
                ' -z '+keypath+'/crt.pem'

        log_debug(cmd)
        (output, status ) = run(cmd, withexitstatus=1)
        log_debug(output.decode("utf-8"))

        if status:
            if int(status) == 231:
                print("Wrong key used? key=%s" % self.key)
            print("Device Not Signed")
            ssh.logout()
            self.write_qst("FAIL")
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
            self.write_qst("FAIL")
            error_critical("Check EEPROM data error")

        ssh.write_wait("reboot")
        msg(100, "Process Completed")

        self.write_qst("PASS")

        sys.stdout.flush()
        time.sleep(10)
        #ssh.logout()

    def write_qst(self, result):

        log_debug("====Print CM Log Start====")

        datetime_str =  datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        version_txt = "/home/user/Desktop/version.txt"
        try:
            f = open(version_txt, "r")
            version = f.readline().strip()
            log_debug("FCD version: " + version)
            f.close()
        except Exception as e:
            log_debug(str(e))

        qst_str = "%s|%s|%s|%s|%s|%s|%s|%s|%s\n" % ( \
            self.mac.upper(), \
            "113-"+self.bom_rev+"-"+self.region, \
            self.board_id.upper(), \
            result, \
            self.opid, \
            self.stationid, \
            version, \
            self.region, \
            datetime_str
        )

        log_debug(qst_str)

        log_file_path = os.path.join("/tftpboot/")
        qst_name = log_file_path + "/" + self.stationid + "_" + datetime_str + ".qst"

        try:
            qstfile = open(qst_name, "w")
            qstfile.write(qst_str)
            qstfile.flush()
            qstfile.close()
            log_debug("QST record wrote")
        except:
            log_debug("QST record write error")

        log_debug("====Print CM Log End====")

#===========================================================================
#           main entry
#===========================================================================

# target_ip=$IP key=$KEY
if __name__ == '__main__':
    
    af_reg = AFAMEFactroy()
    af_reg.run()
