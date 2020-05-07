#!/usr/bin/python3

import re
import sys
import os
import time

from script_base import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

'''
    eb10: US-8-150W
    eb18: US-8-60W
    eb20: US-XG
    eb21: US-16-150W
    eb30: US-24
    eb31: US-24-250W
    eb60: US-48
    eb62: US-48-500W
'''


class BCM5334xLIB(ScriptBase):
    def __init__(self):
        super(BCM5334xLIB, self).__init__()
        self.init_vars()

    def init_vars(self):
        self.flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
        self.flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

        # U-boot erase start address
        self.uberstaddr = {
            '0000': "0xc0000",
            'eb10': "0xc0000",
            'eb18': "0xc0000",
            'eb20': "0x1e0000",
            'eb21': "0xc0000",
            'eb31': "0xc0000",
            'eb60': "0xc0000",
            'eb62': "0xc0000"
        }

        # U-boot erase size
        self.ubersz = {
            '0000': "0x10000",
            'eb10': "0x10000",
            'eb18': "0x10000",
            'eb20': "0x10000",
            'eb21': "0x10000",
            'eb31': "0x10000",
            'eb60': "0x10000",
            'eb62': "0x10000"
        }

        # Shmoo data address
        self.shmooaddr = {
            '0000': "0xd0000",
            'eb10': "0xd0000",
            'eb18': "0xd0000",
            'eb20': "0x1f0000",
            'eb21': "0xd0000",
            'eb31': "0xd0000",
            'eb60': "0xd0000",
            'eb62': "0xd0000"
        }

        # Boot argument
        self.bootargs = {
            '0000': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.flash_mtdparts_32M,
            'eb10': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.flash_mtdparts_32M,
            'eb18': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.flash_mtdparts_32M,
            'eb20': "quiet console=ttyS0,115200 mem=496M " + self.flash_mtdparts_64M,
            'eb21': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.flash_mtdparts_32M,
            'eb31': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.flash_mtdparts_32M,
            'eb60': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.flash_mtdparts_32M,
            'eb62': "quiet console=ttyS0,115200 mem=128M@0x0 mem=128M@0x68000000 " + self.flash_mtdparts_32M,
        }

        self.helperexes = {
            '0000': "helper_BCM5341x",
            'eb10': "helper_BCM5334x",
            'eb18': "helper_BCM5334x",
            'eb20': "helper_BCM5341x",
            'eb21': "helper_BCM5334x",
            'eb31': "helper_BCM5334x",
            'eb60': "helper_BCM5334x",
            'eb62': "helper_BCM5334x"
        }

        self.bootloader_prompt = "u-boot>"
        self.helperexe = self.helperexes[self.board_id]
        self.devregpart = "/dev/`awk -F: '/EEPROM/{print \$1}' /proc/mtd|sed 's~mtd~mtdblock~g'`"
        self.fakemac = "00:90:4c:06:a5:7{}".format(self.row_id)
        self.isMDK = False

    def stop_uboot(self):
        log_debug("Stopping U-boot")
        expect_cal_case1 = "Switching to RD_DATA_DELAY Step"
        expect_cal_case2 = "Validate Shmoo parameters stored in flash ..... failed"
        expect_normal = "Hit any key to stop autoboot"

        expect_list = [
            expect_cal_case1,
            expect_cal_case2,
            expect_normal
        ]
        index = self.pexp.expect_get_index(timeout=60, exptxt=expect_list)
        if index == 0 or index == 1:
            log_debug("Waiting for self calibration in u-boot")
            self.pexp.expect_action(150, exptxt=expect_normal, action="")
        else:
            log_debug("Finding Hit any key")
            self.pexp.expect_action(30, exptxt="", action="")

    def ub_chk_mdk_support(self):
        log_file_path = os.path.join("/tftpboot/", "log_slot" + self.row_id + ".log")
        cmd = "cat {0}".format(log_file_path)
        [stdo, rtc] = self.fcd.common.xcmd(cmd)
        match = re.findall("Found MDK device", stdo, re.S)

        if match:
            log_debug("MDK is supported from U-Boot booting message")
            self.isMDK = True
        else:
            log_debug("MDK is not supported from U-Boot booting message")
            self.isMDK = False

    '''
        Only MFG process will use
    '''
    def ub_clean_shmoo(self):
        log_debug("Cleaning the shmoo calibration data ... ")
        cmd = "sf probe; sf erase {0} 0x10000".format(self.shmooaddr[self.board_id])
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        time.sleep(0.5)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "")

    def ub_uapp_init(self):
        cmd = "go $ubntaddr uappinit"
        self.pexp.expect_action(5, "", "")
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(10, "UBNT application initialized")

    def ub_config_clean(self):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string}
        """
        cmd = "sf probe; sf erase {0} {1}".format(self.uberstaddr[self.board_id], self.ubersz[self.board_id])
        self.pexp.expect_action(30, self.bootloader_prompt, cmd)

        cmd = "go $ubntaddr uclearcfg"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(30, "Done")

        """
            cmd: go $ubntaddr uclearcal -f -e
            will clean the whole EEPROM partition (64KB)
        """
        # cmd = "go $ubntaddr uclearcal -f -e"
        # self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        # self.pexp.expect_only(30, "Done")

    '''
        Only registration process will use
    '''
    def turn_on_console(self):
        cmd = "setenv bootargs '{0}'".format(self.bootargs[self.board_id])
        log_debug("cmd: " + cmd)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, "run bootcmd")
        self.pexp.expect_only(150, "Starting kernel")
