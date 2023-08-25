
# Images

IMAGE-UC-Plug-US= \
    images/ec5a*

IMAGE-UC-Plug-EU= \
    images/ec5b*

IMAGE-UC-Wall-Outlet-US= \
    images/ec5c*

IMAGE-UC-Plug-Dual-US= \
    images/ec5d*

IMAGE-UC-DISPLAY-7=

IMAGE-UC-DISPLAY-13=

IMAGE-UC-DISPLAY-21=

IMAGE-UC-DISPLAY-27=

IMAGE-LVDU-4-24= \
    images/ec3d* \
    images/ec41* \
    lvdu-fw/lvdu-4-fw.bin \
    lvdu-fw/LH*

IMAGE-LVDU-4= \
    images/ec3d* \
    images/ec41* \
    lvdu-fw/lvdu-4-fw.bin \
    lvdu-fw/LH*

IMAGE-LVDU-24= \
    images/ec3d* \
    images/ec41* \
    lvdu-fw/lvdu-4-fw.bin \
    lvdu-fw/LH*

IMAGE-LVDU-1= \
    images/ec48* \
    lvdu-fw/lvdu-1/*

IMAGE-LVDU+=$(IMAGE-LVDU-4-24)
IMAGE-LVDU+=$(IMAGE-LVDU-4)
IMAGE-LVDU+=$(IMAGE-LVDU-24)
IMAGE-LVDU+=$(IMAGE-LVDU-1)

IMAGE-UC-THERMOSTAT =\
    images/ec47* \
    uc-fw/uc-thermostat/*

IMAGE-UC-Magic-Link-Sensor =

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=Connect
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UC-Plug-US+=$(TOOLS-CONFIG) \
    common/aarch64-rpi4-4k-ee
TOOLS-UC-Plug-EU+=$(TOOLS-CONFIG) \
    common/aarch64-rpi4-4k-ee
TOOLS-UC-Wall-Outlet-US+=$(TOOLS-CONFIG) \
    common/aarch64-rpi4-4k-ee
TOOLS-UC-Plug-Dual-US+=$(TOOLS-CONFIG) \
    common/aarch64-rpi4-4k-ee
TOOLS-UC-DISPLAY-7+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-13+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-21+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-27+=$(TOOLS-CONFIG)

TOOLS-LVDU-4-24+=$(TOOLS-CONFIG)
TOOLS-LVDU-4-24+= \
    lvdu_4_24/helper*

TOOLS-LVDU-4+=$(TOOLS-CONFIG)
TOOLS-LVDU-4+= \
    lvdu_4_24/helper*

TOOLS-LVDU-24+=$(TOOLS-CONFIG)
TOOLS-LVDU-24+= \
    lvdu_4_24/helper*

TOOLS-LVDU-1= \
    $(TOOLS-CONFIG) \
    common/aarch64-rpi4-4k-ee

TOOLS-UC-THERMOSTAT+= \
    $(TOOLS-CONFIG) \
    common/aarch64-rpi4-4k-ee

TOOLS-UC-Magic-Link-Sensor+=$(TOOLS-CONFIG)

# Project target

$(eval $(call ProductImage,UC-Plug-US,FCD_$(PRD)_UC-Plug-US_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-Plug-EU,FCD_$(PRD)_UC-Plug-EU_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-Wall-Outlet-US,FCD_$(PRD)_UC-Plug-EU_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-Plug-Dual-US,FCD_$(PRD)_UC-Plug-US_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-7,FCD_$(PRD)_UC-DISPLAY-7_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-13,FCD_$(PRD)_UC-DISPLAY-13_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-21,FCD_$(PRD)_UC-DISPLAY-21_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-27,FCD_$(PRD)_UC-DISPLAY-27_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LVDU-4-24,FCD_$(PRD)_LVDU-4-24_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LVDU-4,FCD_$(PRD)_LVDU-4_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LVDU-24,FCD_$(PRD)_LVDU-24_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LVDU-1,FCD_$(PRD)_LVDU-1_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-THERMOSTAT,FCD_$(PRD)_UC-THERMOSTAT_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-Magic-Link-Sensor,FCD_$(PRD)_UC-Magic-Link-Sensor_$(VER)_$(FWVER)))


# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UC-Plug-US,FCD_$(PRD)_UC-Plug-US_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-Plug-EU,FCD_$(PRD)_UC-Plug-EU_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-Wall-Outlet-US,FCD_$(PRD)_UC-Plug-EU_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-Plug-Dual-US,FCD_$(PRD)_UC-Plug-US_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-7,FCD_$(PRD)_UC-DISPLAY-7_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-13,FCD_$(PRD)_UC-DISPLAY-13_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-21,FCD_$(PRD)_UC-DISPLAY-21_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-27,FCD_$(PRD)_UC-DISPLAY-27_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LVDU-4-24,FCD_$(PRD)_LVDU-4-24_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LVDU-4,FCD_$(PRD)_LVDU-4_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LVDU-24,FCD_$(PRD)_LVDU-24_$(VER)_$(FWVER)))

$(eval $(call ProductCompress,LVDU-1,FCD_$(PRD)_LVDU-1_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-THERMOSTAT,FCD_$(PRD)_UC-THERMOSTAT_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ULED-Instant,FCD_$(PRD)_ULED-Instant_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ULED-Bulb,FCD_$(PRD)_ULED-Bulb_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-Magic-Link-Sensor,FCD_$(PRD)_UC-Magic-Link-Sensor_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00997_ec5a))
$(eval $(call ProductCompress2,01025_ec5b))
$(eval $(call ProductCompress2,01013_ec5c))
$(eval $(call ProductCompress2,01020_ec5d))
$(eval $(call ProductCompress2,03168_ef80))
$(eval $(call ProductCompress2,03182_ef81))
$(eval $(call ProductCompress2,03287_ef83))
$(eval $(call ProductCompress2,03256_ef84))
$(eval $(call ProductCompress2,03383_ef87))
$(eval $(call ProductCompress2,03396_ef88))
$(eval $(call ProductCompress2,UC_DISPLAY-SERIES))
$(eval $(call ProductCompress2,03232_ec47))
$(eval $(call ProductCompress2,03777_ec47))
$(eval $(call ProductCompress2,UC_THERMOSTAT-SERIES))
$(eval $(call ProductCompress2,03076_ec3d))
$(eval $(call ProductCompress2,03548_ec4c))
$(eval $(call ProductCompress2,03435_ec48))
$(eval $(call ProductCompress2,03710_ec48))
$(eval $(call ProductCompress2,03634_ec4a))
$(eval $(call ProductCompress2,03634_ec4b))
$(eval $(call ProductCompress2,03471_ef90))
$(eval $(call ProductCompress2,03564_ec0e))
$(eval $(call ProductCompress2,EV_CHARGER-SERIES))
$(eval $(call ProductCompress2,03279_ec1e))
$(eval $(call ProductCompress2,03119_ec41))
$(eval $(call ProductCompress2,03523_ec80))
$(eval $(call ProductCompress2,04101_efa1))
$(eval $(call ProductCompress2,04143_ef83))
$(eval $(call ProductCompress2,04231_a923))