#!/usr/bin/python3

from binascii import unhexlify
from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

import re
import sys
import time
import os
import stat
import shutil


class LS104XFactory(ScriptBase):
    def __init__(self):
        super(LS104XFactory, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        '''
        airFiber:
            dd11: AF60-XG
        '''
        # U-boot prompt
        self.ubpmt = {
            '0000': "LS104x> ",
            'dd11': "LS104x> "
        }

        # linux console prompt
        self.lnxpmt = {
            '0000': "AF60#",
            'dd11': "AF60#"
        }

        self.helper_img = {
            '0000': "dd11-mfg-nand.bin",
            'dd11': "dd11-mfg-nand.bin"
        }

        self.bootloader = {
            '0000': "dd11-boot.bin",
            'dd11': "dd11-boot.bin"
        }

        self.ubaddr = {
            '0000': "0x0",
            'dd11': "0x0"
        }

        'Nand empty layout, must write before urescue'
        self.nand = {
            '0000': "dd11-nand.bin",
            'dd11': "dd11-nand.bin"
        }

        self.epromaddr = {
            '0000': "0x300000",
            'dd11': "0x300000"
        }

        self.product_class_table = {
            '0000': "0014",
            'dd11': "0014"
        }

        self.pd_dir_table = {
            '0000': "am",
            'dd11': "af_af60"
        }

        self.devregpart = "/dev/mtdblock7"

        self.product_class = self.product_class_table[self.board_id]

        self.linux_prompt = self.lnxpmt[self.board_id]
        self.bootloader_prompt = self.ubpmt[self.board_id]

        self.eeprom_address = self.epromaddr[self.board_id]

        self.tftpdir = self.tftpdir + "/"

        # EX: /tftpboot/tools/af_af60
        self.pd_dir = self.pd_dir_table[self.board_id]
        self.tools_full_dir = os.path.join(self.fcd_toolsdir, self.pd_dir)

        # EX: /tftpboot/tools/af_af60/id_rsa
        #self.id_rsa = os.path.join(self.tools_full_dir, "id_rsa")
        self.bomrev = "13-{0}".format(self.bom_rev)

        # EX: helper in FCD host: /tftpboot/tools/af_af60/helper_IPQ40xx
        #self.helperexe = "helper_IPQ40xx"
        self.helper_path = self.pd_dir

        # EX: /tftpboot/tools/commmon/x86-64k-ee
        #self.eetool = os.path.join(self.fcd_commondir, self.eepmexe)

        #self.dropbear_key = "/tmp/dropbear_key.rsa.{0}".format(self.row_id)

        self.cpu_rev_id = ""
        self.flash_jedec_id = ""
        self.flash_uid = ""

    def stop_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "")

    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ethact FM1@DTSEC3 && setenv ethprime FM1@DTSEC3")
        time.sleep(1)
        self.is_network_alive_in_uboot()

    def uboot_update(self):
        self.stop_uboot()
        self.set_uboot_network()

        log_debug("Upgrade NOR image")

        cmd = "tftpboot a0000000 images/{0}".format(self.bootloader[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(60, "Bytes transferred", "sf probe")

        cmd = "sf erase {0} +$filesize && sf write 0xa0000000 {0} $filesize".format(self.ubaddr[self.board_id])

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        time.sleep(2)

        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "reset")
        self.stop_uboot()
        self.set_uboot_network()

        log_debug("Write NAND empyu layout")

        cmd = "tftpboot a0000000 images/{0}".format(self.nand[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "real_nand erase 0x00000000 0x8000000"
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        cmd = "real_nand write 0xa0000000 0x00000000 $filesize && real_nand write 0xa0000000 0x03C00000 $filesize"
        self.pexp.expect_ubcmd(60, self.bootloader_prompt, cmd)

        self.pexp.expect_ubcmd(120, self.bootloader_prompt, "reset")
        self.stop_uboot()

    def runubntw(self):
        int_reg_code = 0
        int_reg_code = int(self.region, 16)
        cmd = "ubntw all {0} {1} {2} {3}".format(self.mac, self.board_id, self.bomrev, int_reg_code)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(1)

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        self.stop_uboot()

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ubntw dump")

    '''
        Load T1 NAND image and bootloader
        Get device information
    '''
    def getdeviceinfo(self):

        T1_PROMPT = ":~#"

        self.set_uboot_network()
        cmd = "tftpboot a0000000 images/{0}".format(self.helper_img[self.board_id])
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(120, "Bytes transferred", "bootm a0000000")
        msg(35, "Booting T1 NAND image from RAM")
        self.pexp.expect_ubcmd(120, "login:", "root")

        self.pexp.expect_ubcmd(120, T1_PROMPT, "uptime")

        output = self.pexp.expect_get_output("cat /proc/helper_LS1046A_release/cpu_rev_id", T1_PROMPT)
        self.cpu_rev_id = output.split('\n')[1][2:].strip().zfill(8)
        output = self.pexp.expect_get_output("cat /proc/helper_LS1046A_release/flash_jedec_id", T1_PROMPT)
        self.flash_jedec_id = output.split('\n')[1][2:].strip().zfill(8)
        output = self.pexp.expect_get_output("cat /proc/helper_LS1046A_release/flash_uid", T1_PROMPT)
        self.flash_uid = output.split('\n')[1][2:]
        self.flash_uid = self.flash_uid.strip()
        log_debug("\nGet cpu_rev_id: {0}\nflash_jedec_id: {1}\nflash_uid: {2}\n".format(self.cpu_rev_id, self.flash_jedec_id, self.flash_uid))

        self.pexp.expect_lnxcmd(15, T1_PROMPT, "reboot")
        self.stop_uboot()
        time.sleep(1)
        self.set_uboot_network()

    def runurescue(self):
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "urescue -e -f")
        cmd = "atftp --option \"mode octet\" -p -l {0}/{1} {2}".format(self.fwdir, self.fwimg, self.dutip)
        log_debug("Run cmd on host:" + cmd)
        self.fcd.common.xcmd(cmd=cmd)
        self.pexp.expect_only(30, "Firmware Version:")
        log_debug("urescue: FW loaded")
        self.pexp.expect_only(30, "Image Signature Verfied, Success.")
        log_debug("urescue: FW verified")
        self.pexp.expect_only(300, "Bootloader successfully upgraded")
        log_debug("urescue: uboot updated")
        self.pexp.expect_only(300, "NAND partition system1")
        log_debug("urescue: system0 updated")
        self.pexp.expect_only(180, "Firmware update complete.")
        
        msg(35, "urescue: complete")

        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt1")
        cmd = "ifconfig veth0 {0} up".format(self.dutip)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)
        self.chk_lnxcmd_valid()
        self.lnx_netcheck()

    ''' 
        This will over-write scrip_base function and implement by ls104x methods
    '''
    def access_chips_id(self):

        log_debug("Construct chip_id")

        chip_id = ["-i field=product_class_id,format=hex,value=" + self.product_class,
               "-i field=cpu_rev_id,format=hex,value=" + self.cpu_rev_id,
               "-i field=flash_jedec_id,format=hex,value=" + self.flash_jedec_id,
               "-i field=flash_uid,format=hex,value=" + self.flash_uid 
        ]

        log_debug( "chip_id: " + str(chip_id))

        output = ' '.join(chip_id)

        return output

    def scp_put(self, dut_user, dut_pass, dut_ip, dut_file, host_file):
        cmd = [
            'sshpass -p ' + dut_pass,
            'scp',
            '-o StrictHostKeyChecking=no',
            '-o UserKnownHostsFile=/dev/null',
            dut_user + "@" + dut_ip + ":" + dut_file,
            host_file,
        ]
        cmdj = ' '.join(cmd)
        log_debug('Exec "{}"'.format(cmdj))
        [stout, rv] = self.fcd.common.xcmd(cmdj)
        if int(rv) != 0:
            error_critical('Exec "{}" failed'.format(cmdj))
        else:
            log_debug('scp successfully')

    def prepare_eefile(self):

        cmd = "dd if=/dev/mtdblock7 of=/tmp/" +self.eebin + " count=1 bs=65536"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

        self.scp_put(dut_user="ubnt", dut_pass="ubnt1", dut_ip=self.dutip, 
                     dut_file=self.dut_tmpdir + "/" + self.eebin ,
                     host_file=self.tftpdir + self.eebin)

    def lnx_netcheck(self, netifen=False):
        postexp = [
            "64 bytes from",
            self.linux_prompt
        ]
        self.pexp.expect_lnxcmd(15, self.linux_prompt, "ping -c 1 " + self.tftp_server, postexp)
        self.chk_lnxcmd_valid()

    def check_info(self):

        eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)

        self.pexp.expect_ubcmd(240, "Please press Enter to activate this console.", "")
        self.pexp.expect_ubcmd(10, "login:", "ubnt")
        self.pexp.expect_ubcmd(10, "Password:", "ubnt1")

        log_debug("Starting to extract the EEPROM content from SPI flash ...")
        cmd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
        self.pexp.expect_lnxcmd(30, self.linux_prompt, cmd, post_exp=post_txt, valid_chk=True)

        log_debug("Send " + self.eechk + " from DUT to host ...")

        self.tftp_put(remote=self.eechk_path, local=eechk_dut_path, timeout=timeout, post_en=post_en)

        otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, eewrite)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.eechk_path, eewrite_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")


        cmd = "cat /proc/ubnthal/board.info"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, cmd)

    def airos_run(self):
        UPDATE_BOOTIMG_EN = True
        UBNTW_EN = True
        FLASH_TEMP_CFG = False
        URESCUE_EN = True
        GETDEVICEINFO_EN = True
        REGISTER_EN = True
        ADDKEYS_EN = False
        WRSIGN_EN = True
        DEFAULTCONFIG_EN = False
        DATAVERIFY_EN = True

        """
        Main procedure of factory
        """
        msg(1, "Start Procedure")
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        if UPDATE_BOOTIMG_EN:
            msg(10, "Update Boot images")
            self.uboot_update()
            
        if UBNTW_EN:
            msg(20, "Do ubntw write device EEPROM info")
            self.runubntw()

        if GETDEVICEINFO_EN is True:
            msg(30, "Get device info for devreg")
            self.getdeviceinfo()

        ''' TBD
        if FLASH_TEMP_CFG:
            msg(25, "Flash a temporary config")
            self.set_uboot_network()
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "printenv")
            cmd = "tftpboot 0x84000000 tools/{0}/cfg_part.bin".format(self.pd_dir)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
            self.pexp.expect_ubcmd(10, "Bytes transferred", "usetprotect spm off")
            cmd = "sf probe; sf erase {0} {1}; sf write 0x84000000 {0} {1}".format(self.cfg_address, self.cfg_size)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
        '''

        if URESCUE_EN:
            msg(30, "Do urescue")
            self.runurescue()

        if REGISTER_EN is True:
            self.erase_eefiles()
            self.prepare_eefile()
            self.registration()
            msg(50, "Finish do registration ...")

        ''' TBD
        if ADDKEYS_EN is True:
            msg(60, "Add RSA Key")

            cmd = "rm {0}; dropbearkey -t rsa -f {0}".format(self.dropbear_key)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                error_critical("Generate RSA key failed!!")
            else:
                log_debug("Generate RSA key successfully")

            cmd = "{0} -f {1} -K {2}".format(self.eetool, self.eesign_path, self.dropbear_key)
            log_debug("cmd: " + cmd)
            [sto, rtc] = self.fcd.common.xcmd(cmd)
            if (int(rtc) > 0):
                error_critical("Append RSA key failed!!")
            else:
                log_debug("Addend RSA key successfully")
        '''

        if WRSIGN_EN is True:
            cmd = "reboot -f"
            self.pexp.expect_lnxcmd(180, self.linux_prompt, cmd)
            self.stop_uboot()
            self.set_uboot_network()

            msg(70, "Write signed EEPROM")
            cmd = "tftpboot a0000000 {0}".format(self.eesigndate)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_ubcmd(60, "Bytes transferred", "sf probe")
            log_debug("File sent. Writing eeprom")
            cmd = "sf erase {0} +$filesize; sf write a0000000 {0} $filesize".format(self.eeprom_address)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            time.sleep(1)

        if DEFAULTCONFIG_EN is True:
            log_debug("Erase tempoarary config")
            cmd = "sf probe; sf erase {0} {1}".format(self.cfg_address, self.cfg_size)
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            time.sleep(5)

            msg(80, "Write default setting")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv NORESET")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip 192.168.1.254")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr 192.168.1.20")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv bootargs root=/dev/mtdblock5 init=/init")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "saveenv")
            time.sleep(3)
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ubntw dump")
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")

        if DATAVERIFY_EN is True:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
            self.check_info()
            msg(90, "Succeeding in checking the devreg information ...")

        msg(100, "Formal firmware completed...")
        self.close_fcd()


