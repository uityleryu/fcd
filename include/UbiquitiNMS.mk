
# Images

IMAGE-UNMS-R-PRO= \
    images/ee6a* \
    unms-fw/ubnt_unmsr_rev1_boot.img \
    unms-fw/UNMSR.* \

# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
IMAGE-UNMS-S-LITE= \
    images/eed0* \
    unms-fw/UNMS-S-Lite.realtek838x.diag_1.1.2.bix \
    unms-fw/UNMS-S-Lite.uboot_1.1.0.bin \

IMAGE-UISP-S-LITE= \
    images/ee50* \
    unms-fw/DIAG_UISP_S_Lite_1.3.4.5.vmlinux.bix \
    unms-fw/UISP-S-Lite.uboot_1.2.1.bin \

IMAGE-UNMS-R-LITE= \
    images/ee6b* \
    unms-fw/UNMSR.mt7621.* \

IMAGE-UNMS-LTE= \
    images/dca2* \
    images/dca3* \
    unms-fw/LL.qca956x.* \
    unms-fw/unms-lte-initramfs-64MB.img \

IMAGE-UNMS-S-PRO= \
    images/eed1* \
    unms-fw/UNMS-S-Pro.realtek930x.diag_1.3.1.bix \
    unms-fw/UNMS-S-Pro.realtek930x.uboot_1.1.0-6fb76.bin \

IMAGE-UISP-O-LITE= \
    images/ee6c* \
    unms-fw/UISPO.mt7621.* \

IMAGE-UNMS+=$(IMAGE-UNMS-R-PRO)
IMAGE-UNMS+=$(IMAGE-UNMS-S-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-S-LITE)
IMAGE-UNMS+=$(IMAGE-UNMS-R-LITE)
IMAGE-UNMS+=$(IMAGE-UNMS-LTE)
IMAGE-UNMS+=$(IMAGE-UNMS-S-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-O-LITE)


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

TOOLS-UISP-S-LITE=$(TOOLS-UNMS)
TOOLS-UISP-S-LITE+= unms-slite/*

TOOLS-UNMS-R-LITE=$(TOOLS-UNMS)
TOOLS-UNMS-R-LITE+= unms-rlite/*

TOOLS-UNMS-LTE=$(TOOLS-UNMS)
TOOLS-UNMS-LTE+= unms-lte/*

TOOLS-UNMS-S-PRO=$(TOOLS-UNMS)
TOOLS-UNMS-S-PRO+= unms-spro/*

TOOLS-UISP-O-LITE=$(TOOLS-UNMS)
TOOLS-UISP-O-LITE+= uisp-olite/*

# Project target
$(eval $(call ProductImage,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNMS-R-PRO,FCD_$(PRD)_UNMS-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNMS-R-LITE,FCD_$(PRD)_UNMS-R-LITE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductImage,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNMS-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNMS-S-PRO,FCD_$(PRD)_UNMS-S-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNMS-R-PRO,FCD_$(PRD)_UNMS-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNMS-R-LITE,FCD_$(PRD)_UNMS-R-LITE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductCompress,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNMS-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNMS-S-PRO,FCD_$(PRD)_UNMS-S-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))

