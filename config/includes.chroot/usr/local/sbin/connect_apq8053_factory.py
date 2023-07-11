# !/usr/bin/python3

import sys
import time
import os
import re
import stat
import filecmp

from script_base import ScriptBase
from PAlib.Ubnt.edgeswitch import EdgeSwitch
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical
from datetime import datetime

'''
    e980: Viewport            (Android 9)
    ef80: UC-Display-7  (BLE)       (Android 9)
    ef81: UC-Display-13 (BLE)       (Android 9)
    ef87: UC-Display-7  (BLE/WIFI)  (Android 9)
    ef88: UC-Display-13 (BLE/WIFI)  (Android 9)
    ef82: UVP_Touch           (Android 7)
    ef90: UC-Cast             (Android 9)
    ef13: UT-PHONE-TOUCH-W    (Android 7)
    ef0e: UVP_TouchMax        (Android 7)
    ef83: UC-Display-21       (Android 9)
    ef84: UC-Display-27       (Android 9)
    ef85: UniFi Pay 7         (Android 9)
    ef86: UniFi Pay 13        (Android 9)
    ec5e: UA-G2-Reader-Pro    (Android 9)
    ec5f: UA-PRO              (Android 9)
    ec60: UA-BL-PRO           (Android 9)
    ec62: UA-Display-Elevator (Android 9)
    ec61: UA-Display-Gate     (Android 9)
    efa0: EV-Charger          (Android 9)
    efb0: UniFi Touch (Lock)  (Android 7)
    efb1: UniFi Touch (unLock)(Android 7)
    efb2: UniFi Touch White (Lock)(Android 7)
    efb3: UniFi Touch White (unLock)(Android 7)
    efb4: UniFi TouchMax (Lock)(Android 9)
    efb5: UniFi TouchMax (unLock)(Android 9)
    efb6: UniFi TouchMax White (Lock)(Android 9)
    efb7: UniFi TouchMax White (unLock)(Android 9)
    efba: UniFi G3 TouchMax Wallmount   (Android 9)
    efa1: EV-Charger-EU        (Android 9)
    efbb: Phone G3 Touch Pro   (Android 9)
    efbc: Phone G3 Touch Pro Max   (Android 9)
    ec64: UniFi Access G2 Portal(Android 9)

'''


