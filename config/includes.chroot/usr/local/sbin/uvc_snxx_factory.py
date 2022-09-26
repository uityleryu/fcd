#!/usr/bin/python3

import sys
import os
import time
import subprocess
import stat
from soc_lib.snxx_lib import SnxxLib
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical

class SonixDevreg(SnxxLib):
    def __init__(self):
        super(SonixDevreg, self).__init__()

    # def pcmd(self, cmd):
    #     output = subprocess.Popen([cmd], shell=True, executable='/bin/bash', stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
    #                               universal_newlines = True)
    #     output.wait()
    #     [stdout, stderr] = output.communicate()
    #
    #     if (output.returncode != 0):
    #         log_debug("pcmd returncode: " + str(output.returncode))
    #         log_debug(stdout)
    #         return False
    #     else:
    #         return True

    # def xcmd(self, cmd):
    #     output = subprocess.Popen([cmd], shell=True, executable='/bin/bash', stderr=None, stdout=subprocess.PIPE)
    #     output.wait()
    #     [stdout, stderr] = output.communicate()
    #     stdoutd = stdout.decode('UTF-8')
    #     log_debug(stdoutd)
    #     return [stdoutd, output.returncode]

    def critical_error(self, msg):
        self.finalret = False
        # print(msg)
        error_critical(msg)

    # def gen_rsa_key(self):
    #     if os.path.isfile(self.rsakey_path):
    #         cmd = "rm {}".format(self.rsakey_path)
    #         self.pcmd(cmd)
    #
    #     cmd = "dropbearkey -t rsa -f {0}".format(self.rsakey_path)
    #     log_debug(cmd)
    #     self.pcmd(cmd)
    #     '''
    #         The dropbearkey command will be executed in the FCD host.
    #         So, it won't cost too much time
    #     '''
    #     time.sleep(1)
    #
    #     cmd = "chmod 777 {0}".format(self.rsakey_path)
    #     self.pcmd(cmd)
    #
    #     rt = os.path.isfile(self.rsakey_path)
    #     if rt is not True:
    #         otmsg = "Can't find the RSA key file"
    #         critical_error(otmsg)

    # def erase_eefiles(self):
    #     log_debug("Erase existed eeprom information files ...")
    #     files = [self.eebin, self.eetxt, self.eechk, self.eetgz, self.rsakey, self.dsskey, self.eegenbin, self.eesign,
    #              self.eesigndate]
    #     #files = [self.eebin, self.eetxt, self.eechk, self.eetgz, self.rsakey, self.dsskey, self.eegenbin, self.eesigndate]
    #
    #     for f in files:
    #         destf = os.path.join(self.tftpdir, f)
    #         rtf = os.path.isfile(destf)
    #         if rtf is True:
    #             log_debug("Erasing File - " + f + " ...")
    #             os.chmod(destf, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    #             os.remove(destf)
    #         else:
    #             log_debug("File - " + f + " doesn't exist ...")

    def data_provision_64k(self):

        self.gen_rsa_key()

        otmsg = "Starting to do {0} ...".format(self.eepmexe) # X86-64-ee
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
            "-e " + "0", # ethnum
            "-w " + "0", # wifinum
            "-b " + "0", # btnum
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
        log_debug("flash editor cmd: " + sstr)
        # [sto, rtc] = self.xcmd(sstr)
        [sto, rtc] = self.cnapi.xcmd(sstr)
        time.sleep(1)

        if int(rtc) > 0:
            otmsg = "Generating {0} file failed!!".format(self.eegenbin_path)
            self.critical_error(otmsg)
            return
        else:
            otmsg = "Generating {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        #---------> edit e.gen
        log_debug('region: ')
        log_debug(self.region)
        log_debug('eegenbin:')
        log_debug(self.eegenbin)
        log_debug('eegenbin_path:')
        log_debug(self.eegenbin_path)

        region_value = 255
        if self.region == '002a':
            log_debug("SKU: US")
            region_value = 0
        else:
            log_debug("SKU: WorldWide")

        sstr = [
            "echo -e '\\x{:02x}'".format(region_value),
            "| dd of=" + self.eegenbin_path,
            "bs=1",
            "count=1",
            "seek=20",
            "conv=notrunc"
        ]
        sstr = ' '.join(sstr)
        log_debug("add region to flash cmd: " + sstr)
        # [sto, rtc] = self.xcmd(sstr)
        [sto, rtc] = self.cnapi.xcmd(sstr)
        time.sleep(1)
        #<--------
        try:
            res = self.read_devreg_flash_data(self.eeorg_path)
            if res:
                self.critical_error("read_devreg_flash_data failed!!: {0}".format(res))
                return
        except BaseException as err:
            self.critical_error("read_devreg_flash_data exception occurred!!: {0}".format(err))
            return

        log_debug("Writing the information from e.gen to e.org")
        try:
            '''
                Trying to access the initial information from the EEPROM of DUT and save to e.org.0
            '''
            f1 = open(self.eeorg_path, "rb")
            org_tres = list(f1.read())
            f1.close()

            '''
                Creating by the FCD host with the utiltiy eetool
            '''
            f2 = open(self.eegenbin_path, "rb")
            gen_tres = list(f2.read())
            f2.close()

            '''
                Writing the information from e.gen.0 to e.org.0
            '''
            f3 = open(self.eeorg_path, "wb")

            # Write 40K content to the first 40K section
            # 40 * 1024 = 40960 = 0xA000, 40K
            # the for loop will automatically count it from 0 ~ (content_sz - 1)
            # example:  0 ~ 40K = 0 ~ 40959
            content_sz = 40 * 1024
            for idx in range(0, content_sz):
                org_tres[idx] = gen_tres[idx]

            # Write 4K content start from 0xC000
            # 49152 = 0xC000 = 48K
            content_sz = 4 * 1024
            offset = 48 * 1024
            for idx in range(0, content_sz):
                org_tres[idx + offset] = gen_tres[idx + offset]

            # Write 8K content start from 0xE000
            # 57344 = 0xE000 = 56K
            content_sz = 8 * 1024
            offset = 56 * 1024
            for idx in range(0, content_sz):
                org_tres[idx + offset] = gen_tres[idx + offset]

            arr = bytearray(org_tres)
            f3.write(arr)
            f3.close()

            err = self.write_devreg_flash_data(self.eeorg_path)
            if err:
                self.critical_error("write_devreg_flash_data failed!!: {0}".format(err))
                return
        except BaseException as err:
            self.critical_error("Writing the information from e.gen to e.org exception occurred!!: {0}".format(err))
            return

    def prepare_server_need_files(self):
        err = self.read_devreg_helper_and_flash_data(self.eetxt_path, self.eebin_path)
        if err:
            self.critical_error("read_devreg_helper_and_flash_data failed!!: {0}".format(err))
            return

    def access_chips_id(self):
        cmd = [
            "cat " + self.eetxt_path,
            "|",
            'sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\"',
            "|",
            'grep -v \"eeprom\"',
            "|",
            "tr '\\n' ' '"
        ]
        cmdj = " ".join(cmd)
        # [sto, rtc] = self.xcmd(cmdj)
        [sto, rtc] = self.cnapi.xcmd(cmdj)
        if int(rtc) > 0:
            self.critical_error("Extract parameters failed!!")
        else:
            log_debug("Extract parameters successfully")
            return sto

    def registration(self, regsubparams = None):
        log_debug("Starting to do registration ...")
        if regsubparams is None:
            regsubparams = self.access_chips_id()

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

        # if self.sem_ver == "" or self.sw_id == "" or self.fw_ver == "":
        #     clientbin = "/usr/local/sbin/client_x86_release"
        clientbin = "/usr/local/sbin/client_rpi4_release"
        regparam = [
            "-h prod.udrs.io",
            "-k " + self.pass_phrase,
            regsubparams,
            reg_qr_field,
            "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
            "-o field=flash_eeprom,format=binary,pathname=" + self.eesign_path,
            "-o field=registration_id",
            "-o field=result",
            "-o field=device_id",
            "-o field=registration_status_id",
            "-o field=registration_status_msg",
            "-o field=error_message",
            "-x " + self.key_dir + "ca.pem",
            "-y " + self.key_dir + "key.pem",
            "-z " + self.key_dir + "crt.pem"
        ]
        print("WARNING: should plan to add SW_ID ... won't block this time")
        # else:
        #     cmd = "uname -a"
        #     [sto, rtc] = self.xcmd(cmd)
        #     if int(rtc) > 0:
        #         error_critical("Get linux information failed!!")
        #     else:
        #         log_debug("Get linux information successfully")
        #         match = re.findall("armv7l", sto)
        #         if match:
        #             clientbin = "/usr/local/sbin/client_rpi4_release"
        #         else:
        #             clientbin = "/usr/local/sbin/client_x86_release"
        #
        #     regparam = [
        #         "-h prod.udrs.io",
        #         "-k " + self.pass_phrase,
        #         regsubparams,
        #         reg_qr_field,
        #         "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
        #         "-i field=fcd_version,format=hex,value=" + self.sem_ver,
        #         "-i field=sw_id,format=hex,value=" + self.sw_id,
        #         "-i field=sw_version,format=hex,value=" + self.fw_ver,
        #         "-o field=flash_eeprom,format=binary,pathname=" + self.eesign_path,
        #         "-o field=registration_id",
        #         "-o field=result",
        #         "-o field=device_id",
        #         "-o field=registration_status_id",
        #         "-o field=registration_status_msg",
        #         "-o field=error_message",
        #         "-x " + self.key_dir + "ca.pem",
        #         "-y " + self.key_dir + "key.pem",
        #         "-z " + self.key_dir + "crt.pem"
        #     ]

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

    def add_FCD_TLV_info(self):
        log_debug("Gen FCD TLV data into " + self.eesign_path)
        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            self.critical_error("Can't find " + self.eesign)

        nowtime = time.strftime("%Y%m%d", time.gmtime())
        # /tftpboot/tools/common/x86-64k-ee
        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe)
        cmd = "{0} -B {1} -d {2} -r 113-{3}".format(flasheditor, self.eesign_path, nowtime, self.bom_rev)
        log_debug("cmd: " + cmd)
        # sto, rtc = self.xcmd(cmd)
        sto, rtc = self.cnapi.xcmd(cmd)
        log_debug(sto)

        rtf = os.path.isfile("{0}.FCD".format(self.eesign_path))
        if rtf is False:
            rtmsg = "Can't find the file {0}.FCD".format(self.eesign_path)
            self.critical_error(rtmsg)
        else:
            cmd = "mv {0}.FCD {1}".format(self.eesign_path, self.eesigndate_path)
            log_debug("cmd: " + cmd)
            # self.xcmd(cmd)
            self.cnapi.xcmd(cmd)

    def check_devreg_data(self, dut_tmp_subdir=None, mtd_count=None, post_en=True, zmodem=False, timeout=10):
        """check devreg data
        in default we assume the datas under /tmp on dut
        but if there is sub dir in your tools.tar, you should set dut_subdir

        you MUST make sure there is eesign file under /tftpboot

        Keyword Arguments:
            dut_subdir {[str]} -- like udm, unas, afi_aln...etc, take refer to structure of fcd-script-tools repo
        """
        log_debug("Send signed eeprom file adding date code from host to DUT ...")

        # Determine what eeprom should be written into DUT finally
        if self.FCD_TLV_data is True:
            eewrite = self.eesigndate
        else:
            eewrite = self.eesign

        eewrite_path = os.path.join(self.tftpdir, eewrite)

        err = self.write_devreg_flash_data(eewrite_path)
        if err:
            self.critical_error("write_devreg_flash_data failed!!: {0}".format(err))
            return

    def run(self):
        PROVISION_EN = True
        DOHELPER_EN = True
        REGISTER_EN = True
        SCHEK_SEC_STATUS = True

        """
        Main procedure of factory
        """
        msg(1, "Start Procedure")

        err = self.open_serial_port("/dev/" + self.dev)
        if err:
            self.critical_error("open_serial_port failed!!: {0}".format(err))
            sys.exit("open_serial_port failed!!: {0}".format(err))

        time.sleep(5)

        err = self.prepare_cmd()
        if err:
            self.critical_error("prepare_cmd failed!!: {0}".format(err))
            sys.exit("prepare_cmd failed!!: {0}".format(err))

        msg(5, "Open serial port successfully ...")

        self.finalret = True

        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if self.finalret is True:
            if PROVISION_EN is True:
                msg(20, "Sendtools to DUT and data provision ...")
                time_start = time.time()
                self.data_provision_64k()

                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='PROVISION', time=duration))

        if self.finalret is True:
            if DOHELPER_EN is True:
                msg(40, "Do helper to get the output file to devreg server ...")
                time_start = time.time()

                self.erase_eefiles()
                self.prepare_server_need_files()

                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='HELPER', time=duration))

        if self.finalret is True:
            if REGISTER_EN is True:
                time_start = time.time()

                self.registration()
                msg(50, "Finish doing registration ...")
                self.check_devreg_data()
                msg(60, "Finish doing signed file and EEPROM checking ...")

                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='REGISTER', time=duration))

        if self.finalret is True:
            if SCHEK_SEC_STATUS:
                time_start = time.time()
                [err, status] = self.devreg_check_sec()
                if err:
                    self.critical_error("devreg_check_sec failed!!: request check sec: {0}".format(err))
                else:
                    log_debug("Check security status: {0}".format(status))

                duration = int(time.time() - time_start)
                log_debug('==> duration_{cap}: {time} seconds'.format(cap='SCHEK_SEC_STATUS', time=duration))

                if "FAILED" in status:
                    self.critical_error("Failed to check sec status")

        msg(100, "Complete FCD process ...")
        self.close_fcd()

def main():
    log_debug("---Start---")
    devreg = SonixDevreg()
    devreg.run()
    log_debug("---Done---")

if __name__ == '__main__':
    main()
