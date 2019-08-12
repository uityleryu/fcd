#!/usr/bin/python3

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.ssh_client import SSHClient
from ubntlib.fcd.logger import log_debug, msg, error_critical

import time
import os
import stat
import filecmp


PROVISION_EN = True
DOHELPER_EN = True
REGISTER_EN = True
FWUPDATE_EN = True
DATAVERIFY_EN = True


class USUDCALPINEFactoryGeneral(ScriptBase):
    def __init__(self):
        super(USUDCALPINEFactoryGeneral, self).__init__()

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

        self.ver_extract()
        self.firmware = "{}-fw.bin".format(self.board_id)
        self.eepmexe = "x86-64k-ee"
        self.username = "ubnt"
        self.password = "ubnt"
        self.polling_mins = 5
        self.host_toolsdir_dedicated = os.path.join(self.fcd_toolsdir, "uvc")
        self.fw_path = os.path.join(self.fwdir, self.firmware)

        # a580 = G3BATTERY, a563 = G4PRO
        # number of Ethernet
        ethnum = {
            'a580': "0",
            'a563': "1"
        }

        # number of WiFi
        wifinum = {
            'a580': "1",
            'a563': "0"
        }

        # number of Bluetooth
        btnum = {
            'a580': "1",
            'a563': "0"
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
            'a563': "ifconfig eth0 "
        }

    def upload_flash_module(self):

        flash_module_path = os.path.join(self.host_toolsdir_dedicated, self.flash_module)

        mod_name_inDUT = self.flash_module.split(".")[0].split("_")[0]

        cmd_grep = "lsmod | grep {}".format(mod_name_inDUT)
        if self.session.execmd(cmd_grep) == 0:
            # return 0: there is m25p80, return 1: there is not.
            log_debug("flash module {} loaded aleready".format(self.flash_module))
            return

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
            error_critical("failed to install module {}".format(self.flash_module))

        # UVC-G3BATTERY
        if self.product_name == "UVC-G3BATTERY":

            log_debug("installing spi-ambarella.ko module")
            cmd_ins = "insmod spi-ambarella.ko"
            cmd_grep = "lsmod | grep spi_ambarella"
            self.session.execmd(cmd_ins)
            if self.session.execmd(cmd_grep) == 0:
                log_debug("flash module spi_ambarella installed successfully")
            else:
                error_critical("failed to install module spi_ambarella")

        # cameras need to erase the flash first; Otherwise e.b.0 will not be the same with e.g.0
        self.session.execmd("mtd erase {}".format(self.devregpart))

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
            error_critical(otmsg)
        else:
            otmsg = "Generating {0} files successfully".format(self.eegenbin_path)
            log_debug(otmsg)

        host_path = "/tftpboot/{}".format(self.eegenbin)
        dut_path = "/tmp/{}".format(self.eegenbin)
        self.session.put_file(host_path, dut_path)
        time.sleep(1)

        cmd_grep = "ls /tmp | grep {}".format(self.eegenbin)
        if self.session.execmd(cmd_grep) == 0:
            log_debug("{} uploaded successfully".format(self.eegenbin))
        else:
            error_critical("{} uploaded failed".format(self.eegenbin))

        # cameras need to erase the flash first; Otherwise e.b.0 will not be the same with e.g.0
        self.session.execmd("mtd erase {}".format(self.devregpart))

        cmd_dd = "dd if=/tmp/{0} of={1} bs=1k count=64".format(self.eegenbin, self.devregpart)
        log_debug(cmd_dd)
        self.session.execmd(cmd_dd)

        # check if it duplicated successfully
        devregpart_name = self.devregpart.split("/")[-1]
        cmd_grep = "ls /{} | grep {}".format(self.devregpart.replace(devregpart_name, ""), devregpart_name)
        if self.session.execmd(cmd_grep) == 0:
            log_debug("{} duplicated successfully".format(devregpart_name))
        else:
            error_critical("{} duplicated failed".format(devregpart_name))

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
            error_critical("{} uploaded failed".format(self.helperexe))

        cmd_chmod = "chmod 777 {}".format(helperexe_path)
        if self.session.execmd(cmd_chmod) == 0:
            log_debug("{} chmod 777 successfully".format(self.helperexe))
        else:
            error_critical("{} chmod 777 failed".format(self.helperexe))

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
            error_critical("provided {} & {} failed".format(self.eebin, self.eetxt))

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
            error_critical(otmsg)

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
            error_critical("{} uploaded failed".format(self.eesign))

        # chmod
        cmd_chmod = "chmod 777 {}".format(eesign_dut_path)
        if self.session.execmd(cmd_chmod) == 0:
            log_debug("{} chmod 777 successfully".format(eesign_dut_path))
        else:
            error_critical("{} chmod 777 failed".format(eesign_dut_path))

        # UVC-G3BATTERY
        if self.product_name == "UVC-G3BATTERY":
            log_debug("Remove and re-install spi-ambarella.ko & m25p80.ko.")
            self.session.execmd("rmmod m25p80; rmmod spi_ambarella")
            self.upload_flash_module()

            self.session.execmd("touch /var/lock/security")

            # cameras need to erase the flash first; Otherwise e.b.0 will not be the same with e.g.0
            self.session.execmd("mtd erase {}".format(self.devregpart))

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
            # cameras need to erase the flash first; Otherwise e.b.0 will not be the same with e.g.0
            self.session.execmd("mtd erase {}".format(self.devregpart))

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
                log_debug("Comparing files successfully")
            else:
                error_critical("Comparing files failed!!")
        else:
            otmsg = "Can't find the {0} and {1} files ...".format(self.eechk, self.eesign)
            log_debug(otmsg)

    def fwupdate(self):
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
            error_critical("firmware {} uploaded failed".format(self.firmware))

        log_debug("installing firmware")
        cmd = "fwupdate -m"
        if self.session.execmd(cmd) == 0:
            log_debug("firmware {} updated successfully".format(self.firmware))
        else:
            log_debug("firmware {} updated failed".format(self.firmware))

        self.session.close()

    def check_info_ssh(self):
        time.sleep(20)  # for g3battery
        self.session.polling_connect(mins=10)
        log_debug("reconnected with DUT successfully")

        # check the following items
        chk_items = {"board.name": self.board_name, "board.sysid": self.board_id, "board.hwaddr": self.mac}
        for keys, values in chk_items.items():
            cmd = "cat /etc/board.info | grep {}".format(keys)
            log_debug("cmd = " + cmd)

            msg = str(self.session.execmd_getmsg(cmd)).lower()
            logmsg = "host {} = {}, DUT {}".format(keys, values.lower(), msg)

            if values.lower() not in msg:
                otmsg = logmsg + "{} in host and DUT are NOT the same".format(keys)
                error_critical(otmsg)
            else:
                otmsg = logmsg + "{} in host and DUT are the same".format(keys)
                log_debug(otmsg)

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
            error_critical(otmsg)
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
            error_critical("{} renamed to {} failed!".format(eesignFCD_path, self.eesign_path))

    def g3battery_modify_eegenbin(self):

        if self.product_name == "UVC-G3BATTERY":
            ascii_g3_path = os.path.join(self.host_toolsdir_dedicated, "eegen-ascii_g3battery.bin")

            cmd_modify = "sudo cp {} {}.t".format(self.eegenbin_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                error_critical("Generating e.g.0.t file failed!!")
            else:
                log_debug("Generating e.g.0.t files successfully")

            cmd_modify = "sudo dd if={} of={}.t bs=1 count=2 seek=20".format(ascii_g3_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                error_critical("Generating e.g.0.t file failed!!")
            else:
                log_debug("Generating e.g.0.t files successfully")

            cmd_modify = "sudo dd if={} of={}.t bs=1 skip=22 seek=22".format(self.eegenbin_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                error_critical("Generating e.g.0.t file failed!!")
            else:
                log_debug("Generating e.g.0.t files successfully")

            cmd_modify = "sudo mv {}.t {}".format(self.eegenbin_path, self.eegenbin_path)
            [sto, rtc] = self.fcd.common.xcmd(cmd_modify)
            if int(rtc) > 0:
                error_critical("Modified e.g.0 file failed!!")
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
        time.sleep(1)

        log_debug("Uploading flash module...")

        self.upload_flash_module()

        '''
            ============ Registration start ============
              The following flow almost become a regular procedure for the registration.
              So, it doesn't have to change too much. All APIs are came from script_base.py
        '''
        if PROVISION_EN is True:
            msg(20, "Send tools to DUT and data provision ...")
            self.data_provision_64k_ssh(self.devnetmeta)

        if DOHELPER_EN is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_ssh()

        if REGISTER_EN is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data_ssh()
            msg(50, "Finish doing signed file and EEPROM checking ...")
        '''
            ============ Registration End ============
        '''
        if FWUPDATE_EN is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_EN is True:
            self.check_info_ssh()
            msg(80, "Succeeding in checking the devreg information ...")

        msg(100, "Completing firmware upgrading ...")
        self.close_fcd()


def main():
    uvc_factory_general = USUDCALPINEFactoryGeneral()
    uvc_factory_general.run()


if __name__ == "__main__":
    main()
