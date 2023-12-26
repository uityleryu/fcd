#!/usr/bin/python3
import os, time, filecmp

from script_base import ScriptBase
from PAlib.Framework.fcd.expect_tty import ExpttyProcess
from PAlib.Framework.fcd.logger import log_debug, log_error, msg, error_critical

from PAlib.Util.udapi_helper import UDAPIHelper
from PAlib.Framework.fcd.ssh_client import SSHClient

class AFIPQ5018Rework(ScriptBase):
    def __init__(self):
        super(AFIPQ5018Rework, self).__init__()
        self.init_vars()


    def init_vars(self):
        # script specific vars

        self.dutip = "192.168.1.20"

        self.devregpart = "/dev/mtdblock4"
        self.bomrev = "113-" + self.bom_rev
        self.rd_tool = "rd_mod.sh"
        self.rd_tool_dp = "/tmp/" + self.rd_tool
        self.rd_tool_hp = "/tftpboot/tools/common/" + self.rd_tool
        self.eedump = "eeprom"
        self.eedump_dp= "/tmp/" + self.eedump
        self.helper = "helper_IPQ5018"
        self.helper_dp = "/tmp/" + self.helper
        self.helper_hp = "/tftpboot/tools/common/" + self.helper

    def wait_dut_ip(self):
        cnt = 0
        while cnt < 60:
            if self.cnapi.ip_is_alive(self.dutip) == True:
                log_debug( "{} is up".format(self.dutip))
                break
            else:
                log_error( "{} is not up, retry...".format(self.dutip))
                time.sleep(1)
                cnt = cnt + 1
        else:
            error_critical( "{} is not up".format(self.dutip))


    def set_host_ssh(self):
        self.wait_dut_ip()
        time.sleep(20)

        dut_helper = UDAPIHelper(ip=self.dutip, username="ubnt", password="ubnt")
        dut_helper.login()
        service_json = dut_helper.getservices()
        service_json['sshServer']['enabled'] = True
        if self.board_id == 'ac11':
            service_json['sshServer']['passwordAuthentication'] = True

        dut_helper.setservices(service_json)

        sshclient_obj = SSHClient(host=self.dutip,
                                username="ubnt",
                                password="ubnt",
                                polling_connect=True,
                                polling_mins=7)
        self.set_sshclient_helper(ssh_client=sshclient_obj)


    def patch_eeprom(self):
        self.scp_get(self.user, self.password, self.dutip, self.rd_tool_hp, self.rd_tool_dp)

        if self.region == "0000":
            arg = "00"
        elif self.region == "002a":
            arg = "42"
        else:
            arg = "00"

        cmd = ". {} {} 2>&1".format(self.rd_tool_dp, arg)
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)

        cmd = "hexdump -C -s 0x8000 -n 256 {} 2>&1".format(self.devregpart)
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)


    def run_helper(self):
        self.scp_get(self.user, self.password, self.dutip, self.helper_hp, self.helper_dp)

        helper_args_type="default"
        HELPER_PROD_CLASS_ARG = {
            'default': "-c",
            'new': "--output-product-class-fields",
        }

        prod_class_arg = HELPER_PROD_CLASS_ARG.get(helper_args_type, HELPER_PROD_CLASS_ARG['default'])

        eebin_dut_path = os.path.join(self.dut_tmpdir, self.eebin)
        eetxt_dut_path = os.path.join(self.dut_tmpdir, self.eetxt)

        cmd = "{} -q {} product_class={} -o field=flash_eeprom,format=binary,pathname={} > {}".format(
            self.helper_dp, prod_class_arg, self.product_class, eebin_dut_path, eetxt_dut_path
        )
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)
        time.sleep(1)

        files = [self.eetxt, self.eebin]
        for fh in files:
            # Ex: /tftpboot/e.t.0
            srcp = os.path.join(self.tftpdir, fh)

            # Ex: /tmp/e.t.0
            dstp = "{0}/{1}".format(self.dut_tmpdir, fh)
            self.scp_put(self.user, self.password, self.dutip, srcp, dstp)

        log_debug("Send helper output files from DUT to host ...")


    def write_signed_check(self):
        eewrite = self.eesigndate
        eewrite_path = os.path.join(self.tftpdir, eewrite)
        eewrite_dut_path = os.path.join(self.dut_tmpdir, eewrite)

        # Copy Signed data to DUT
        self.scp_get(self.user, self.password, self.dutip, eewrite_path, eewrite_dut_path)

        # Write to mtd
        cmd = "flashcp -v {0} {1}".format(eewrite_dut_path, "/dev/mtd4")
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)

        eechk_dut_path = os.path.join(self.dut_tmpdir, self.eechk)
        # Read mtd out
        cmd = "dd if={} of={} bs=1k count=64".format(self.devregpart, eechk_dut_path)
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)

        # Send read out data to host for comparision
        self.scp_put(self.user, self.password, self.dutip, self.eechk_path, eechk_dut_path)
        self.print_eeprom_content(self.eechk_path)
        otmsg = "Starting to compare the {0} and {1} files ...".format(self.eechk, eewrite)
        log_debug(otmsg)
        rtc = filecmp.cmp(self.eechk_path, eewrite_path)
        if rtc is True:
            log_debug("Comparing files successfully")
        else:
            error_critical("Comparing files failed!!")


    def reboot_dut(self):
        cmd = "reboot -f"
        out = self.session.execmd(cmd, get_exit_val=False)
        self.session.close()

        time.sleep(30)     


    def check_fw_status(self):
        cmd = "jq .regulatory /etc/board.json"
        out = self.session.execmd_getmsg(cmd)
        log_debug(out)


        if self.region == "0000":
            text = "{}"
        elif self.region == "002a":
            text = "fcc"
        else:
            text = "{}"

        if text not in out:
            error_critical("DUT RegDomain Error!")
        else:
            log_debug("DUT RegDomain correct")


    def run(self):
        """Main procedure of factory
        """
        log_debug(msg="The HEX of the QR code=" + self.qrhex)
        
        self.ver_extract()

        time.sleep(2)

        # Cleanup Old files
        self.erase_eefiles()

        # Enable SSH server and Connect SSH
        self.set_host_ssh()
        msg(10, "Enable SSH on DUT successfully ...")
       
        # Patch DUT EEPROM RegDomain
        self.patch_eeprom()
        msg(20, "Patch Original EEPROM successfully ...")

        # Get HW Info for Registration
        self.run_helper()
        msg(30, "Get HW info successfully ...")

        # Registration
        self.registration()
        msg(40, "Finish doing registration ...")

        # Write Signed Data
        self.write_signed_check()
        msg(50, "Finish doing signed file and EEPROM checking ...")

        # Reboot DUT
        self.reboot_dut()
        msg(60, "DUT Rebooting ...")

        # Check FW status
        self.set_host_ssh()
        msg(70, "DUT Re-Loging successfully ...")

        self.check_fw_status()
        msg(100, "Check FW status successfully ...")


def main():
    afipq5018_rework = AFIPQ5018Rework()
    afipq5018_rework.run()

if __name__ == "__main__":
    main()
