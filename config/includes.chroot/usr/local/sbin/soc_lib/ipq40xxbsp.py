#!/usr/bin/python3
import os, time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class IPQ40XXBSPFactory(ScriptBase):
    def __init__(self):
        super(IPQ40XXBSPFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.partimg = "images/" + self.board_id + "-partition.bin"
        self.ubimg = "images/" + self.board_id + "-boot.bin"
        self.fwimg = "images/" + self.board_id + ".bin"
        
        self.devregpart = "/dev/mtdblock8"
        self.bomrev = "113-" + self.bom_rev
       
        self.uboot_address = {
            '0000': "0xf0000",
            'dcb4': "0xf0000",    # Unifi-PoE af
            'dcb5': "0xf0000"     # Unifi-PoE at

        }
        self.ubaddr = self.uboot_address[self.board_id]

        self.uboot_size = {
            '0000': "0xa0000",
            'dcb4': "0xa0000",
            'dcb5': "0xa0000"
        }
        self.ubsize = self.uboot_size[self.board_id]

        self.bootloader_prompt = "IPQ40xx#"

        self.linux_prompt_select = {
            '0000': "#",    #prompt will be like "UBNT-BZ.5.65.0#"
            'dcb4': "#",
            'dcb5': "#"
        }
        self.linux_prompt = self.linux_prompt_select[self.board_id]

        self.ethnum = {
            '0000': "1",
            'dcb4': "1",
            'dcb5': "1"
        }

        self.wifinum = {
            '0000': "2",
            'dcb4': "2",
            'dcb5': "2"
        }

        self.btnum = {
            '0000': "1",
            'dcb4': "1",
            'dcb5': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.BOOT_BSP_IMAGE    = True
        self.CHK_CAL           = True
        self.PROVISION_ENABLE  = True
        self.DOHELPER_ENABLE   = True
        self.REGISTER_ENABLE   = True 
        self.FWUPDATE_ENABLE   = True
        self.DATAVERIFY_ENABLE = True

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0)
        self.is_network_alive_in_linux()

    def check_calibration(self):
        cmd = "hexdump -n 2 -C /tmp/wifi0.caldata"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        exp_list = ["00000000  20 2f"]
        index = self.pexp.expect_get_index(5, exp_list)
        if index == self.pexp.TIMEOUT:
            error_critical("Unable to check the calibrated data ... ")
        elif not index == 0:
            error_critical("No calibrated data, Board is not callibrated")

        cmd = "hexdump -n 2 -C /tmp/wifi1.caldata"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        exp_list = ["00000000  20 2f"]
        index = self.pexp.expect_get_index(5, exp_list)
        if index == self.pexp.TIMEOUT:
            error_critical("Unable to check the calibrated data ... ")
        elif not index == 0:
            error_critical("No calibrated data, Board is not callibrated")

    def update_uboot(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")

        self.pexp.expect_action(40, "to stop", "\033")
        self.set_ub_net(self.premac)
        self.is_network_alive_in_uboot()

        cmd = "tftpboot 0x84000000 "+ self.partimg
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "sf probe")

        cmd = "sf erase 0x40000 0x20000;sf write 0x84000000 0x40000 0x10000;"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)

        cmd = "tftpboot 0x84000000 " + self.ubimg
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "sf probe")

        cmd = "sf erase {0} {1}; sf write $fileaddr {0} 0x$filesize".format(self.ubaddr, self.ubsize)

        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        time.sleep(1)

        cmd = "sf probe;sf erase 0xe0000 0x10000;"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        time.sleep(1)

        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "re")

        self.pexp.expect_action(20, exptxt="Hit any key to stop autoboot|Autobooting in", 
                                action= "\x1b\x1b")

    def urescue(self):
        self.set_ub_net(self.premac)
        self.is_network_alive_in_uboot()

        cmd = "nand erase.chip"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue -f")

        cmd = "atftp --option \"mode octet\" -p -l /tftpboot/{0} {1}".format(self.fwimg, self.dutip)
        log_debug("Run cmd on host:" + cmd)
        self.fcd.common.xcmd(cmd=cmd)

        self.pexp.expect_only(30, "Version:")
        log_debug("urescue: FW loaded")

        self.pexp.expect_only(180, "Updating kernel0 partition")
        log_debug("urescue: kernel0 partition updated")

        self.pexp.expect_only(180, "Updating bs partition")
        log_debug("urescue bs updated")

        self.pexp.expect_only(180, "Updating 0:SBL1 partition")
        log_debug("urescue 0:SBL1 updated")

    def check_info(self):

        self.pexp.expect_ubcmd(600, "Please press Enter to activate this console", "")

        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=False)
        time.sleep(30)
        self.pexp.expect_lnxcmd(5, self.linux_prompt, "exit")

        self.pexp.expect_ubcmd(10, "Please press Enter to activate this console", "")

        self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=False)

        self.pexp.expect_lnxcmd(5, self.linux_prompt, "cat /etc/version")
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cat /proc/ubnthal/board")

        self.pexp.expect_only(10, self.linux_prompt)

    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.ver_extract()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        if self.BOOT_BSP_IMAGE is True:
            self.init_bsp_image()
            msg(10, "Boot up to linux console and network is good ...")

        if self.CHK_CAL is True:
            self.check_calibration()
            msg(15, "Booard got Calibration data ...")

        if self.PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if self.DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if self.REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if self.FWUPDATE_ENABLE is True:
            self.update_uboot()
            msg(60, "Uboot upgrade success ...")
            self.urescue()
            msg(70, "Urescue success ...")

        if self.DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()

