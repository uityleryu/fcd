
# Images

IMAGE-UISP-R-PRO= \
    images/ee6a* \
    images/ee6d* \
    unms-fw/ubnt_uispr_alpinev2_rev1_boot* \
    unms-fw/UISPR.alpine* \

IMAGE-ee6a=$(IMAGE-UISP-R-PRO)

# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
IMAGE-UNMS-S-LITE= \
    images/eed0* \
    unms-fw/UNMS-S-Lite.realtek838x.diag_1.1.2.bix \
    unms-fw/UNMS-S-Lite.uboot_1.1.0.bin \

IMAGE-eed0=$(IMAGE-UNMS-S-LITE)

IMAGE-UISP-S-LITE= \
    images/ee50* \
    unms-fw/DIAG_UISP_S_Lite_1.3.4.5.vmlinux.bix \
    unms-fw/UISP-S-Lite.uboot_1.2.1.bin \

IMAGE-ee50=$(IMAGE-UISP-S-LITE)

IMAGE-UISP-R-LITE= \
    images/ee6b* \
    unms-fw/UISPR.mt7621* \

IMAGE-ee6b=$(UISP-R-LITE)

IMAGE-UISP-LTE= \
    images/dca2* \
    images/dca3* \
    unms-fw/LL.qca956x.* \
    unms-fw/uisp-lte-initramfs-64MB.img \

IMAGE-dca2=$(IMAGE-UISP-LTE)

IMAGE-UISP-S-PRO= \
    images/eed1* \
    unms-fw/DIAG_UISP_S_Pro_1.3.5-DEV03.vmlinux.bix \
    unms-fw/u-boot-uisp-s-pro_1.3.0.bin

IMAGE-UISP-O-LITE= \
    images/ee6c* \
    unms-fw/UISPO.mt7621.* \

IMAGE-UISP-R-PRO-XG= \
    images/ee6d* \
    unms-fw/ubnt_uispr_alpinev2_rev1_boot* \
    unms-fw/UISPR.alpine* \

IMAGE-UISP-O-PRO= \
    images/eed3* \
    unms-fw/DIAG_UISP_O_Pro_1.3.4.7.8-Dev03.vmlinux.bix \
    unms-fw/UISP_O_PRO_Pre_u-boot-60495.bin

IMAGE-UISP-S-MICRO= \
    images/ee6f* \
    unms-fw/DIAG_UISP_S_Micro_1.3.6.vmlinux.bix \
    unms-fw/UISP-S-Micro.uboot_1.2.4-737d.bin \

IMAGE-ee6f=$(IMAGE-UISP-S-MICRO)

IMAGE-UISP-R-Micro= \
    images/ee6e* \
    unms-fw/UISPR.mt7621* \

IMAGE-UNMS+=$(IMAGE-UISP-R-PRO)
IMAGE-UNMS+=$(IMAGE-UNMS-S-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-S-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-R-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-LTE)
IMAGE-UNMS+=$(IMAGE-UISP-S-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-O-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-R-PRO-XG)
IMAGE-UNMS+=$(IMAGE-UISP-O-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-S-MICRO)


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

TOOLS-UISP-R-PRO=$(TOOLS-UNMS)
TOOLS-UISP-R-PRO+= uisp-r-pro/*

TOOLS-UNMS-S-LITE=$(TOOLS-UNMS)
TOOLS-UNMS-S-LITE+= unms-slite/*

TOOLS-UISP-S-LITE=$(TOOLS-UNMS)
TOOLS-UISP-S-LITE+= unms-slite/*

TOOLS-UISP-R-LITE=$(TOOLS-UNMS)
TOOLS-UISP-R-LITE+= uisp-r-lite/*

TOOLS-UISP-LTE=$(TOOLS-UNMS)
TOOLS-UISP-LTE+= unms-lte/*

TOOLS-UISP-S-PRO=$(TOOLS-UNMS)
TOOLS-UISP-S-PRO+= unms-spro/*

TOOLS-UISP-O-LITE=$(TOOLS-UNMS)
TOOLS-UISP-O-LITE+= uisp-o-lite/*

TOOLS-UISP-R-PRO-XG=$(TOOLS-UNMS)
TOOLS-UISP-R-PRO-XG+= uisp-r-pro-xg/*

TOOLS-UISP-O-PRO=$(TOOLS-UNMS)
TOOLS-UISP-O-PRO+= unms-spro/*

TOOLS-UISP-S-MICRO=$(TOOLS-UNMS)
TOOLS-UISP-S-MICRO+= unms-slite/*

TOOLS-ee6f=$(TOOLS-UNMS)
TOOLS-ee6f+= unms-slite/*

TOOLS-UISP-R-Micro=$(TOOLS-UNMS)
TOOLS-UISP-R-Micro+= uisp-r-lite/helper_MT7621_release

# Project target
$(eval $(call ProductImage,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-R-PRO,FCD_$(PRD)_UISP-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-R-LITE,FCD_$(PRD)_UISP-R-LITE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductImage,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-PRO,FCD_$(PRD)_UISP-S-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-R-PRO-XG,FCD_$(PRD)_UISP-R-PRO-XG_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-O-PRO,FCD_$(PRD)_UISP-O-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-MICRO,FCD_$(PRD)_UISP-S-MICRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-R-Micro,FCD_$(PRD)_UISP-R-Micro_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-R-PRO,FCD_$(PRD)_UISP-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-R-LITE,FCD_$(PRD)_UISP-R-LITE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductCompress,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-PRO,FCD_$(PRD)_UISP-S-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-R-PRO-XG,FCD_$(PRD)_UISP-R-PRO-XG_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-O-PRO,FCD_$(PRD)_UISP-O-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-MICRO,FCD_$(PRD)_UISP-S-MICRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ee6f,FCD_$(PRD)_ee6f_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-R-Micro,FCD_$(PRD)_UISP-R-Micro_$(VER)_$(FWVER)))
