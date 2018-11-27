#!/usr/bin/python3


class US(object):

    # board IDs
    USW_XG = "eb20"
    USW_6XG_150 = "eb23"
    USW_24_PRO = "eb36"
    USW_48_PRO = "eb67"
    usw_group_1 = [USW_XG, USW_6XG_150, USW_24_PRO, USW_48_PRO]

    def __init__(self, args):
        self.fake_mac = r"00:90:4c:06:a5:7" + args.row_id
        self.ip = r"192.168.1." + str((int(args.row_id) + 21))

        self.flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
        self.flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

        self.use_64mb_flash = 0

        self.rsa_key = "dropbear_rsa_host_key"
        self.dss_key = "dropbear_dss_host_key"

        if args.qrcode is not None:
            self.qrcode_hex = args.qrcode.encode('utf-8').hex()

    def print_variables(self):
        print("fake_mac=%s, ip=%s" % (self.fake_mac, self.ip))

    def get_helper(self, board_id=None):
        if board_id == self.USW_XG:
            return "helper_BCM5341x"
        elif board_id in [self.USW_6XG_150, self.USW_24_PRO, self.USW_48_PRO]:
            return "helper_BCM5616x"
        else:
            return "helper_BCM5334x"

