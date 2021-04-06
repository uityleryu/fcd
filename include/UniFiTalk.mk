
# Images

IMAGE-UT-PHONE-FLEX= \
    images/ef0d* \
    uvp-fw/uvp-flex_1.0.13.bin.unsign

IMAGE-UT-ATA= \
    images/ef0f* \
    uvp-fw/uvp-flex_1.0.13.bin.unsign

IMAGE-UT-PHONE-TOUCH=
IMAGE-UT-PHONE-TOUCHMAX=

IMAGE-UT-CONFERENCE=

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiTalk
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UT-PHONE-FLEX=$(TOOLS-CONFIG)
TOOLS-UT-PHONE-FLEX+= uvp/*

TOOLS-UT-ATA=$(TOOLS-CONFIG)
TOOLS-UT-ATA+= uvp/*

TOOLS-UT-CONFERENCE=$(TOOLS-CONFIG)
TOOLS-UT-CONFERENCE+= uvp/*

TOOLS-UT-PHONE-TOUCH=$(TOOLS-CONFIG)
TOOLS-UT-PHONE-TOUCHMAX=$(TOOLS-CONFIG)

# Project target

$(eval $(call ProductImage,UT-PHONE-FLEX,FCD_$(PRD)_UT-PHONE-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UT-ATA,FCD_$(PRD)_UT-ATA_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UT-PHONE-TOUCH,FCD_$(PRD)_UT-PHONE-TOUCH_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UT-PHONE-TOUCHMAX,FCD_$(PRD)_UT-PHONE-TOUCHMAX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UT-CONFERENCE,FCD_$(PRD)_UT-CONFERENCE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UT-PHONE-FLEX,FCD_$(PRD)_UT-PHONE-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UT-ATA,FCD_$(PRD)_UT-ATA_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UT-PHONE-TOUCH,FCD_$(PRD)_UT-PHONE-TOUCH_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UT-PHONE-TOUCHMAX,FCD_$(PRD)_UT-PHONE-TOUCHMAX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UT-CONFERENCE,FCD_$(PRD)_UT-CONFERENCE_$(VER)_$(FWVER)))

# ==================================================================================================

IMAGE-ef0d= \
    images/ef0d* \
    uvp-fw/uvp-flex_1.0.13.bin.unsign

IMAGE-ef0f= \
    images/ef0f* \
    uvp-fw/uvp-flex_1.0.13.bin.unsign

IMAGE-ef12=

# -----------------------------------------------------------------------------------------

TOOLS-ef0d=$(TOOLS-CONFIG)
TOOLS-ef0d+= uvp/*

TOOLS-ef0f=$(TOOLS-CONFIG)
TOOLS-ef0f+= uvp/*

TOOLS-ef12=$(TOOLS-CONFIG)
TOOLS-ef12+= uvp/helper_DVF99_release_ata_max

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,ef0d,FCD_$(PRD)_ef0d_$(VER)_$(FWVER),$(ALL)))
$(eval $(call ProductCompress2,ef0f,FCD_$(PRD)_ef0f_$(VER)_$(FWVER),$(ALL)))
$(eval $(call ProductCompress2,ef12,FCD_$(PRD)_ef12_$(VER)_$(FWVER),$(ALL)))
