
#!/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

from script_base import ScriptBase
from ubntlib.equipment.edgeswitch import EdgeSwitch
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


class CONNECTAPQ8053actoryGeneral(ScriptBase):
    def __init__(self):
        super(CONNECTAPQ8053actoryGeneral, self).__init__()
        self.PROVISION_ENABLE = True
        self.REGISTER_ENABLE = True
        self.INFOCHECK_ENABLE = True
        self.init_vars()

    def init_vars(self):
        self.ver_extract()
        self.linux_prompt = "msm8953_uct"

        # defalut JEDEC ID for EMMC
        self.df_jedecid = "0007f100"

        # default product class: basic
        self.df_prod_class = "0014"

        # number of mac
        self.macnum = {
            'ef80': "1",
            'ef81': "1",
            'ec60': "1"
        }

        # number of WiFi
        self.wifinum = {
            'ef80': "0",
            'ef81': "0",
            'ec60': "1"
        }

        # number of Bluetooth
        self.btnum = {
            'ef80': "1",
            'ef81': "1",
            'ec60': "1"
        }

        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum
        }

    def access_chips_id(self):
        cmd = "cat /sys/devices/soc0/soc_id"
        tmp = self.pexp.expect_get_output(cmd, self.linux_prompt)
        tmp = tmp.replace('\r', '')
        cpuid = tmp.split("\n")

        # left zero padding
        cpuid[1] = cpuid[1].zfill(8)

        cmd = "cat /sys/class/block/mmcblk0/device/cid"
        tmp = self.pexp.expect_get_output(cmd, self.linux_prompt)
        tmp = tmp.replace('\r', '')
        uuid = tmp.split("\n")

        # 07f100 is hard code by Mike
        optotal = [
            "-i field=product_class_id,format=hex,value={0}".format(self.df_prod_class),
            "-i field=cpu_rev_id,format=hex,value={0}".format(str(cpuid[1])),
            "-i field=flash_uid,format=hex,value={0}".format(uuid[1]),
            "-i field=flash_jedec_id,format=hex,value={0}".format(self.df_jedecid)
        ]
        optotal = ' '.join(optotal)

        return optotal

    def data_provision_64k(self, netmeta, post_en=True):
        self.gen_rsa_key()

        post_exp = None
        if post_en is True:
            post_exp = self.linux_prompt

        otmsg = "Starting to do {0} ...".format(self.eepmexe)
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
            "-e " + netmeta['ethnum'][self.board_id],
            "-w " + netmeta['wifinum'][self.board_id],
            "-b " + netmeta['btnum'][self.board_id],
            "-k " + self.rsakey_path
        ]
        sstr = ' '.join(sstr)
        log_debug("flash editor cmd: " + sstr)
        [sto, rtc] = self.cnapi.xcmd(sstr)
        time.sleep(0.5)
        if int(rtc) > 0:
            otmsg = "Flash editor filling out {0} file failed!!".format(self.eegenbin_path)
            error_critical(otmsg)
        else:
            otmsg = "Flash editor filling out {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        self.eebin_path = self.eegenbin_path

    def registration(self):
        log_debug("Starting to do registration ...")
        regsubparams = self.access_chips_id()

        # The HEX of the QR code
        if self.qrcode is None or not self.qrcode:
            reg_qr_field = ""
        else:
            reg_qr_field = "-i field=qr_code,format=hex,value=" + self.qrhex

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

        regparam = [
            "-h devreg-prod.ubnt.com",
            "-k " + self.pass_phrase,
            regsubparams,
            reg_qr_field,
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

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)

        clit = ExpttyProcess(self.row_id, cmd, "\n")
        clit.expect_only(30, "Ubiquiti Device Security Client")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        log_debug("Excuting client_x86 registration successfully")

    def check_mac(self):
        comac = self.mac_format_str2comma(self.mac)
        egsw = EdgeSwitch()
        for ct in range(0, 60):
            portn = int(self.row_id) + 1
            rtmsg = "EdgeSwitch port: {0}".format(portn)
            log_debug(rtmsg)
            egmac = egsw.get_mac(port=portn)
            time.sleep(1)
            if egmac is not False:
                rtmsg = "Get DUT MAC address: {0}".format(egmac.upper())
                log_debug(rtmsg)
                rtmsg = "Input MAC address: {0}".format(comac.upper())
                log_debug(rtmsg)
                egsw.close()
                if comac.upper() == egmac.upper():
                    log_debug("MAC comparison successfully")
                    return True
                else:
                    error_critical(msg="MAC address comparison failed!")
            else:
                rtmsg = "Retry {} .. to get MAC address".format(ct + 1)
                log_debug(rtmsg)
        else:
            error_critical(msg="Can't get the MAC address from EGS!")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.cnapi.print_current_fcd_version()

        for ct in range(0, 60):
            portn = int(self.row_id) + 1
            rtmsg = "EdgeSwitch port: {0}".format(portn)
            log_debug(rtmsg)
            egsw = EdgeSwitch()
            dutip = egsw.get_ip(port=portn)
            time.sleep(1)
            egsw.close()
            if dutip is not False:
                rtmsg = "DUT Ethernet IP address: {0}".format(dutip)
                log_debug(rtmsg)
                break
            else:
                rtmsg = "Retry {} .. to get IP address".format(ct + 1)
                log_debug(rtmsg)
        else:
            error_critical(msg="Can't get the IP address from EGS!")

        # ADB connection to Android platform
        for i in range(0, 60):
            try:
                cmd = "adb connect {0}:5555".format(dutip)
                self.cnapi.xcmd(cmd)

                cladb = ExpttyProcess(self.row_id, "adb root", "\n")
                cladb.expect_only(2, "adbd is already running as root")

                pexpect_cmd = "adb -e -s {0}:5555 shell".format(dutip)
                log_debug(msg=pexpect_cmd)
                pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
            except Exception as e:
                # Ctrl+C anyway to avoid hangup cmd
                cladb.expect_action(3, "", "\003")
                if i < 3:
                    print("Retry {0}".format(i + 1))
                    time.sleep(1)
                    continue
                else:
                    print("Exceeded maximum retry times {0}".format(i))
                    raise e
            else:
                break

        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.erase_eefiles()
            self.data_provision_64k(self.devnetmeta)

            lmac = self.mac_format_str2list(self.mac)
            bmac = '\\x{0}\\x{1}\\x{2}\\x{3}\\x{4}\\x{5}'.format(lmac[0], lmac[1], lmac[2], lmac[3], lmac[4], lmac[5])
            cmd = "echo -n -e \'{0}\' > /mnt/vendor/persist/eth_mac".format(bmac)
            log_debug("cmd: " + cmd)
            time.sleep(1)
            self.pexp.expect_action(10, self.linux_prompt, cmd)

        if self.REGISTER_ENABLE is True:
            msg(40, "Sendtools to DUT and data provision ...")
            self.registration()

        if self.INFOCHECK_ENABLE is True:
            msg(60, "Check the information ...")
            self.pexp.expect_action(5, self.linux_prompt, "reboot")
            self.check_mac()

        msg(100, "Complete FCD process ...")
        self.close_fcd()


def main():
    factory = CONNECTAPQ8053actoryGeneral()
    factory.run()

if __name__ == "__main__":
    main()
