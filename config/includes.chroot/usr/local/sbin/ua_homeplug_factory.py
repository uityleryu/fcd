#!/usr/bin/python3

from script_base import ScriptBase
from PAlib.Framework.fcd.pserial import SerialExpect
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg, error_critical, log_info
from xmodem import XMODEM
from PAlib.Framework.fcd.ssh_client import SSHClient

import sys
import time
import os
import re
import traceback


DOHELPER_ENABLE = True
REGISTER_ENABLE = True
QRCODE_ENABLE = True
CHECK_MAC_ENABLE = True




class UAHOMEPLUGFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UAHOMEPLUGFactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        # script specific vars
        self.bomrev = "113-" + self.bom_rev
        self.sysid = self.bom_rev.split('-')[0]
        self.hwrev = self.bom_rev.split('-')[1]
        self.linux_prompt = "EH:"
        self.prodclass = "0014"

        # Base path
        self.toolsdir = "tools/"
        self.plctool = os.path.join(self.tftpdir, "tools", "ua_extender", "fcd", "plctool")
        self.plcinit = os.path.join(self.tftpdir, "tools", "ua_extender", "fcd", "plcinit")
        self.modpib = os.path.join(self.tftpdir, "tools", "ua_extender", "fcd", "modpib")
        self.gen_bin = os.path.join(self.tftpdir, "tools", "ua_extender", "fcd", "gen_flash_block_bin.py")
        self.fwbin = os.path.join(self.tftpdir, "ua-fw", self.board_id + '.bin')
        self.common_dir = os.path.join(self.tftpdir, "tools", "common")

        self.ncert = "cert_{0}.pem".format(self.row_id)
        self.nkey = "key_{0}.pem".format(self.row_id)
        self.nkeycert = "key_cert_{0}.bin".format(self.row_id)
        self.nkeycertchk = "key_cert_chk_{0}.bin".format(self.row_id)
        self.cert_path = os.path.join(self.tftpdir, self.ncert)
        self.key_path = os.path.join(self.tftpdir, self.nkey)
        self.keycert_path = os.path.join(self.tftpdir, self.nkeycert)
        self.keycertchk_path = os.path.join(self.tftpdir, self.nkeycertchk)
        self.flasheditor = os.path.join(self.common_dir, self.eepmexe)

        # check MAC
        self.DAK = ""

        self.mac_check_dict = {
            'ec44': True,
        }

        # number of Ethernet
        self.ethnum = {
            'ec44': "1",
        }

        # number of WiFi
        self.wifinum = {
            'ec44': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ec44': "1",
        }

        tool_list = [self.plctool, self.plcinit, self.modpib, self.gen_bin]
        for tool in tool_list:
            cmd = "sudo chmod 777 {}".format(tool)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if int(rtc) > 0:
                self.critical_error("{} chmod 777 failed".format(tool))
            else:
                log_debug("{} chmod 777 successfully".format(tool))

    def prepare_server_need_files(self):
        log_debug("Starting to create a 64KB binary file ...")
        cmd = "python {} {} {} {} {} {}".format(self.gen_bin, self.board_id, self.mac, self.sysid, self.hwrev, self.eebin_path)
        log_debug('cmd : {}'.format(cmd))
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Generating " + self.eebin_path + " file failed!!")
        else:
            log_debug("Generating " + self.eebin_path + " files successfully")

    def registration(self):
        log_debug("Starting to do registration ...")
        try:
            uid = "0777" + self.board_id + self.mac
            log_info('uid = {}'.format(uid))

            cpuid = "00006410"
            log_info('cpuid = {}'.format(cpuid))

            jedecid = "0007f101"
            log_info('jedecid = {}'.format(jedecid))

        except Exception as e:
            log_debug("Extract UID, CPUID and JEDEC failed")
            log_debug("{}".format(traceback.format_exc()))
            error_critical("{}\n{}".format(sys.exc_info()[0], e))

        log_debug("Extract UID, CPUID and JEDEC successfully")

        cmd = [
            "sudo /usr/local/sbin/client_x86_release",
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            #"-i field=product_class_id,value=basic "
            "-i field=product_class_id,format=hex,value=" + self.prodclass, 
            "-i field=flash_jedec_id,format=hex,value=" + jedecid,
            "-i field=flash_uid,format=hex,value=" + uid,
            "-i field=cpu_rev_id,format=hex,value=" + cpuid,
            "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
            "-i field=fcd_id,format=hex,value=0012",
            "-i field=fcd_version,format=hex,value=" + self.sem_ver,
            "-i field=sw_id,format=hex,value=" + self.sw_id,
            "-i field=sw_version,format=hex,value=" + self.fw_ver,
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
        if QRCODE_ENABLE:
            cmd.append("-i field=qr_code,format=hex,value=" + self.qrhex)

        cmdj = ' '.join(cmd)

        log_debug(cmdj)
        clit = ExpttyProcess(self.row_id, cmdj, "\n")
#        clit.expect_only(30, "Ubiquiti Device Security Client")
#        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        cmd[2] = "-k " + self.input_args.pass_phrase
        poscmd = ' '.join(cmd)
        print("CMD: \n" + poscmd)

        log_debug("Executing client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign_path)

        log_debug("Add the date code in the devreg binary file")

    def _read_version(self, msg):
        # only for LOCK-R(a911) and 60G-LAS(a918)
        msg_versw = msg.split("VER-SW:")[-1].split("\r")[0].split(";")
        msg_verhw = msg.split("VER-HW:")[-1].split("\r")[0].split(";")
        msg_verswhw = msg_versw + msg_verhw
        version = {}
        for ii in msg_verswhw:
            version[ii.split("-", 1)[0]] = ii.split("-", 1)[1]
        return version

    def _reset(self):
        # it needs to reset for updating the MAC, otherwise the MAC would be like "VER-HW:MAC-ff.ff.ff.ff.ff.ff"
        log_info('Sending the reset command')
        rtv_reset = self.ser.execmd_getmsg(self.cmd_reset)
        log_info('rtv_reset = {}'.format(rtv_reset))
        time.sleep(1)

    def check_connect(self):
        log_debug('check connecting...')
        time_end = time.time() + 10
        while time.time() < time_end:
            [sto, rtc] = self.fcd.common.xcmd(self.plctool + " -i eth1 -I > /tmp/temp.log")
            [sto, rtc] = self.fcd.common.xcmd("grep -c \"DAK\" /tmp/temp.log")
            if sto == "1":
                log_info("connect with DUT success")
                return True
            time.sleep(1)
        error_critical('connect with DUT FAIL')


    def get_DAK(self):
        log_debug('get DAK..')
        time_end = time.time() + 10
        while time.time() < time_end:
            [sto, rtc] = self.fcd.common.xcmd('cat /tmp/temp.log | grep DAK | awk -F" " \'{ print $2 }\' | tr -d "\n"')
            self.DAK = sto
            log_info("DAK:{}".format(self.DAK))
            return True

    def write_mac(self):
        log_debug('modpib MAC')
        cmd = "{} -M {} {}".format(self.modpib, self.mac, self.fwbin)
        log_debug('cmd : {}'.format(cmd))
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        log_debug("sto = {}, rtc = {}".format(sto, rtc))
        if int(rtc) > 0:
            error_critical("modpib MAC failed")
        else:
            log_info("modpib MAC success")

        log_debug('write MAC to device factory default') # need to clarify why mac cannot set to default
        cmd = "{} -i eth1 -P {} -D {} -FF".format(self.plcinit, self.fwbin, self.DAK) # eth1 need to be a variable
        log_debug('cmd : {}'.format(cmd))
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("write MAC to device factory success")
        else:
            self.check_connect()
            log_info("write MAC to device factory success")

        log_debug('write MAC to device device user section')
        cmd = "{} -i eth1 -P {} -FF".format(self.plctool, self.fwbin) # eth1 need to be a variable
        log_debug('cmd : {}'.format(cmd))
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("write MAC to device user section failed")
        else:
            self.check_connect()
            log_info("write MAC to device user section success")
            return True

    def check_mac(self):
        log_debug("Starting to check MAC")
        log_info("self.mac_check_dict = {}".format(self.mac_check_dict))

        if self.mac_check_dict[self.board_id] is False:
            log_debug("skip check the MAC in DUT")
            return

        [sto, rtc] = self.fcd.common.xcmd(self.plctool + " -i eth1 -I > /tmp/temp.log")
        [sto, rtc] = self.fcd.common.xcmd('cat /tmp/temp.log |grep MAC | awk -F" " \'{print $2 }\' | tr -d "\n"')
        dut_mac = sto.replace(":","").upper()
        expect_mac = self.mac.upper()

        log_info("MAC_DUT    = {}".format(dut_mac))
        log_info("MAC_expect = {}".format(expect_mac))

        if dut_mac == expect_mac:
            log_debug('MAC_DUT and MAC_expect are match')
        else:
            error_critical("MAC_DUT and MAC_expect are NOT match")


    def critical_error(self, msg):
        self.finalret = False
        self.errmsg = msg
        error_critical(msg)

    def write_devreg_data_to_dut(self):
        log_info('write_devreg_data_to_dut')
        dut_rom_path = '/tmp/rom384.bin'
        self.session.put_file(self.eesign_path, dut_rom_path)
        time.sleep(1)

        duetime = 6
        p_board_id = self.board_id
        p_country_code = 0
        p_rev = int(self.bom_rev.split('-')[1])
        p_MAC_QR = self.mac + '-' + self.qrcode
        p_rompath = dut_rom_path

        para = [
            str(p_board_id),
            str(p_country_code),
            str(p_rev),
            str(p_MAC_QR),
            str(p_rompath)
        ]

        paras = ' '.join(para)
        print('paras: ' + paras)

        ret = False
        for i in range(3):
            if self.nfc_write(paras, 6) is True:
                ret = True
                break

        rstr = 'write_devreg_data_to_dut: '
        if ret is False:
            self.critical_error(rstr + 'fail!')
        else:
            log_info(rstr + 'succeed.')


    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.print_current_fcd_version()
        self.check_connect()
        msg(10, "Connect with DUT success")
        self.get_DAK()
        msg(20, "Get DAK in DUT success")
        self.write_mac()
        msg(30, "Write MAC in DUT success")

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(40, "Finish erasing ee files ...")
            self.prepare_server_need_files()
            msg(50, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            if self.board_id != 'ec3a' and self.board_id != 'ec38':
                self.registration()
                msg(60, "Finish doing registration ...")
                msg(70, "Finish doing signed file and EEPROM checking ...")

        if CHECK_MAC_ENABLE is True:
            self.check_mac()
            msg(80, "Finish checking MAC in DUT ...")


        msg(100, "Completing registration ...")
        self.close_fcd()



def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        ua_extender_factorty = UAHOMEPLUGFactoryGeneral()
        ua_extender_factorty.run()


if __name__ == "__main__":
    main()
