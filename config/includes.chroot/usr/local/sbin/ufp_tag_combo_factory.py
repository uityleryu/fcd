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
QRCODE_ENABLE = False
CHECK_MAC_ENABLE = True


cmds_led = {
             "red"   : "echo 4 > /proc/gpio/led_pattern",
             "blue"  : "echo 1 > /proc/gpio/led_pattern",
             "white" : "echo 2 > /proc/gpio/led_pattern ",
             "blink" : "echo 1 2 > /proc/gpio/led_pattern",
           }

cmds_buzzer = {
                "start" : "500 100 1000 100",
                "pass"  : "500 150 0 100 500 100 0 100 900 500",
                "fail"  : "1000 50 900 50 800 50 700 50 600 50 500 50",
              }


msg_idx_connectwithualite = 70
msg_idx_preparefiles      = 75
msg_idx_getcardinfo       = 80
msg_idx_geneeprom         = 82
msg_idx_devreg            = 85
msg_idx_writerom          = 90



class UFPEFR32FactoryGeneral(ScriptBase):
    def __init__(self):
        super(UFPEFR32FactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        # script specific vars
        self.bomrev = "113-" + self.bom_rev
        self.linux_prompt = "EH:"
        self.prodclass = "0014"
        self.dut_dhcp_ip = ""
        self.dut_port = ""
        self.baudrate = 921600

        # Base path
        self.toolsdir = "tools/"
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
        self.cmd_version = "VERSION"
        self.cmd_reset = "RESET"
        self.cmd_erase_devreg = "ERASEDEVREG"
        self.cmd_devregcheck = "DEVREGCHECK"
        self.cmd_getqrcode = "GETQRCODE"

        self.mac_check_dict = {
            'a911': False,
            'a912': False,
            'a918': True,
            'a913': True,
            'a914': True,
            'ec3a': True,
            'ec38': True,
        }

        # number of Ethernet
        self.ethnum = {
            'a911': "0",
            'a912': "0",
            'a918': "0",
            'a913': "0",
            'a914': "0",
            'ec3a': "0",
            'ec38': "0",
        }

        # number of WiFi
        self.wifinum = {
            'a911': "0",
            'a912': "0",
            'a918': "0",
            'a913': "0",
            'a914': "0",
            'ec3a': "0",
            'ec38': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'a911': "1",
            'a912': "1",
            'a918': "1",
            'a913': "1",
            'a914': "1",
            'ec3a': "1",
            'ec38': "1",
        }

    def prepare_server_need_files(self):
        log_debug("Starting to create a 64KB binary file ...")
        self.gen_rsa_key()

        sstr = [
            self.flasheditor,
            "-F",
            "-f " + self.eebin_path,
            "-r " + self.bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
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
            uid_rtv = self.ser.execmd_getmsg("GETUID")
            res = re.search(r"UNIQUEID:27-(.*)\n", uid_rtv, re.S)
            uid = res.group(1)
            log_info('uid = {}'.format(uid))

            cpuid_rtv = self.ser.execmd_getmsg("GETCPUID")
            res = re.search(r"CPUID:(.*)\n", cpuid_rtv, re.S)
            cpuid = res.group(1)
            log_info('cpuid = {}'.format(cpuid))

            jedecid_rtv = self.ser.execmd_getmsg("GETJEDEC")
            res = re.search(r"JEDECID:(.*)\n", jedecid_rtv, re.S)
            jedecid = res.group(1)
            log_info('jedecid = {}'.format(jedecid))

        except Exception as e:
            log_debug("Extract UID, CPUID and JEDEC failed")
            log_debug("{}".format(traceback.format_exc()))
            error_critical("{}\n{}".format(sys.exc_info()[0], e))

        log_debug("Extract UID, CPUID and JEDEC successfully")

        cmd = [
            "sudo /usr/local/sbin/client_x86_release_20190507",
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
        if QRCODE_ENABLE:
            cmd.append("-i field=qr_code,format=hex,value=" + self.qrhex)
        else:
            if self.board_id in ['a913', 'a914', 'ec3a']:
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
        
        if self.board_id in ['a913', 'a914']:
            log_debug("cmd_erase_devreg")
            self.ser.execmd(self.cmd_erase_devreg)
            time.sleep(0.5)

        log_debug("DUT request the signed 64KB file ...")

        if self.board_id in ["a912", "a918"]:
            self.ser.execmd_expect("xstartdevreg", "begin upload")
        elif self.board_id in ["a911"]:
            self.ser.execmd("xstartdevreg")
            time.sleep(0.5)
        elif self.board_id in ['a913', 'a914']:
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
        rtv_reset = self.ser.execmd_getmsg(self.cmd_reset)
        log_info('rtv_reset = {}'.format(rtv_reset))
        time.sleep(1)

    def check_connect(self):
        log_debug('check connecting...')
        time_end = time.time() + 10
        while time.time() < time_end:
            rtv_verison = self.ser.execmd_getmsg(self.cmd_version)
            if 'VER-SW' in rtv_verison:
                log_info("connect with DUT success")
                return True
            time.sleep(1)
        error_critical('connect with DUT FAIL')
            
        

    def check_mac(self):
        log_debug("Starting to check MAC")
        log_info("self.mac_check_dict = {}".format(self.mac_check_dict))

        if self.mac_check_dict[self.board_id] is False:
            log_debug("skip check the MAC in DUT ...")
            return

        self._reset()

        rtv_verison = self.ser.execmd_getmsg(self.cmd_version)
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

        rtv_devregcheck = self.ser.execmd_getmsg(self.cmd_devregcheck)
        if 'CHECK SUCCESS' in rtv_devregcheck:
            log_debug('DEVREG: CHECK SUCCESS')
        else:
            error_critical('DEVREG: CHECK FAIL')


        rtv_getqrcode = self.ser.execmd_getmsg(self.cmd_getqrcode)
        msg_qrcode = rtv_getqrcode.split("QRCODE:6-")[-1].split("\r")[0].strip('\n\t\r')
        msg = 'QRCODE_DUT = {}   (x = {})'.format(msg_qrcode, self.qrcode)
        if msg_qrcode == self.qrcode:
            log_debug('[PASS] ' + msg)
        else:
            error_critical('[FAIL] ' + msg)


    #-------------------------------------------------------------
    #    for NFC part --->
    #-------------------------------------------------------------


    def NFC_init(self):

        self.ip = '192.168.1.2{}'.format(self.row_id)
        self.username = "ubnt"
        self.password = "ubnt"
        self.polling_mins = 5
        if self.board_id == 'ec3a' or self.board_id == 'ec38':
            self.client_name = 'client_rpi4_release'
        else:
            self.client_name = 'client_x86_release_20200414'
        self.host_toolsdir_dedicated = os.path.join(self.fcd_toolsdir, "ufp")
        
        self.helperexe = 'nxp-nfc-nci'
        self.eerom_status = 0
        self.eerom_name = 'rom384.bin'
        self.errmsg = ""

        print('----REPLACE INFO-----------------------')
        if self.board_id == 'a913':
            self.board_id = 'a916'
        elif self.board_id == 'a914':
            self.board_id = 'a917'

        if self.board_id == 'ec3a' or self.board_id == 'ec38':
            self.mac = self.mac_addr_increase(self.mac, 0)
        else:
            self.mac = self.mac_addr_increase(self.mac, 1)

        #for debug if have no non-devreg board on hand
        '''
        self.mac = 'FCECDAFF2923'
        #self.qrcode = 'af1tn1'
        '''

        if self.qrcode is not None:
            self.qrhex = self.qrcode.encode('utf-8').hex()
        
        print("--------------TAG-NFC-------------- [[[")
        print('self.product_name: ' + self.product_name)
        print('self.board_id: ' + self.board_id)
        print('self.bom_rev: ' + self.bom_rev)
        print("mac: " + self.mac)
        print("qrcode: " + self.qrcode)
        print("ip: " + self.ip)
        print("client_name: " + self.client_name)    
        print('host_toolsdir_dedicated: ' + self.host_toolsdir_dedicated)
        print("--------------TAG-NFC-------------- ]]]")

    def mac_addr_increase(self, mac='112233445566', inc=1):
        mac = "{:012X}".format(int(mac, 16) + inc)
        return mac


    def critical_error(self, msg):
        self.finalret = False
        self.errmsg = msg
        self.set_led('red')
        self.set_buzzer('fail')
        error_critical(msg)


    def NFC_prepare_server_need_files(self):
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
            log_info("{} uploaded successfully".format(self.helperexe))
        else:
            self.critical_error("{} uploaded failed".format(self.helperexe))

        cmd_chmod = "chmod 777 {}".format(helperexe_path)
        if self.session.execmd(cmd_chmod) == 0:
            log_info("{} chmod 777 successfully".format(self.helperexe))
        else:
            self.critical_error("{} chmod 777 failed".format(self.helperexe))


    def stop_nfc(self):
        log_info('STOP NFC...')
        cmd = "sed -i -e '/nfcd/s/^/#/' /etc/inittab && kill -1 1"
        self.session.execmd(cmd) 

    def set_led(self, color='red'):
        log_info('set_led( {} )'.format(color))
        self.session.execmd(cmds_led[color]) 


    def set_buzzer(self, tone='test'):
        log_info('set_buzzer( {} )'.format(tone))
        cmd = 'echo {} > /proc/ubnt_udoor/buzzer_freq'.format(cmds_buzzer[tone])
        print('buzzer: ' + cmd)
        self.session.execmd( cmd )


    def get_uacard_info(self):
        duetime = 3
        cmd_info = 'rm /tmp/info.txt; {}/{} -fcdinfo > /tmp/info.txt & sleep {} && pkill SIGINT {}'.format(self.dut_tmpdir, self.helperexe, duetime, self.helperexe)
        readraw = '1'
        
        card_exist = False
        for i in range(3):
            cmd_clear = 'killall {}; rm /tmp/info.txt'.format(self.helperexe)
            print(cmd_clear)
            self.session.execmd(cmd_clear) 

            print(cmd_info)
            self.session.execmd(cmd_info) 
            readraw = self.session.execmd_getmsg('cat /tmp/info.txt')
            log_debug(readraw)
            if 'PASS' in readraw:
                card_exist = True
                break

        self.session.execmd(cmd_clear) 
        if card_exist is False:
            return False

        print(readraw)
        regex = re.compile(r"(\w+) = (.+)")
        ss = regex.findall(readraw)
        self.dut_atqa = ss[0][1].replace(" ", "")
        self.dut_nfcid = ss[1][1].replace(" ", "")
        self.dut_sak = ss[2][1].replace(" ", "")
        self.dut_ats = ss[3][1].replace(" ", "")
        self.dut_desire = ss[4][1].replace(" ", "")
        self.dut_cpuid = self.dut_atqa + self.dut_sak

        print('dut_atqa: {}'.format(self.dut_atqa))
        print('dut_nfcid: {}'.format(self.dut_nfcid))
        print('dut_sak: {}'.format(self.dut_sak))
        print('dut_ats: {}'.format(self.dut_ats))
        print('dut_desire: {}'.format(self.dut_desire))
        print('dut_cpuid: {}'.format(self.dut_cpuid))
        return card_exist

    
    def NFC_registration(self):
        log_info("Starting to do registration ...")
        bom = int(self.bom_rev.split('-')[0])
        rev = int(self.bom_rev.split('-')[1])
        bom = '{:06x}'.format(bom)
        rev = '{:02x}'.format(rev)
        pcba = bom+rev
        print(pcba)

        self.fcd_id = '0001'
        self.sem_ver = '00010103'
        self.sw_id = '0001'
        self.fw_ver = '00010101'

        cmd = [
            "sudo /usr/local/sbin/" + self.client_name,
            "-h prod.udrs.io",
            "-k " + self.pass_phrase,
            "-i field=product_class_id,value=" + 'basic384b',
            "-i field=flash_jedec_id,format=hex,value=" + '00' + self.dut_desire,
            "-i field=flash_uid,format=hex,value=" + self.dut_nfcid,
            "-i field=cpu_rev_id,format=hex,value="+ '00' + self.dut_cpuid,
            "-i field=base_mac_address,format=hex,value=" + self.mac,
            "-i field=qr_code,format=hex,value=" + self.qrhex,
            "-i field=subsystem_id,format=hex,value=" + self.board_id,
            "-i field=subvendor_id,format=hex,value=0777 ",
            "-i field=pcba,format=hex,value=" + pcba,        
            "-o field=flash_eeprom,format=binary,pathname=" + self.eesign_path,
            "-i field=fcd_id,format=hex,value=" + self.fcd_id,
            "-i field=fcd_version,format=hex,value=" + self.sem_ver,
            "-i field=sw_id,format=hex,value=" + self.sw_id,
            "-i field=sw_version,format=hex,value=" + self.fw_ver,
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

        cmdj = ' '.join(cmd)

        log_info(cmdj)
        try:
            clit = ExpttyProcess(self.row_id, cmdj, "\n")
            clit.expect_only(30, "Hostname")
            clit.expect_only(30, "field=result,format=u_int,value=1")
        except Exception as e:
            self.critical_error('devreg fail!')

        cmd[2] = "-k " + self.input_args.pass_phrase
        poscmd = ' '.join(cmd)
        print("CMD: \n" + poscmd)

        log_info("Excuting client_x86 registration successfully")

        rtf = os.path.isfile(self.eesign_path)
        if rtf is not True:
            self.critical_error("Can't find " + self.eesign_path)


    def nfc_write(self, paras, waittime):
        self.session.execmd('killall {}'.format(self.helperexe))
        self.session.execmd('rm /tmp/info.txt')
        cmd_write = '{}/{} -d 2 -fcdcreate {} &> /tmp/info.txt &'.format(self.dut_tmpdir, self.helperexe, paras)
        print('cmd_write: ' + cmd_write)
        self.session.execmd(cmd_write)

        time_end = time.time() + waittime
        while time.time() < time_end:
            time.sleep(1)
            ret = int(self.session.execmd_getmsg('cat /tmp/info.txt 2>&1 | grep PASS &> /dev/null; echo $?'))
            if ret == 0:
                readraw = self.session.execmd_getmsg('cat /tmp/info.txt 2>&1')
                print(readraw)
                return True
        return False


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


    def NFC_run(self):
        """
        Main procedure of factory
        """

        msg(msg_idx_connectwithualite, "connect to ua-lite.")
        self.NFC_init()
        sshclient_obj = SSHClient(host=self.ip,
                                  username=self.username,
                                  password=self.password,
                                  polling_connect=True,
                                  polling_mins=self.polling_mins)

        self.set_sshclient_helper(ssh_client=sshclient_obj)
        log_info(self.session.execmd_getmsg("pwd"))
        time.sleep(1)
        time_start = time.time()
        self.finalret = True

        
        msg(msg_idx_preparefiles, "prepare server need files.")
        self.set_led('white')
        self.set_buzzer('start')
        self.stop_nfc()
        self.NFC_prepare_server_need_files()
        
        
        #get card info
        
        ret = False
        self.set_led('blue')
        msg(msg_idx_getcardinfo, "get card info.")
        timeout = time.time() + 60
        while time.time() < timeout:
            if self.get_uacard_info() is True:
                self.set_led('blink')
                ret = True
                break
            time.sleep(1)

        if ret is False:
            self.critical_error('card not exist')

        msg(msg_idx_devreg, "connect with devreg server.")
        self.NFC_registration()
        
        msg(msg_idx_writerom, "write devreg data to eerom.")
        self.write_devreg_data_to_dut()

        duration = int(time.time() - time_start)
        log_info('==> duration_{cap}: {time} seconds'.format(cap='NFC_regist', time=duration))

        self.set_led('white')
        self.set_buzzer('pass')
        msg(95, "Complete FCD process. (NFC)")

    #-------------------------------------------------------------
    #    for NFC part <----
    #-------------------------------------------------------------



    def run(self):
        """
        Main procedure of factory
        """
        self.fcd.common.print_current_fcd_version()
        if self.board_id != 'ec3a' and self.board_id != 'ec38':
            self.fcd.common.config_stty(self.dev)

            # Connect into DU and set pexpect helper for class using picocom
            serialcomport = "/dev/{0}".format(self.dev)
            serial_obj = SerialExpect(port=serialcomport, baudrate=self.baudrate)
            self.set_serial_helper(serial_obj=serial_obj)
            time.sleep(1)

            msg(5, "Open serial port successfully ...")
            self.ser.execmd("")
            self.check_connect()
            msg(10, "Connect with DUT success")

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(20, "Finish erasing ee files ...")
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            if self.board_id != 'ec3a' and self.board_id != 'ec38':
                self.registration()
                msg(40, "Finish doing registration ...")
                self.put_devreg_data_in_dut()
                msg(50, "Finish doing signed file and EEPROM checking ...")

        if CHECK_MAC_ENABLE is True:
            if self.board_id != 'ec3a' and self.board_id != 'ec38':
                self.check_mac()
                msg(60, "Finish checking MAC in DUT ...")

        self.NFC_run()
        msg(70, "Finish write devreg file in NFC ...")

        msg(100, "Completing registration ...")
        self.close_fcd()



def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        udm_factory_general = UFPEFR32FactoryGeneral()
        udm_factory_general.run()


if __name__ == "__main__":
    main()
