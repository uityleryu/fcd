#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

import sys
import time
import os
import re
import stat
import filecmp
import json
import socket
import struct
import binascii
import subprocess

NEED_DROPBEAR = True
PROVISION_ENABLE = True
DOHELPER_ENABLE = True
REGISTER_ENABLE = True
FWUPDATE_ENABLE = True
DATAVERIFY_ENABLE = True

FCD_PROTO_VERSION_01 = 0x1
FCD_CMD_WRITE_DEVREG = 0x1
FCD_CMD_READ_DEVREG = 0x2
FCD_CMD_WRITE_KEYCERT = 0x3
FCD_CMD_READ_KEYCERT = 0x4


class USM487FactoryGeneral(ScriptBase):
    def __init__(self):
        super(USM487FactoryGeneral, self).__init__()
        self.init_vars()
        self.ver_extract()

    def init_vars(self):
        # script specific vars
        self.bomrev = "113-" + self.bom_rev
        self.eepmexe = "x86-4k-ee"
        self.username = "root"
        self.password = "ubnt"
        self.bootloader_prompt = "UBNT"
        self.linux_prompt = "/>"
        self.prodclass = "0015"
        self.flashjedecid = "0007f116"
        self.dut_dhcp_ip = ""
        self.dut_port = ""

        # Base path
        self.toolsdir = "tools/"
        self.dut_usmdir = os.path.join(self.dut_tmpdir, "tools", "usw_mini")
        self.host_usmdir = os.path.join(self.tftpdir, "tools", "usw_mini")

        self.ncert = "cert_{0}.pem".format(self.row_id)
        self.nkey = "key_{0}.pem".format(self.row_id)
        self.nkeycert = "key_cert_{0}.bin".format(self.row_id)
        self.nkeycertchk = "key_cert_chk_{0}.bin".format(self.row_id)
        self.cert_path = os.path.join(self.tftpdir, self.ncert)
        self.key_path = os.path.join(self.tftpdir, self.nkey)
        self.keycert_path = os.path.join(self.tftpdir, self.nkeycert)
        self.keycertchk_path = os.path.join(self.tftpdir, self.nkeycertchk)

        # number of Ethernet
        self.ethnum = {
            'ed30': "1",
        }

        # number of WiFi
        self.wifinum = {
            'ed30': "0",
        }

        # number of Bluetooth
        self.btnum = {
            'ed30': "0",
        }

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.eepmexe + "...")
        flasheditor = os.path.join(self.host_usmdir, self.eepmexe)
        sstr = [
            flasheditor,
            "-F",
            "-f " + self.eebin_path,
            "-r " + self.bomrev,
            "-s 0x" + self.board_id,
            "-m " + self.mac,
            "-c 0x" + self.region,
            "-e " + self.ethnum[self.board_id],
            "-w " + self.wifinum[self.board_id],
            "-b " + self.btnum[self.board_id],
        ]
        sstr = ' '.join(sstr)
        log_debug(sstr)
        [sto, rtc] = self.fcd.common.xcmd(sstr)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Generating " + self.eebin_path + " file failed!!")
        else:
            log_debug("Generating " + self.eebin_path + " files successfully")

    def registration(self):
        log_debug("Starting to do registration ...")

        uid = self.pexp.expect_get_output("uid", self.linux_prompt, 10)
        res = re.search(r"UID = (.*)\n", uid, re.S)
        uids = res.group(1)

        cpuid = self.pexp.expect_get_output("model", self.linux_prompt, 10)
        res = re.search(r"Model = (.*)\n", cpuid, re.S)
        cpuids = res.group(1)

        cmd = [
            "sudo /usr/local/sbin/client_x86_release_20190507",
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            "-i field=product_class_id,format=hex,value=" + self.prodclass,
            "-i field=flash_jedec_id,format=hex,value=" + self.flashjedecid,
            "-i field=flash_uid,format=hex,value=" + uids,
            "-i field=cpu_rev_id,format=hex,value=" + cpuids,
            "-i field=qr_code,format=hex,value=" + self.qrhex,
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

        cmdj = ' '.join(cmd)

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

    def issue_cmd(self, send_sock, cmd, send_data):
        send_size = len(send_data)
        values = (FCD_PROTO_VERSION_01, cmd, 0x0, send_size)
        packer = struct.Struct('!BBHI')
        packed_data = packer.pack(*values)
        send_header_size = packer.size

        try:
            # Send data
            send_sock.sendall(packed_data)
            if send_size > 0:
                print("sending data size =", len(send_data))
                send_sock.sendall(send_data)
        except Exception as e:
            print(e)
            print('Send failed!')
            return False

        return True

    def send_file(self, fname, send_sock, opcmd):
        rtf = os.path.isfile(fname)
        if rtf is False:
            error_critical(fname + " is not existed")
        else:
            log_debug(msg=fname + " is existed")

        f = open(fname, "rb")
        contents = f.read()

        # Send command
        rt = self.issue_cmd(send_sock, opcmd, contents)
        if rt is False:
            error_critical("Write failed")

        # Receive response
        resp_packer = struct.Struct('!BBHII')
        resp_header_size = resp_packer.size
        try:
            send_sock.setblocking(1)
            resp = send_sock.recv(resp_header_size)
            resp_proto, resp_cmd, resp_flags, resp_datalen, ret_code = resp_packer.unpack(resp)
            print("Response: size = ", len(resp))
            print("Response: Proto = " + hex(resp_proto))
            print("Response: Cmd = " + hex(resp_cmd))
            print("Response: Flags = " + hex(resp_flags))
            print("Response: DataLen = " + hex(resp_datalen))
            print("Response: ret_code = " + hex(ret_code))
        except Exception as e:
            print(e)
            print('recv header failed!')
            return False

        return True

    def recv_file(self, fname, send_sock, opcmd):
        f = open(fname, 'wb')

        # Send command
        rt = self.issue_cmd(send_sock, opcmd, '')
        if rt is False:
            error_critical("Read failed")

        # Receive response
        resp_packer = struct.Struct('!BBHII')
        resp_header_size = resp_packer.size
        try:
            send_sock.setblocking(1)
            resp = send_sock.recv(resp_header_size)
            resp_proto, resp_cmd, resp_flags, resp_datalen, ret_code = resp_packer.unpack(resp)
            print("Response: Proto = ", hex(resp_proto))
            print("Response: Cmd = ", hex(resp_cmd))
            print("Response: Flags = ", hex(resp_cmd))
            print("Response: DataLen = ", hex(resp_datalen))
            print("Response: ret_code = ", hex(ret_code))

            if resp_datalen == 0:
                return True

        except Exception as e:
            print(e)
            return False

        try:
            while (resp_datalen > 0):
                data = send_sock.recv(resp_datalen)
                print("Response: Recv Data len", len(data))
                f.write(data)
                resp_datalen -= len(data)
        except Exception as e:
            print(e)
            f.close()
            return False

        f.close()

        return True

    def check_devreg_data(self):
        log_debug("Write DevReg to Device")
        self.send_file(self.eesign_path, self.sock, FCD_CMD_WRITE_DEVREG)
        time.sleep(2)
        log_debug("Read DevReg From Device")
        self.recv_file(self.eechk_path, self.sock, FCD_CMD_READ_DEVREG)
        time.sleep(2)
        rt = filecmp.cmp(self.eesign_path, self.eechk_path)
        if rt is True:
            log_debug("DevReg Verify .... OK!")
        else:
            error_critical("DevReg Verify .... FAILED!")

    def get_dhcp_ip(self):
        self.pexp.expect_action(10, self.linux_prompt, "ip dhcp")
        self.pexp.expect_only(60, "Connected")
        netinfo = self.pexp.expect_get_output("ip", self.linux_prompt, 10)
        res = re.search(r"IP      : (.*)", netinfo, re.S)
        self.dut_dhcp_ip = res.group(1)

    def set_ipaddr(self):
        self.pexp.expect_action(10, self.linux_prompt, "ip down")
        self.pexp.expect_only(20, "Service Stopped")
        self.pexp.expect_action(10, self.linux_prompt, "setenv ipaddr {}".format(self.dutip), send_action_delay=True)
        self.pexp.expect_action(10, self.linux_prompt, "setenv dhcp_enable 0", send_action_delay=True)
        self.pexp.expect_action(10, self.linux_prompt, "ip up")
        self.pexp.expect_only(20, "Service Started")
        time.sleep(5)

    def create_socket(self):
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "fcd enable")

        self.set_ipaddr()

        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_addrport = (self.dutip, 23)
        self.sock.connect(server_addrport)
        time.sleep(1)

    def genkey(self):
        log_debug("Erase existed key cert files ...")
        files = [self.ncert, self.nkey]
        for f in files:
            destf = os.path.join(self.tftpdir, f)
            rtf = os.path.isfile(destf)
            if rtf is True:
                log_debug("Erasing File - " + f + " ...")
                os.chmod(destf, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.remove(destf)
            else:
                log_debug("File - " + f + " doesn't exist ...")

        ptn = "\"/C=TW/ST=TW/L=Taipei/O=ui.com/OU={0}/CN={1}\"".format(self.mac, self.mac + self.qrcode)

        cmd = [
           "cd " + self.tftpdir + ";",
           "openssl",
           "req -x509 -newkey rsa:2048",
           "-keyout " + self.nkey,
           "-out " + self.ncert,
           "-days 3650",
           "-nodes -subj",
           ptn
        ]

        cmd = ' '.join(cmd)
        log_debug("genkey cmd:\n" + cmd)

        [sto, rtc] = self.fcd.common.xcmd(cmd)
        time.sleep(1)
        if int(rtc) > 0:
            error_critical("Generating key files failed!!")
        else:
            log_debug("Generating key files successfully")

        fcert = open(self.cert_path, "rb")
        fkey = open(self.key_path, "rb")
        fout = open(self.keycert_path, "wb")

        contents = fcert.read()
        contents = contents.ljust(2048, b'\0')
        fcert.close()
        print("Cert size ", len(contents))

        key = fkey.read()
        key = key.ljust(2048, b'\0')
        fkey.close()
        print("Key size ", len(key))

        contents += key
        fout.write(contents)
        fout.close()
        print("Write CERT and KEY files to key_cert.bin size ", len(contents))

    def check_keycert(self):
        rtf = os.path.isfile(self.keycert_path)
        if rtf is not True:
            error_critical("Can't find " + self.keycert_path)

        log_debug("Write key cert to Device")
        self.send_file(self.keycert_path, self.sock, FCD_CMD_WRITE_KEYCERT)
        time.sleep(2)
        log_debug("Read key cert from Device")
        self.recv_file(self.keycertchk_path, self.sock, FCD_CMD_READ_KEYCERT)
        time.sleep(2)
        rt = filecmp.cmp(self.keycert_path, self.keycertchk_path)
        if rt is True:
            log_debug("Key cert Verify .... OK!")
        else:
            error_critical("Key cert Verify .... FAILED!")

    def check_info(self):
        self.pexp.expect_only(80, "Send normal inform to")  # ensure devreg thread is started
        self.pexp.expect_action(10, "", "")
        self.pexp.expect_action(10, self.linux_prompt, "fcd devreg")
        self.pexp.expect_only(60, "Security check result: Pass")
        self.pexp.expect_action(10, "", "")
        out = self.pexp.expect_get_output("version", self.linux_prompt, 20)
        res = re.search(r"Version = (\d+\.\d+\.\d+)", out, re.S)
        catfw = res.group(1).split(" ")

        if catfw[0] == self.fw_dotver:
            log_debug("FW version check PASS")
        else:
            error_critical("FW version check FAILED !!!")

        self.pexp.expect_action(10, self.linux_prompt, "resetenv")
        self.pexp.expect_action(10, self.linux_prompt, "saveenv")
        time.sleep(2)
        env = self.pexp.expect_get_output("printenv", self.linux_prompt, 10)
        if "fw_url" in env:
            error_critical("Reset environment FAILED!!!")
        else:
            log_debug("Reset environment check PASS")

    def stop_HTTP_Server(self):
        self.http_srv.shutdown()

    def create_HTTP_Server(self, port):
        self.http_srv = HTTPServer(('', port), SimpleHTTPRequestHandler)
        t = Thread(target=self.http_srv.serve_forever)
        t.setDaemon(True)
        t.start()
        log_debug('http server running on port {}'.format(self.http_srv.server_port))

    def fwupdate(self, backtoT1=False):
        os.chdir(self.fwdir)

        port = "800"+self.row_id
        self.create_HTTP_Server(int(port))

        fw_url = "http://{}:{}/{}-fw.bin".format(self.tftp_server, port, self.board_id)
        log_debug("fw_url:\n" + fw_url)

        if backtoT1 is True:
            # rename mfg to fw for updating
            log_debug("rename mfg img")
            os.rename("{}-fw.bin".format(self.board_id), "{}-fw.bin.bk".format(self.board_id))
            os.rename("{}-mfg.bin".format(self.board_id), "{}-fw.bin".format(self.board_id))
        else:
            # Reset for clear FCD enable which make fwupdate fail
            self.pexp.expect_action(10, self.linux_prompt, "reset")
            self.pexp.expect_only(60, "Service Started")
            self.pexp.expect_action(10, "", "")
            self.set_ipaddr()
            self.pexp.expect_action(10, self.linux_prompt, "fwupdate "+fw_url, send_action_delay=True)

        try:
            self.pexp.expect_only(200, "Run application from")
            self.stop_HTTP_Server()
        finally:
            if backtoT1 is True:
                # restore name of mfg and fw
                log_debug("restore name of mfg img")
                os.rename("{}-fw.bin".format(self.board_id), "{}-mfg.bin".format(self.board_id))
                os.rename("{}-fw.bin.bk".format(self.board_id), "{}-fw.bin".format(self.board_id))

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/{0} -b 115200".format(self.dev)
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Open serial port successfully ...")
        self.pexp.expect_only(60, "# Bootloader #")

        try:
            # do_fwupgrade = 1 means the fwupdate have been failed before
            self.pexp.expect_only(5, "do_fwupgrade=1")
            log_debug(msg="Update to MFG img first!")
            self.fwupdate(backtoT1=True)
        except Exception as e:
            log_debug("Skip back to MFG img")
        finally:
            pass

        self.pexp.expect_only(60, "Service Started")
        self.create_socket()

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            self.prepare_server_need_files()
            msg(30, "Finish preparing the devreg file ...")

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")
            self.genkey()
            self.check_keycert()
            msg(60, "Finish doing key cert checking ...")

        if FWUPDATE_ENABLE is True:
            msg(70, "Updating formal firmware ...")
            self.fwupdate()

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    if len(sys.argv) < 10:  # TODO - hardcode
        msg(no="", out=str(sys.argv))
        error_critical(msg="Arguments are not enough")
    else:
        us_m487_general = USM487FactoryGeneral()
        us_m487_general.run()

if __name__ == "__main__":
    main()
