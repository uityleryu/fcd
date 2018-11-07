#!/usr/bin/python3

class USFactory(object):

    # model ID
    USW_XG = "eb20"
    USW_6XG_150 = "eb23"
    USW_24_PRO = "eb36"
    USW_48_PRO ="eb67"
    usw_group_1 = [USW_XG, USW_6XG_150, USW_24_PRO, USW_48_PRO]

    def __init__(self, args):
        """
        ex: ['eb23', 'b4fbe451f2ba', '4w3IYmVMHKzj', '/media/chike/Ubuntu 18.04.1 LTS amd64/keys/', 
            'ttyUSB1', '1', '192.168.1.7', '02604-20', 'mYvJIK']
        """
        self.board_id = args[0]
        self.mac = args[1]
        self.pass_phrase = args[2]
        self.key_dir = args[3]
        self.dev = args[4]
        self.row_id = args[5]
        self.bom_rev = args[7]
        self.qrcode = args[8]

        self.firmware_img = self.board_id + ".bin"
        self.rsa_key = "dropbear_rsa_host_key"
        self.dss_key = "dropbear_dss_host_key"
        self.ip = r"192.168.1." + str((int(self.row_id) + 21))
        self.qrcode_hex = self.qrcode.encode('utf-8').hex()

        self.flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
        self.flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

        self.use_64mb_flash = 0

    def print_variables(self):
        print("In Us Factory Variable: board_id=%s, mac=%s, row_id=%s, bom_rev=%s, qrcode=%s" \
            % (self.board_id, self.mac, self.row_id, self.bom_rev, self.qrcode))
        print("firmware_img=%s, ip=%s" % (self.firmware_img, self.ip))   

    def is_board_id_in_group(self, group=None):
        if group is not None:
            return (self.board_id in group)
        else:
            print("Group is not assigned")
            return False
    
    def get_helper(self, board_id=None):
        if board_id is None:
            board_id = self.board_id
        if board_id is self.USW_XG:
            return "helper_BCM5341x"
        elif board_id in [self.USW_6XG_150, self.USW_24_PRO, self.USW_48_PRO]:
            return "helper_BCM5616x"
        else:
            return "helper_BCM5334x"
