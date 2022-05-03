
# Images

IMAGE-UA-GATE= \
    images/ec46* \
    ua-fw/ua-gate* \
    ua-fw/GT.mt7621*

IMAGE-UA-ThermalScan= \
    images/ec70* \
    ua-fw/thermalscan.*

IMAGE-UA+=$(IMAGE-UA-GATE)
IMAGE-UA+=$(IMAGE-UA-ThermalScan)

IMAGE-UA-ELEVATOR= \
    images/ec3b* \
    ua-fw/ua-elevator* \
    ua-fw/ua-gate-nor-v2.bin \
    ua-fw/EL.mt7621* \
    ua-fw/e9a5-openwrt-4.0.12-88* 

IMAGE-UA+=$(IMAGE-UA-ELEVATOR)

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
# Project specific tools
TOOLS-UA+=$(TOOLS-CONFIG)
TOOLS-UA-GATE+=$(TOOLS-UA)
TOOLS-UA-HOTEL+=$(TOOLS-CONFIG)
TOOLS-UA-ThermalScan+=$(TOOLS-UA)
TOOLS-UA-ThermalScan+= \
    uvc/128k_ff.bin

TOOLS-UA-ELEVATOR+=$(TOOLS-UA)

# Project target
$(eval $(call ProductImage,UA-GATE,FCD_$(PRD)_UA-GATE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-ThermalScan,FCD_$(PRD)_ThermalScan_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-ELEVATOR,FCD_$(PRD)_UA-ELEVATOR_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-HOTEL,FCD_$(PRD)_UA-HOTEL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UA-Fob,FCD_$(PRD)_UA-Fob_$(VER)_$(FWVER)))
# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UA-GATE,FCD_$(PRD)_UA-GATE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ThermalScan,FCD_$(PRD)_ThermalScan_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-HOTEL,FCD_$(PRD)_UA-HOTEL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ELEVATOR,FCD_$(PRD)_UA-ELEVATOR_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-ReaderLite,FCD_$(PRD)_UA-READERLITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-Display-Gate,FCD_$(PRD)_UA-DISPLAY-GATE$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-SENSE-GATE,FCD_$(PRD)_UA-SENSE-GATE$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UA-Fob,FCD_$(PRD)_UA-Fob$(VER)_$(FWVER)))
# ==================================================================================================
# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,02966-ec60))
$(eval $(call ProductCompress2,03329-ec46))
$(eval $(call ProductCompress2,03329-ec3b))
$(eval $(call ProductCompress2,03291-ec43))
$(eval $(call ProductCompress2,02940_ec40))
$(eval $(call ProductCompress2,03610_ec4d))
$(eval $(call ProductCompress2,03675_ec40))
$(eval $(call ProductCompress2,03587_ec61))
$(eval $(call ProductCompress2,03628_ec61))
$(eval $(call ProductCompress2,03624_ec51))
$(eval $(call ProductCompress2,03823_ec3a))
$(eval $(call ProductCompress2,UA_DISPLAY-SERIES))
