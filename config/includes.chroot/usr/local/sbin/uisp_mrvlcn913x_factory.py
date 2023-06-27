#!/usr/bin/python3

import os
import time

from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, msg
from script_base import ScriptBase


class UispMrvlcn913xFactoryGeneral(ScriptBase):
    def __init__(self):
        super(UispMrvlcn913xFactoryGeneral, self).__init__()
        self.ver_extract()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = self.board_id + "-fw.bin"
        self.fwDtb = self.board_id + "-fw.dtb"

        self.bootloader_prompt = "Marvell>>"
        self.diagPrompt = "UBNT_Diag>"
        self.devregpart = "/dev/mtdblock3"
        self.helperexe = "helper_CN913x_release"
        self.bomrev = "113-" + self.bom_rev
        self.username = "ubnt"
        self.password = "ubnt"
        self.linux_prompt = "#"
        self.linux_prompt_new = "~$"
        self.diagBin = self.board_id + "-diag.bin"
        self.diagDtb = self.board_id + "-diag.dtb"
        self.fwImageName = "Image.uisprplus"
        self.fwDtbName = "cn9131-db.dtb.uisprplus"
        self.recovery = "{}-recovery".format(self.board_id)

        # Base path
        self.tftpdir = self.tftpdir + "/"
        self.toolsdir = "tools/"

        # helper path
        helperpath = {
            "ee7a": "uisp_r_plus",
        }

        self.helper_path = helperpath[self.board_id]

        # number of ethernet
        self.ethnum = {
            "ee7a": "8",
        }

        # number of wifi
        self.wifinum = {
            "ee7a": "0",
        }

        # number of bluetooth
        self.btnum = {
            "ee7a": "1",
        }

        # ethernet interface
        self.netif = {
            "ee7a": "eth7",
        }

        self.devnetmeta = {
            "ethnum": self.ethnum,
            "wifinum": self.wifinum,
            "btnum": self.btnum,
        }

    def stopUboot(self):
        self.pexp.expect_action(60, "to stop", "\033\033")

    def setFakeEEPROM(self):
        self.stopUboot()
        cmd = [
            "mw.l 0x08000000 77077aee",
            "mw.l 0x08000004 04c80400",
            "mw.l 0x08000008 ffdaecfc",
            "mw.w 0x0800000c 0000",
            "sf probe",
            "sf erase 0x410000 0x1000",
            "sf write 0x08000000 0x41000c 0x4",
            "sf write 0x08000004 0x410010 0x4",
            "sf write 0x08000008 0x410000 0x4",
            "sf write 0x0800000c 0x410004 0x2",
            "sf write 0x08000008 0x410006 0x4",
            "sf write 0x0800000c 0x41000a 0x2",
            "env default -a",
            "saveenv",
            "reset",
        ]
        expect_only = {
            "sf erase 0x410000 0x1000": "Erased: OK",
            "sf write 0x0800000c 0x41000a 0x2": "Written: OK",
        }
        for i in cmd:
            self.pexp.expect_ubcmd(10, self.bootloader_prompt, i)
            if i in expect_only.keys():
                self.pexp.expect_only(30, expect_only[i])

    def setUbootIP(self):
        self.set_ub_net()

    def updateUboot(self):
        self.stopUboot()
        self.copy_file(
            source=os.path.join(self.fwdir, self.board_id + "-uboot.bin"),
            dest=os.path.join(self.tftpdir, "boot.img"),
        )
        self.setUbootIP()
        self.is_network_alive_in_uboot()

        write = "tftpboot $loadaddr boot.img; sf probe; sf erase 0x0 0x400000; sf write $loadaddr 0x0 $filesize;"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, write)
        self.pexp.expect_only(120, "Written: OK")

        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def resettingUbootEnvironment(self):
        self.stopUboot()

        cmd = "env default -a; saveenv;"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.pexp.expect_only(20, "done")
        self.pexp.expect_ubcmd(30, self.bootloader_prompt, "reset")

    def bootingDiagImageUboot(self):
        self.stopUboot()

        cmd = "setenv ubnt_debug_legacy_boot on; setenv bootargs ubnt-flash-factory pci=pcie_bus_perf console=ttyS0,115200;"
        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)

        self.setUbootIP()
        self.is_network_alive_in_uboot()

        recovery = "images/" + self.recovery
        cmd = "tftpboot 0x18000004 {}; bootm 0x18000004".format(recovery)

        self.pexp.expect_ubcmd(10, self.bootloader_prompt, cmd)
        self.pexp.expect_only(60, "Bytes transferred =")

    def bootingDiagImageKernel(self):
        self.login(retry=6)

    def configureNetworkingKernel(self):
        cmd = "ifconfig {0} {1}".format(self.netif[self.board_id], self.dutip)
        self.pexp.expect_lnxcmd(
            timeout=10,
            pre_exp=self.linux_prompt,
            action=cmd,
            post_exp=self.linux_prompt,
        )
        self.is_network_alive_in_linux()

        catVersion = "cat /etc/version"
        self.pexp.expect_lnxcmd(
            timeout=10,
            pre_exp=self.linux_prompt,
            action=catVersion,
            post_exp=self.linux_prompt,
        )

    def unlock_write_protection(self):
        cmd = "echo 5edfacbf > /proc/ubnthal/.uf"
        self.pexp.expect_lnxcmd(
            timeout=10,
            pre_exp=self.linux_prompt,
            action=cmd,
            post_exp=self.linux_prompt,
        )

    def tftpGetDiagImage(self):
        cmd = "cd /tmp && tftp -b 4096 -m -gr ee7a-diag.bin {}".format(self.tftp_server)

    def upgradeByEmmc(self):
        cmd = "diag-emmc.sh format"
        self.pexp.expect_lnxcmd(20, self.linux_prompt, cmd)
        done = ": done"
        for i in range(3):
            self.pexp.expect_only(15, done)
        self.scp_get(
            "root",
            "ubnt",
            self.dutip,
            self.tftpdir + "images/" + self.fwimg,
            "/tmp/{}".format(self.fwImageName),
        )
        self.scp_get(
            "root",
            "ubnt",
            self.dutip,
            self.tftpdir + "images/" + self.fwDtb,
            "/tmp/{}".format(self.fwDtbName),
        )

        cmd = "diag-emmc.sh upgrade"
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ls /tmp", self.linux_prompt)
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "cd /tmp && " + cmd, "done.")

    def upgradingFWImage(self):
        self.scp_get(
            "ubnt",
            "ubnt",
            self.dutip,
            self.tftpdir + "images/" + self.diagBin,
            "/tmp/{}".format(self.diagBin),
        )
        self.pexp.expect_lnxcmd(10, self.linux_prompt, "ls /tmp", self.linux_prompt)

        cmd = "ubnt-upgrade -d {}".format(self.diagBin)
        self.pexp.expect_lnxcmd(
            100, self.linux_prompt, "cd /tmp && " + cmd, "Upgrade completed!"
        )

    def addExecPrefix(self, cmd):
        return 'exec "{}"'.format(cmd)

    def check_info_diag(self):
        for i in [
            "version",
            self.addExecPrefix("cat /proc/version"),
            self.addExecPrefix("cat /proc/ubnthal/board"),
            self.addExecPrefix("cat /proc/ubnthal/system.info"),
        ]:
            self.pexp.expect_lnxcmd(20, self.diagPrompt, "{}\r".format(i))

        self.pexp.expect_only(
            20, "flashSize=", err_msg="No flashSize, factory sign failed."
        )
        self.pexp.expect_only(20, "systemid=" + self.board_id)
        self.pexp.expect_only(20, "serialno=" + self.mac.lower())
        self.pexp.expect_only(20, self.diagPrompt)

    def check_info(self):
        for i in [
            "cat /proc/version",
            "cat /proc/ubnthal/board",
            "cat /proc/ubnthal/system.info",
        ]:
            self.pexp.expect_lnxcmd(20, self.linux_prompt_new, i)

        self.pexp.expect_only(
            20, "flashSize=", err_msg="No flashSize, factory sign failed."
        )
        self.pexp.expect_only(20, "systemid=" + self.board_id)
        self.pexp.expect_only(20, "serialno=" + self.mac.lower())
        self.pexp.expect_only(20, self.linux_prompt_new)

    def gotoLinuxShell(self):
        self.pexp.expect_lnxcmd(10, self.diagPrompt, "exec sh\r", self.linux_prompt_new)

    def ctrlC(self):
        self.pexp.expect_lnxcmd(10, self.diagPrompt, "\x03")

    def run(self):
        """
        Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)

        self.fcd.common.config_stty(self.dev)
        self.fcd.common.print_current_fcd_version()

        # Connect into DUT and set pexpect helper for class using picocom
        pexpect_cmd = "sudo picocom /dev/" + self.dev + " -b 115200"
        log_debug(msg=pexpect_cmd)

        pexpect_obj = ExpttyProcess(self.row_id, pexpect_cmd, "\n")
        self.set_pexpect_helper(pexpect_obj=pexpect_obj)
        time.sleep(1)

        msg(5, "Open serial port successfully ...")

        msg(10, "Setting fake EEPROM ...")
        self.setFakeEEPROM()

        msg(15, "Updating uboot ...")
        self.updateUboot()

        msg(20, "Resetting uboot environment ...")
        self.resettingUbootEnvironment()

        msg(25, "Booting diag image (u-boot) ...")
        self.bootingDiagImageUboot()

        msg(30, "Booting diag image (kernel) ...")
        self.bootingDiagImageKernel()

        msg(35, "Starting to configure the networking (kernel) ...")
        self.configureNetworkingKernel()

        msg(40, "Starting to unlock write protection ...")
        self.unlock_write_protection()

        msg(45, "Sending tools to DUT and data provision ...")
        self.data_provision_64k(self.devnetmeta)

        msg(50, "Do helper to get the output file to devreg server ...")
        self.erase_eefiles()
        self.prepare_server_need_files()

        msg(55, "Doing registration ...")
        self.registration()

        msg(65, "Checking registration ...")
        self.check_devreg_data()

        msg(70, "Upgrading FW by ubnt-upgrade ...")
        self.upgradingFWImage()

        msg(75, "Reset ub-boot env ...")
        self.resettingUbootEnvironment()

        self.pexp.expect_only(120, "Starting kernel ...")
        msg(80, "Login kernel ...")

        self.pexp.expect_only(120, "Enter UBNT DIAG")
        msg(85, "Enter Diag shell ...")

        msg(90, "Start check info in Diag shell ...")
        self.check_info_diag()
        msg(95, "Completed check info in Diag shell ...")

        msg(100, "Completed FCD process ...")
        self.close_fcd()


def main():
    uispMrvlcn913xFactory = UispMrvlcn913xFactoryGeneral()
    uispMrvlcn913xFactory.run()


if __name__ == "__main__":
    main()