class CONNECTAPQ8053actoryGeneral(ScriptBase):
    def __init__(self):
        super(CONNECTAPQ8053actoryGeneral, self).__init__()
        self.PROVISION_ENABLE = True
        self.REGISTER_ENABLE = True
        self.INFOCHECK_ENABLE = True

        self.init_vars()

    def init_vars(self):
        self.ver_extract()

        # defalut JEDEC ID for EMMC
        emmc_jedec = {
            'e980': "0007f100",
            'ef80': "0007f100",  # UI EMMC PN: 140-04199
            'ef81': "0007f100",  # UI EMMC PN: 140-04199
            'ef82': "0007f100",
            'ef13': "0007f100",
            'ef87': "0007f100",  # UI EMMC PN: 140-04199
            'ef88': "0007f100",  # UI EMMC PN: 140-04199
            'ef90': "0007f102",  # UI EMMC PN: 140-04869
            'ef0e': "0007f100",
            'ef83': "0007f100",  # UI EMMC PN: 140-04199
            'ef84': "0007f100",  # UI EMMC PN: 140-04199
            'ef85': "0007f100",
            'ef86': "0007f100",
            'ec5e': "0007f100",
            'ec5f': "0007f100",
            'ec60': "0007f100",
            'ec61': "0007f100",
            'ec62': "0007f100",
            'efa0': "0007f100",
            'efb0': "0007f100",
            'efb1': "0007f100",
            'efb2': "0007f100",
            'efb3': "0007f100",
            'efb4': "0007f100",
            'efb5': "0007f100",
            'efb6': "0007f100",
            'efb7': "0007f100",
            'efba': "0007f100",
            'efa1': "0007f100",
            'efbb': "0007f100",
            'efbc': "0007f100",
            'ec64': "0007f100"
        }

        # default product class: basic
        self.df_prod_class = "0014"
        self.usbadb_list = [
            "e980", "ec60", "ec62", "ef0e", "ef80", "ef81", "ef82",
            "ef83", "ef84", "ef87", "ef88", "ef90", "ef13", "ec61",
            "efb0", "efb1", "efb2", "efb3", "efb4", "efb5", "efb6",
            "efb7", "efa0", "ec5e", "ec5f", "efba", "efa1", "efbb",
            "efbc", "ec64"
        ]

        self.ospl = {
            'e980': "adr9",
            'ef80': "adr9",
            'ef81': "adr9",
            'ef82': "adr7",
            'ef13': "adr7",
            'ef87': "adr9",
            'ef88': "adr9",
            'ef90': "adr9",
            'ef0e': "adr9",
            'ef83': "adr9",
            'ef84': "adr9",
            'ef85': "adr9",
            'ef86': "adr9",
            'ec5e': "adr9",
            'ec60': "adr9",
            'ec62': "adr9",
            'ec61': "adr9",
            'efa0': "adr9",
            'efb0': "adr7",
            'efb1': "adr7",
            'efb2': "adr7",
            'efb3': "adr7",
            'efb4': "adr9",
            'efb5': "adr9",
            'efb6': "adr9",
            'efb7': "adr9",
            'ec5f': "adr9",
            'efba': "adr9",
            'efa1': "adr9",
            'efbb': "adr9",
            'efbc': "adr9",
            'ec64': "adr9"
        }

        self.lnxpmt = {
            'e980': "protectbox",
            'ef80': "msm8953_uct",
            'ef81': "unifi_p13",
            'ef87': "msm8953_uct",
            'ef88': "unifi_p13",
            'ef82': "msm8953_uvp",
            'ef13': "msm8953_uvp",
            'ef0e': "uvp_touchmax",
            'ef83': "unifi_p21",
            'ef84': "unifi_p27",
            'ef85': "",
            'ef86': "",
            'ef90': "uc_cast",
            'ec5e': "uapro_g2",
            'ec5f': "frontrow_da",
            'ec60': "msm8953_uapro",
            'ec62': "",
            'ec61': "ud_gate",
            'efa0': "ev_charger",
            'efb0': "msm8953_uvp",
            'efb1': "msm8953_uvp",
            'efb2': "msm8953_uvp",
            'efb3': "msm8953_uvp",
            'efb4': "uvp_touchmax",
            'efb5': "uvp_touchmax",
            'efb6': "uvp_touchmax",
            'efb7': "uvp_touchmax",
            'efba': "utp_wallmount",
            'efa1': "ev_charger",
            'efbb': "utp_g3_pro",
            'efbc': "utp_g3_pro_max",
            'ec64': "rdr_mdu"
        }

        # Number of Ethernet
        self.macnum = {
            'e980': "1",
            'ef80': "1",
            'ef81': "1",
            'ef87': "1",
            'ef88': "1",
            'ef82': "1",
            'ef13': "1",
            'ef0e': "1",
            'ef83': "1",
            'ef84': "1",
            'ef85': "0",
            'ef86': "0",
            'ef90': "1",
            'ec5e': "1",
            'ec5f': "1",
            'ec60': "1",
            'ec62': "1",
            'ec61': "1",
            'efa0': "1",
            'efb0': "1",
            'efb1': "1",
            'efb2': "1",
            'efb3': "1",
            'efb4': "1",
            'efb5': "1",
            'efb6': "1",
            'efb7': "1",
            'efba': "1",
            'efa1': "1",
            'efbb': "1",
            'efbc': "1",
            'ec64': "1"
        }

        # Number of WiFi
        self.wifinum = {
            'e980': "0",
            'ef80': "0",
            'ef81': "0",
            'ef87': "1",
            'ef88': "1",
            'ef82': "1",
            'ef13': "1",
            'ef0e': "1",
            'ef83': "1",
            'ef84': "0",
            'ef85': "1",
            'ef86': "1",
            'ef90': "1",
            'ec5e': "1",
            'ec5f': "1",
            'ec60': "1",
            'ec62': "0",
            'ec61': "0",
            'efa0': "1",
            'efb0': "1",
            'efb1': "1",
            'efb2': "1",
            'efb3': "1",
            'efb4': "1",
            'efb5': "1",
            'efb6': "1",
            'efb7': "1",
            'efba': "1",
            'efa1': "1",
            'efbb': "1",
            'efbc': "1",
            'ec64': "0"
        }

        # Number of Bluetooth
        self.btnum = {
            'e980': "1",
            'ef80': "1",
            'ef81': "1",
            'ef87': "1",
            'ef88': "1",
            'ef82': "1",
            'ef13': "1",
            'ef0e': "1",
            'ef83': "1",
            'ef84': "0",
            'ef85': "1",
            'ef86': "1",
            'ef90': "1",
            'ec5e': "1",
            'ec5f': "1",
            'ec60': "1",
            'ec62': "1",
            'ec61': "1",
            'efa0': "1",
            'efb0': "1",
            'efb1': "1",
            'efb2': "1",
            'efb3': "1",
            'efb4': "1",
            'efb5': "1",
            'efb6': "1",
            'efb7': "1",
            'efba': "2",
            'efa1': "1",
            'efbb': "2",
            'efbc': "2",
            'ec64': "1"
        }

        self.qrcode_dict = {
            'e980': True,
            'ef80': True,
            'ef81': True,
            'ef87': True,
            'ef88': True,
            'ef82': True,
            'ef13': True,
            'ef0e': True,
            'ef83': True,
            'ef84': True,
            'ef85': True,
            'ef86': True,
            'ef90': True,
            'ec5e': True,
            'ec5f': False,
            'ec60': True,
            'ec62': True,
            'ec61': True,
            'efa0': True,
            'efb0': True,
            'efb1': True,
            'efb2': True,
            'efb3': True,
            'efb4': True,
            'efb5': True,
            'efb6': True,
            'efb7': True,
            'efba': True,
            'efa1': True,
            'efbb': True,
            'efbc': True,
            'ec64': True
        }

        self.devnetmeta = {
            'ethnum': self.macnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }
        
        #Add method for write BOM ID/ QR ID
        self.write_persist = {
            'e980': False,
            'ef80': False,
            'ef81': False,
            'ef87': False,
            'ef88': False,
            'ef82': False,
            'ef13': False,
            'ef0e': False,
            'ef83': False,
            'ef84': False,
            'ef85': False,
            'ef86': False,
            'ef90': False,
            'ec5e': True,
            'ec5f': False,
            'ec60': False,
            'ec62': False,
            'ec61': False,
            'efa0': False,
            'efb0': False,
            'efb1': False,
            'efb2': False,
            'efb3': False,
            'efb4': False,
            'efb5': False,
            'efb6': False,
            'efb7': False,
            'efba': True,
            'efa1': False,
            'efbb': True,
            'efbc': True,
            'ec64': True
        }

        self.cladb = None
        self.linux_prompt = self.lnxpmt[self.board_id]
        self.df_jedecid = emmc_jedec[self.board_id]

        if self.ospl[self.board_id] == "adr9":
            if self.board_id == "e980":
                self.persist_cfg_file = "/persist/WCNSS_qcom_cfg_extra.ini"
                self.cfg_file = ""
                self.f_eth_mac = "/metadata/ethmac.txt"
                self.f_qr_id = ""
            elif self.board_id == "ef84":
                self.persist_cfg_file = ""
                self.cfg_file = ""
                self.f_eth_mac = "/mnt/vendor/persist/eth_mac"
                self.f_qr_id = "/mnt/vendor/persist/qr_id"
            elif self.board_id == "ef90":
                self.persist_cfg_file = "/persist/WCNSS_qcom_cfg_extra.ini"
                self.f_eth_mac = "/vendor/factory/MAC_ADDR"
                self.f_qr_id = "/vendor/factory/qr_id"
                self.f_wifi_country_code = "/vendor/factory/wificountrycode"
                self.cfg_file = ""
            elif self.board_id == "ec5f":
                self.persist_cfg_file = ""
                self.f_eth_mac = "/persist/eth/.macadd"
                self.f_qr_id = ""
                self.cfg_file = ""
            else:
                self.persist_cfg_file = "/mnt/vendor/persist/WCNSS_qcom_cfg.ini"
                self.cfg_file = "/data/vendor/wifi/WCNSS_qcom_cfg.ini"
                self.f_eth_mac = "/mnt/vendor/persist/eth_mac"
                self.f_qr_id = "/mnt/vendor/persist/qr_id"
        else:
            self.persist_cfg_file = "/persist/WCNSS_qcom_cfg.ini"
            self.cfg_file = "/data/misc/wifi/WCNSS_qcom_cfg.ini"
            self.f_eth_mac = "/persist/eth_mac"
            self.f_qr_id = "/persist/qr_id"

        if self.region == "0000":
            self.android_cc = "000"
        elif self.region == "002a":
            self.android_cc = "USI"

    def get_dut_ip(self):
        portn = int(self.row_id) + 1
        rtmsg = "EdgeSwitch port: {0}".format(portn)
        log_debug(rtmsg)
        for ct in range(0, 4):
            try:
                self.egsw = EdgeSwitch(ip='192.168.1.30', id='ubnt', pw='ubnt1234')
            except Exception as e:
                if ct < 3:
                    print("Retry {0}".format(ct + 1))
                    time.sleep(1)
                    continue
                else:
                    print("Exceeded maximum retry times {0}".format(ct))
                    raise e
            else:
                break

        self.dutip = self.egsw.get_ip(port=portn, retry=60)
        if self.dutip is False:
            error_critical("Get DUT IP address failed!!")

    def connect_adb_eth(self):
        # ADB connection to Android platform by Ethernet
        retry = 60
        for i in range(0, retry):
            try:
                cmd = "adb connect {0}:5555".format(self.dutip)
                [buffer, returncode] = self.cnapi.xcmd(cmd)
                if "connected to {}".format(self.dutip) not in buffer:
                    if i < retry:
                        print("Retry {0}".format(i + 1))
                        time.sleep(1)
                        continue
                    else:
                        print("Exceeded maximum retry times {0}".format(i))
                        error_critical(msg="ADB over ethernet Failed!")

                self.cladb = ExpttyProcess(self.row_id, "adb root", "\n")
                self.cladb.expect_only(2, "adbd is already running as root")

                pexpect_cmd = "adb -e -s {0}:5555 shell".format(self.dutip)
                log_debug(msg=pexpect_cmd)
                pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
            except Exception as e:
                # Ctrl+C anyway to avoid hangup cmd
                self.cladb.expect_action(3, "", "\003")
                if i < retry:
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

    def connect_adb_usb(self):
        # ADB connection to Android platform by USB
        retry = 60
        for i in range(0, retry):
            try:
                self.cladb = ExpttyProcess(self.row_id, "adb root", "\n")
                self.cladb.expect_only(10, "adbd is already running as root")
                # if self.board_id == "ef90":
                #     self.cladb.expect_action(10, "", "adb shell logcat > /tmp/dut_sys_log.txt &")

                pexpect_cmd = "adb shell"
                log_debug(msg=pexpect_cmd)
                pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
            except Exception as e:
                # Ctrl+C anyway to avoid hangup cmd
                self.cladb.expect_action(7, "", "\003")
                self.cladb.close()
                self.cladb = None
                if i < retry:
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

    def access_chips_id(self):
        if self.board_id == "ef90":
            cmd = "cat /sys/devices/system/cpu/cpu0/regs/identification/midr_el1"
            tmp = self.pexp.expect_get_output(cmd, self.linux_prompt)
            cpuid = tmp.replace('\r', '').split("\n")

            # extract the last 8 characters
            cpuid_for_server = cpuid[1][-8:]
        else:
            cmd = "cat /sys/devices/soc0/soc_id"
            tmp = self.pexp.expect_get_output(cmd, self.linux_prompt)
            cpuid = tmp.replace('\r', '').split("\n")

            # left zero padding
            cpuid_for_server = cpuid[1].zfill(8)

        cmd = "cat /sys/class/block/mmcblk0/device/cid"
        tmp = self.pexp.expect_get_output(cmd, self.linux_prompt)
        tmp = tmp.replace('\r', '')
        uuid = tmp.split("\n")

        # 07f100 is hard code by Mike
        optotal = [
            "-i field=product_class_id,format=hex,value={0}".format(self.df_prod_class),
            "-i field=cpu_rev_id,format=hex,value={0}".format(str(cpuid_for_server)),
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

    def registration(self):
        log_debug("Starting to do registration ...")
        regsubparams = self.access_chips_id()

        clientbin = "/usr/local/sbin/client_rpi4_release"

        regparam = [
            "-h prod.udrs.io",
            "-k {}".format(self.pass_phrase),
            regsubparams,
            "-i field=flash_eeprom,format=binary,pathname={}".format(self.eegenbin_path),
            "-i field=fcd_version,format=hex,value={}".format(self.sem_ver),
            "-i field=sw_id,format=hex,value={}".format(self.sw_id),
            "-i field=sw_version,format=hex,value={}".format(self.fw_ver),
            "-o field=flash_eeprom,format=binary,pathname={}".format(self.eesign_path),
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

        # The HEX of the QR code
        if self.qrcode_dict[self.board_id]:
            regparam.append("-i field=qr_code,format=hex,value={}".format(self.qrhex))

        regparam = ' '.join(regparam)

        cmd = "sudo {0} {1}".format(clientbin, regparam)
        print("cmd: " + cmd)

        clit = ExpttyProcess(self.row_id, cmd, "\n")

        # Due update new client, the title become "Security Service Device Registration Client"
        clit.expect_only(30, "Security Service Device")
        clit.expect_only(30, "Hostname")
        clit.expect_only(30, "field=result,format=u_int,value=1")

        log_debug("Excuting client_x86 registration successfully")

    def check_mac_by_edsw(self):
        comac = self.mac_format_str2comma(self.mac)
        for ct in range(0, 60):
            portn = int(self.row_id) + 1
            rtmsg = "EdgeSwitch port: {0}".format(portn)
            log_debug(rtmsg)
            egmac = self.egsw.get_mac(port=portn)
            time.sleep(1)
            if egmac is not False:
                rtmsg = "Get DUT MAC address: {0}".format(egmac.upper())
                log_debug(rtmsg)
                rtmsg = "Input MAC address: {0}".format(comac.upper())
                log_debug(rtmsg)
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

    def check_qrcode(self):
        pass

    def write_and_check_mac_e980(self):
        mode_script_source = os.path.join(self.tftpdir, "protectbox", "usb_mode.sh")
        mode_script_target = os.path.join("/data", "usb_mode.sh")
        self.cnapi.xcmd("adb push {} {}".format(mode_script_source, mode_script_target))
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "chmod 777 {}".format(mode_script_target))
        lmac = self.mac_format_str2comma(self.mac)
        cmd = "lan78xx-update-mac {}".format(lmac)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)
        self.pexp.close()
        time.sleep(2)
        self.cnapi.xcmd("adb tcpip 5555")
        # reconnect using adb over ethernet
        time.sleep(2)
        self.cnapi.xcmd("adb shell {} host &".format(mode_script_target))
        time.sleep(20)
        #self.get_dut_ip()
        # use static IP address - FTU configuration
        cmd = "echo \"ubnt\" | sudo -S ip addr add {}/24 dev eth0".format("192.168.168.19")
        self.cnapi.xcmd(cmd)
        time.sleep(2)
        self.dutip = "192.168.168.11"
        self.connect_adb_eth()
        cmd = "ethtool -E eth0 magic 0x78A5 offset 0 length 512 < /data/lan7801_eeprom.bin"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        time.sleep(2)
        cmd = "ethtool -e eth0 offset 1 length 6 maconly 2"
        output = self.pexp.expect_get_output(cmd, self.linux_prompt)
        if lmac.upper() not in output:
            error_critical("Fail to write Eth MAC address ...")
        # switch back to usb adb
        self.pexp.expect_lnxcmd(10, "", "")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "{} usb &".format(mode_script_target))
        self.pexp.close()
        time.sleep(2)
        self.cnapi.xcmd("adb disconnect {}".format(self.dutip))
        time.sleep(5)
        self.connect_adb_usb()
        # write BT MAC
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "rm -rf /persist/bluetooth/.bt_nv.bin")
        btmac = self.mac_format_str2comma(hex(int(self.mac, 16) + 1)[2:].zfill(12))
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "btnvtool -b {}".format(btmac))
        output = self.pexp.expect_get_output("btnvtool -g", self.linux_prompt)
        if btmac.upper() not in output:
            error_critical("Fail to write BT MAC address ...")


    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        if self.board_id in self.usbadb_list:
            self.connect_adb_usb()
        else:
            self.get_dut_ip()
            self.connect_adb_eth()

        msg(5, "Open serial port successfully ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.erase_eefiles()
            self.data_provision_64k(self.devnetmeta)

            # Write MAC
            if self.board_id == "ef90":
                lmac = self.mac_format_str2comma(self.mac)
                moount = 'mount -o rw,remount /vendor/factory'
                cmd = "echo {0} > {1}".format(lmac, self.f_eth_mac)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, moount, valid_chk=True)
            elif self.board_id == "ec5f":
                lmac = self.mac_format_str2comma(self.mac)
                cmd = "mkdir /persist/eth; echo {0} > {1}".format(lmac, self.f_eth_mac)
            elif self.board_id == "e980":
                cmd = ""
                self.write_and_check_mac_e980()
            else:
                lmac = self.mac_format_str2list(self.mac)
                bmac = '\\x{0}\\x{1}\\x{2}\\x{3}\\x{4}\\x{5}'.format(lmac[0], lmac[1], lmac[2], lmac[3], lmac[4],
                                                                     lmac[5])
                cmd = "echo -n -e \'{0}\' > {1}".format(bmac, self.f_eth_mac)

            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

            # Write QR code
            if self.board_id == 'e980' or self.board_id == 'ec5f':
                pass
            else:
                cmd = "echo {0} > {1}".format(self.qrcode, self.f_qr_id)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

            # Write Country Code
            '''
                If finding
                   /data/vendor/wifi/WCNSS_qcom_cfg.ini (Android9)
                   /data/misc/wifi/WCNSS_qcom_cfg.ini   (Android7)
                then, remove them
            '''
            if self.board_id == "ef90":
                if self.region is not None:
                    if self.region == '0000':
                        wifi_country_code = 'EU'
                    elif self.region == '002a':
                        wifi_country_code = 'US'
                    cmd = "echo {0} > {1}".format(wifi_country_code, self.f_wifi_country_code)
                    self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)
            if self.board_id != "ef90" or self.board_id != "ec5f":
                cmd = "rm {}".format(self.cfg_file)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

            #Set permission
            cmd = "chmod 644 {}".format(self.f_eth_mac)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
            cmd = "chmod 644 {}".format(self.f_qr_id)
            self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
            
            # Write persist cfg file
            if self.board_id == "e980" or self.board_id == "ef90" or self.board_id == "ef84" or self.board_id == 'ec5f':
                # No WiFi, No need to write teh country code
                pass
            else:
                cmd = "sed -i 's/^gStaCountryCode=*//g' {}".format(self.persist_cfg_file)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)
                if self.android_cc != "000":
                    cmd = "sed -i 's/^END$/gStaCountryCode={}\n\nEND/g' {}".format(self.android_cc,
                                                                                   self.persist_cfg_file)
                    self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

            #Write Wifi/BT MAC,BOM ID and QR ID
            if self.write_persist[self.board_id] is True:
                nextmac = self.mac
                if self.wifinum[self.board_id] == '1':
                    self.wifimac = nextmac = hex(int(nextmac, 16) + 1)[2:].zfill(12)
                    cmd = "write_wlan_mac -w  {}".format(self.mac_format_str2comma(nextmac))
                    self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)
                if self.btnum[self.board_id] != '0':
                    self.btmac = nextmac = hex(int(nextmac, 16) + 1)[2:].zfill(12)
                    nextmac = ":".join(nextmac[i:i + 2] for i in range(0, len(nextmac), 2))
                    cmd = "btnvtool -b {}".format(nextmac)
                    self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

                cmd = "echo 113-{} > /mnt/vendor/persist/bom_id".format(self.bom_rev)
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

                cmd = "echo {} > /mnt/vendor/persist/bom_hwver".format(self.bom_rev[-2:])
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

                cmd = "chmod 644 /mnt/vendor/persist/bom_id"
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)

                cmd = "chmod 644 /mnt/vendor/persist/bom_hwver"
                self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd, valid_chk=True)


        if self.REGISTER_ENABLE is True:
            msg(40, "Send tools to DUT and data provision ...")
            self.registration()

        if self.INFOCHECK_ENABLE is True:
            msg(60, "Check the information ...")
            if self.board_id == "ef90":
                cmd = "cat /vendor/factory/MAC_ADDR"
                getmac = self.pexp.expect_get_output(cmd, self.linux_prompt)
                m_gmac = re.findall(r"macaddr=(.*)", getmac)
                if m_gmac:
                    log_debug("Get MAC address: " + m_gmac[0])
                    if lmac not in m_gmac[0]:
                        error_critical("Check MAC is not matched !!")

                cmd = "cat /vendor/factory/qr_id"
                getqrid = self.pexp.expect_get_output(cmd, self.linux_prompt)
                log_debug("Get QRID: " + getqrid)
                m_gqr = re.findall(r"qr_id=(.*)", getqrid)
                if m_gqr:
                    log_debug("Get QR_ID: " + m_gqr[0])
                    if self.qrcode not in m_gqr[0]:
                        error_critical("Check QRID is not matched !!")
            else:
                cmd = "cat {}| xxd -p".format(self.f_eth_mac)
                getmac = self.pexp.expect_get_output(cmd, self.linux_prompt)
                m_gmac = re.findall(r"([0-9A-Fa-f]{12})", getmac)[0].replace(" ","")
                log_debug("Get MAC address: " + m_gmac)
                if self.mac == m_gmac:
                    log_debug("Check Eth MAC is matched !!")
                else:
                    error_critical("Check Eth MAC is not matched !!")

                if self.write_persist[self.board_id] is True:
                    if self.wifinum[self.board_id] == "1":
                        cmd = "write_wlan_mac -r"
                        getmac = self.pexp.expect_get_output(cmd, self.linux_prompt)
                        m_gmac = getmac.replace(':','')
                        if self.wifimac in m_gmac:
                            log_debug("Check Wifi MAC is matched !!")
                        else:
                            error_critical("Check Wifi MAC is not matched !!")

                    if self.btnum[self.board_id] != "0":
                        cmd = "btnvtool -z"
                        getmac = self.pexp.expect_get_output(cmd, self.linux_prompt).strip()
                        m_gmac = getmac.replace('.',':').split('\n')[1]
                        # if no new line, remove prompt string
                        m_gmac = m_gmac.split(self.lnxpmt[self.board_id])[0]
                        m_gmac = ''.join([ss.zfill(2) for ss in m_gmac.split(':')])
                        log_debug(m_gmac)
                        if self.btmac in m_gmac:
                            log_debug("Check BT MAC is matched !!")
                        else:
                            error_critical("Check BT MAC is not matched !!")

                    cmd = "cat /mnt/vendor/persist/bom_id"
                    m_gbomid = self.pexp.expect_get_output(cmd, self.linux_prompt)
                    if self.bom_rev in m_gbomid:
                        log_debug("Check BOM ID is matched !!")
                    else:
                        error_critical("Check BOM ID is not matched !!")

                    cmd = "cat /mnt/vendor/persist/bom_hwver"
                    m_gbomrev = self.pexp.expect_get_output(cmd, self.linux_prompt)
                    if self.bom_rev[-2:] in m_gbomrev:
                        log_debug("Check BOM Rev is matched !!")
                    else:
                        error_critical("Check BOM Rev is not matched !!")

                if self.qrcode_dict[self.board_id] is True:
                    cmd = "cat {}".format((self.f_qr_id))
                    m_gqrid = self.pexp.expect_get_output(cmd, self.linux_prompt)
                    if self.qrcode in m_gqrid:
                        log_debug("Check QR ID is matched !!")
                    else:
                        error_critical("Check QR ID is not matched !!")


        if self.board_id == "ef90":
            msg(80, "Wait clean boot ...")
            # time.sleep(40)
            t_secs = 60
            dt_last = datetime.now()
            ts = datetime.now() - dt_last
            while ts.seconds <= t_secs:
                cmd = "getprop sys.boot_completed"
                status = self.pexp.expect_get_output(cmd, self.linux_prompt)
                if '1' in status:
                    log_debug("System boot completed!!")
                    break

            dt_last = datetime.now()
            ts = datetime.now() - dt_last
            while ts.seconds <= t_secs:
                cmd = "getprop sys.bootstat.first_boot_completed"
                status = self.pexp.expect_get_output(cmd, self.linux_prompt)
                if '1' in status:
                    log_debug("System first boot completed!!")
                    break

            log_debug('DUT system log:')
            cmd = "logcat"
            status = self.pexp.expect_get_output(cmd, self.linux_prompt)

            msg(90, "Sync data ...")
            cmd = "sync"
            status = self.pexp.expect_get_output(cmd, self.linux_prompt)
            time.sleep(1)
            cmd = "setprop sys.powerctl reboot,shutdown"
            status = self.pexp.expect_get_output(cmd, self.linux_prompt)
            time.sleep(10)

            # try:
            #     rsp = self.cladb.expect_get_output('cat /tmp/dut_sys_log.txt', 'RPi')
            #     log_debug('DUT system log:\n{}'.format(rsp))
            # except Exception as e:
            #     # Ctrl+C anyway to avoid hangup cmd
            #     self.cladb.expect_action(7, "", "\003")
            #     self.cladb.close()
            #     self.cladb = None
            #     log_debug("Get DUT system log exception occurred!!\n{}".format(e))
            #     raise e

        msg(100, "Complete FCD process ...")
        if not self.board_id in self.usbadb_list:
            self.egsw.close()

        self.close_fcd()


def main():
    factory = CONNECTAPQ8053actoryGeneral()
    factory.run()


if __name__ == "__main__":
    main()
