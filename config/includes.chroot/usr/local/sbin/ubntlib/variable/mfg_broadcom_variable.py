#!/usr/bin/python3

class MFGBroadcomVariable(object):

    # board IDs
    USW_XG = "eb20"
    USW_6XG_150 = "eb23"
    USW_24_PRO = "eb36"
    USW_48_PRO ="eb67"
    usw_group_1 = [USW_XG, USW_6XG_150, USW_24_PRO, USW_48_PRO]

    def __init__(self, args):
        """
        ex: ['-e', 'ttyUSB1', '1', 'eb23', 'eb23-mfg.bin', '192.168.1.19']
        """
        self.erasecal = args[0]
        self.dev = args[1]
        self.row_id = args[2]
        self.board_id = args[3]
        self.firmware_img = args[4]

        self.fake_mac = r"00:90:4c:06:a5:7" + self.row_id
        self.ip = r"192.168.1." + str((int(self.row_id) + 21))

        self.flash_mtdparts_64M = r"mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
        self.flash_mtdparts_32M = r"mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

        self.use_64mb_flash = 0


    def print_variables(self):
        print("In MFGVariable: erasecal=%s, dev=%s, row_id=%s, board_id=%s, firmware_img=%s" \
            % (self.erasecal, self.dev, self.row_id, self.board_id, self.firmware_img))
        print("fake_mac=%s, ip=%s" % (self.fake_mac, self.ip))   

    def is_board_id_in_group(self, group=None):
        if group is not None:
            return (self.board_id in group)
        else:
            print("Group is not assigned")
            return False

