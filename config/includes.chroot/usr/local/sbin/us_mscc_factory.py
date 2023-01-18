import os
import time
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from script_base import ScriptBase
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class UsMsccFactory(ScriptBase):
    def __init__(self):
        super().__init__()
        self.ver_extract()
        self.get_path = os.path.join
        self.fw_img = self.board_id + '-fw.bin' 
        self.mfg_img = self.board_id + '-mfg.bin' 
        self.ubidiag_img = self.board_id + '-ubidiag.bin' 
        self.bootloader_prompt = 'uboot>'
        self.bomrev = '113-' + self.bom_rev
        self.helperexe = 'helper_VSC7514'
        self.tools_dir = 'usc_8'
        self.devregpart = "/dev/mtdblock6"

        self.flashed_dir = os.path.join(self.tftpdir, self.tools, "common")
        self.macnum = {
            'ed01': "3",
            'ed04': "3",
        }
        self.wifinum = {
            'ed01': "0",
            'ed04': "0",
        }
        self.btnum = {
            'ed01': "0",
            'ed04': "0",
        }
        self.devnetmeta = {
            'ethnum'          : self.macnum,
            'wifinum'         : self.wifinum,
            'btnum'           : self.btnum,
            'flashed_dir'     : self.flashed_dir
        }

    def stop_uboot(self, uappinit_en=False):
        log_debug("Stopping U-boot")
        self.pexp.expect_action(240, "Hit any key to stop autoboot", "\x1b")

    def fcd_server_cmd(self, cmd, msg):
        log_debug('FCD server cmd: "{}"'.format(cmd))
        [sto, rtc] = self.fcd.common.xcmd(cmd)
        if (int(rtc) > 0):
            log_error("{} failed.".format(msg))
            log_error("The error message of {} is \n{}".format(msg, sto))
            return False
        return True

    def curl_image(self, img):
        find_img = {
            'mfg': self.mfg_img,
            'fw': self.fw_img,
            'ubidiag': self.ubidiag_img
        }
        images_path = '/tftpboot/images/' + find_img[img] 
        cmd = 'curl tftp://{} -T {}'.format(self.dutip, images_path)
        if self.fcd_server_cmd(cmd, 'curl image') is False:
            error_critical("Failed to {}".format(msg))

    def ubntrescue(self):
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, 'bootubnt ubntrescue')
        self.pexp.expect_ubcmd(15, self.bootloader_prompt, 'bootubnt', post_exp="Loading")

    def set_eth_addr(self):
        cmd = 'sete ethaddr {}'.format(self.mac)

    def set_boot_net(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "setenv serverip " + self.tftp_server)

    def is_network_alive_in_uboot(self, ipaddr=None, retry=5, timeout=16):
        is_alive = False
        if ipaddr is None:
            ipaddr = self.tftp_server

        cmd = "ping {0}".format(ipaddr)
        exp = "host {0} is alive".format(ipaddr)

        ping_retry_cnt = 0
        while ping_retry_cnt < 2:
            try:
                self.pexp.expect_ubcmd(timeout=timeout, exptxt="", action=cmd, post_exp=exp, retry=retry)
                log_debug('ping is successful, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -n')
                break
            except:
                log_error('ping is failed, the ARP table of FCD Host is \n')
                self.fcd.common.xcmd(cmd='arp -n')
                ping_retry_cnt += 1
        else:
            error_critical('ping is failed in uboot, after {} retries.'.format(retry * (ping_retry_cnt)))

    def set_uboot(self, reset=False):
        self.stop_uboot()
        self.set_boot_net()
        self.is_network_alive_in_uboot()
        if reset:
            self.pexp.expect_ubcmd(15, self.bootloader_prompt, "reset")
        return

    def fwupdate(self, fw_type):
        self.set_uboot()
        self.ubntrescue()
        self.curl_image(fw_type)
        self.pexp.expect_only(60, "Bytes transferred = ")
        return

    def reboot(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot -f")

    def check_info(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/system.info")
        self.pexp.expect_only(10, "flashSize=", err_msg="No flashSize, factory sign failed.")
        self.pexp.expect_only(10, "systemid=" + self.board_id, err_msg="systemid error")
        self.pexp.expect_only(10, "serialno=" + self.mac, err_msg="serialno(mac) error")

    def login(self):
        super().login(press_enter=True, timeout=240)

    def copy_and_unzipping_tools_to_dut(self, timeout=15, post_exp=True):
        log_debug("Send tools.tar from host to DUT ...")
        post_txt = self.linux_prompt if post_exp is True else None
        source = os.path.join(self.tftpdir, self.tools, "tools.tar")
        target = os.path.join(self.dut_tmpdir, "tools.tar")
        self.zmodem_send_to_dut(source, self.dut_tmpdir)
        cmd = "tar -xzvf {0} -C {1}".format(target, self.dut_tmpdir)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt, valid_chk=True)
        src = os.path.join(self.dut_tmpdir, "*")
        cmd = "chmod -R 777 {0}".format(src)
        self.pexp.expect_lnxcmd(timeout=timeout, pre_exp=self.linux_prompt, action=cmd, post_exp=post_txt, valid_chk=True)

    def data_provision_64k(self, netmeta, post_en=True):
        self.gen_rsa_key()

        post_exp = None
        if post_en is True:
            post_exp = self.linux_prompt

        otmsg = "Starting to do {0} ...".format(self.eepmexe)
        log_debug(self.eepmexe)
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

        cmd = "dd if={0} of={1}/{2} bs=1k count=64".format(self.devregpart, self.dut_tmpdir, self.eeorg)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)
        time.sleep(0.1)

        dstp = "{0}/{1}".format(self.dut_tmpdir, self.eeorg)
        self.zmodem_recv_from_dut(dstp, self.tftpdir)

        log_debug("Writing the information from e.gen.{} to e.org.{}".format(self.row_id, self.row_id))
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

        content_sz = 40 * 1024
        for idx in range(0, content_sz):
            org_tres[idx] = gen_tres[idx]

        content_sz = 4 * 1024
        offset = 48 * 1024
        for idx in range(0, content_sz):
            org_tres[idx + offset] = gen_tres[idx + offset]

        content_sz = 8 * 1024
        offset = 56 * 1024
        for idx in range(0, content_sz):
            org_tres[idx + offset] = gen_tres[idx + offset]

        arr = bytearray(org_tres)
        f3.write(arr)
        f3.close()

        eeorg_dut_path = os.path.join(self.dut_tmpdir, self.eeorg)
        self.zmodem_send_to_dut(self.eeorg_path, self.dut_tmpdir)

        cmd = "dd if={0}/{1} of={2} bs=1k count=64".format(self.dut_tmpdir, self.eeorg, self.devregpart)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=post_exp)
        time.sleep(0.1)

    def prepare_server_need_files(self):
        log_debug("Starting to do " + self.helperexe + "...")
        srcp = os.path.join(self.tools, self.tools_dir, self.helper_path, self.helperexe)

        helperexe_path = os.path.join(self.dut_tmpdir, self.helperexe)
        self.zmodem_send_to_dut(self.get_path(self.tftpdir, srcp), self.dut_tmpdir)
        cmd = "chmod 777 {0}".format(helperexe_path)
        self.pexp.expect_lnxcmd(timeout=20, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt,
                                valid_chk=True)

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)
        sstr = [
            helperexe_path,
            "-q",
            "-c product_class=" + self.product_class,
            "-o field=flash_eeprom,format=binary,pathname=" + eebin_dut_path,
            ">",
            eetxt_dut_path
        ]
        sstr = ' '.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)
        time.sleep(1)

        files = [self.eetxt, self.eebin]
        for fh in files:
            srcp = os.path.join(self.tftpdir, fh)

            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.zmodem_recv_from_dut(dstp, self.tftpdir)

        log_debug("Send helper output files from DUT to host ...")

    def run(self):
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)

        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)
        msg(5, "Open serial port successfully ...")

        msg(10, "Update to mfg image")
        self.fwupdate('mfg')
        self.set_uboot(reset=True)
        self.login()

        msg(20, "Send tools")
        self.copy_and_unzipping_tools_to_dut()
        self.data_provision_64k(self.devnetmeta)
        self.erase_eefiles()
        self.prepare_server_need_files()
        
        msg(30, "Start regisration")
        self.registration()

        msg(40, "Check devreg")
        self.check_devreg_data(zmodem=True)
        self.reboot()
        
        msg(60, 'Update to FW image')
        self.fwupdate('fw')
        self.login()

        msg(80, 'Check info')
        self.check_info()

        msg(100, 'FCD is done')
        self.close_fcd()

def main():
    us_factory_general = UsMsccFactory()
    us_factory_general.run()

if __name__ == "__main__":
    main()   
