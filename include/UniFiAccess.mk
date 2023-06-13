
# Images

IMAGE-UA-GATE= \
    images/ec46* \
    ua-fw/ua-gate* \
    ua-fw/GT.mt7621*

IMAGE-UA-ThermalScan= \
    images/ec70* \
    ua-fw/thermalscan.*

IMAGE-UA-ELEVATOR= \
    images/ec3b* \
    ua-fw/ua-elevator* \
    ua-fw/ua-gate-nor-v2.bin \
    ua-fw/EL.mt7621* \
    ua-fw/e9a5-openwrt-4.0.12-88*

IMAGE-UA-ELEVATOR-EXTENDER-TX= \
    images/ec44* \
    images/ec45* \
    ua-fw/ua-elevator-*

IMAGE-UA-ELEVATOR-EXTENDER-RX= \
    images/ec45* \
    ua-fw/ua-elevator-*

IMAGE-UA+=$(IMAGE-UA-GATE)
IMAGE-UA+=$(IMAGE-UA-ThermalScan)
IMAGE-UA+=$(IMAGE-UA-ELEVATOR)
IMAGE-UA+=$(IMAGE-UA-ELEVATOR-EXTENDER-TX)
IMAGE-UA+=$(IMAGE-UA-ELEVATOR-EXTENDER-RX)


# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiAccess
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee \
    common/aarch64-rpi4-4k-ee

TOOLS-UA-HOTEL=\
    ua_hotel/hash32-arm-rpi

TOOLS-UA-Fob=$(TOOLS-UA)
TOOLS-UA-Fob+= \
    ufp/nxp-nfc-nci

TOOLS-UA-Card=$(TOOLS-UA)
TOOLS-UA-Card+= \
    ufp/nxp-nfc-nci

# Project specific tools
TOOLS-UA+=$(TOOLS-CONFIG)
TOOLS-UA-GATE+=$(TOOLS-UA)
TOOLS-UA-HOTEL+=$(TOOLS-CONFIG)
TOOLS-UA-ThermalScan+=$(TOOLS-UA)
TOOLS-UA-ThermalScan+= \
    uvc/128k_ff.bin

TOOLS-UA-ELEVATOR+=$(TOOLS-UA)
TOOLS-UA-ELEVATOR-EXTENDER-TX+=$(TOOLS-CONFIG)
TOOLS-UA-ELEVATOR-EXTENDER-TX+= \
    ua_extender/fcd/plctool \
    ua_extender/fcd/plcinit \
    ua_extender/fcd/modpib \
    ua_extender/fcd/gen_flash_block_bin.py \
    ua_extender/ec44.bin \
    ua_extender/ec45.bin

TOOLS-UA-ELEVATOR-EXTENDER-RX+=$(TOOLS-CONFIG)
TOOLS-UA-ELEVATOR-EXTENDER-RX+= \
    ua_extender/fcd/plctool \
    ua_extender/fcd/plcinit \
    ua_extender/fcd/modpib \
    ua_extender/fcd/gen_flash_block_bin.py \
    ua_extender/ec45.bin


# Project target
$(eval $(call ProductImage,UA-GATE,FCD_$(PRD)_UA-GATE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-ThermalScan,FCD_$(PRD)_ThermalScan_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-ELEVATOR,FCD_$(PRD)_UA-ELEVATOR_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-HOTEL,FCD_$(PRD)_UA-HOTEL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-Fob,FCD_$(PRD)_UA-Fob_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-G2-Reader-Pro,FCD_$(PRD)_UA-G2-Reader-Pro_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-ELEVATOR-EXTENDER-TX,FCD_$(PRD)_UA-ELEVATOR-EXTENDER-TX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-ELEVATOR-EXTENDER-RX,FCD_$(PRD)_UA-ELEVATOR-EXTENDER-RX_$(VER)_$(FWVER)))
# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UA-GATE,FCD_$(PRD)_UA-GATE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ThermalScan,FCD_$(PRD)_ThermalScan_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-HOTEL,FCD_$(PRD)_UA-HOTEL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ELEVATOR,FCD_$(PRD)_UA-ELEVATOR_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ReaderLite,FCD_$(PRD)_UA-READERLITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-Display-Gate,FCD_$(PRD)_UA-DISPLAY-GATE$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-SENSE-GATE,FCD_$(PRD)_UA-SENSE-GATE$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-Fob,FCD_$(PRD)_UA-Fob$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-Card,FCD_$(PRD)_UA-Card$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-G2-Reader-Pro,FCD_$(PRD)_UA-G2-Reader-Pro$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ELEVATOR-EXTENDER-TX,FCD_$(PRD)_UA-ELEVATOR-EXTENDER-TX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ELEVATOR-EXTENDER-RX,FCD_$(PRD)_UA-ELEVATOR-EXTENDER-RX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-G2-Portal,FCD_$(PRD)_UA-G2-Portal$(VER)_$(FWVER)))
# ==================================================================================================
# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,02668_ec5f))
$(eval $(call ProductCompress2,02966_ec60))
$(eval $(call ProductCompress2,03329_ec46))
$(eval $(call ProductCompress2,03329_ec3b))
$(eval $(call ProductCompress2,03291_ec43))
$(eval $(call ProductCompress2,02940_ec40))
$(eval $(call ProductCompress2,03610_ec4d))
$(eval $(call ProductCompress2,03675_ec40))
$(eval $(call ProductCompress2,03587_ec61))
$(eval $(call ProductCompress2,03628_ec61))
$(eval $(call ProductCompress2,03624_ec51))
$(eval $(call ProductCompress2,03823_ec3a))
$(eval $(call ProductCompress2,03224_ec38))
$(eval $(call ProductCompress2,03172_ec42))
$(eval $(call ProductCompress2,03919_ec42))
$(eval $(call ProductCompress2,03003_ec3b))
$(eval $(call ProductCompress2,03920_ec3b))
$(eval $(call ProductCompress2,UA_DISPLAY-SERIES))
$(eval $(call ProductCompress2,03625_ec5e))
$(eval $(call ProductCompress2,UA_HUB_4P-SERIES))
$(eval $(call ProductCompress2,04035_ec53))
$(eval $(call ProductCompress2,UA_Elevator-SERIES))
$(eval $(call ProductCompress2,03693_ec64))
