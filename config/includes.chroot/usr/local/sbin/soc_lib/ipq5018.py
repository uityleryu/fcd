#!/usr/bin/python3
import os, time

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

class IPQ5018BSPFactory(ScriptBase):
    def __init__(self):
        super(IPQ5018BSPFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.ubimg = "images/" + self.board_id + "-uboot.bin"
        self.fwimg = "images/" + self.board_id + ".bin"
        
        self.devregpart = "/dev/mtdblock9"
        self.bomrev = "113-" + self.bom_rev
       
        self.uboot_address = {
            '0000': "0x00120000",
            'a658': "0x00120000",    # Wave-Nano
            'a659': "0x00120000",    # LBE-AX
            'a660': "0x00120000",    # Prism-AX-OMT
            'a661': "0x00120000",    # Prism-AX
            'a662': "0x00120000",    # LiteAP-AX-GPS
            'a663': "0x00120000",    # NBE-AX
            'a664': "0x00120000"     # Wave-LR
        }
        self.ubaddr = self.uboot_address[self.board_id]

        self.uboot_size = {
            '0000': "0x000a0000",
            'a658': "0x000a0000",
            'a659': "0x000a0000",
            'a660': "0x000a0000",
            'a661': "0x000a0000",
            'a662': "0x000a0000",
            'a663': "0x000a0000",
            'a664': "0x000a0000"

        }
        self.ubsize = self.uboot_size[self.board_id]

        self.bootloader_prompt = "IPQ5018#"

        self.linux_prompt_select = {
            '0000': "#",    #prompt will be like "UBNT-BZ.5.65.0#"
            'a658': "#",
            'a659': "#",
            'a660': "#",
            'a661': "#",
            'a662': "#",
            'a663': "#",
            'a664': "#"
        }
        self.linux_prompt = "root@OpenWrt:/#"
        self.prod_prompt = "ubnt@OpenWrt:~#"

        self.ethnum = {
            '0000': "1",
            'a658': "1",
            'a659': "1",
            'a660': "1",
            'a661': "1",
            'a662': "1",
            'a663': "1",
            'a664': "1"
        }

        self.wifinum = {
            '0000': "2",
            'a658': "1",
            'a659': "1",
            'a660': "1",
            'a661': "1",
            'a662': "1",
            'a663': "1",
            'a664': "1"
        }

        self.btnum = {
            '0000': "1",
            'a658': "1",
            'a659': "1",
            'a660': "1",
            'a661': "1",
            'a662': "1",
            'a663': "1",
            'a664': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

        self.BOOT_BSP_IMAGE    = True 
        self.PROVISION_ENABLE  = True 
        self.DOHELPER_ENABLE   = True 
        self.REGISTER_ENABLE   = True 
        if self.board_id == "a658" :
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True
        elif self.board_id == "a659" :
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True
        elif self.board_id == "a660" :
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True
        elif self.board_id == "a661" :
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True
        elif self.board_id == "a662" :
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True
        elif self.board_id == "a663" :
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True
        elif self.board_id == "a664" :
            self.FWUPDATE_ENABLE   = True
            self.DATAVERIFY_ENABLE = True
        else:
            self.FWUPDATE_ENABLE   = False
            self.DATAVERIFY_ENABLE = False

    def init_bsp_image(self):
        self.pexp.expect_only(60, "Starting kernel")
        self.pexp.expect_lnxcmd(180, "UBNT BSP INIT", "dmesg -n1", self.linux_prompt, retry=0)
        self.is_network_alive_in_linux()

    def update_uboot(self):
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "reboot", "")

        self.pexp.expect_action(40, "to stop", "\033")
        self.set_ub_net(self.premac)
        self.is_network_alive_in_uboot()

        cmd = "tftpboot $loadaddr " + self.ubimg

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(30, "Bytes transferred", "sf probe")

        cmd = "sf erase {0} +{1}; sf write $fileaddr {0} 0x$filesize".format(self.ubaddr, self.ubsize)

        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)
        time.sleep(1)
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, "re")

        self.pexp.expect_action(20, exptxt="Hit any key to stop autoboot|Autobooting in", 
                                action= "\x1b\x1b")

    def urescue(self):
        self.set_ub_net(self.premac)
        self.is_network_alive_in_uboot()

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "saveenv")

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue -e")

        cmd = "atftp --option \"mode octet\" -p -l /tftpboot/{0} {1}".format(self.fwimg, self.dutip)
        log_debug("Run cmd on host:" + cmd)
        self.fcd.common.xcmd(cmd=cmd)

        self.pexp.expect_only(30, "Version:")
        log_debug("urescue: FW loaded")

        if self.board_id == "a658" or self.board_id == "a664":
            self.pexp.expect_only(180, "Flashing system0")
            log_debug("urescue: Flashing system0")

            self.pexp.expect_only(180, "Flashing system1")
            log_debug("urescue: Flashing system1")

            self.pexp.expect_only(180, "Firmware update complete.")
            log_debug("urescue: Firmware update complete.")

        else:
            self.pexp.expect_only(180, "Updating 0:HLOS partition")
            log_debug("urescue: HLOS partitio updated")

            self.pexp.expect_only(180, "Updating rootfs partition")
            log_debug("urescue rootfs updated")

            self.pexp.expect_only(180, "Updating bs partition")
            log_debug("urescue bs updated")

    def check_info(self):

        if self.board_id == "a658" or self.board_id == "a664":
            self.pexp.expect_ubcmd(600, "running real init", "")
            self.pexp.expect_ubcmd(10, "login:", "ubnt")
            self.pexp.expect_ubcmd(10, "Password:", "ubnt")
            self.linux_prompt = "/var/home/ubnt #"
            self.pexp.expect_lnxcmd(5, self.linux_prompt, "cat /usr/lib/version")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "jq  .identification /etc/board.json")

        else:
            self.pexp.expect_action(300, "entered forwarding state", "")

            time.sleep (3)

            self.linux_prompt = "ubnt@OpenWrt:~#"

            self.login(self.user, self.password, timeout=300, log_level_emerg=True, press_enter=False)

            self.pexp.expect_lnxcmd(5, self.linux_prompt, "cat /etc/version")
            self.pexp.expect_lnxcmd(10, self.linux_prompt, "grep board /proc/ubnthal/board.info")

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

