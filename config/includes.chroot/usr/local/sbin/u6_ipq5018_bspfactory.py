#!/usr/bin/python3
import time
import os
import stat
from udm_alpine_factory import ScriptBase
from ubntlib.fcd.expect_tty import ExpttyProcess
from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical

BOOT_BSP_IMAGE    = True
PROVISION_ENABLE  = True
DOHELPER_ENABLE   = True
REGISTER_ENABLE   = True
FWUPDATE_ENABLE   = False
DATAVERIFY_ENABLE = False

class temp_ScriptBase(ScriptBase):

    def prepare_server_need_files_bspnode(self, nodes=None):
        log_debug("Starting to extract cpuid, flash_jedecid and flash_uuid from bsp node ...")
        # The sequencial has to be cpu id -> flash jedecid -> flash uuid
        if nodes is None:
            nodes = ["/proc/bsp_helper/cpu_rev_id",
                     "/proc/bsp_helper/flash_jedec_id",
                     "/proc/bsp_helper/flash_uid"]

        if self.product_class == 'basic':
            product_class_hexval = "0014"
        else:
            error_critical("product class is '{}', FCD only supports 'basic' now".format(self.product_class))

        # Gen "e.t" from the nodes which were provided in BSP image
        for i in range(0, len(nodes)):
            if nodes[i] == "/proc/bsp_helper/flash_uid" :
                sstr = [
                    "fcd_reg_val{}=`".format(i + 1),
                    "cat ",
                    nodes[i],
                    "`"
                ]
            else :
                sstr = [
                    "fcd_reg_val{}=`".format(i + 1),
                    "cat ",
                    nodes[i],
                    " | awk -F \"x\" '{print $2}'",
                    "`"
                ]

            sstr = ''.join(sstr)
            log_debug(sstr)
            self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                    valid_chk=True)

        sstr = [
            "echo -e \"field=product_class_id,format=hex,value={}\n".format(product_class_hexval),
            "field=cpu_rev_id,format=hex,value=$fcd_reg_val1\n",
            "field=flash_jedec_id,format=hex,value=$fcd_reg_val2\n",
            "field=flash_uid,format=hex,value=$fcd_reg_val3",
            "\" > /tmp/{}".format(self.eetxt)
        ]
        sstr = ''.join(sstr)
        log_debug(sstr)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=sstr, post_exp=self.linux_prompt,
                                valid_chk=True)

        # copy "e.org" as "e.b"
        cmd = "cp -a /tmp/{} /tmp/{}".format(self.eeorg, self.eebin)
        self.pexp.expect_lnxcmd(timeout=10, pre_exp=self.linux_prompt, action=cmd, post_exp=self.linux_prompt)

        files = [self.eetxt, self.eebin]
        for fh in files:
            srcp = os.path.join(self.tftpdir, fh)
            dstp = "/tmp/{0}".format(fh)
            self.tftp_put(remote=srcp, local=dstp, timeout=10)
        log_debug("Send bspnode output files from DUT to host ...")



class U6IPQ5018BspFactory(temp_ScriptBase):
    def __init__(self):
        super(U6IPQ5018BspFactory, self).__init__()
        self.init_vars()

    def init_vars(self):
        # script specific vars
        self.fwimg = "images/" + self.board_id + "-fw.bin"
        self.fcdimg = "images/" + self.board_id + "-fcd.bin"
        self.devregpart = "/dev/mtdblock9"
        self.bomrev = "113-" + self.bom_rev
        self.bootloader_prompt = "IPQ5018#"
        self.linux_prompt = "root@OpenWrt:/#"

        self.ethnum = {
            'a650': "1",
            'a651': "1",
            'a652': "1",
            'a653': "1",
            'a654': "1"
        }

        self.wifinum = {
            'a650': "2",
            'a651': "2",
            'a652': "2",
            'a653': "2",
            'a654': "2"
        }

        self.btnum = {
            'a650': "1",
            'a651': "1",
            'a652': "1",
            'a653': "1",
            'a654': "1"
        }

        self.devnetmeta = {
            'ethnum': self.ethnum,
            'wifinum': self.wifinum,
            'btnum': self.btnum
        }

    def init_bsp_image(self):
        self.pexp.expect_lnxcmd(90, "UBNT BSP INIT", "dmesg -n1", "")
        self.pexp.expect_lnxcmd(10, "", "", self.linux_prompt)
        self.is_network_alive_in_linux()

    def fwupdate(self):
        pass

    def check_info(self):
        pass

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

        self.pexp.expect_only(30, "Starting kernel")
        if BOOT_BSP_IMAGE is True:
            self.init_bsp_image()
            msg(10, "Boot up to linux console and network is good ...")

        if PROVISION_ENABLE is True:
            msg(20, "Sendtools to DUT and data provision ...")
            self.data_provision_64k(netmeta=self.devnetmeta, post_en=False)

        if DOHELPER_ENABLE is True:
            self.erase_eefiles()
            msg(30, "Do helper to get the output file to devreg server ...")
            self.prepare_server_need_files_bspnode()

        if REGISTER_ENABLE is True:
            self.registration()
            msg(40, "Finish doing registration ...")
            self.check_devreg_data()
            msg(50, "Finish doing signed file and EEPROM checking ...")

        if FWUPDATE_ENABLE is True:
            self.fwupdate()
            msg(70, "Succeeding in downloading the upgrade tar file ...")

        if DATAVERIFY_ENABLE is True:
            self.check_info()
            msg(80, "Succeeding in checking the devrenformation ...")

        msg(100, "Completing FCD process ...")
        self.close_fcd()


def main():
    u6ipq5018_bspfactory = U6IPQ5018BspFactory()
    u6ipq5018_bspfactory.run()

if __name__ == "__main__":
    main()
