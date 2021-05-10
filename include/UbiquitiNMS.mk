
# Images
IMAGE-UISP-P-LITE= \
    images/eefa* \
    unms-fw/UISP-P-Lite.bin \
    unms-fw/u-boot-ar933x-ep.bin \
    unms-fw/uisp_p_lite_epx_cfg.bin \
    unms-fw/UISPP* \

IMAGE-UISP-CONSOLE= \
    images/ee6a* \
    unms-fw/ubnt_uispr_alpinev2_rev1_boot* \
    unms-fw/UISPR.alpine* \

IMAGE-UISP-LTE= \
    images/dca2* \
    images/dca3* \
    unms-fw/LL.qca956x.* \
    unms-fw/uisp-lte-initramfs-64MB.img \

IMAGE-UISP-S-PRO= \
    images/eed1* \
    unms-fw/DIAG_UISP_S_Pro_1.3.5-DEV03.vmlinux.bix \
    unms-fw/u-boot-uisp-s-pro_1.3.0.bin

IMAGE-UISP-O-LITE= \
    images/ee6c* \
    unms-fw/UISPO.mt7621.* \

IMAGE-UISP-O-PRO= \
    images/eed3* \
    unms-fw/DIAG_UISP_O_Pro_1.3.4.7.8-Dev03.vmlinux.bix \
    unms-fw/UISP_O_PRO_Pre_u-boot-60495.bin

IMAGE-UISP-R= \
    images/ee6e* \
    unms-fw/UISPR.mt7621* \

IMAGE-UNMS+=$(IMAGE-UISP-CONSOLE)
IMAGE-UNMS+=$(IMAGE-UISP-LTE)
IMAGE-UNMS+=$(IMAGE-UISP-S-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-O-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-O-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-S-MICRO)
IMAGE-UNMS+=$(IMAGE-UISP-R)
IMAGE-UNMS+=$(IMAGE-UISP-P-LITE)

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

TOOLS-UISP-CONSOLE=$(TOOLS-UNMS)
TOOLS-UISP-CONSOLE+= uisp-console/helper_AL324_release

TOOLS-UNMS-S-LITE=$(TOOLS-UNMS)
TOOLS-UNMS-S-LITE+= unms-slite/*

TOOLS-UISP-S-LITE=$(TOOLS-UNMS)
TOOLS-UISP-S-LITE+= unms-slite/*

TOOLS-UISP-LTE=$(TOOLS-UNMS)
TOOLS-UISP-LTE+= unms-lte/*

TOOLS-UISP-S-PRO=$(TOOLS-UNMS)
TOOLS-UISP-S-PRO+= unms-spro/*

TOOLS-UISP-O-LITE=$(TOOLS-UNMS)
TOOLS-UISP-O-LITE+= uisp-o-lite/*

TOOLS-UISP-O-PRO=$(TOOLS-UNMS)
TOOLS-UISP-O-PRO+= unms-spro/*

TOOLS-UISP-R=$(TOOLS-UNMS)
TOOLS-UISP-R+= uisp-r/helper_MT7621_release

TOOLS-UISP-P-LITE=$(TOOLS-UNMS)
TOOLS-UISP-P-LITE+= uisp-p-lite/*

# Project target
$(eval $(call ProductImage,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-CONSOLE,FCD_$(PRD)_UISP-CONSOLE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductImage,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-PRO,FCD_$(PRD)_UISP-S-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-O-PRO,FCD_$(PRD)_UISP-O-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-R,FCD_$(PRD)_UISP-R_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-P-LITE,FCD_$(PRD)_UISP-P-LITE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-CONSOLE,FCD_$(PRD)_UISP-CONSOLE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductCompress,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-PRO,FCD_$(PRD)_UISP-S-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-O-PRO,FCD_$(PRD)_UISP-O-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ee6f,FCD_$(PRD)_ee6f_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-R,FCD_$(PRD)_UISP-R_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-P-LITE,FCD_$(PRD)_UISP-P-LITE_$(VER)_$(FWVER)))

# ==================================================================================================

IMAGE-00973-ee6a=$(IMAGE-UISP-CONSOLE)
IMAGE-dca2=$(IMAGE-UISP-LTE)

# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
IMAGE-00900-ee50=\
    images/ee50* \
    unms-fw/DIAG_UISP_S_Lite_1.3.4.5.vmlinux.bix \
    unms-fw/UISP-S-Lite.uboot_1.2.1.bin \

IMAGE-00817-eed0=\
    images/eed0* \
    unms-fw/UNMS-S-Lite.realtek838x.diag_1.1.2.bix \
    unms-fw/UNMS-S-Lite.uboot_1.1.0.bin \

# UISP-S
IMAGE-00988-ee6f= \
    images/ee6f* \
    unms-fw/DIAG_UISP_S_1.3.6_DEV05.vmlinux.bix \
    unms-fw/u-boot-1.3.0-c174.bin \

# ---------------------------------------------------------------------------------------------------

TOOLS-00988-ee6f=$(TOOLS-UNMS)
TOOLS-00988-ee6f+= unms-slite/*

TOOLS-00817-eed0=$(TOOLS-UNMS)
TOOLS-00817-eed0+=unms-slite/*

TOOLS-00900-ee50=$(TOOLS-UNMS)
TOOLS-00900-ee50+=unms-slite/*

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00817-eed0))
$(eval $(call ProductCompress2,00900-ee50))
$(eval $(call ProductCompress2,00988-ee6f))
