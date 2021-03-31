#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.pserial import SerialExpect
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, msg, error_critical, log_info
from xmodem import XMODEM

import sys
import time
import os
import re
import traceback

DOHELPER_ENABLE = True
REGISTER_ENABLE = True
SET_SKU_ENABLE = True
CHECK_MAC_ENABLE = True


class UFPEFR32FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UFPEFR32FactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        # script specific vars
        self.linux_prompt = "EH:"
        self.prodclass = "0014"
        self.baudrate = 921600
        self._reseted_flag = False

        # check MAC
        self.cmd_version = "VERSION"
        self.cmd_reset = "RESET"
        self.cmd_erase_devreg = "ERASEDEVREG"

        self.mac_check_dict = {
            'a911': True,
            'a912': False,
            'a915': True,
            'a918': True,
            'a919': True,
        }

        self.qrcode_dict = {
            'a911': False,
            'a912': False,
            'a915': False,
            'a918': False,
            'a919': True,
        }

        self.sku_dict = {
            'a911': True,
            'a912': False,
            'a915': False,
            'a918': False,
            'a919': False,
        }

        # number of Ethernet
        self.ethnum = {
            'a911': "0",
            'a912': "0",
            'a915': "0",
            'a918': "0",
            'a919': "0",
        }

        # number of WiFi
        self.wifinum = {
            'a911': "0",
            'a912': "0",
            'a915': "0",
            'a918': "0",
            'a919': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'a911': "1",
            'a912': "1",
            'a915': "1",
            'a918': "1",
            'a919': "1",
        }

    def prepare_server_need_files(self):
        log_debug("Starting to create a 64KB binary file ...")
        self.gen_rsa_key()

        flasheditor = os.path.join(self.fcd_commondir, self.eepmexe)
        sstr = [
            flasheditor,
            "-F",
            "-f " + self.eebin_path,
            "-r 113-{0}".format(self.bom_rev),
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
        log_debug('sstr = {}'.format(sstr))

        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Generating " + self.eebin_path + " file failed!!")
        else:
            log_debug("Generating " + self.eebin_path + " files successfully")

    def _sense_cmd_before_registration(self):

        log_debug("check dut connection".center(60, "="))
        rtv = self.ser.execmd_getmsg(cmd="app 20", waitperiod=0, sleep_time=0.5)
        log_debug('command "app 20" rtv = {}'.format([rtv]))
        if rtv == "" or rtv == "app 20\n":
            error_critical("DUT is not connected, please check the connection")
        log_debug("DUT is connected")

        log_debug("disable all sensors".center(60, "="))
        cmd_clr_all_disable = "app 43 02 05 00 00 32 00 00 96 00 00 05 20 03 23 05 0F 15 04 05 07 00 00 0F 0A 3C"
        log_debug(cmd_clr_all_disable+"\n")
        self.ser.execmd(cmd=cmd_clr_all_disable)
        time.sleep(2)

    def registration(self):
        log_debug("Starting to do registration ...")

        if self.board_id == "a912":
            self._sense_cmd_before_registration()

        try:
            uid_rtv = self.ser.execmd_getmsg("GETUID", ignore=True)
            res = re.search(r"UNIQUEID:27-(.*)\n", uid_rtv, re.S)
            uid = res.group(1)
            log_info('uid = {}'.format(uid))

            cpuid_rtv = self.ser.execmd_getmsg("GETCPUID", ignore=True)
            res = re.search(r"CPUID:(.*)\n", cpuid_rtv, re.S)
            cpuid = res.group(1)
            log_info('cpuid = {}'.format(cpuid))

            jedecid_rtv = self.ser.execmd_getmsg("GETJEDEC", ignore=True)
            res = re.search(r"JEDECID:(.*)\n", jedecid_rtv, re.S)
            jedecid = res.group(1)
            log_info('jedecid = {}'.format(jedecid))


        except Exception as e:
            log_debug("Extract UID, CPUID and JEDEC failed")
            log_debug("{}".format(traceback.format_exc()))
            error_critical("{}\n{}".format(sys.exc_info()[0], e))

        log_debug("Extract UID, CPUID and JEDEC successfully")

        cmd = "uname -a"
        [sto, rtc] = self.cnapi.xcmd(cmd)
        if int(rtc) > 0:
            error_critical("Get linux information failed!!")
        else:
            log_debug("Get linux information successfully")
            match = re.findall("armv7l", sto)
            if match:
                clientbin = "/usr/local/sbin/client_rpi4_release"
            else:
                clientbin = "/usr/local/sbin/client_x86_release_20190507"

        cmd = [
            "sudo {0}".format(clientbin),
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            "-i field=product_class_id,format=hex,value=" + self.prodclass,
            "-i field=flash_jedec_id,format=hex,value=" + jedecid,
            "-i field=flash_uid,format=hex,value=" + uid,
            "-i field=cpu_rev_id,format=hex,value=" + cpuid,
            "-i field=flash_eeprom,format=binary,pathname=" + self.eebin_path,
            "-i field=fcd_id,format=hex,value=" + self.fcd_id,
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
        if self.qrcode_dict[self.board_id]:
            cmd.append("-i field=qr_code,format=hex,value=" + self.qrhex)

        cmdj = ' '.join(cmd)

        log_debug(cmdj)
        clit = ExpttyProcess(self.row_id, cmdj, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        cmd[2] = "-k " + self.input_args.pass_phrase
        poscmd = ' '.join(cmd)
        print("CMD: \n" + poscmd)

        log_debug("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            error_critical("Can't find " + self.eesign_path)

        log_debug("Add the date code in the devreg binary file")

    def put_devreg_data_in_dut(self):
        log_debug("DUT request the signed 64KB file ...")

        if self.board_id in ["a912", "a918"]:
            self.ser.execmd_expect("xstartdevreg", "begin upload")
        elif self.board_id in ["a911", "a915", "a919", "a920"]:
            self.ser.execmd("xstartdevreg")
            time.sleep(0.5)

        log_debug("Starting xmodem file transfer ...")
        modem = XMODEM(self.ser.xmodem_getc, self.ser.xmodem_putc, mode='xmodem1k')
        stream = open(self.eesign_path, 'rb')
        modem.send(stream, retry=64)

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
        try:
            rtv_reset = self.ser.execmd_getmsg(self.cmd_reset,ignore=True)
            log_info('rtv_reset = {}'.format(rtv_reset))
        except Exception as e:
            log_info('')
            log_info("{}".format(traceback.format_exc()))
            log_info("{}".format(sys.exc_info()[0]))
            log_info("{}".format(e))
            log_info('')
            log_info('This might be the garbled code of the return value in LOCK_R (a911)')

        self._reseted_flag = True
        time.sleep(3)

    def set_sku(self):
        # parameters
        cmd_set_sku = 'FCDSKUSET:{sku}'
        cmd_get_sku = 'FCDSKUGET'
        expected_rsp = 'SKU: {sku}'
        region_name_dict = {"World": 'US',
                            "USA/Canada": 'US',
                            'EU': 'EU',
                            "Scandi": 'SCANDI'}

        # set_sku
        log_debug("Starting to set SKU")
        log_info("self.sku_dict = {}".format(self.sku_dict))
        log_info('self.region_name = {}'.format(self.region_name))

        if self.sku_dict[self.board_id] is False:
            log_debug("Skip setting SKU ...")
            return

        if self.region_name not in list(region_name_dict.keys()):
            msg = 'self.region_name ({}) is not in region_name_dict {}, Skip setting SKU ...'
            error_critical(msg.format(self.region_name, region_name_dict))
            return

        sku_code = region_name_dict[self.region_name]
        cmd_set_sku = cmd_set_sku.format(sku=sku_code)
        log_info("cmd_set_sku = {}".format(cmd_set_sku))
        self.ser.execmd_getmsg(cmd_set_sku)
        time.sleep(0.5)

        self._reset()

        # check SKU
        log_info("cmd_get_sku = {}".format(cmd_get_sku))
        rtv_get_sku = self.ser.execmd_getmsg(cmd_get_sku)

        expected_rsp = expected_rsp.format(sku=sku_code)
        if expected_rsp not in rtv_get_sku:
            error_critical('expected_rsp ({}) not in rtv_get_sku, set SKU fail..'.format(expected_rsp))
        else:
            log_debug('expected_rsp ({}) in rtv_get_sku, set SKU success..'.format(expected_rsp))

    def check_mac(self):
        log_debug("Starting to check MAC")
        log_info("self.mac_check_dict = {}".format(self.mac_check_dict))

        if self.mac_check_dict[self.board_id] is False:
            log_debug("skip check the MAC in DUT ...")
            return

        if self._reseted_flag is not True:
            self._reset()
        else:
            log_info('Have reseted before, skip this time')

        rtv_verison = self.ser.execmd_getmsg(self.cmd_version,ignore=True)

        version = self._read_version(rtv_verison)
        for key, value in version.items():
            log_info("{} = {}".format(key, value))

        dut_mac = version["MAC"].replace(".", "").upper()
        expect_mac = self.mac.upper()
        log_info("MAC_DUT    = {}".format(dut_mac))
        log_info("MAC_expect = {}".format(expect_mac))
        log_info("FW version in DUT = {}".format(version["SWv"]))

        if dut_mac == expect_mac:
            log_debug('MAC_DUT and MAC_expect are match')
        else:
            error_critical("MAC_DUT and MAC_expect are NOT match")

    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        serialcomport = "/dev/{0}".format(self.dev)
        serial_obj = serialExpect(port=serialcomport, baudrate=self.baudrate)
        self.set_serial_helper(serial_obj=serial_obj)
        time.sleep(1)

        msg(5, "Open serial port successfully ...")
        time.sleep(1)
        self.ser.execmd("")

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Finish erasing ee files ...")
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.put_devreg_data_in_dut()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if SET_SKU_ENABLE is True:
            self.set_sku()
            msg(60, "Finish settingSKU ...")

        if CHECK_MAC_ENABLE is True:
            self.check_mac()
            msg(70, "Finish checking MAC in DUT ...")

        msg(100, "Completing registration ...")
        self.close_fcd()

class serialExpect(SerialExpect):
    def execmd_getmsg(self, cmd="", waitperiod=2, sleep_time=0.5, pre_n=True, print_en=True, ignore=False):
        if pre_n is True:
            self._enter()

        if cmd != "":
            cmd = "{0}\n".format(cmd)
            self.ser.write(cmd.encode())
            self.ser.flush()
            time.sleep(sleep_time)

        outstream = []
        stoptm = time.time() + waitperiod
        while True:
            if self.ser.inWaiting() > 0:
                out = self.ser.read(self.ser.in_waiting)
                if ignore:
                    dout = out.decode("utf-8", "ignore")
                else:
                    dout = out.decode()
                outstream.append(dout)
            if time.time() > stoptm:
                break

            time.sleep(0.1)

        jotsm = "".join(outstream)

        if print_en is True:
            print(jotsm)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return jotsm

def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        udm_factory_general = UFPEFR32FactoryGeneral()
        udm_factory_general.run()


if __name__ == "__main__":
    main()
