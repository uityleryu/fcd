#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.ssh_client import SSHClient
from ubntlib.fcd.logger import log_debug, msg, error_critical, log_error

import time
import os
import stat
import filecmp
import configparser


PROVISION_EN  = True
DOHELPER_EN   = True
REGISTER_EN   = True
FWUPDATE_EN   = True
DATAVERIFY_EN = True


class UVCFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UVCFactoryGeneral, self).__init__()

        if self.product_name == "UVC-G3BATTERY":
            self.board_name = "UVC G3 Battery"
            self.devregpart = "/dev/mtd15"
            self.ip = "192.168.2.20"
            self.flash_module = "m25p80_g3battery.ko"
            self.helperexe = "helper_S2LM_g3battery"

        elif self.product_name == "UVC-G4PRO":
            self.board_name = "UVC G4 Pro"
            self.devregpart = "/dev/mtd10"
            self.ip = "192.168.1.20"
            self.flash_module = "m25p80_g4pro.ko"
            self.helperexe = "helper_S5L_g4pro"

        elif self.product_name == "UVC-G4PTZ":
            self.board_name = "UVC G4 PTZ"
            self.devregpart = "/dev/mtd8"
            self.ip = "192.168.1.20"
            self.flash_module = "m25p80_uvcg4ptz.ko"
            self.helperexe = "helper_uvcg4ptz"

        elif self.product_name == "UVC-G4DOORBELL":
            self.board_name = "UVC G4 Doorbell"
            self.devregpart = "/dev/mtd10"
            self.ip = "192.168.2.20"
            self.flash_module = "m25p80_uvcg4doorbell.ko"
            self.helperexe = "helper_uvcg4doorbell"

        elif self.product_name == "UVC-G4BULLET":
            self.board_name = "UVC G4 Bullet"
            self.devregpart = "/dev/mtd8"
            self.ip = "192.168.2.20"
            self.flash_module = "m25p80_uvcg4bullet.ko"
            self.helperexe = "helper_uvcg4bullet"

        elif self.product_name == "UVC-G4DOME":
            self.board_name = "UVC G4 Dome"
            self.devregpart = "/dev/mtd8"
            self.ip = "192.168.2.20"
            self.flash_module = "m25p80_uvcg4dome.ko"
            self.helperexe = "helper_uvcg4dome"

        elif self.product_name == "UVC-G3MINI":
            self.board_name = "UVC G3 Mini"
            self.devregpart = "/dev/mtd11"
            self.ip = "192.168.2.20"
            self.flash_module = "m25p80_uvcg3flexmini.ko"
            self.helperexe = "helper_uvcg3flexmini"



        self.fillff = "128k_ff.bin"
        self.ver_extract()
        self.firmware = "{}-fw.bin".format(self.board_id)
        self.eepmexe = "x86-64k-ee"
        self.username = "ubnt"
        self.password = "ubnt"
        self.polling_mins = 5
        self.host_toolsdir_dedicated = os.path.join(self.fcd_toolsdir, "uvc")
        self.fw_path = os.path.join(self.fwdir, self.firmware)
        self.fwinfo_path = os.path.join(self.fwdir, "{}-fw.ini".format(self.board_id))
        self.fwinfo_extract()
        self.eerom_status = 0
        self.errmsg = ""

        # a580 = G3BATTERY
        # a563 = G4PRO
        # a564 = G4PTZ
        # a571 = G4DOORBELL
        # a572 = G4BULLET
        # a573 = G4DOME
        # a590 = G3MINI

        # number of Ethernet
        ethnum = {
            'a580': "0",
            'a563': "1",
            'a564': "1",
            'a571': "0",
            'a572': "1",
            'a573': "1",
            'a590': "0"
        }

        # number of WiFi
        wifinum = {
            'a580': "1",
            'a563': "0",
            'a564': "0",
            'a571': "1",
            'a572': "0",
            'a573': "0",
            'a590': "1"            
        }

        # number of Bluetooth
        btnum = {
            'a580': "1",
            'a563': "0",
            'a564': "0",
            'a571': "1",
            'a572': "0",
            'a573': "0",
            'a590': "1" 
        }

        flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.devnetmeta = {
            'ethnum'          : ethnum,
            'wifinum'         : wifinum,
            'btnum'           : btnum,
            'flashed_dir'     : flashed_dir
        }

        self.netif = {
            'a580': "ifconfig eth0 ",
            'a563': "ifconfig eth0 ",
            'a564': "ifconfig eth0 ",
            'a571': "ifconfig eth0 ",
            'a572': "ifconfig eth0 ",
            'a573': "ifconfig eth0 ",
            'a590': "ifconfig eth0 "           
        }

    def ezreadini(self, path, section, item):
        try:
            config = configparser.ConfigParser()
            config.read(path)
            readstr = config[section][item]
            return readstr
        except Exception as e:
            print(str(e))
            return str("")


    def fwinfo_extract(self):
        log_debug("fwinfo_path: " + self.fwinfo_path)        

        self.main_fw_bin_path = self.ezreadini(self.fwinfo_path, 'MAIN', 'main_fw_bin_path')
        print("main_fw_bin_path:" + self.main_fw_bin_path)

        self.main_fw_bin_name = self.ezreadini(self.fwinfo_path, 'MAIN', 'main_fw_bin_name')
        print("main_fw_bin_name:" + self.main_fw_bin_name)

        self.main_fw_bin_md5 = self.ezreadini(self.fwinfo_path, 'MAIN', 'main_fw_bin_md5')
        print("main_fw_bin_md5:" + self.main_fw_bin_md5)

        self.main_fw_bin_size = self.ezreadini(self.fwinfo_path, 'MAIN', 'main_fw_bin_size')
        print("main_fw_bin_size:" + self.main_fw_bin_size)

        self.main_fw_version = self.ezreadini(self.fwinfo_path, 'MAIN', 'main_fw_version')
        print("main_fw_version:" + self.main_fw_version)



    def critical_error(self, msg):
        self.finalret = False
        self.errmsg = msg
        log_error(msg)

    def upload_flash_module(self):
        flash_fillff_path = os.path.join(self.host_toolsdir_dedicated, self.fillff)
        host_path = flash_fillff_path
        dut_path = "/tmp/{}".format(self.fillff)
        self.session.put_file(host_path, dut_path)

        flash_module_path = os.path.join(self.host_toolsdir_dedicated, self.flash_module)
        mod_name_inDUT = self.flash_module.split(".")[0].split("_")[0]
        cmd_grep = "lsmod | grep {}".format(mod_name_inDUT)
        if self.session.execmd(cmd_grep) == 0:
            # return 0: there is m25p80, return 1: there is not.
            log_debug("flash module {} loaded already".format(self.flash_module))

        else:
            log_debug("uploading kernal file")
            host_path = flash_module_path
            dut_path = "/tmp/{}".format(self.flash_module)
            self.session.put_file(host_path, dut_path)

            log_debug("installing flash module")
            cmd_ins = "insmod /tmp/{}".format(self.flash_module)

            self.session.execmd(cmd_ins)
            if self.session.execmd(cmd_grep) == 0:
                log_debug("flash module {} installed successfully".format(self.flash_module))
            else:
                self.critical_error("failed to install module {}".format(self.flash_module))

            # UVC-G3BATTERY
            if self.product_name == "UVC-G3BATTERY":
                log_debug("installing spi-ambarella.ko module")
                cmd_ins = "insmod spi-ambarella.ko"
                cmd_grep = "lsmod | grep spi_ambarella"
                self.session.execmd(cmd_ins)
                if self.session.execmd(cmd_grep) == 0:
                    log_debug("flash module spi_ambarella installed successfully")
                else:
                    self.critical_error("failed to install module spi_ambarella")

        self.session.execmd('rm /tmp/eerom_backup.bin')   
        cmd_dd = "dd if={} of={} bs=1k count=128".format(self.devregpart, '/tmp/eerom_backup.bin')
        log_debug(cmd_dd)
        self.session.execmd(cmd_dd)        


    def erase_flash_rom(self):
        log_debug("erasing flash module")
        cmdstr = "mtd write /tmp/{} {} 2>&1".format(self.fillff, self.devregpart)
        log_debug(cmdstr)
        rmsg = self.session.execmd_getmsg(cmdstr)
        log_debug(rmsg)

        log_debug("dump flash module")
        cmdstr = "hexdump -C {} 2>&1".format(self.devregpart)
        log_debug(cmdstr)
        rmsg = self.session.execmd_getmsg(cmdstr)
        log_debug(rmsg)
        self.eerom_status = 1

    def check_if_need_register_again(self):
        log_debug('check_if_need_register_again')
        exp_md5_00 = '7bb95b85a48f9db61088daed1363e030'
        exp_md5_ff = '2a274787910027a701cab3e3592304b4'

        cmdstr = "hexdump {} -s 0 -n 36864 -e '16/1 \"%02x\"' | md5sum".format(self.devregpart)
        exp_md5_basic = (self.session.execmd_getmsg(cmdstr)).split()[0]

        cmdstr = "hexdump {} -s 0 -n 36864 -e '16/1 \"%02x\"' | md5sum".format('/tmp/eerom_backup.bin')
        chk_md5_basic = (self.session.execmd_getmsg(cmdstr)).split()[0]

        cmdstr = "hexdump {} -s 36k -n 32 -e '16/1 \"%02x\"' | md5sum".format('/tmp/eerom_backup.bin')
        chk_md5_reg = (self.session.execmd_getmsg(cmdstr)).split()[0]

        log_debug('exp_md5_00: ' + exp_md5_00)
        log_debug('exp_md5_ff: ' + exp_md5_ff)
        log_debug('exp_md5_basic: ' + exp_md5_basic)
        log_debug('chk_md5_basic: ' + chk_md5_basic)
        log_debug('chk_md5_reg: ' + chk_md5_reg)

        if chk_md5_basic != exp_md5_basic:
            log_debug('md5_basic part of current eerom is not the same')
            return False

        if chk_md5_reg == exp_md5_00 or chk_md5_reg == exp_md5_ff:
            log_debug('md5_reg part of current eerom is empty')
            return False

        return True



    def check_if_need_restore_eerom(self):
        log_debug('check_if_need_restore_eerom')
        cmdstr = 'wc /tmp/eerom_backup.bin &> /dev/null; echo $?'
        rmsg = self.session.execmd_getmsg(cmdstr)
        if  int(rmsg) != 0:
            log_debug('/tmp/eerom_backup.bin does not exist')
            return -1
        log_debug('/tmp/eerom_backup.bin exist')

        if self.eerom_status !=0 and self.eerom_status != 9:
            log_debug('need to restore previos eerom back')
            self.erase_flash_rom()
            cmd_dd = "dd if={} of={} bs=1k count=128".format('/tmp/eerom_backup.bin', self.devregpart)
            log_debug(cmd_dd)
            self.session.execmd(cmd_dd)   
            self.eerom_status = 0
            return 1
        return 0


    def data_provision_64k_ssh(self, netmeta):

        self.gen_rsa_key()

        otmsg = "Starting to do {0} ...".format(self.eepmexe) # X86-64-ee
        log_debug(otmsg)

        flasheditor = os.path.join(netmeta['flashed_dir'], self.eepmexe)

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
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)

        if int(rtc) > 0:
            otmsg = "Generating {0} file failed!!".format(self.eegenbin_path)
            self.critical_error(otmsg)
        else:
            otmsg = "Generating {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        #---------> edit e.gen.0
        print('region: ')
        print(self.region)
        print('eegenbin:')
        print(self.eegenbin)
        print('eegenbin_path:')
        print(self.eegenbin_path)
        print('devregpart:')
        print(self.devregpart)
        
        region_value = 255
        if self.region == '002a':
            print("SKU: US")
            region_value = 0
        else:
            print("SKU: WorldWide")

        sstr = [
            "sudo echo -e '\\x{:02x}'".format(region_value),
            "| dd of=" + self.eegenbin_path,
            "bs=1",
            "count=1",
            "seek=20",
            "conv=notrunc"
        ]
        sstr = ' '.join(sstr)
        log_debug("add region to flash cmd: " + sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)

        #<--------





        host_path = "/tftpboot/{}".format(self.eegenbin)
        dut_path = "/tmp/{}".format(self.eegenbin)
        self.session.put_file(host_path, dut_path)
        time.sleep(1)

        cmd_grep = "ls /tmp | grep {}".format(self.eegenbin)
        if self.session.execmd(cmd_grep) == 0:
            log_debug("{} uploaded successfully".format(self.eegenbin))
        else:
            self.critical_error("{} uploaded failed".format(self.eegenbin))

        cmd_dd = "dd if=/tmp/{0} of={1} bs=1k count=64".format(self.eegenbin, self.devregpart)
        log_debug(cmd_dd)
        self.session.execmd(cmd_dd)

        # check if it duplicated successfully
        devregpart_name = self.devregpart.split("/")[-1]
        cmd_grep = "ls /{} | grep {}".format(self.devregpart.replace(devregpart_name, ""), devregpart_name)
        if self.session.execmd(cmd_grep) == 0:
            log_debug("{} duplicated successfully".format(devregpart_name))
        else:
            self.critical_error("{} duplicated failed".format(devregpart_name))

    def prepare_server_need_files_ssh(self):
        log_debug("Starting to do " + self.helperexe + "...")

        src = os.path.join(self.host_toolsdir_dedicated, self.helperexe)
        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)

        self.session.execmd("rm {}".format(helperexe_path))

        host_path = src
        dut_path = helperexe_path
        self.session.put_file(host_path, dut_path)
        time.sleep(1)

        # check if it uploaded successfully
        cmd_grep = "ls {} | grep {}".format(self.dut_tmpdir, self.helperexe)
        if self.session.execmd(cmd_grep) == 0:
            log_debug("{} uploaded successfully".format(self.helperexe))
        else:
            self.critical_error("{} uploaded failed".format(self.helperexe))

        cmd_chmod = "chmod 777 {}".format(helperexe_path)
        if self.session.execmd(cmd_chmod) == 0:
            log_debug("{} chmod 777 successfully".format(self.helperexe))
        else:
            self.critical_error("{} chmod 777 failed".format(self.helperexe))

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class=camera2",
            "-o field=flash_eeprom,format=binary,pathname=" + eebin_dut_path,
            ">",
            eetxt_dut_path
        ]
        sstr = ' '.join(sstr)

        log_debug(sstr)
        self.session.execmd(sstr)
        if self.session.execmd(cmd_chmod) == 0:
            log_debug("provided {} & {} successfully".format(self.eebin, self.eetxt))
        else:
            self.critical_error("provided {} & {} failed".format(self.eebin, self.eetxt))

        log_debug("Send helper output tgz file from DUT to host ...")
        files = [self.eebin, self.eetxt, self.eegenbin]

        for fh in files:
            fh_path = os.path.join(self.tftpdir, fh)

            # os.chmod(fh_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            host_path = fh_path
            dut_path = os.path.join(self.dut_tmpdir, fh)
            self.session.get_file(dut_path, host_path)
            time.sleep(1)

        # UVC-G3BATTERY
        # modify following addr
        # addr: 0x0014 -> 0xFF  (world-wide)
        # addr: 0x0015 -> 0x01 (BatteryPack: APACK)
        # this project skips the step of compare e.b.0 & e.g.0, it's too nuch work to dd cause its helper
        if self.product_name == "UVC-G3BATTERY":
            self.g3battery_modify_eegenbin()
            cmd_cp = "cp {} {}".format(self.eegenbin_path, self.eebin_path)
            self.fcd.common.xcmd(cmd_cp)

        rtc = filecmp.cmp(self.eegenbin_path, self.eebin_path)

        if rtc is True:
            otmsg = "Comparing files {0} and {1} are the same".format(self.eebin, self.eegenbin)
            log_debug(otmsg)
        else:
            cmd = "cmp /tmp/{} /tmp/{}".format(self.eebin, self.eegenbin)
            log_debug(self.session.execmd_getmsg(cmd))

            otmsg = "Comparing files failed!! {0}, {1} are not the same".format(self.eebin, self.eegenbin)
            self.critical_error(otmsg)

    def check_devreg_data_ssh(self, dut_tmp_subdir=None, mtd_count=None, post_exp=True, timeout=10):
        """check devreg data
        in  ructure of fcd-script-tools repo
        """
        log_debug("Send signed eeprom file from host to DUT ...")

        eechk_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eechk) if dut_tmp_subdir is not None \
            else os.path.join(self.dut_tmpdir, self.eechk)
        eesign_dut_path = os.path.join(self.dut_tmpdir, dut_tmp_subdir, self.eesign) if dut_tmp_subdir is not None \
            else os.path.join(self.dut_tmpdir, self.eesign)

        # upload e.s.0(64kb) to DUT
        host_path = self.eesign_path
        dut_path = eesign_dut_path
        self.session.put_file(host_path, dut_path)
        time.sleep(1)
        # check if it uploaded successfully
        cmd_grep = "ls /tmp | grep {}".format(self.eesign)
        if self.session.execmd(cmd_grep) == 0:
            log_debug("{} uploaded successfully".format(self.eesign))
        else:
            self.critical_error("{} uploaded failed".format(self.eesign))

        # chmod
        cmd_chmod = "chmod 777 {}".format(eesign_dut_path)
        if self.session.execmd(cmd_chmod) == 0:
            log_debug("{} chmod 777 successfully".format(eesign_dut_path))
        else:
            self.critical_error("{} chmod 777 failed".format(eesign_dut_path))

        # UVC-G3BATTERY
        if self.product_name == "UVC-G3BATTERY":
            log_debug("Remove and re-install spi-ambarella.ko & m25p80.ko.")
            self.session.execmd("rmmod m25p80; rmmod spi_ambarella")
            self.upload_flash_module()

            self.session.execmd("touch /var/lock/security")

            # cameras need to erase the flash first; Otherwise e.b.0 will not be the same with e.g.0
            self.erase_flash_rom()

            log_debug("Starting to write signed info to SPI flash ...")
            cmd_dd = "dd if={0} of={1} bs=1k count=64".format(eesign_dut_path, self.devregpart)
            log_debug(cmd_dd)
            self.session.execmd(cmd_dd)

            log_debug("Starting to extract the EEPROM content from SPI flash ...")
            cmd_dd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
            log_debug(cmd_dd)
            self.session.execmd(cmd_dd)

            self.session.execmd("rm /var/lock/security")
            self.session.execmd("sync")

        else:
            self.erase_flash_rom() 

            log_debug("Starting to write signed info to SPI flash ...")
            cmd_dd = "dd if={0} of={1} bs=1k count=64".format(eesign_dut_path, self.devregpart)
            log_debug(cmd_dd)
            self.session.execmd(cmd_dd)

            log_debug("Starting to extract the EEPROM content from SPI flash ...")
            cmd_dd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
            log_debug(cmd_dd)
            self.session.execmd(cmd_dd)

        os.mknod(self.eechk_path)
        os.chmod(self.eechk_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        # get e.c.0 from DUT to host
        log_debug("Send " + self.eechk + " from DUT to host ...")
        host_path = self.eechk_path
        dut_path = eechk_dut_path
        self.session.get_file(dut_path, host_path)
        time.sleep(3)  # in case the e.c.0 is still in transfering

        # compare e.s.0 and e.c.0
        if os.path.isfile(self.eechk_path):
            otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, self.eesign)
            log_debug(otmsg)
            rtc = filecmp.cmp(self.eechk_path, self.eesign_path)
            if rtc is True:
                self.eerom_status = 9 #eerom on DUT has devreg success data
                log_debug("Comparing files successfully")
            else:
                self.critical_error("Comparing files failed!!")
        else:
            otmsg = "Can't find the {0} and {1} files ...".format(self.eechk, self.eesign)
            log_debug(otmsg)

    def fwupdate(self):
        log_debug("Clear /tmp before upload fw")
        cmd = "rm /tmp/e.*; rm /tmp/helper*; rm /tmp/m25p80*; rm /tmp/eerom_backup*"
        log_debug(cmd)
        self.session.execmd(cmd)

        cmd = 'cat /etc/inittab | grep -v "ubnt_analytics" > /tmp/inittab; mv /tmp/inittab /etc/inittab; init -q ; pkill -9 ubnt_analytics'
        log_debug(cmd)
        self.session.execmd(cmd)        

        log_debug("Updating firmware...")
        host_path = self.fw_path
        dut_path = os.path.join(self.dut_tmpdir, "fwupdate.bin")
        self.session.put_file(host_path, dut_path)
        time.sleep(1)

        # check if it uploaded successfully
        cmd_grep = "ls /tmp | grep fwupdate.bin"
        if self.session.execmd(cmd_grep) == 0:
            log_debug("firmware {} uploaded successfully".format(self.firmware))
        else:
            self.critical_error("firmware {} uploaded failed".format(self.firmware))

        cmdstr = 'md5sum /tmp/fwupdate.bin'
        rmsg = (self.session.execmd_getmsg(cmdstr)).split()[0]
        print('fw md5 upload: ' + rmsg)
        print('fw md5 expect: ' + self.main_fw_bin_md5)



        # reset2defaults
        log_debug("=== reset2defaults ===")  

        cmd = 'md5sum /etc/persistent/server.pem'
        rmsg = (self.session.execmd_getmsg(cmd)).split()[0]
        rmsg = 'md5_server.pem_prev: ' + rmsg
        print(rmsg)
        log_debug(rmsg)

        cmd = 'touch /etc/persistent/reset.flag; cfgmtd -w -p /etc'
        log_debug(cmd)
        self.session.execmd(cmd)

        cmd = "cfgmtd -c"
        log_debug(cmd)
        self.session.execmd(cmd)

        cmd = "echo \"test.factory=1\" >> /tmp/system.cfg"
        log_debug(cmd)
        self.session.execmd(cmd)



        log_debug("installing firmware")
        cmd = "fwupdate -m"
        log_debug(cmd)
        if self.session.execmd(cmd) == 0:
            log_debug("firmware {} updated successfully".format(self.firmware))
        else:
            log_debug("firmware {} updated failed".format(self.firmware))

        self.session.close()

    def check_info_ssh(self):
        time.sleep(20)    
        sshclient_obj = SSHClient(host=self.ip,
                                  username=self.username,
                                  password=self.password,
                                  polling_connect=True,
                                  polling_mins=3)
        self.set_sshclient_helper(ssh_client=sshclient_obj)
        log_debug("reconnected with DUT successfully")


        cmd = 'md5sum /etc/persistent/server.pem'
        rmsg = (self.session.execmd_getmsg(cmd)).split()[0]
        rmsg = 'md5_server.pem_new: ' + rmsg
        print(rmsg)
        log_debug(rmsg)


        # show fw version
        cmd = 'cat /usr/lib/version'
        fwver_read = (self.session.execmd_getmsg(cmd)).split()[0]
        msgstr_read   = "fw version   read: [{}]".format(fwver_read)
        log_debug(msgstr_read)

        msgstr_expect = "fw version expect: [{}]".format(self.main_fw_version)
        print(msgstr_read)
        print(msgstr_expect)

        if self.main_fw_version != "":
            log_debug(msgstr_expect)
            if fwver_read != self.main_fw_version:
                self.critical_error('fw version not match')
            else:
                log_debug("fw version match.")

        # check the following items
        chk_items = {"board.name": self.board_name, "board.sysid": self.board_id, "board.hwaddr": self.mac}
        for keys, values in chk_items.items():
            cmd = "cat /etc/board.info | grep {}".format(keys)
            log_debug("cmd = " + cmd)

            msg = str(self.session.execmd_getmsg(cmd)).lower()
            logmsg = "host {} = {}, DUT {}".format(keys, values.lower(), msg)

            if values.lower() not in msg:
                otmsg = logmsg + "{} in host and DUT are NOT the same".format(keys)
                self.critical_error(otmsg)
            else:
                otmsg = logmsg + "{} in host and DUT are the same".format(keys)
                log_debug(otmsg)

        msg_info= self.session.execmd_getmsg('cat /etc/board.info')
        print(msg_info)


    def eesign_datecode(self):

        log_debug("Adding the datecode into eesign(e.s.0)")

        eesignFCD_path = self.eesign_path+".FCD"
        date = time.strftime("%Y%m%d" , time.localtime())
        flasheditor = os.path.join(self.devnetmeta['flashed_dir'], self.eepmexe)

        sstr = [
                    flasheditor,
                    "-B",
                    self.eesign_path,
                    "-d",
                    date
                ]

        sstr = ' '.join(sstr)

        log_debug("flash editor cmd: " + sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)

        if int(rtc) > 0:
            otmsg = "Generating {0} file failed!!".format(eesignFCD_path)
            self.critical_error(otmsg)
        else:
            otmsg = "Generating {0} files successfully".format(eesignFCD_path)
            log_debug(otmsg)

        # rename e.s.0.FCD to e.s.0 and check if date and "TlvInfo" in stander output
        cmd = "sudo mv {} {}".format(eesignFCD_path, self.eesign_path)
        self.fcd.common.xcmd(cmd)

        cmd = "hexdump {} -s 0xd000 -n 100 -C".format(self.eesign_path)
        [sto, rtc] = self.fcd.common.xcmd(cmd)

        if date in str(sto) and "TlvInfo" in str(sto):
            log_debug("{} renamed to {} successfully".format(eesignFCD_path, self.eesign_path))
        else:
            self.critical_error("{} renamed to {} failed!".format(eesignFCD_path, self.eesign_path))

    def g3battery_modify_eegenbin(self):

        if self.product_name == "UVC-G3BATTERY":
            ascii_g3_path = os.path.join(self.host_toolsdir_dedicated, "eegen-ascii_g3battery.bin")

            cmd_modify = "sudo cp {} {}.t".format(self.eegenbin_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                self.critical_error("Generating e.g.0.t file failed!!")
            else:
                log_debug("Generating e.g.0.t files successfully")

            cmd_modify = "sudo dd if={} of={}.t bs=1 count=2 seek=20".format(ascii_g3_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                self.critical_error("Generating e.g.0.t file failed!!")
            else:
                log_debug("Generating e.g.0.t files successfully")

            cmd_modify = "sudo dd if={} of={}.t bs=1 skip=22 seek=22".format(self.eegenbin_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                self.critical_error("Generating e.g.0.t file failed!!")
            else:
                log_debug("Generating e.g.0.t files successfully")

            cmd_modify = "sudo mv {}.t {}".format(self.eegenbin_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                self.critical_error("Modified e.g.0 file failed!!")
            else:
                log_debug("Modified e.g.0 files successfully")

    def run(self):
        """
        Main procedure of factory
        """

        sshclient_obj = SSHClient(host=self.ip,
                                  username=self.username,
                                  password=self.password,
                                  polling_connect=True,
                                  polling_mins=self.polling_mins)

        self.set_sshclient_helper(ssh_client=sshclient_obj)
        log_debug(self.session.execmd_getmsg("pwd"))
        log_debug(self.session.execmd_getmsg("uptime"))
        log_debug(self.session.execmd_getmsg("cat /usr/lib/version"))
        log_debug(self.session.execmd_getmsg("cat /etc/board.info"))
        time.sleep(1)

        log_debug("Uploading flash module...")

        time_start = time.time()
        self.upload_flash_module()
        self.eerom_status = 0
        self.finalret = True
        duration = int(time.time() - time_start)
        log_debug('==> duration_{cap}: {time} seconds'.format(cap='upload_flash', time=duration))




        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if self.finalret is True:
            if PROVISION_EN is True:
                time_start = time.time()

                if self.finalret is True:
                    msg(20, "Erase flash...")
                    self.erase_flash_rom()
                
                if self.finalret is True:
                    msg(25, "Send tools to DUT and data provision ...")
                    self.data_provision_64k_ssh(self.devnetmeta)
                
                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='PROVISION', time=duration))

        
        if self.finalret is True:
            if DOHELPER_EN is True:
                time_start = time.time()

                if self.finalret is True:    
                    try:
                        self.erase_eefiles()
                    except Exception as e:
                        print(str(e))
                        self.critical_error("helper erase_eefiles fail")

                if self.finalret is True:    
                    msg(30, "Do helper to get the output file to devreg server ...")
                    self.prepare_server_need_files_ssh()
                    
                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='DOHELPER', time=duration))            


        if self.finalret is True:
            if REGISTER_EN is True:
                time_start = time.time()

                msg(40, "Checking registration ...")
                if self.check_if_need_register_again() is True:
                    msg(50, "Do not need doing registration again...")        

                else:
                    if self.finalret is True: 
                        msg(43, "Doing registration ...")
                        try:
                            self.registration()
                            msg(49, "register PASS")
                        except Exception as e:
                            print(str(e))
                            msg(48, "register FAIL")
                            self.critical_error("register FAIL")
                    

                    if self.finalret is True:
                        self.check_devreg_data_ssh()
                        msg(50, "Finish doing signed file and EEPROM checking ...")

                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='REGISTER', time=duration))   


        #always check if need to write back eerom bin
        self.check_if_need_restore_eerom()


        '''
            ============ Registration End ============
        '''
        if self.finalret is True:
            if FWUPDATE_EN is True:
                time_start = time.time()
                self.fwupdate()
                msg(70, "Succeeding in downloading the upgrade tar file ...")
                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='FWUPDATE', time=duration))              

        if self.finalret is True:
            if DATAVERIFY_EN is True:
                time_start = time.time()
                self.check_info_ssh()
                msg(80, "Succeeding in checking the devreg information ...")
                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='DATAVERIFY', time=duration))

        log_debug('=================================================================================.')


        if self.finalret is True:
            msg(100, "Complete FCD process.")
        else:
            log_debug('done.')
            error_critical(self.errmsg)

        self.close_fcd()


def main():
    uvc_factory_general = UVCFactoryGeneral()
    uvc_factory_general.run()


if __name__ == "__main__":
    main()
