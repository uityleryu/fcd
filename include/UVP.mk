
# Images

IMAGE-UVP-FLEX= \
    images/ef0d* \
    uvp-fw/uvp-flex_1.0.13.bin.unsign

IMAGE-UVP-ATA=

IMAGE-UVP-CONF-SPK=

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiVOIP
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UVP-FLEX+=$(TOOLS-CONFIG)
TOOLS-UVP-FLEX+= uvp/*

TOOLS-UVP-ATA+=$(TOOLS-CONFIG)
# TOOLS-UVP-ATA+=

TOOLS-UVP-CONF-SPK+=$(TOOLS-CONFIG)
TOOLS-UVP-CONF-SPK+= uvp/*

# Project target

$(eval $(call ProductImage,UVP-FLEX,FCD_$(PRD)_UVP-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVP-ATA,FCD_$(PRD)_UVP-ATA_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVP-CONF-SPK,FCD_$(PRD)_UVP-CONF-SPK_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UVP-FLEX,FCD_$(PRD)_UVP-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVP-ATA,FCD_$(PRD)_UVP-ATA_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVP-CONF-SPK,FCD_$(PRD)_UVP-CONF-SPK_$(VER)_$(FWVER)))
