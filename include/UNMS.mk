
# Images

IMAGE-UNMS-R-PRO= \
    images/ee6a* \
    unms-fw/ubnt_unmsr_rev1_boot.img \
    unms-fw/UNMSR.* \

IMAGE-UNMS-S-LITE= \
    images/eed0* \
    unms-fw/diag_unms_s_lite_0.0.1.bix \
    unms-fw/u-boot_unms_s_lite_0.0.1.bin \

IMAGE-UNMS-R-LITE= \
    images/ee6b* \
    unms-fw/UNMSR.mt7621.* \

IMAGE-UNMS+=$(IMAGE-UNMS-R-PRO)
IMAGE-UNMS+=$(IMAGE-UNMS-S-LITE)
IMAGE-UNMS+=$(IMAGE-UNMS-R-LITE)
# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UbiquitiNMS
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UNMS+=$(TOOLS-CONFIG)

TOOLS-UNMS-R-PRO=$(TOOLS-UNMS)
TOOLS-UNMS-R-PRO+= unms-rpro/*

TOOLS-UNMS-S-LITE=$(TOOLS-UNMS)
TOOLS-UNMS-S-LITE+= unms-slite/*

TOOLS-UNMS-R-LITE=$(TOOLS-UNMS)
TOOLS-UNMS-R-LITE+= unms_rlite/*

# Project target

$(eval $(call ProductImage,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNMS-R-PRO,FCD_$(PRD)_UNMS-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNMS-R-LITE,FCD_$(PRD)_UNMS-R-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductImage,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNMS-R-PRO,FCD_$(PRD)_UNMS-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNMS-R-LITE,FCD_$(PRD)_UNMS-R-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
