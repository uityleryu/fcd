#!/usr/bin/python

import re
import sys
import time
import os
import stat
import shutil

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
                    error_critical("Cannot ping to Device")
            else:
                time.sleep(5)
                break

        log_debug("Signing Radio ip=%s, username=%s, password=%s, key=%s, product=%s" 
            %( self.target_ip, self.username, self.password, self.key, self.product ))
        ssh = pyssh(self.target_ip, self.username, self.password)
        scp = pyssh(self.target_ip, self.username, self.password)
        (status, stdout) = ssh.login(verbose=False)

        if status:
            msg(5, "Download Helper File")
            if self.product == 'AF':
                ssh.scp("/tftpboot/tools/helper_AM18xx", ':/var/tmp/helper_AM18xx')
                ssh.write_wait('ls -l /var/tmp/helper_AM18xx')
                ssh.write_wait('chmod 555 /var/tmp/helper_AM18xx')
                msg(10, "Run Helper File")
                ssh.write_wait("/var/tmp/helper_AM18xx -c product_class=airfiber,format=hex >/var/tmp/helperfile")
                msg(15, 'Reading helper output file')
                scp.scp(":/var/tmp/helperfile", "/tmp/helperfile")
                msg(20,'Reading image from flash')
                ssh.write_wait("dd if=/dev/mtdblock7 of=/var/tmp/EEPROM",timeout=5)

            elif self.product == 'AME':
                ssh.scp("/tftpboot/tools/af_ltu5/helper_UBNTAME", ':/var/tmp/helper_UBNTAME')
                ssh.write_wait('ls -l /var/tmp/helper_UBNTAME')
                ssh.write_wait('chmod 555 /var/tmp/helper_UBNTAME')
                msg(10, "Run Helper File")
                ssh.write_wait("/var/tmp/helper_UBNTAME -c product_class=airfiber,format=hex >/var/tmp/helperfile")
                msg(15, 'Reading helper output file')
                scp.scp(":/var/tmp/helperfile", "/tmp/helperfile")
                msg(20,'Reading image from flash')
                ssh.write_wait("/var/tmp/helper_UBNTAME -q -o field=flash_eeprom,format=binary,pathname=/var/tmp/EEPROM",timeout=5)

            msg(25, 'Copying image to computer')
            scp.scp(':/var/tmp/EEPROM', '/tmp/EEPROM')

            msg(50, 'Signing image key: %s' % self.key)
            with open("/tmp/helperfile", 'r') as content_file:
                content = content_file.read()
            content = content.splitlines()

            if self.product == 'AF':
                cmd = './client_x86_release -h devreg-prod.ubnt.com -i field=flash_eeprom,format=binary,pathname=/tmp/EEPROM -o field=flash_eeprom,format=binary,pathname=/tmp/EEPROM_SIGNED ' \
                    '-k '+passphrase+' -i '+content[9]+' -i '+content[10]+ ' -i '+content[11]+' -i '+content[7]+'  -x '+keypath+'/ca.pem -y '+keypath+'/key.pem -z '+keypath+'/crt.pem' 
                #cmd = 'files/client_x64' +' -i field=flash_eeprom,format=binary,pathname=' + tmp_EEPROM + \
                #' -o field=error_message -o field=flash_eeprom,format=binary,pathname=' + tmp_EEPROM_SIGNED + \
                #' -k '+passphrase+' -i '+content[9]+' -i '+content[10]+ ' -i '+content[11]+' -i '+content[7]+ \
                #' -x '+keypath+'/ca.pem -y '+keypath+'/key.pem -z '+keypath+'/crt.pem'
            
            elif self.product == 'AME':
                log_debug("LINE->%s" % content[9])	#field=product_class_id		#print "LINE->%s" % content[7]
                log_debug("LINE->%s" % content[11])	#field=flash_jedec_id		#print "LINE->%s" % content[9]
                log_debug("LINE->%s" % content[12])	#field=flash_uid		#print "LINE->%s" % content[10]
                log_debug("LINE->%s" % content[13])	#field=AM18xx_cpu_rev_id	#print "LINE->%s" % content[11]
                #cmd = 'client_x86_release -i field=flash_eeprom,format=binary,pathname=EEPROM -o field=flash_eeprom,format=binary,pathname=EEPROM_SIGNED ' \
                #      '-k '+passphrase+' -i '+content[9]+' -i '+content[10]+ ' -i '+content[11]+' -i '+content[7]+'  -x '+keypath+'/ca.pem -y '+keypath+'/key.pem -z '+keypath+'/crt.pem'
                cmd = './client_x86_release -h devreg-prod.ubnt.com -i field=flash_eeprom,format=binary,pathname=/tmp/EEPROM -o field=flash_eeprom,format=binary,pathname=/tmp/EEPROM_SIGNED -o field=result ' \
                     '-k '+passphrase+' -i '+content[9]+' -i '+content[11]+ ' -i '+content[12]+' -i '+content[13]+'  -x '+keypath+'/ca.pem -y '+keypath+'/key.pem -z '+keypath+'/crt.pem'

            log_debug(cmd)
            (output, status ) = run(cmd, withexitstatus=1)
            log_debug(output.decode("utf-8"))
            if status:
                print("Sign cmd:%s" %(cmd))
                if int(status) == 231:
                    print("Wrong key used? key=%s" % self.key)
                print("Radio Not Signed")
                ssh.logout()
                error_critical("Signature Failed Error: %d" % status)
            else:
                print("Copying signed image to unit")
                scp.scp('/tmp/EEPROM_SIGNED', ':/var/tmp/EEPROM_SIGNED')

                msg(70, "Writing image to flash")
                if self.product == 'AF':
                    ssh.write_wait("dd of=/dev/mtdblock7 if=/var/tmp/EEPROM_SIGNED", timeout=20)
                elif self.product == 'AME':
                    ssh.write_wait("/var/tmp/helper_UBNTAME -q -i field=flash_eeprom,format=binary,pathname=/var/tmp/EEPROM_SIGNED", timeout=20)

            if self.product == 'AF':
                ssh.write_wait("hexdump -C -s 0x0 -n 100 /dev/mtdblock7")
                ssh.write_wait("hexdump -C -s 0xa000 -n 100 /dev/mtdblock7")
            elif self.product == 'AME':
                ssh.write_wait("hexdump -C -s 0x0 -n 100 /dev/mtdblock4")
                ssh.write_wait("hexdump -C -s 0xa000 -n 100 /dev/mtdblock4")
            
            cmd = 'hexdump -C -s 0x0 -n 100 /tmp/EEPROM; hexdump -C -s 0xa0000 -n 100 /tmp/EEPROM'
            (output, status ) = run(cmd, withexitstatus=1)
            log_debug(output.decode("utf-8"))

            msg(90, "Radio Signed!")
            ssh.write_wait("reboot")
            msg(100, "Process Completed")
            sys.stdout.flush()
            time.sleep(10)
            #ssh.logout()
        else:
            error_critical("Radio not found: %s" % stdout)
        
#===========================================================================
#           main entry
#===========================================================================

# target_ip=$IP key=$KEY
if __name__ == '__main__':
    
    af_reg = AFAMEFactroy()
    af_reg.run()
