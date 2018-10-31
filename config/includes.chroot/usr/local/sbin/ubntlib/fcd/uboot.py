#!/usr/bin/python3

from ubntlib.fcd.logger import log_debug, log_error, msg, error_critical


uboot_prompt = "u-boot>"
cmd_prefix = r"go $ubntaddr "

class Uboot(object):
    def __init__(self, pexpect_obj):
        self.__pexpect = pexpect_obj

    def sf_erase(self, address, erase_size):
        """
        run cmd in uboot :[sf erase address erase_size]
        Arguments:
            address {string}
            erase_size {string} 
        """
        log_debug(msg="Initializing sf => sf probe")
        self.__pexpect.proc.sendline('sf probe')
        self.__pexpect.expect2actu1(timeout=20, exptxt=uboot_prompt, action="")

        earse_cmd = "sf erase " + address + " " +erase_size
        log_debug(msg="run cmd " + earse_cmd)
        self.__pexpect.proc.sendline(earse_cmd)
        self.__pexpect.expect2actu1(timeout=20, exptxt=uboot_prompt, action="")
    
    def uclearcal(self, args="-f -e"):
        """
        run cmd in uboot: uclearcal {args}
        for wifi usage only
        """
        self.__pexpect.proc.sendline(cmd_prefix + "uclearcal " + args)
        self.__pexpect.expect2actu1(timeout=20, exptxt="Done.", action="")
        self.__pexpect.expect2actu1(timeout=20, exptxt=uboot_prompt, action="")
        log_debug(msg="Calibration Data erased")
