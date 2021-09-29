#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.ssh_client import SSHClient
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_error

import time
import os
import stat
import filecmp
import configparser


# a580 = G3BATTERY
# a563 = G4PRO
# a564 = G4PTZ
# a571 = G4DOORBELL
# a572 = G4BULLET
# a573 = G4DOME
# a574 = G4DOORBELLPRO
# a5a0 = AI360
# a590 = G3MINI
# a595 = G4INS
# a5a2 = AIBullet
# ec70 = Thermal Scan


PROVISION_EN  = True
DOHELPER_EN   = True
REGISTER_EN   = True
FWUPDATE_EN   = True
DATAVERIFY_EN = True
# REGISTER_EN   = False
# FWUPDATE_EN   = False
# DATAVERIFY_EN = False


class UVCFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UVCFactoryGeneral, self).__init__()

        self.devregpart = ''
        self.mtd_name = 'spi'
        self.helper_rule = 0
        '''
        Please set "self.helper_rule = 1" in each product if it follows new rule that
        doesn't need m25p80 and helper, refer to "UVC-G4PTZ"
        '''
        if self.product_name == "UVC-G3BATTERY":
            self.board_name = "UVC G3 Battery"
            self.devregpart = "/dev/mtd15"
            self.ip = "192.168.2.20"
            self.flash_module = "m25p80_g3battery.ko"
            self.helperexe = "helper_S2LM_g3battery"

        elif self.product_name == "UVC-G4PRO":
            self.board_name = "UVC G4 Pro"
            if self.bom_rev.split('-')[1] == "11":
                self.devregpart = "/dev/mtd8"
            else:
                self.devregpart = "/dev/mtd10"
            self.ip = "192.168.1.20"
            self.flash_module = "m25p80_g4pro.ko"
            self.helperexe = "helper_S5L_g4pro"

        elif self.product_name == "UVC-G4PTZ":
            self.board_name = "UVC G4 PTZ"
            self.ip = "192.168.1.20"
            self.helper_rule = 1

        elif self.product_name == "UVC-G4DOORBELL":
            self.board_name = "UVC G4 Doorbell"
            self.devregpart = "/dev/mtd10"
            self.ip = "192.168.2.20"
            self.flash_module = "m25p80_uvcg4doorbell.ko"
            self.helperexe = "helper_uvcg4doorbell"

        elif self.product_name == "UVC-G4BULLET":
            second_falsh_en = True
            if second_falsh_en is True:
                self.board_name = "UVC-G4BULLET"
                self.ip = "192.168.2.20"
                self.mtd_name = 'spi'
                self.helper_rule = 1
            else:
                self.board_name = "UVC G4 Bullet"
                self.devregpart = "/dev/mtd8"
                self.ip = "192.168.2.20"
                self.flash_module = "m25p80_uvcg4bullet.ko"
                self.helperexe = "helper_uvcg4bullet"

        elif self.product_name == "UVC-G4DOME":
            second_falsh_en = True
            if second_falsh_en is True:
                self.board_name = "UVC-G4DOME"
                self.ip = "192.168.1.20"
                self.mtd_name = 'spi'
                self.helper_rule = 1
            else:
                self.board_name = "UVC G4 Dome"
                self.devregpart = "/dev/mtd8"
                self.ip = "192.168.2.20"
                self.flash_module = "m25p80_uvcg4dome.ko"
                self.helperexe = "helper_uvcg4dome"

        elif self.product_name == "UVC-G4DOORBELLPRO":
            self.board_name = "UVC G4 Doorbell Pro"
            self.devregpart = "/dev/mtd8"
            self.ip = "169.254.2.20"
            self.flash_module = "m25p80_uvcg4doorbellpro.ko"
            self.helperexe = "helper_uvcg4doorbellpro"

        elif self.product_name == "UVC-AI360":
            # second_falsh_en = False
            second_falsh_en = True
            if second_falsh_en is True:
                self.board_name = "UVC AI 360"
                self.ip = "192.168.1.20"
                self.mtd_name = 'amba_nor'
                self.helper_rule = 1
            else:
                self.board_name = "UVC AI 360"
                self.devregpart = "/dev/mtd0"
                self.ip = "192.168.1.20"
                self.flash_module = ""
                self.helperexe = "helper_uvcai360"

        elif self.product_name == "UVC-G3MINI":
            second_falsh_en = True
            if second_falsh_en is True:
                self.board_name = "UVC G3 Mini"
                self.ip = "192.168.2.20"
                self.mtd_name = 'spi'
                self.helper_rule = 1
            else:
                self.board_name = "UVC G3 Mini"
                self.devregpart = "/dev/mtd11"
                self.ip = "192.168.2.20"
                self.flash_module = "m25p80_uvcg3flexmini.ko"
                self.helperexe = "helper_uvcg3flexmini"

        elif self.product_name == "UVC-G4INS":
            self.board_name = "UVC G4 Instant"
            self.ip = "169.254.2.20"
            self.helper_rule = 1

        elif self.product_name == "UVC-AIBULLET":
            self.board_name = "UVC AI Bullet"
            self.ip = "192.168.1.20"
            self.mtd_name = 'amba_nor'
            self.helper_rule = 1

        elif self.product_name == "UA-Thermal-Scan":
            self.board_name = "UniFi Thermal Scan"
            self.ip = "192.168.1.20"
            self.mtd_name = 'amba_nor'
            self.helper_rule = 1

        elif self.product_name == "UVC-AITHETA":
            self.board_name = "UVC AI THETA"
            self.ip = "192.168.1.73"
            self.mtd_name = 'amba_nor'
            self.helper_rule = 1

        ''' '''
        self.fillff = "128k_ff.bin"
        self.ver_extract()
        self.firmware = "{}-fw.bin".format(self.board_id)
        self.username = "ubnt"
        self.password = "ubnt"
        self.polling_mins = 5
        self.host_toolsdir_dedicated = os.path.join(self.fcd_toolsdir, "uvc")
        self.fw_path = os.path.join(self.fwdir, self.firmware)
        self.fwinfo_path = os.path.join(self.fwdir, "{}-fw.ini".format(self.board_id))
        self.fwinfo_extract()
        self.eerom_status = 0
        self.errmsg = ""

        # number of Ethernet
        ethnum = {
            'a580': "0",
            'a563': "1",
            'a564': "1",
            'a571': "0",
            'a572': "1",
            'a573': "1",
            'a574': "0",
            'a590': "0",
            'a595': "0",
            'a5a0': "1",
            'a5a2': '1',
            'ec70': '1',
            'a5a3': '1'
        }

        # number of WiFi
        wifinum = {
            'a580': "1",
            'a563': "0",
            'a564': "0",
            'a571': "1",
            'a572': "0",
            'a573': "0",
            'a574': "1",
            'a590': "1",
            'a595': "1",
            'a5a0': "0",
            'a5a2': '0',
            'ec70': '0',
            'a5a3': '0'
        }

        # number of Bluetooth
        btnum = {
            'a580': "1",
            'a563': "0",
            'a564': "0",
            'a571': "1",
            'a572': "0",
            'a573': "0",
            'a574': "1",
            'a590': "1",
            'a595': "1",
            'a5a0': "0",
            'a5a2': '0',
            'ec70': '0',
            'a5a3': '0'
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
            'a574': "ifconfig eth0 ",
            'a590': "ifconfig eth0 ",
            'a595': "ifconfig eth0 ",
            'a5a0': "ifconfig eth0 ",
            'a5a2': "ifconfig eth0 ",
            'ec70': "ifconfig eth0 "

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

        self.fw_dir = self.ezreadini(self.fwinfo_path, 'MAIN', 'fw_dir')
        print("fw_dir: " + self.fw_dir)

        ini_fw_dir = os.path.join(self.tftpdir, self.fw_dir)
        print("ini_fw_dir: " + ini_fw_dir)

        self.fw_name = self.ezreadini(self.fwinfo_path, 'MAIN', 'fw_name')
        print("fw_name: " + self.fw_name)

        self.ini_fw_path = os.path.join(self.tftpdir, ini_fw_dir, self.fw_name)
        print("ini_fw_path: " + self.ini_fw_path)

        self.fw_version = self.ezreadini(self.fwinfo_path, 'MAIN', 'fw_version')
        print("fw_version: " + self.fw_version)

    def critical_error(self, msg):
        self.finalret = False
        self.errmsg = msg
        log_error(msg)

    def _get_urescue_fw_version(self):
        try:
            mtd = self.session.execmd_getmsg('cat /proc/mtd | grep urc')
            mtd = '/dev/{}'.format(mtd.split(':')[0])
            cmd = "hexdump {} -s 4 -n 64 -e '16/1 \"%c\"'".format(mtd)
            print(cmd)
            version = self.session.execmd_getmsg(cmd)
            version = version.strip('\n\t\r\0')
        except Exception as e:
            print(str(e))
            version = ''
        return version

    def get_fw_version(self):
        try:
            cmd = 'cat /usr/lib/version'
            print(cmd)
            version = self.session.execmd_getmsg(cmd)
            version = version.strip('\n\t\r\0')
        except Exception as e:
            print(str(e))
            version = ''
        return version

    def get_devreg_mtd(self):
        mtd_all = self.session.execmd_getmsg('cat /proc/mtd')
        print('mtd all = {}'.format(mtd_all))

        mtd = self.session.execmd_getmsg('cat /proc/mtd | grep {}'.format(self.mtd_name))
        print('mtd = {}'.format(mtd))
        mtd = '/dev/{}'.format(mtd.split(':')[0])
        return mtd

    def get_cpu_id(self):
        res = self.session.execmd_getmsg('cat /tmp/bsp_helper/cpuid').strip('\n')
        if res == 'AMBA':
            ssi_ident_id = '414d4241'
            ssi_version_id = '312e3030'
        elif res == 'SStar':
            ssi_ident_id = '53537461'
            ssi_version_id = '53537461'
        else:
            ssi_ident_id = '00000000'
            ssi_version_id = '00000000'
        return ssi_ident_id, ssi_version_id

    def get_jedec_id(self):
        res = self.session.execmd_getmsg('cat /tmp/bsp_helper/jedec_id').strip('\n')
        id = res.zfill(8)
        return id

    def get_flash_uid(self):
        res = self.session.execmd_getmsg('cat /tmp/bsp_helper/otp').strip('\n')
        id = res
        return id

    def helper_generate_e_t(self, output_path='/tmp/e.t'):
        log_debug('helper_generate_e_t to {}'.format(output_path))
        ssi_ident_id, ssi_version_id = self.get_cpu_id()
        jedec_id = self.get_jedec_id()
        flash_uid = self.get_flash_uid()

        sstr = [
            'field=product_class_id,format=hex,value=000a',
            'field=flash_jedec_id,format=hex,value={}'.format(jedec_id),
            'field=flash_uid,format=hex,value={}'.format(flash_uid),
            'field=AMBA_ssi_ident_id,format=hex,value={}'.format(ssi_ident_id),
            'field=AMBA_ssi_version_id,format=hex,value={}'.format(ssi_version_id)
        ]
        sstr = '\n'.join(sstr)
        log_debug(sstr)

        cmd = 'echo "{}" > {}'.format(sstr, output_path)
        if self.session.execmd(cmd) == 0:
            log_debug("provided {} successfully".format(output_path))
        else:
            self.critical_error("provided {} failed".format(output_path))

    def helper_generate_e_b(self, output_path='/tmp/e.b'):
        log_debug('helper_generate_e_b to {}'.format(output_path))

        cmd_dd = "dd if={} of={} bs=1k count=64".format(self.devregpart, output_path)
        if self.session.execmd(cmd_dd) == 0:
            log_debug("provided {} successfully".format(output_path))
        else:
            self.critical_error("provided {} failed".format(output_path))

    def upload_flash_module(self):
        if self.devregpart == '':
            self.devregpart = self.get_devreg_mtd()
        log_debug('devpart:' + self.devregpart)

        if self.helper_rule == 1:
            dut_ff_path = "/tmp/{}".format(self.fillff)
            cmd = "tr '\\000' '\\377' < /dev/zero | dd of={} bs=1k count=128".format(dut_ff_path)
            log_debug(cmd)
            self.session.execmd(cmd)

        else:
            flash_fillff_path = os.path.join(self.host_toolsdir_dedicated, self.fillff)
            host_path = flash_fillff_path
            dut_path = "/tmp/{}".format(self.fillff)
            self.session.put_file(host_path, dut_path)

            if self.flash_module != "":  # need to upload and install module
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

        if self.product_name != "UVC-G3MINI":
            log_debug("dump flash module")
            cmdstr = "hexdump -C {} 2>&1".format(self.devregpart)
            log_debug(cmdstr)
            rmsg = self.session.execmd_getmsg(cmdstr)
            log_debug(rmsg)
            self.eerom_status = 1

    def check_if_need_register_again(self):
        return False

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
        print('rmsg = {}'.format(rmsg))

        if int(rmsg) != 0:
            log_debug('"/tmp/eerom_backup.bin" does "NOT" exist')
            return -1
        log_debug('"/tmp/eerom_backup.bin" exist')

        if self.eerom_status != 0 and self.eerom_status != 9:
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

        if self.region == '002a':
            print("SKU: US")
            region_value = 0
        else:
            print("SKU: WorldWide")
            region_value = 255

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
        log_debug("cmd_grep: {}".format(cmd_grep))

        if self.session.execmd(cmd_grep) == 0:
            log_debug("{} duplicated successfully".format(devregpart_name))
        else:
            self.critical_error("{} duplicated failed".format(devregpart_name))

    def prepare_server_need_files_ssh(self):
        log_debug('prepare_server_need_files_ssh()')

        if self.helper_rule == 1:
            eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
            eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
            self.helper_generate_e_t(eetxt_dut_path)
            self.helper_generate_e_b(eebin_dut_path)
        else:

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
                self.eerom_status = 9  # eerom on DUT has devreg success data
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
        host_path = self.ini_fw_path
        dut_path = os.path.join(self.dut_tmpdir, "fwupdate.bin")
        self.session.put_file(host_path, dut_path)
        time.sleep(1)

        # check if it uploaded successfully
        cmd_grep = "ls /tmp | grep fwupdate.bin"
        if self.session.execmd(cmd_grep) == 0:
            log_debug("firmware {} uploaded successfully".format(self.ini_fw_path))
        else:
            self.critical_error("firmware {} uploaded failed".format(self.ini_fw_path))

        cmdstr = 'md5sum /tmp/fwupdate.bin'
        rmsg = (self.session.execmd_getmsg(cmdstr)).split()[0]
        print('fw md5 upload: ' + rmsg)

        # reset2defaults
        log_debug("=== reset2defaults ===")

        cmd = 'md5sum /etc/persistent/server.pem'
        rmsg = (self.session.execmd_getmsg(cmd)).split()[0]
        rmsg = 'md5_server.pem_prev: ' + rmsg
        print(rmsg)
        log_debug(rmsg)

        try:
            cmd = 'ps | grep burnin.sh | grep -v grep | awk \'{print $1}\' | xargs kill -9'
            log_debug(cmd)
            self.session.execmd(cmd)

            cmd = 'sed -i "s@null::respawn:/bin/ubnt_ctlserver@#null::respawn:/bin/ubnt_ctlserver@"   /etc/inittab && init -q && killall -9 ubnt_ctlserver'
            log_debug(cmd)
            self.session.execmd(cmd)
        except:
            print('skip')

        cmd = "echo \"test.factory=1\" >> /tmp/system.cfg"
        log_debug(cmd)
        self.session.execmd(cmd)

        cmd = 'touch /etc/persistent/reset.flag; cfgmtd -w -p /etc'
        log_debug(cmd)
        self.session.execmd(cmd)

        cmd = 'touch /etc/persistent/fastboot.flag && cfgmtd -w -p /etc'
        log_debug(cmd)
        self.session.execmd(cmd)
        time.sleep(0.2)

        log_debug("installing firmware")
        cmd = "fwupdate -m"
        log_debug(cmd)
        if self.session.execmd(cmd) == 0:
            log_debug("firmware {} updated successfully".format(self.ini_fw_path))
        else:
            log_debug("firmware {} updated failed".format(self.ini_fw_path))
        self.session.close()

    def check_info_ssh(self):
        time_start = time.time()
        time.sleep(50)

        try:
            sshclient_obj = SSHClient(host=self.ip,
                                    username=self.username,
                                    password=self.password,
                                    polling_connect=True,
                                    polling_mins=7)
            self.set_sshclient_helper(ssh_client=sshclient_obj)
            log_debug("reconnected with DUT successfully")
        except Exception as e:
            print(str(e))
            self.critical_error("reconnected with DUT timeout fail")

        log_debug('Reboot duration = {:.2f} sec'.format(time.time() - time_start))

        cmd = "sudo rm /t/home/ubnt/.ssh/known_hosts; sync; sleep 1".format(self.row_id)
        log_debug(cmd)
        [output, rv] = self.cnapi.xcmd(cmd)

        time.sleep(5)
        cmd = 'md5sum /etc/persistent/server.pem'
        rmsg = (self.session.execmd_getmsg(cmd)).split()[0]
        log_debug('md5_server.pem_new: {}'.format(rmsg))

        # show fw version
        cmd = 'cat /usr/lib/version'
        fwver_read = (self.session.execmd_getmsg(cmd)).split()[0]
        msgstr_read = "fw version in DUT = [{}]".format(fwver_read)
        log_debug(msgstr_read)

        msgstr_expect = "fw version expect = [{}]".format(self.fw_version)

        if self.fw_version != "":
            log_debug(msgstr_expect)
            if fwver_read != self.fw_version:
                self.critical_error('[Fail] fw version not match')
            else:
                log_debug("[Pass] fw version match.")

        # check the following items
        chk_items = {"board.sysid": self.board_id, "board.hwaddr": self.mac}
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

        msg_info = self.session.execmd_getmsg('cat /etc/board.info')
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

    def _get_init_dut_info(self):
        log_debug('===Init dut info'.ljust(80, '='))

        pwd = self.session.execmd_getmsg("pwd")
        print('pwd = {}'.format(pwd))

        uptime = self.session.execmd_getmsg("uptime")
        print('uptime = {}'.format(uptime))

        fw_version = self.session.execmd_getmsg("cat /usr/lib/version")
        print('cat /usr/lib/version = \n{}'.format(fw_version))

        board_info = self.session.execmd_getmsg("cat /etc/board.info")
        print('board_info = {}'.format(board_info))

        urescue_fw_version = self._get_urescue_fw_version()
        print('urescue_fw = {}'.format(urescue_fw_version))

        time.sleep(1)

    def _log_duration(self, action, time_start):
        duration_msg = '\n\n ===> [Time Elapsed] {cap}: {time} sec'
        duration = int(time.time() - time_start)
        log_debug(duration_msg.format(cap=action, time=duration))

    def run(self):
        """  Main procedure of factory
        """

        sshclient_obj = SSHClient(host=self.ip,
                                  username=self.username,
                                  password=self.password,
                                  polling_connect=True,
                                  polling_mins=self.polling_mins)

        self.set_sshclient_helper(ssh_client=sshclient_obj)
        self._get_init_dut_info()

        log_debug("Uploading flash module...")

        time_start = time.time()
        self.upload_flash_module()
        self.eerom_status = 0
        self.finalret = True
        self._log_duration('upload_flash', time_start)

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
                self._log_duration('PROVISION', time_start)

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
                self._log_duration('DOHELPER', time_start)

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
                self._log_duration('REGISTER', time_start)

        # always check if need to write back eerom bin
        self.check_if_need_restore_eerom()

        ''' ============ Registration End ============
        '''
        if self.finalret is True:
            if FWUPDATE_EN is True:
                time_start = time.time()
                self.fwupdate()
                msg(70, "Succeeding in downloading the upgrade tar file ...")
                self._log_duration('FWUPDATE', time_start)

        if self.finalret is True:
            if DATAVERIFY_EN is True:
                time_start = time.time()
                self.check_info_ssh()
                msg(80, "Succeeding in checking the devreg information ...")
                self._log_duration('DATAVERIFY', time_start)

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