class IPQ40XXMFGGeneral(ScriptBase):
    """
    command parameter description for BackToT1
    command: python3
    para0:   script
    para1:   slot ID
    para2:   UART device number
    para3:   FCD host IP
    para4:   system ID
    para5:   Erase calibration data selection
    ex: [script, 1, 'ttyUSB1', '192.168.1.19', 'eb23', True]
    """
    def __init__(self):
        super(IPQ40XXMFGGeneral, self).__init__()
        self.mem_addr = "0x84000000"
        self.nor_bin = "{}-mfg-nor.bin".format(self.board_id)
        self.mfg_img = "{}-mfg.img".format(self.board_id)
        self.set_bootloader_prompt("IPQ40xx#")

    def update_nor(self):
        cmd = "sf probe; sf erase 0x0 0x2d0000; sf write {} 0x0 0x2d0000".format(self.mem_addr)
        log_debug(cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_only(60, "Written: OK")

        if self.erasecal == "True":
            cmd = "sf erase 0x2d0000 0x10000"
            log_debug("Erase calibration data ...")
            log_debug(cmd)
            self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(60, "Erased: OK")

        '''
        if self.erase_devreg == "True":
            devreg_offset = "0x230000"
            cmd = "sf erase 0x230000 0x010000"
            log_debug("Erase devreg data ...")
            log_debug(cmd)
            self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(60, "Erased: OK")
        '''

        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action="reset")

    def update_emmc(self):
        cmd = "mmc erase 0x0 0x2a422; mmc write {} 0x0 0x2a422".format(self.mem_addr)
        log_debug(cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(60, "blocks erased: OK")
        self.pexp.expect_only(60, "blocks written: OK")
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action="reset")

    def update_img(self):
        cmd = "imgaddr={}; source $imgaddr:script".format(self.mem_addr)
        log_debug(cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(60, "Flashing u-boot")
        self.pexp.expect_only(60, "Flashing ubi")
        self.pexp.expect_action(60, exptxt=self.bootloader_prompt, action="reset")

    def stop_uboot(self, timeout=60):
        self.pexp.expect_action(timeout=timeout, exptxt="Hit any key to stop autoboot|Autobooting in", 
                                action= "\x1b\x1b")

    def transfer_img(self, address, filename):
        img = os.path.join(self.image, filename)
        img_size = str(os.stat(os.path.join(self.tftpdir, img)).st_size)
        self.pexp.expect_action(10, self.bootloader_prompt, "tftpb {} {}".format(address, img))
        self.pexp.expect_only(60, "Bytes transferred = {}".format(img_size))

    def t1_image_check(self):
        self.pexp.expect_only(30, "Starting kernel")
        self.pexp.expect_lnxcmd(120, "UBNT BSP INIT", "dmesg -n1", "#", retry=0)

    def run(self):
        """
        Main procedure of back to T1
        """

        # Connect into DUT using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(2)
        msg(5, "Open serial port successfully ...")

        # Update NOR(uboot)
        self.stop_uboot()
        msg(10, 'Stop in uboot...')
        # U6-Enterprise-IW , default Eth0 is not work but Eth1 work
        if self.board_id == "a656":
            self.set_ub_net(self.premac, ethact="eth1")
        else:
            self.set_ub_net(self.premac)

        self.is_network_alive_in_uboot()
        msg(20, 'Network in uboot works ...')
        self.transfer_img(address=self.mem_addr, filename=self.nor_bin)
        msg(30, 'Transfer NOR done')
        self.update_nor()
        msg(40, 'Update NOR done ...')

        # Update EMMC(kernel)
        self.stop_uboot()
        msg(50, 'Stop in uboot...')
        # U6-Enterprise-IW , default Eth0 is not work but Eth1 work
        if self.board_id == "a656":
            self.set_ub_net(self.premac, ethact="eth1")
        else:
            self.set_ub_net(self.premac)

        self.is_network_alive_in_uboot()
        msg(60, 'Network in uboot works ...')
        self.transfer_img(address=self.mem_addr, filename=self.mfg_img)
        msg(70, 'Transfer EMMC done')
        self.update_img()
        msg(80, 'Update EMMC done ...')

        # Check if we are in T1 image
        self.t1_image_check()
        msg(90, 'Check T1 image done ...')

        msg(100, "Back to T1 has completed")
        self.close_fcd()