class IPQ5018MFGGeneral(ScriptBase):
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
        super(IPQ5018MFGGeneral, self).__init__()
        self.mem_addr = "0x44000000"
        self.nor_bin = "{}-nor.bin".format(self.board_id)
        self.emmc_bin = "{}-emmc.bin".format(self.board_id)
        self.set_bootloader_prompt("IPQ5018#")

    def update_nor(self):
        cmd = "sf probe; sf erase 0x0 0x1C0000; sf write {} 0x0 0x1C0000".format(self.mem_addr)
        log_debug(cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(60, "Erased: OK")
        self.pexp.expect_only(60, "Written: OK")

        if self.erasecal == "True":
            cal_offset = "0x1C0000"
            cmd = "sf erase 0x1C0000 0x070000"
            log_debug("Erase calibration data ...")
            log_debug(cmd)
            self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(60, "Erased: OK")

        if self.erase_devreg == "True":
            devreg_offset = "0x230000"
            cmd = "sf erase 0x230000 0x010000"
            log_debug("Erase devreg data ...")
            log_debug(cmd)
            self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
            self.pexp.expect_only(60, "Erased: OK")

        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action="reset")

    def update_emmc(self):
        cmd = "mmc erase 0x0 0x2a422; mmc write {} 0x0 0x2a422".format(self.mem_addr)
        log_debug(cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_only(60, "blocks erased: OK")
        self.pexp.expect_only(60, "blocks written: OK")
        cmd = "mmc erase 0x48422 0x40000"
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action=cmd)
        self.pexp.expect_action(10, exptxt=self.bootloader_prompt, action="reset")

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
        self.transfer_img(address=self.mem_addr, filename=self.emmc_bin)
        msg(70, 'Transfer EMMC done')
        self.update_emmc()
        msg(80, 'Update EMMC done ...')

        # Check if we are in T1 image
        self.t1_image_check()
        msg(90, 'Check T1 image done ...')

        msg(100, "Back to T1 has completed")
        self.close_fcd()