class LS104XMFG(ScriptBase):
    def __init__(self):
        super(LS104XMFG, self).__init__()
        self.init_vars()

    def init_vars(self):
        '''
            dd11: AF60-XG
        '''
        # U-boot prompt
        self.ubpmt = {
            '0000': "af60> ",
            'dd11': "af60> "
        }

        self.nor_img = {
            '0000': "dd11-mfg-nor.bin",
            'dd11': "dd11-mfg-nor.bin"
        }

        self.nand_img = {
            '0000': "dd11-mfg-nand.bin",
            'dd11': "dd11-mfg-nand.bin"
        }

        self.nor_addr = {
            '0000': "0x0",
            'dd11': "0x0"
        }

        self.nor_sz = {
            '0000': "0x510000",
            'dd11': "0x510000"
        }

        self.nand_addr = {
            '0000': "0",
            'dca0': "0"
        }

        self.nand_boot_addr = {
            '0000': "0x7b06a98",
            'dca0': "0x7b06a98"
        }

        self.bootloader_prompt = self.ubpmt[self.board_id]

    def stop_uboot(self):
        self.pexp.expect_ubcmd(30, "Hit any key to stop autoboot", "\033")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "")

    def set_uboot_network(self):
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ipaddr " + self.dutip)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv serverip " + self.tftp_server)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "setenv ethact FM1@DTSEC3 && setenv ethprime FM1@DTSEC3")
        time.sleep(1)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "ping " + self.tftp_server)
        self.pexp.expect_only(30, "is alive")

    def run(self):

        WRITE_NOR_EN = True
        WRITE_NAND_EN = True
        ERASE_CAL_EN = False
        ERASE_CCODE_EN = False

        """
        Main procedure of factory
        """
        msg(1, "Start Procedure")
        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()
        # Connect into DU and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)
        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Stop U-boot")
        self.stop_uboot()
        time.sleep(1)
        self.set_uboot_network()

        if WRITE_NOR_EN:
            msg(10, "Get NOR Image")
            cmd = "tftpboot a0000000 images/{}".format(self.nor_img[self.board_id])
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_only(30, "Bytes transferred")
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf probe 0:0")

            msg(20, "Write NOR image")
            cmd = "sf erase {0} {1} && sf write a0000000 {0} $filesize".format(self.nor_addr[self.board_id], self.nor_sz[self.board_id])
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_only(120, "Written: OK")

        if WRITE_NAND_EN:
            msg(30, "Get NAND Image")
            cmd = "tftpboot a0000000 images/{}".format(self.nand_img[self.board_id])
            self.pexp.expect_ubcmd(120, self.bootloader_prompt, cmd)
            self.pexp.expect_only(120, "Bytes transferred")

            msg(40, "Write NAND image")
            cmd = "real_nand erase.chip && real_nand write a0000000 0 $filesize"
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)
            self.pexp.expect_only(180, "bytes written: OK")

            msg(50, "Write Boot Command")
            cmd = "setenv bootcmd \"nand read a0000000 0 0x7b06a98 && bootm a0000000\""
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

            cmd = "saveenv"
            self.pexp.expect_ubcmd(30, self.bootloader_prompt, cmd)

        if ERASE_CAL_EN:
            if self.erasecal == "True":
                self.pexp.expect_ubcmd(30, self.bootloader_prompt, "sf erase 0x170000 0x10000")
                time.sleep(5)

        if ERASE_CCODE_EN:
            msg(70, "Cleanup CountryCode")
            cmd = "sf read 0x84000000 0x170000 0x10000 && mw 0x8400100c 00200000 && mw 0x8400500c 00200000 && sf write 0x84000000 0x170000 0x10000"
            self.pexp.expect_action(180, self.ubpmt[self.board_id], cmd)
            time.sleep(5)

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "reset")
        time.sleep(60)

        msg(90, "Reboot")
        self.pexp.expect_only(120, "Linux version 4.14.67")

        msg(100, "Back to ART has completed")
        self.close_fcd()